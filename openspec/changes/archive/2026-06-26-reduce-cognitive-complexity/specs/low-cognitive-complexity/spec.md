## ADDED Requirements

### Requirement: All functions have cognitive complexity ≤ 15
Every Python function in the codebase SHALL have a cognitive complexity score of 15 or lower, as measured by SonarCloud's `python:S3776` rule.

#### Scenario: Route handler login is below threshold
- **WHEN** SonarCloud analyzes `app/routes.py`
- **THEN** the `login` function has cognitive complexity ≤ 15

#### Scenario: Route handler create_game is below threshold
- **WHEN** SonarCloud analyzes `app/routes.py`
- **THEN** the `create_game` function has cognitive complexity ≤ 15

#### Scenario: Route handler create_user is below threshold
- **WHEN** SonarCloud analyzes `app/routes.py`
- **THEN** the `create_user` function has cognitive complexity ≤ 15

#### Scenario: CLI create_admin is below threshold
- **WHEN** SonarCloud analyzes `scripts/create_admin.py`
- **THEN** the `create_admin` function has cognitive complexity ≤ 15

#### Scenario: No S3776 issues remain
- **WHEN** SonarCloud re-analyzes the entire project
- **THEN** rule `python:S3776` fires on zero lines
