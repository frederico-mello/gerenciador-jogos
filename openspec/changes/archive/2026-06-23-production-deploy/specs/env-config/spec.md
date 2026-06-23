## MODIFIED Requirements

### Requirement: Carregar variáveis de ambiente de arquivo .env
A aplicação Flask SHALL carregar variáveis de ambiente a partir de um arquivo `.env` na raiz do projeto, quando presente, sem sobrescrever variáveis de ambiente já definidas.

#### Scenario: .env presente com FLASK_SECRET_KEY
- **WHEN** o arquivo `.env` existe na raiz do projeto contendo `FLASK_SECRET_KEY=chave-secreta`
- **THEN** a aplicação utiliza `chave-secreta` como `SECRET_KEY` e não emite warning de chave dev insegura

#### Scenario: Variável de ambiente tem prioridade sobre .env
- **WHEN** a variável de ambiente `FLASK_SECRET_KEY` está definida como `ambiente-secreta`
- **AND** o arquivo `.env` contém `FLASK_SECRET_KEY=arquivo-secreta`
- **THEN** a aplicação utiliza `ambiente-secreta` como `SECRET_KEY`

#### Scenario: Ausência de .env e de variável de ambiente
- **WHEN** não há arquivo `.env` nem variável de ambiente `FLASK_SECRET_KEY`
- **THEN** a aplicação utiliza a chave dev insegura e emite warning

#### Scenario: FLASK_ENV=production sem SECRET_KEY definida
- **WHEN** `FLASK_ENV=production` está definida e `FLASK_SECRET_KEY` não está definida ou está vazia
- **THEN** a aplicação recusa iniciar e imprime erro "FLASK_SECRET_KEY é obrigatória em produção"

#### Scenario: FLASK_ENV=production com SECRET_KEY curta
- **WHEN** `FLASK_ENV=production` está definida e `FLASK_SECRET_KEY` tem menos de 32 caracteres
- **THEN** a aplicação recusa iniciar e imprime erro "FLASK_SECRET_KEY deve ter pelo menos 32 caracteres em produção"

#### Scenario: FLASK_ENV=production com SECRET_KEY válida
- **WHEN** `FLASK_ENV=production` está definida e `FLASK_SECRET_KEY` tem 32+ caracteres
- **THEN** a aplicação utiliza a chave definida e não emite warning

## ADDED Requirements

### Requirement: Variáveis de ambiente de produção
O sistema SHALL suportar as seguintes variáveis de ambiente para configuração de produção: `FLASK_ENV` (development/production), `GUNICORN_WORKERS` (número de workers, default: `2 * cores + 1`), `GUNICORN_BIND` (bind address, default: `unix:/run/gunicorn.sock`).

#### Scenario: Valores default quando variáveis não definidas
- **WHEN** `GUNICORN_WORKERS` e `GUNICORN_BIND` não estão definidas
- **THEN** o Gunicorn usa `2 * cores + 1` workers e escuta no socket `/run/gunicorn.sock`

#### Scenario: Valores customizados via variáveis
- **WHEN** `GUNICORN_WORKERS=8` e `GUNICORN_BIND=0.0.0.0:9000` estão definidas
- **THEN** o Gunicorn usa 8 workers e escuta na porta 9000 em TCP

## REMOVED Requirements

*(nenhum)*
