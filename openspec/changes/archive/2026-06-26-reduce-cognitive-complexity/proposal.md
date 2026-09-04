## Why

SonarCloud flagged 8 `python:S3776` CRITICAL issues — 7 in `app/routes.py` and 1 in `scripts/create_admin.py` — where functions exceed the cognitive complexity threshold of 15. The worst offenders have complexity scores of 27, 26, and 25 (nearly double the limit). High cognitive complexity makes functions hard to understand, test, and maintain. Breaking them into smaller, focused functions with clear responsibilities reduces defect risk and improves readability.

## What Changes

- **app/routes.py**: Refactor 7 route handler functions by extracting validation logic, form processing, and role-checking into helper functions
  - `login` (complexity 22 → ≤15)
  - `edit_game` (complexity 22 → ≤15)
  - `create_game` (complexity 26 → ≤15)
  - `edit_user` (complexity 25 → ≤15)
  - `create_user` (complexity 27 → ≤15)
  - `emprestimo_admin` (complexity 19 → ≤15)
  - `edit` (complexity 22 → ≤15)
- **scripts/create_admin.py**: Refactor `create_admin` (complexity 18 → ≤15)

## Capabilities

### New Capabilities
- `low-cognitive-complexity`: All functions in the codebase have cognitive complexity ≤ 15, as measured by SonarCloud's `python:S3776` rule.

### Modified Capabilities
<!-- None — refactoring preserves existing behavior through decomposition. -->

## Impact

- Affected files: `app/routes.py` (7 functions), `scripts/create_admin.py` (1 function)
- No API, dependency, or behavior changes.
- Moderate regression risk — requires full test suite pass to confirm no behavioral change.
