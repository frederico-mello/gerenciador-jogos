## ADDED Requirements

### Requirement: SQL injection false positive is documented
The system SHALL include a `# NOSONAR` comment with justification on `app/db.py:34` to document that `SCHEMA_PATH.read_text()` reads a static, developer-controlled schema file and does not constitute a SQL injection vulnerability.

#### Scenario: SonarCloud no longer flags the line
- **WHEN** SonarCloud re-analyzes the code
- **THEN** rule `pythonsecurity:S3649` does not fire on `app/db.py:34`

### Requirement: HTML description is sanitized before rendering
The system SHALL sanitize the Markdown-rendered HTML in game descriptions before passing it to the template with `|safe`, stripping dangerous tags (script, iframe, event handlers) while preserving formatting tags expected in legitimate Markdown output.

#### Scenario: Safe HTML passes through sanitization
- **WHEN** a game description contains `<h2>Sobre</h2><p>Texto com <strong>negrito</strong> e <a href="http://exemplo.com">link</a></p>`
- **THEN** the rendered page displays the formatted HTML unchanged

#### Scenario: Script tag is stripped
- **WHEN** a game description contains `<script>alert('xss')</script><p>Conteúdo</p>`
- **THEN** the script tag is removed and only `<p>Conteúdo</p>` is rendered

#### Scenario: Event handler attribute is stripped
- **WHEN** a game description contains `<p onclick="alert(1)">Conteúdo</p>`
- **THEN** the onclick attribute is removed and `<p>Conteúdo</p>` is rendered

### Requirement: CLI file path is validated before opening
The system SHALL resolve and validate the `csv_path` argument in `import_schools.py` before calling `open()`, ensuring the resolved path is an actual regular file and does not escape expected directories via `..` traversal.

#### Scenario: Valid CSV path is accepted
- **WHEN** `csv_path` points to a regular CSV file in an accessible directory
- **THEN** `open()` proceeds normally

#### Scenario: Nonexistent path is rejected
- **WHEN** `csv_path` points to a file that does not exist
- **THEN** the script prints an error and exits before attempting to open the file

#### Scenario: Path traversal attempt is rejected
- **WHEN** `csv_path` contains `../` components that resolve outside the expected working directory
- **THEN** the script prints an error and exits
