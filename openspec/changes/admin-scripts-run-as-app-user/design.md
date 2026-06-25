## Context

Em produção (`/opt/gerenciador-jogos`), o app roda como `www-data` via systemd (`deploy/gunicorn.service`, `User=www-data`). O `deploy/setup.sh` configura ownership:

- `.env` → `www-data:www-data`, modo `640`
- `instance/` → `www-data:www-data`
- `data/` → `www-data:www-data`

Os scripts administrativos (`scripts/create_admin.py`, `scripts/init_db.py`, `scripts/import_from_downloads.py`) escapam a esse modelo quando invocados diretamente por um usuário não-`www-data` (ex.: `frederico`):

1. `PermissionError` ao ler `.env` (em `load_dotenv()`, chamado em `app/__init__.py:15`).
2. **Pior**: `init_db()` em `create_admin.py:40` roda ANTES de `create_app()`, criando `instance/jogos.db` com o owner errado. O Gunicorn (como `www-data`) então falha em produção com erro de permissão no banco — silencioso e diferido.

O sintoma visível (traceback do `dotenv`) é o alarme correto: indica "usuário errado". A solução é fazer a invocação correta ser canônica e fácil, e a invocação errada produzir uma mensagem útil em vez de um traceback cryptic.

## Goals / Non-Goals

**Goals:**
- Tornar a invocação correta de scripts administrativos (como `www-data`) trivial e canônica via um wrapper único.
- Garantir que arquivos criados pelos scripts (`instance/jogos.db`, `data/`) tenham owner `www-data`, compatível com o runtime do Gunicorn.
- Produzir erro amigável e acionável quando alguém tentar rodar um script admin do jeito errado.
- Documentar o padrão no README para futuros operadores.
- Preservar o comportamento funcional existente dos scripts.

**Non-Goals:**
- NÃO modificar `load_dotenv()` em `app/__init__.py` — o crash é um alarme útil.
- NÃO refatorar scripts para Flask CLI commands (`flask create-admin`). Mudança de escopo; mesma raiz (owner errado) exigiria o mesmo wrapper mesmo assim.
- NÃO adicionar suporte a ambientes Windows para o wrapper (`.sh`) — wrapper é para produção Linux; desenvolvimento local Windows continua invocando `python scripts\...` diretamente (não há `.env` locked-down nem usuário `www-data` lá).
- NÃO cobrir outros scripts além dos 3 administrativos identificados.
- NÃO adicionar automação de deploy (ex.: tornar `run-as-app.sh` chamado pelo `setup.sh`).

## Decisions

### Decisão 1: Wrapper único compartilhado, não um por script

**Escolha**: Um único `scripts/run-as-app.sh` que recebe o caminho do script como argumento:
```bash
./scripts/run-as-app.sh scripts/create_admin.py
./scripts/run-as-app.sh scripts/init_db.py
```

**Rationale**: Os 3 scripts compartilham exatamente o mesmo pré-requisito (rodar como `www-data` no venv). Um wrapper único evita drift entre N wrappers e é mais fácil de manter.

**Alternativas consideradas**:
- *Um wrapper por script* (`scripts/create_admin.sh`, etc.): reúsa pouquíssima lógica, multiplica pontos de manutenção. Rejeitado.
- *Documentar apenas o comando `sudo -u www-data venv/bin/python ...` no README*: funciona, mas é fácil esquecer/sintaxe errada; wrapper formaliza o contrato. Rejeitado.

### Decisão 2: `run-as-app.sh` resolve `APP_DIR` a partir do próprio wrapper, não hardcoded

**Escolha**: O wrapper deriva `APP_DIR` via `$(dirname "$(readlink -f "$0")")/..`, em vez de hardcode `/opt/gerenciador-jogos`.

**Rationale**: Funciona tanto em produção (`/opt/gerenciador-jogos`) quanto em clones de dev/staging em outros paths. O venv é resolvido como `$APP_DIR/venv/bin/python`.

**Alternativa considerada**:
- *Hardcode `/opt/gerenciador-jogos`*: casaria com o path de produção documentado, mas quebraria em staging/dev clones. Rejeitado.

### Decisão 3: Guarda de usuário via `getpass.getuser()`, comparando a `www-data`

**Escolha**: No topo de cada script admin (antes de qualquer import do app):
```python
import getpass, sys
if getpass.getuser() != "www-data":
    sys.exit("ERRO: este script deve ser rodado como www-data. Use: ./scripts/run-as-app.sh scripts/<script>.py")
```

