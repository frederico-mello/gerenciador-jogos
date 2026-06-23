## 1. Route and Template

- [x] 1.1 Implement `GET /admin/users/criar` route rendering `admin_user_create.html`
- [x] 1.2 Implement `POST /admin/users/criar` route with validation and user creation
- [x] 1.3 Add "Novo usuário" link to toolbar in `admin_users.html`
- [x] 1.4 Protect routes with `@role_required("admin_sistema")`

## 2. Form Validation

- [x] 2.1 Validate required fields (nome, email, senha, confirmacao)
- [x] 2.2 Validate email uniqueness
- [x] 2.3 Validate password minimum length (4 chars)
- [x] 2.4 Validate password confirmation match
- [x] 2.5 Validate role is one of allowed values
- [x] 2.6 Flash error messages and re-render form with status 400 on validation failure

## 3. CSRF Protection

- [x] 3.1 Include CSRF token in creation form template

## 4. Tests

- [x] 4.1 Test admin can access creation form (GET)
- [x] 4.2 Test admin creates user successfully (POST)
- [x] 4.3 Test duplicate email rejection
- [x] 4.4 Test short password rejection
- [x] 4.5 Test password mismatch rejection
- [x] 4.6 Test non-admin gets 403
