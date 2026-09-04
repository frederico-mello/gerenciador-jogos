## Why

SonarCloud flagged 22 BLOCKER-level `python:S6437` issues across 6 test files for "compromised passwords." These are test fixtures using deterministic passwords like `"admin123"` and `"123"` to seed test users via `generate_password_hash()` — a necessary pattern for deterministic test assertions. The rule is correct for production code but fires on tests where literal passwords are required. Consolidating to a single constant eliminates the duplication while making the one remaining definition auditable as a justified false positive.

## What Changes

- Define `TEST_PASSWORD = "123"` module-level constant in `tests/conftest.py` with a `# NOSONAR` justification comment
- Replace all password string literals in test files with `TEST_PASSWORD` import from `conftest.py`
- This eliminates 22 instances of duplicated password literals across 6 test files

## Capabilities

### New Capabilities
- `test-password-constants`: Test password literals are consolidated into a single auditable constant, reducing SonarCloud BLOCKER false positives and code duplication.

### Modified Capabilities
<!-- None — test-only internal refactoring, no behavior change. -->

## Impact

- Affected files: `tests/conftest.py`, `tests/test_auth.py`, `tests/test_create_admin.py`, `tests/test_loans.py`, `tests/test_loans_extras.py`, `tests/test_school_routes.py`
- No production code changes, no API changes, no dependency changes.
