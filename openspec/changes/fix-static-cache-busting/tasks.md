## 1. Helper de versão de estáticos

- [x] 1.1 Implementar `static_v(filename)` em `app/__init__.py` (context processor em `create_app()`): fingerprint sha256 truncado de `"{mtime_ns}:{size}"` via `os.stat`, cache em dict no processo, fallback sem `?v=` se o stat falhar. Verificar: `GET /` renderiza `<link ... style.css?v=<hex10>>`.
- [x] 1.2 Teste unitário do helper: fingerprint estável para arquivo inalterado, muda quando `mtime_ns`/`size` mudam, e URL sem `?v=` quando o arquivo não existe. Verificar: `pytest tests/ -k static_v` passa.

## 2. Migração das templates

- [x] 2.1 `app/templates/base.html:7`: trocar `url_for('static', filename='style.css')` por `static_v('style.css')`. Verificar: HTML renderizado contém `style.css?v=`.
- [x] 2.2 `app/templates/form.html:131-132`: trocar as duas referências de EasyMDE por `static_v('vendor/easymde.min.css')` e `static_v('vendor/easymde.min.js')`. Verificar: `GET /novo` contém `easymde.min.css?v=` e `easymde.min.js?v=`.
- [x] 2.3 Confirmar que nenhuma outra referência a `url_for('static', ...)` resta nos templates. Verificar: `grep url_for('static' app/templates` retorna vazio.

## 3. Verificação

- [x] 3.1 Suite de testes existente continua verde: `pytest tests/` (baseline 154 passed, 1 skipped). Verificar: nenhum teste quebrado pelo helper ou pelas templates.
- [x] 3.2 Confirmar que `deploy/nginx.conf` não foi alterado (`git diff --stat` não lista o arquivo). Verificar: diff só contém `app/__init__.py`, `app/templates/base.html`, `app/templates/form.html`, testes e artefatos OpenSpec.