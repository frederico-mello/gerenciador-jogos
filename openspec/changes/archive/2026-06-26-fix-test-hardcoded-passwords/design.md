## Context

SonarCloud rule `python:S6437` detects hardcoded passwords in source code. This is a legitimate security concern for production code but produces false positives in test suites where deterministic passwords are necessary. The project's 6 test files contain 22 instances of literal password strings used to create test users and authenticate against them.

**Current state:** Each test file independently uses `generate_password_hash("123")` or `generate_password_hash("admin123")` and then logs in with the corresponding cleartext. The rule fires on every occurrence.

## Goals / Non-Goals

**Goals:**
- Reduce 22 S6437 BLOCKERs to 1 auditable constant with NOSONAR suppression
- Reduce code duplication in tests (same password repeated)
- Keep tests deterministic and readable

**Non-Goals:**
- Changing the password itself (tests must keep working)
- Using environment variables for test passwords (unnecessary indirection for tests)
- Adjusting SonarCloud Quality Profile rules

## Decisions

### 1. Single constant in conftest.py

**Decision**: Define `TEST_PASSWORD = "123"  # NOSONAR` in `tests/conftest.py` and import it in all test files. Use this constant for both `generate_password_hash()` and login form data.

**Rationale**: `conftest.py` is already shared across all test modules. A single constant with a `# NOSONAR` justification comment documents that this is an intentional test password. Since conftest is auto-imported by pytest, no explicit import is needed — but explicit imports make the dependency visible and avoid silent coupling.

**Alternative considered**: Using pytest fixtures. Rejected because the password is used in multiple different fixtures and inline test code, not just fixture setup. A constant is simpler and doesn't require fixture parameterization.

### 2. Keep all existing passwords unified to "123"

**Decision**: Normalize all test passwords to `TEST_PASSWORD` (currently "123" is the most common). Where tests used "admin123" before, accept that `TEST_PASSWORD` is sufficient — the admin user's password in tests doesn't need to differ from standard users.

**Rationale**: Simplifies to one constant. The password length is irrelevant for test assertions — what matters is that the hash matches the cleartext used for login.

**Alternative considered**: Keeping two constants (user vs admin password). Rejected — adds complexity with no test value.

### 3. `# NOSONAR` on the constant definition

**Decision**: Use SonarCloud's comment-based suppression on the one remaining literal.

**Rationale**: SonarCloud may still flag the constant definition itself. `# NOSONAR` with a justification comment ("test-only password for deterministic assertions") documents the intentional exception.

## Risks / Trade-offs

- **Constant value change**: Some tests may have been using "admin123" vs "123" for different test users. → Mitigation: Run full test suite after change to catch any mismatches.
- **Accidental production use**: If `TEST_PASSWORD` is ever imported into production code, it would be a real vulnerability. → Mitigation: The constant name itself signals "test-only"; code review catches accidental imports.
