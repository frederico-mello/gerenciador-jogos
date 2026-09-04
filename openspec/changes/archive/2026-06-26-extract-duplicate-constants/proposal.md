## Why

SonarCloud detected 23 `S1192`-family issues across Python, shell, and SQL files where string literals are duplicated 3 to 11 times. This duplication inflates the new-code duplication metric (12.5% vs 3% threshold) that is causing the Quality Gate to fail. Extracting these to named constants reduces duplication, improves maintainability (single place to edit messages/routes/paths), and directly addresses the failing quality gate metric.

## What Changes

- **Python (app)**: Extract duplicated validation messages, route endpoint names, and template filenames into class-level or module-level constants in `app/routes.py`, `app/models.py`, and `app/auth.py`
- **SQL (app/schema.sql)**: Replace repeated column default value literal with a variable
- **Shell (deploy/setup.sh)**: Extract repeated path string and separator string into shell variables

## Capabilities

### New Capabilities
- `literal-deduplication`: String literals duplicated 3+ times in source code are consolidated into named constants, reducing code duplication and improving maintainability.

### Modified Capabilities
<!-- None — these are implementation-level refactorings, no behavioral changes. -->

## Impact

- Affected files: `app/routes.py` (13 occurrences), `app/models.py` (4), `deploy/setup.sh` (2), `app/auth.py` (2), `scripts/create_admin.py` (1), `app/schema.sql` (1)
- No API, dependency, or behavior changes.
