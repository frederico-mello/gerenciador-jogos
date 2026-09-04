## 1. Input labels

- [x] 1.1 Add `id` and `<label>` to search/filter inputs in `admin_users.html` (2 inputs)
- [x] 1.2 Add `id` and `<label>` to search/filter inputs in `admin_schools.html` (2 inputs)
- [x] 1.3 Add `id` and `<label>` to search/filter input in `emprestimos_admin.html` (1 input)

## 2. ARIA role fixes

- [x] 2.1 Replace `role="admin_sistema"` with `data-role="admin_sistema"` in `admin_users.html`
- [x] 2.2 Replace `role="admin_jogos"` with `data-role="admin_jogos"` in `admin_users.html`
- [x] 2.3 Replace `role="usuario"` with `data-role="usuario"` in `admin_users.html`

## 3. Semantic HTML elements

- [x] 3.1 Replace `<div role="status">` with `<output>` in `base.html:41`, preserving Bootstrap classes
- [x] 3.2 Replace `<div role="dialog">` with `<dialog>` in `detail.html:156`, preserving styling

## 4. Contrast fixes

- [x] 4.1 Adjust text/background color at `style.css:101` to meet 4.5:1 contrast ratio
- [x] 4.2 Adjust text/background color at `style.css:558` to meet 4.5:1 contrast ratio

## 5. Link text differentiation

- [x] 5.1 Add distinguishing text to duplicate links in `form.html` so each link target is identifiable

## 6. Verification

- [x] 6.1 Run `python -m pytest` to verify no regressions
- [x] 6.2 Visual check: render admin pages, detail page, and form to confirm labels and colors are correct
