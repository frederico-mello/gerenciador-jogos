## ADDED Requirements

### Requirement: Shell scripts use `[[` for conditionals
All conditional expressions in `deploy/setup.sh` and `scripts/run-as-app.sh` SHALL use the Bash keyword `[[ ... ]]` instead of the aliased `test` command `[ ... ]`.

#### Scenario: Conditional tests use double brackets
- **WHEN** reviewing any conditional test in the shell scripts
- **THEN** the test uses `[[ expression ]]` syntax, not `[ expression ]`

#### Scenario: SonarCloud no longer flags single brackets
- **WHEN** SonarCloud re-analyzes the shell scripts
- **THEN** rule `shelldre:S7688` fires on zero lines
