## 1. Define shared constant

- [x] 1.1 Add `TEST_PASSWORD = "123"  # NOSONAR` to `tests/conftest.py`

## 2. Update test files

- [x] 2.1 Replace password literals in `tests/test_auth.py` with `TEST_PASSWORD` (9 occurrences)
- [x] 2.2 Replace password literals in `tests/test_create_admin.py` with `TEST_PASSWORD` (9 occurrences)
- [x] 2.3 Replace password literal in `tests/conftest.py` own fixtures with `TEST_PASSWORD` (1 occurrence, in `auth_client` fixture)
- [x] 2.4 Replace password literal in `tests/test_loans.py` with `TEST_PASSWORD` (1 occurrence)
- [x] 2.5 Replace password literal in `tests/test_loans_extras.py` with `TEST_PASSWORD` (1 occurrence)
- [x] 2.6 Replace password literal in `tests/test_school_routes.py` with `TEST_PASSWORD` (1 occurrence)

## 3. Verification

- [x] 3.1 Run `python -m pytest` to verify all tests pass with the unified password
