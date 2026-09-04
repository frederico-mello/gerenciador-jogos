## ADDED Requirements

### Requirement: Duplicated string literals are consolidated into constants
The source code SHALL define named constants for any string literal that appears 3 or more times within the same file, replacing all occurrences with the constant reference.

#### Scenario: Validation message is defined once
- **WHEN** `app/routes.py` contains validation logic
- **THEN** each repeated message (e.g., "Nome é obrigatório.", "Email é obrigatório.") is defined as a module-level constant once and referenced by name

#### Scenario: Endpoint name is defined once
- **WHEN** `app/routes.py` calls `redirect(url_for(...))` or `render_template(...)`
- **THEN** each repeated endpoint name (e.g., "games.admin_users", "games.index") is defined as a module-level constant once and referenced by name

#### Scenario: SQL fragment is defined once
- **WHEN** `app/models.py` builds SQL query strings
- **THEN** each repeated SQL fragment (e.g., " AND ", " WHERE ", " ORDER BY nome", "updated_at = ?") is defined as a module-level constant once

#### Scenario: Shell repeated path is a variable
- **WHEN** `deploy/setup.sh` references the Nginx config path multiple times
- **THEN** the path string is defined as a shell variable once and referenced via `${VAR}`

#### Scenario: SonarCloud no longer flags the literals
- **WHEN** SonarCloud re-analyzes the code
- **THEN** rule `python:S1192`, `shelldre:S1192`, and `plsql:S1192` issue counts are significantly reduced
