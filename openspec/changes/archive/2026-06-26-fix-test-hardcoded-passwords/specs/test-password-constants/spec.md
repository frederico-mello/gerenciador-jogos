## ADDED Requirements

### Requirement: Test passwords use a single constant
The test suite SHALL define a single `TEST_PASSWORD` constant in `tests/conftest.py` and use it in all test fixtures and assertions that require a deterministic password.

#### Scenario: Single constant definition exists
- **WHEN** `tests/conftest.py` is inspected
- **THEN** it defines `TEST_PASSWORD = "123"  # NOSONAR` at module level

#### Scenario: Test fixtures use the constant
- **WHEN** a test fixture calls `generate_password_hash(TEST_PASSWORD)`
- **THEN** the generated hash matches the cleartext `TEST_PASSWORD` for login assertions

#### Scenario: No other password literals in tests
- **WHEN** SonarCloud analyzes the test suite
- **THEN** rule `python:S6437` fires at most once (on the constant definition itself)
