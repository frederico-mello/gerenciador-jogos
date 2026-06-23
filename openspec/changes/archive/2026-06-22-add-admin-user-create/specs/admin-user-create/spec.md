## ADDED Requirements

### Requirement: Admin accesses creation form
The system SHALL render a user creation form at `GET /admin/users/criar` for admin_sistema users.

#### Scenario: Admin opens creation form
- **WHEN** an admin_sistema user accesses `GET /admin/users/criar`
- **THEN** the system SHALL render `admin_user_create.html` with status 200

#### Scenario: Non-admin gets 403
- **WHEN** a user without admin_sistema role accesses `GET /admin/users/criar`
- **THEN** the system SHALL return status 403

### Requirement: Admin creates user with valid data
The system SHALL create a new user when an admin_sistema submits the creation form with valid data.

#### Scenario: Successful creation
- **WHEN** an admin_sistema submits `POST /admin/users/criar` with valid nome, email, senha, confirmacao, role, and optional escola_id and ativo
- **THEN** the system SHALL create the user via `models.create_user()`, flash "criado" message, and redirect to `/admin/users`

#### Scenario: Created user has correct attributes
- **WHEN** an admin_sistema creates a user with role "admin_jogos", escola_id "1", and ativo "1"
- **THEN** the persisted user SHALL have the specified role, escola_id, and ativo=1

### Requirement: Form validation on creation
The system SHALL validate all required fields and show appropriate error messages.

#### Scenario: Missing nome
- **WHEN** an admin_sistema submits `POST /admin/users/criar` without nome
- **THEN** the system SHALL flash "Nome é obrigatório" and re-render the form with status 400

#### Scenario: Missing email
- **WHEN** an admin_sistema submits `POST /admin/users/criar` without email
- **THEN** the system SHALL flash "Email é obrigatório" and re-render the form with status 400

#### Scenario: Duplicate email
- **WHEN** an admin_sistema submits `POST /admin/users/criar` with an email already in use
- **THEN** the system SHALL flash "Email já cadastrado" and re-render the form with status 400

#### Scenario: Short password
- **WHEN** an admin_sistema submits `POST /admin/users/criar` with senha shorter than 4 characters
- **THEN** the system SHALL flash "Senha deve ter pelo menos 4 caracteres" and re-render the form with status 400

#### Scenario: Passwords don't match
- **WHEN** an admin_sistema submits `POST /admin/users/criar` with senha and confirmacao that differ
- **THEN** the system SHALL flash "Senhas não conferem" and re-render the form with status 400

#### Scenario: Invalid role
- **WHEN** an admin_sistema submits `POST /admin/users/criar` with an invalid role value
- **THEN** the system SHALL flash "Papel inválido" and re-render the form with status 400

### Requirement: CSRF protection on creation form
The system SHALL include CSRF token protection on the creation form.

#### Scenario: Form includes CSRF token
- **WHEN** `admin_user_create.html` is rendered
- **THEN** the form SHOULD contain a hidden CSRF token input
