## ADDED Requirements

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

## MODIFIED Requirements

*(nenhum)*

## REMOVED Requirements

*(nenhum)*