**Rationale**:
- `getpass.getuser()` é stdlib, cross-platform, e retorna o usuário real efetivo (funciona sob `sudo -u www-data`).
- Comparar a string fixa `"www-data"` é simples e bate com o usuário definido em `deploy/gunicorn.service`.
- `sys.exit` com mensagem (exit code 1) é fail-fast e óbvio em scripts interativos.
- O check acontece ANTES de `init_db()` ou `create_app()`, evitando tanto o crash do `dotenv` quanto o side-effect do `init_db()` criando DB com owner errado.

**Alternativas consideradas**:
- *Checar `os.geteuid() == 0` (root)*: permissivo demais — root também criaria arquivos com owner errado. Rejeitado.
- *Tolerar `load_dotenv()` falhar e silenciar*: abafa o alarme e piora o problema de ownership (vira falha silenciosa em produção). Rejeitado (vide Decisão 5).
- *Ler usuário esperado de env var*: flexível, mas adiciona configuração que ninguém vai usar. Rejeitado por YAGNI.

### Decisão 4: Guarda em cada script, não num módulo compartilhado

**Escolha**: Repetir as ~3 linhas do guarda literalmente no topo de cada um dos 3 scripts, em vez de extrair para `scripts/_guard_user.py`.

**Rationale**: Scripts admin são standalone (cada um faz `sys.path.insert(...)` próprio e importa do `app`). Importar um helper de `scripts/` adicionaria acoplamento e path-magic. A duplicação é mínima (3 linhas) e o custo de drift é baixo (a mensagem é a mesma). O princípio de DRY não justifica o acoplamento aqui.

**Alternativa considerada**:
- *`scripts/_guard_user.py` compartilhado*: DRY, mas exige manipular `sys.path` extra e quebra o pattern standalone dos scripts. Rejeitado.

### Decisão 5: NÃO tocar em `load_dotenv()` (preservar o alarme)

**Escolha**: `app/__init__.py` permanece inalterado. `load_dotenv()` continua podendo levantar `PermissionError` se o `.env` for ilegível.

**Rationale**: O crash do `dotenv` é um sintoma barulhento e correto — sinaliza "usuário errado". Com o guarda na Decisão 3, o usuário nunca chega ao `load_dotenv()` rodando do jeito errado (o guarda falha antes). Abafar `load_dotenv()` seria defesa em profundância útil apenas se o guarda falhasse silenciosamente — o que não é o caso. Tocar em `load_dotenv()` também mudaria comportamento da aplicação web (caminho não-testado), aumentando blast radius sem benefício real.

**Alternativa considerada**:
- *`try: load_dotenv() except PermissionError: pass`*: defesa em profundência, mas mascararia bugs reais de permissão no runtime web. Rejeitado.

## Risks / Trade-offs

- **[Wrapper depende de `sudo` e do usuário `www-data` existir]** → Wrapper falha claramente se `www-data` não existir ou se o usuário invocador não tiver sudo sem senha. Mitigação: a mensagem de erro do `sudo` é clara; em deploy novo, `www-data` é criado pelo `setup.sh`. Aceitável.
- **[Drift entre as 3 cópias do guarda]** → Se a mensagem do guarda mudar, esquecer um script gera inconsistência. Mitigação: snippets idênticos; qualquer alteração deve varrer os 3 (testes no `tasks.md` cobrem todos). Trade-off aceito em nome da simplicidade (Decisão 4).
- **[Usuário pode burlar o guarda rodando direto como `www-data` via `sudo -u` sem o wrapper]** → O guarda aceita qualquer execução como `www-data`, não apenas via wrapper. Isso é intencional: o guarda valida o *pré-requisito* (usuário certo), não o *meio* (wrapper). Burlar o wrapper mas ainda rodar como `www-data` não causa dano.
- **[Guarda quebra execução em dev local Windows]** → Em Windows não há `www-data`. Mitigação: scripts admin em dev local são raros (dev usa Flask web UI para criar admin via `/admin/users/criar`); para criar admin inicial em dev, o usuário pode temporariamente comentar o guarda ou rodar via wrapper WSL. **Decisão**: o guarda deve falhar graciosamente em Windows com mensagem indicando "ignorar em dev", em vez de crashar com `KeyError` do `getpass`. Detalhe de implementação capturado no `tasks.md`.
- **[Não cobre futuros scripts admin que forem adicionados]** → Quem criar um 4º script pode esquecer o guarda. Mitigação: README documenta o padrão; revisão de PR deve pegar. Trade-off aceito (não justifica metaprogramação).
