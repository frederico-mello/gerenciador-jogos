## Why

SonarCloud detected 3 security issues: a SQL-injection false positive in db.py (static schema file, not user input), auto-escape disabled on user-generated HTML content in detail.html (real XSS risk), and unvalidated CLI file path in import_schools.py (path traversal). All need resolution either through documented suppression of false positives or actual fixes for real vulnerabilities.

## What Changes

- **app/db.py:34**: Add `# NOSONAR` comment with justification — `SCHEMA_PATH.read_text()` reads a static, developer-controlled file, not user input. No SQL injection vector exists.
- **app/templates/detail.html:40**: Replace `{{ descricao_html|safe }}` with a sanitization step that strips dangerous tags/attributes from user-editable Markdown-rendered HTML before marking it safe.
- **scripts/import_schools.py:55**: Validate that `csv_path` resolves to an expected directory or is an absolute path owned by the caller before calling `open()`.

## Capabilities

### New Capabilities
- `security-hardening`: Resolve documented security vulnerabilities and false-positive suppressions in the SonarCloud baseline.

### Modified Capabilities
<!-- None — these are implementation-level fixes, not spec-level behavior changes. -->

## Impact

- Affected code: `app/db.py`, `app/templates/detail.html`, `scripts/import_schools.py`
- No API, dependency, or breaking changes.
