## ADDED Requirements

### Requirement: Resetar senha de administrador existente pelo script de bootstrap
O script `scripts/create_admin.py` SHALL detectar quando o email informado já pertence a um usuário com `role='admin_sistema'` e oferecer a opção de resetar a senha desse usuário.

#### Scenario: Admin existe e usuário confirma reset de senha
- **WHEN** o script recebe um email já cadastrado como `admin_sistema`
- **AND** o usuário confirma a opção de reset de senha
- **THEN** o script atualiza o `password_hash` do usuário existente para a nova senha informada
- **AND** o script imprime mensagem confirmando o reset

#### Scenario: Admin existe e usuário cancela
- **WHEN** o script recebe um email já cadastrado como `admin_sistema`
- **AND** o usuário não confirma a opção de reset de senha
- **THEN** o script encerra sem alterar o banco de dados

### Requirement: Promover usuário existente a admin_sistema pelo script de bootstrap
O script `scripts/create_admin.py` SHALL detectar quando o email informado pertence a um usuário com papel diferente de `admin_sistema` e oferecer a opção de promovê-lo a `admin_sistema` e resetar sua senha.

#### Scenario: Usuário comum existe e usuário confirma promoção
- **WHEN** o script recebe um email já cadastrado com papel diferente de `admin_sistema`
- **AND** o usuário confirma a opção de promoção
- **THEN** o script altera o `role` do usuário para `admin_sistema`
- **AND** atualiza o `password_hash` para a nova senha informada
- **AND** o script imprime mensagem confirmando a promoção e reset

#### Scenario: Usuário comum existe e usuário cancela
- **WHEN** o script recebe um email já cadastrado com papel diferente de `admin_sistema`
- **AND** o usuário não confirma a opção de promoção
- **THEN** o script encerra sem alterar o banco de dados

### Requirement: Manter criação de novo administrador quando email não existe
O script `scripts/create_admin.py` SHALL continuar criando um novo usuário `admin_sistema` quando o email informado ainda não está cadastrado.

#### Scenario: Novo email informado
- **WHEN** o script recebe um email que não existe no banco
- **THEN** o script cria um novo usuário com `role='admin_sistema'` e `ativo=1`
- **AND** imprime mensagem confirmando a criação

## MODIFIED Requirements

*(nenhum)*

## REMOVED Requirements

*(nenhum)*
