## 1. Extract authorization helpers

- [x] 1.1 Create `_require_login()` helper that checks session and redirects to login if missing
- [x] 1.2 Create `_require_role(role)` helper that checks user role and returns 403 if insufficient
- [x] 1.3 Apply `_require_login()` and `_require_role()` across all affected route handlers, replacing inline auth checks

## 2. Extract validation helpers

- [x] 2.1 Create `_validate_game_form(form)` that returns a list of error messages for name/area/descricao
- [x] 2.2 Create `_validate_user_form(form, is_edit=False)` that returns a list of error messages for nome/email/senha/role
- [x] 2.3 Apply validation helpers in create_game, edit_game, create_user, edit_user route handlers

## 3. Refactor route handlers by complexity (easiest first)

- [x] 3.1 Refactor `emprestimo_admin` (complexity 19): extract loan status update logic into `_process_loan_action()`
- [x] 3.2 Refactor `login` (complexity 22): extract login validation into `_validate_login()`
- [x] 3.3 Refactor `edit_game` (complexity 22): apply `_validate_game_form()` and extract image handling into `_handle_game_image()`
- [x] 3.4 Refactor `edit` (complexity 22): extract loan edit logic into `_process_loan_edit()`
- [x] 3.5 Refactor `edit_user` (complexity 25): apply `_validate_user_form(is_edit=True)` and extract password handling into `_handle_user_password()`
- [x] 3.6 Refactor `create_game` (complexity 26): apply `_validate_game_form()` and `_handle_game_image()`
- [x] 3.7 Refactor `create_user` (complexity 27): apply `_validate_user_form(is_edit=False)` and extract creation logic into `_create_user()`

## 4. Refactor create_admin.py

- [x] 4.1 Refactor `create_admin` (complexity 18) in `scripts/create_admin.py` by extracting input validation and user creation into helpers

## 5. Verification

- [x] 5.1 Run `python -m pytest` after each route handler refactoring
- [x] 5.2 Run full test suite after all refactorings
- [x] 5.3 Manual smoke test: login, create game, edit game, create user, edit user, edit loan, admin loan actions
