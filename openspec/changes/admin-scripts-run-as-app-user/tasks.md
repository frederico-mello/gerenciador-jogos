## 1. Wrapper script

- [x] 1.1 Criar `scripts/run-as-app.sh` com shebang `#!/usr/bin/env bash`, `set -euo pipefail`, que derive `APP_DIR` via `$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)` e faça `exec sudo -u www-data "$APP_DIR/venv/bin/python" "$@"`
- [x] 1.2 Tornar o wrapper executável (`chmod +x scripts/run-as-app.sh`) — feito via `git update-index --chmod=+x` (Windows não tem chmod; bit 0755 confirmado em `git ls-files -s`)
- [ ] 1.3 Verificar manualmente em ambiente Linux (ou via WSL) que `./scripts/run-as-app.sh scripts/init_db.py` resolve o caminho do venv corretamente quando o projeto está em `/opt/gerenciador-jogos` e quando está em outro diretório (cenário "Wrapper funciona independente do path de produção") — **pendente verificação do usuário (ambiente Windows aqui)**

## 2. Guarda de usuário nos 3 scripts administrativos

- [x] 2.1 Adicionar no topo de `scripts/create_admin.py` (antes de qualquer import do app ou de `init_db()`) o guarda usando `getpass.getuser()` comparado a `"www-data"`, com `sys.exit(1)` e mensagem em stderr apontando para `./scripts/run-as-app.sh scripts/create_admin.py`
- [x] 2.2 Adicionar o mesmo guarda (com o nome do script correto na mensagem) em `scripts/init_db.py`, antes de qualquer import do app
- [x] 2.3 Adicionar o mesmo guarda (com o nome do script correto na mensagem) em `scripts/import_from_downloads.py`, antes de qualquer import do app
- [x] 2.4 Garantir que o guarda lida com Windows gracefully: em Windows (`os.name == "nt"`), o `getpass.getuser()` retorna o usuário Windows (não há `www-data`); o guarda deve imprimir uma mensagem indicando "em desenvolvimento local Windows, comente o guarda ou use o wrapper Linux/WSL" em vez de crashar de forma confusa. Capturar essa lógica num bloco condicional no guarda. — **implementado em todos os 3 scripts: branch `if os.name == "nt":` escreve warning em stderr e continua (não faz sys.exit)**

## 3. Validação do guarda

- [ ] 3.1 Confirmar que rodando como não-`www-data` (ex.: usuário normal em Linux/WSL), `python scripts/create_admin.py` termina com exit code 1 e a mensagem esperada, SEM criar nenhum arquivo em `instance/` ou `data/` (cenário "Guarda executa antes de qualquer side-effect persistente")
- [ ] 3.2 Confirmar que rodando como `www-data` (via wrapper ou `sudo -u www-data`), `scripts/create_admin.py` prossegue além do guarda e chega no prompt de credenciais (cenário "Script invocado via wrapper como www-data prossegue normalmente")
- [ ] 3.3 Confirmar que o comportamento funcional dos 3 scripts executados como `www-data` é idêntico ao anterior (rodar cada um e validar output esperado) (cenário "Comportamento funcional dos scripts é preservado")

## 4. Documentação

- [x] 4.1 Adicionar seção "Scripts administrativos em produção" no `README.md` (na seção de deploy/produção) explicando: (a) que `.env`, `instance/`, `data/` pertencem a `www-data`, (b) que rodar como outro usuário causa erro de permissão e/ou ownership incorreto, (c) o comando canônico via `./scripts/run-as-app.sh` para cada um dos 3 scripts

## 5. Sanidade de pré-existente (verificar landmine já disparado)

- [x] 5.1 Documentar no PR/comunicação ao operador que verifique `ls -la /opt/gerenciador-jogos/instance/` no servidor — se `jogos.db` existir com owner diferente de `www-data:www-data` (resquício de execução anterior falha do script), rodar `sudo chown www-data:www-data instance/jogos.db` antes/depois do deploy. (Não é código; é runbook.) — **capturado como sub-seção "Runbook" dentro da nova seção do README**

## 6. Verificação final

- [x] 6.1 Rodar a suíte de testes existente (`python -m pytest`) para garantir que nenhuma mudança em `scripts/` quebrou testes que importam esses scripts — **134 passed, 1 skipped (48s)**
- [x] 6.2 Revisar diff final: confirmar que `app/__init__.py` permanece intocado (decisão explícita de não mexer em `load_dotenv`) — **`git diff HEAD -- app/__init__.py` vazio, confirmado intocado**
