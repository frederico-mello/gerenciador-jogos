## Context

SonarCloud flagged 3 security issues in the project. One is a false positive (SQL injection on a static schema file), two are real vulnerabilities: disabled Jinja2 auto-escaping on user-editable Markdown-rendered HTML, and an unvalidated CLI file path in the school CSV importer.

**Current state:**
- `app/db.py:34` — `conn.executescript(SCHEMA_PATH.read_text())` where `SCHEMA_PATH = Path(__file__).parent / "schema.sql"`. The scanner sees a string argument to `executescript` and flags it. The string is always a static, developer-controlled file.
- `app/templates/detail.html:40` — `{{ descricao_html|safe }}`. The `descricao_html` variable is produced by `markdown.markdown()` (Python-Markdown 3.10) rendering of user-editable game descriptions. `|safe` bypasses Jinja2 auto-escaping, allowing any HTML in the rendered output — including `<script>` tags injected via raw HTML embedded in Markdown.
- `scripts/import_schools.py:55` — `open(csv_path, ...)` where `csv_path` is a CLI positional argument. No validation before opening, allowing arbitrary file reads.

## Goals / Non-Goals

**Goals:**
- Document the SQL injection false positive with a `# NOSONAR` suppression comment
- Sanitize Markdown-rendered HTML before rendering with `|safe`
- Validate the CLI file path in `import_schools.py` before opening

**Non-Goals:**
- Changing the Markdown rendering library (Python-Markdown)
- Adding a full path validation framework for all CLI tools
- Modifying SonarCloud Quality Profile rules

## Decisions

### 1. db.py suppression strategy

**Decision**: Add `# NOSONAR: pythonsecurity:S3649 — SCHEMA_PATH is a static file, not user-controlled` on the relevant line.

**Rationale**: The `# NOSONAR` mechanism is SonarCloud's recommended approach for justified false positives. It survives code moves and is auditable in code review. The justification comment makes intent clear to future maintainers.

**Alternative considered**: Switching to `conn.execute()` with individual statements. Rejected because `executescript` correctly handles multi-statement schema files (which `schema.sql` is). The false alarm is on the API, not the data flow.

### 2. XSS sanitization in detail.html

**Decision**: Sanitize `descricao_html` in the route handler (Python side, `app/routes.py`) using `bleach` (new explicit dependency, added to `requirements.txt`) to strip dangerous tags/attributes before passing to the template.

**Rationale**: Sanitizing in the route handler (not the template) keeps the template simple and ensures the sanitized value is safe regardless of template usage. Python-Markdown 3.x removed its built-in safe mode, so an external sanitizer is required. `bleach` is the standard choice for HTML sanitization in Python. Stripping all tags except a safe allowlist (p, h1-h6, ul, ol, li, a, img, table, tr, td, th, strong, em, code, pre, br, hr, blockquote) covers legitimate Markdown output while removing `<script>`, `<iframe>`, event handlers, etc.

**Alternative considered**: Removing `|safe` and using `{{ descricao_html }}` (auto-escaped). Rejected — all HTML formatting would render as escaped text, breaking game description pages.

### 3. Path validation in import_schools.py

**Decision**: Resolve `csv_path` with `Path.resolve()` and validate it's within an expected directory or is an absolute path the script can read. Use `Path.resolve()` to eliminate `../` traversal and check the resolved path exists and is a regular file before opening.

**Rationale**: `Path.resolve()` collapses `..` components and returns an absolute path. Validating the resolved path is within a known location prevents path traversal attacks. This is a pragmatic defense-in-depth measure for a CLI administrative tool.

**Alternative considered**: Using `os.path.abspath` + regex. Rejected — `Path.resolve()` is more robust (handles symlinks, `.` and `..` components correctly on all platforms).

## Risks / Trade-offs

- **bleach approach**: If the sanitization allowlist is too restrictive, legitimate Markdown features (e.g., `<span>` for custom styling in game descriptions) may be stripped. → Mitigation: Review existing game description HTML for common tag usage before finalizing the allowlist.
- **Path validation scope**: Only `import_schools.py` is patched in this change. Other CLI scripts may have similar issues but are out of scope. → Mitigation: The SonarCloud issue only flags this one file; broader path hardening belongs in a future change.
- **NOSONAR comment**: If `SCHEMA_PATH` is ever made dynamic in the future, the suppression should be revisited. → Mitigation: The justification comment serves as documentation for future reviewers.
