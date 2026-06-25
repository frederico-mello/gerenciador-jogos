## ADDED Requirements

### Requirement: Wrapper para invocação de scripts administrativos como o usuário da aplicação

O sistema SHALL fornecer um script `scripts/run-as-app.sh` (bash) que executa um script Python arbitrário passado como argumento usando o interpretador do venv do projeto, como o usuário `www-data` (via `sudo -u www-data`), derivando o diretório-raiz do projeto a partir da localização do próprio wrapper (não hardcoded).

#### Scenario: Invocação canônica de script administrativo
- **WHEN** um operador executa `./scripts/run-as-app.sh scripts/create_admin.py` no servidor de produção
- **THEN** o wrapper invoca `sudo -u www-data "$APP_DIR/venv/bin/python" scripts/create_admin.py`, onde `$APP_DIR` é resolvido como o diretório-pai do diretório que contém o wrapper

#### Scenario: Argumentos do script são repassados
- **WHEN** um operador executa `./scripts/run-as-app.sh scripts/create_admin.py --nome "Alice" --email a@b.c --senha "123"`
- **THEN** todos os argumentos após o nome do script são repassados intactos ao Python

#### Scenario: Wrapper funciona independente do path de produção
- **WHEN** o projeto está clonado em `/opt/meu-staging/gerenciador-jogos` e o operador executa `./scripts/run-as-app.sh scripts/init_db.py` a partir desse clone
- **THEN** o wrapper resolve `APP_DIR=/opt/meu-staging/gerenciador-jogos` e usa `/opt/meu-staging/gerenciador-jogos/venv/bin/python`, sem depender de path hardcoded

#### Scenario: Falha explícita quando sudo não está disponível
- **WHEN** o wrapper é executado e o `sudo` não consegue escalar para `www-data` (ex.: usuário sem permissão sudo)
- **THEN** o wrapper termina com código não-zero, propagando a mensagem de erro do `sudo` (sem swallowing silencioso)

### Requirement: Guarda de usuário com falha rápida e mensagem acionável em scripts administrativos

Cada script administrativo (`scripts/create_admin.py`, `scripts/init_db.py`, `scripts/import_from_downloads.py`) SHALL verificar, antes de qualquer import da aplicação ou chamada a `init_db()`/`create_app()`, que está sendo executado como o usuário `www-data`, terminando com código de saída não-zero e mensagem indicando o uso do wrapper caso contrário.

#### Scenario: Script invocado por usuário não-www-data falha com mensagem acionável
- **WHEN** um usuário que não seja `www-data` (ex.: `frederico`) executa `python scripts/create_admin.py`
- **THEN** o script termina imediatamente com código de saída 1 e imprime uma mensagem em stderr mencionando o uso de `./scripts/run-as-app.sh scripts/create_admin.py`, sem executar `init_db()`, `create_app()`, nem qualquer acesso a `.env` ou banco de dados

#### Scenario: Script invocado via wrapper como www-data prossegue normalmente
- **WHEN** o script é executado via `./scripts/run-as-app.sh scripts/create_admin.py`
- **THEN** o guarda detecta usuário `www-data` e permite que o script continue sua execução normal (prompt por credenciais, criação de admin, etc.)

#### Scenario: Guarda executa antes de qualquer side-effect persistente
- **WHEN** um usuário não-`www-data` executa o script
- **THEN** nenhum arquivo é criado ou modificado em `instance/` ou `data/` (em particular, `init_db()` não é chamado, evitando criação de `jogos.db` com owner errado)

#### Scenario: Comportamento funcional dos scripts é preservado
- **WHEN** qualquer um dos três scripts administrativos é executado como `www-data` (diretamente ou via wrapper)
- **THEN** seu comportamento funcional (criar admin, inicializar banco, importar jogos) é idêntico ao comportamento anterior a esta mudança

### Requirement: Documentação no README sobre scripts administrativos em produção

O `README.md` SHALL incluir uma seção documentando que scripts administrativos em produção devem ser invocados via `scripts/run-as-app.sh`, com a justificativa (ownership de `.env`, `instance/`, `data/` pelo usuário `www-data`) e exemplos para cada um dos três scripts.

#### Scenario: Seção presente e indexada
- **WHEN** um operador lê o `README.md`
- **THEN** encontra uma seção "Scripts administrativos em produção" (ou título equivalente) listando os três scripts e o comando canônico para cada um via `run-as-app.sh`

#### Scenario: Justificativa do ownership é explicada
- **WHEN** um operador lê a seção
- **THEN** a documentação explica que `.env`, `instance/`, e `data/` pertencem a `www-data` em produção, e que rodar scripts como outro usuário causa erros de permissão e/ou ownership incorreto de arquivos
