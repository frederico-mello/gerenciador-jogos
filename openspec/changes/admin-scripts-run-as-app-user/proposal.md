## Why

Os scripts administrativos (`scripts/create_admin.py`, `scripts/init_db.py`, `scripts/import_from_downloads.py`) quebram com `PermissionError` quando executados diretamente por um usuário não-`www-data`, porque `.env` (modo 640) e os diretórios `instance/` e `data/` pertencem ao usuário `www-data` (modelo de deploy definido em `deploy/setup.sh` e `deploy/gunicorn.service`). O problema é pior do que parece: como `init_db()` é chamado antes de `create_app()` em `create_admin.py`, o `instance/jogos.db` pode ser criado com owner errado (ex.: `frederico:frederico`), fazendo o Gunicorn (que roda como `www-data`) quebrar em produção com um erro silencioso e diferido de permissão no banco.

Precisamos de uma forma canônica de invocar esses scripts — como o usuário correto (`www-data`) — e de erros amigáveis quando alguém tentar rodá-los do jeito errado, em vez do traceback cryptic do `dotenv` 5 níveis abaixo.

## What Changes

- **Adicionar** `scripts/run-as-app.sh`: wrapper que executa o Python do venv como `www-data`, garantindo leitura de `.env` e ownership correto dos arquivos criados (`instance/jogos.db`, `data/`).
- **Adicionar** guarda de usuário no topo dos 3 scripts administrativos (`create_admin.py`, `init_db.py`, `import_from_downloads.py`): falha fast com mensagem clara indicando usar o wrapper, quando executado por usuário diferente de `www-data`.
- **Atualizar** `README.md` com seção "Scripts administrativos em produção" documentando a invocação via `run-as-app.sh` e porquê.
- **Intencionalmente NÃO alterar** `load_dotenv()` em `app/__init__.py`: o crash atual é um alarme útil (indica "usuário errado"); abafá-lo esconderia o problema de ownership em vez de resolvê-lo.

## Capabilities

### New Capabilities
<!-- Nenhuma. A mudança estende uma capability existente. -->

### Modified Capabilities
- `production-infra`: Adiciona requisitos sobre invocação canônica de scripts administrativos como o usuário `www-data` (via wrapper), guarda de usuário com erro amigável, e documentação no README. A capability já cobre o modelo de usuário `www-data` (systemd, setup.sh); esta mudança fecha o gap dos scripts administrativos que escapam a esse modelo.

## Impact

- **Novos arquivos**: `scripts/run-as-app.sh`.
- **Arquivos modificados**: `scripts/create_admin.py`, `scripts/init_db.py`, `scripts/import_from_downloads.py` (guarda de usuário no topo), `README.md` (nova seção).
- **Sem mudanças em código da aplicação**: `app/__init__.py`, models, routes, db — intocados.
- **Sem mudanças de schema/API**: sem migração de banco, sem novas rotas.
- **Sem novas dependências**: usa apenas stdlib (`os`, `getpass`, `sys`) no guarda e `bash`/`sudo` no wrapper.
- **Retrocompatibilidade**: o comportamento funcional dos scripts é preservado; apenas a forma canônica de invocação muda. Usuários que já os invocavam como `www-data` (ex.: via sudo manual) continuam funcionando.
