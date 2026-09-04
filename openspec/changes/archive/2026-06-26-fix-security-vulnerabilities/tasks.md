## 1. SQL injection false positive

- [x] 1.1 Add `# NOSONAR` comment on `app/db.py:34` with justification explaining `SCHEMA_PATH.read_text()` reads a static file

## 2. XSS sanitization

- [x] 2.1 Add `bleach>=6.0` to `requirements.txt`
- [x] 2.2 Run `pip install bleach` to install the new dependency
- [x] 2.3 Import `bleach` in `app/routes.py`
- [x] 2.4 Define `ALLOWED_TAGS` and `ALLOWED_ATTRIBUTES` constants covering safe Markdown HTML output
- [x] 2.5 Apply `bleach.clean(descricao_html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)` in the game detail route handler before passing to template
- [x] 2.6 Run `python -m pytest` to verify no regressions

## 3. Path traversal validation

- [x] 3.1 Import `Path` from `pathlib` in `scripts/import_schools.py` (if not already)
- [x] 3.2 Resolve `csv_path` with `Path(csv_path).resolve()` and validate it exists and is a file before calling `open()`
- [x] 3.3 Print a clear error message and exit with non-zero code for invalid paths
- [x] 3.4 Run `python scripts/import_schools.py` with a nonexistent path to verify error handling works
