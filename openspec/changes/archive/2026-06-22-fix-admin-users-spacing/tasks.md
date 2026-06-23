## 1. CSS: Actions column spacing

- [x] 1.1 Add `.actions` selector to `style.css` with `display: flex; flex-wrap: wrap; gap: 8px; align-items: center;`

## 2. Template: Toolbar refactor

- [x] 2.1 Replace `<div class="toolbar">` with `<div class="list-header">` in `admin_users.html`
- [x] 2.2 Replace `<form class="filters">` with `<form class="filter-form">` in `admin_users.html`
- [x] 2.3 Wrap the "Novo usuário" link in a `<div class="list-actions">` container

## 3. Template: Actions column wrapper

- [x] 3.1 Ensure all elements in `<td class="actions">` are direct children of the flex container (no extra wrapping needed if `td.actions` is the flex parent)
- [x] 3.2 Verify inline forms maintain `display:inline` or inherit flex child behavior correctly

## 4. Verification

- [x] 4.1 Visually confirm spacing between buttons in `/admin/users`
- [x] 4.2 Test filter submission still works
- [x] 4.3 Test inactivate/reactivate button still submits correctly
