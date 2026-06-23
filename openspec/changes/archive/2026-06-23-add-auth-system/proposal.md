## Why

O sistema hoje é single-user: qualquer visitante de `localhost:5000` pode criar, editar e excluir jogos sem identificação. Para suportar empréstimos (Change 2), precisamos distinguir 3 papéis com permissões diferentes:
- **`admin_sistema`**: poder total, incluindo CRUD de usuários e promote/demote de papéis.
- **`admin_jogos`**: CRUD de jogos + gerenciamento de empréstimos (mas não gerencia usuários nem papéis).
- **`usuario`**: vê catálogo (read-only público) e solicita empréstimos.

Além disso, usuários podem se cadastrar sozinhos (self-registration), indicando a escola em que trabalham (lista controlada do Change 0). O primeiro `admin_sistema` é criado via CLI (`scripts/create_admin.py`), resolvendo o chicken-and-egg de bootstrapping.

## What Changes

- **Nova tabela `users`** com `id`, `nome`, `email` (UNIQUE), `password_hash`, `role` (CHECK em 3 valores), `escola_id` (FK → `schools`, NULL para admins), `ativo` (soft delete), timestamps.
- **Hash de senha com `werkzeug.security`** (`generate_password_hash`, `check_password_hash`).
- **Sessão Flask** (já embutida) com `SECRET_KEY` lida de env var `FLASK_SECRET_KEY`.
- **Decorators `@login_required` e `@role_required(*roles)`** em novo módulo `app/auth.py`.
- **Rotas de auth**: `GET/POST /login`, `GET/POST /registrar` (com `<select>` de escola via AJAX/autocomplete), `GET /logout`.
- **CRUD de usuários** para `admin_sistema`: `GET /admin/users` (lista com filtros), `GET /admin/users/<id>/editar`, `POST /admin/users/<id>/editar`, `POST /admin/users/<id>/inativar` (soft delete), `POST /admin/users/<id>/role` (promote/demote).
- **Proteção das rotas existentes**: `/novo`, `/<id>/editar`, `/<id>/excluir` passam a requerer `@role_required('admin_sistema', 'admin_jogos')`. `/admin/schools` (do Change 0) passa a requerer `@role_required('admin_sistema')`.
- **Catálogo `/` e `/` e `/media/` permanecem públicos** (read-only).
- **Proteção CSRF** via `Flask-WTF` (`FlaskForm` + `CSRFProtect`) em todos os forms.
- **Script CLI `scripts/create_admin.py`** para bootstrap do primeiro `admin_sistema`.
- **Extensão do `scripts/init_db.py`** para criar tabela `users`.
- **Templates**: `login.html`, `registrar.html`, `admin_users.html`, `admin_user_form.html`; nav dinâmico por role em `base.html`.
- **Novo capability** `auth` no OpenSpec + delta em `web-ui`.

## Capabilities

### New Capabilities
- `auth`: Autenticação por sessão Flask, 3 papéis, self-registration com escola, CRUD de usuários para admin_sistema, hash de senha, CSRF protection.

### Modified Capabilities
- `web-ui`: Rotas de jogos `/novo`, `/<id>/editar`, `/<id>/excluir` agora requerem `@role_required('admin_sistema', 'admin_jogos')`. Nav diferenciado por role. Novas rotas de auth e admin/users. Rotas `/admin/schools` (do Change 0) agora requerem `@role_required('admin_sistema')`.

## Impact

- **Schema**: nova tabela `users` em `app/schema.sql`. `scripts/init_db.py` estendido.
- **Novo módulo**: `app/auth.py` (decorators, helpers de sessão).
- **Dependências Python**: adicionar `Flask-WTF` a `requirements.txt` (CSRF + forms).
- **Config**: `SECRET_KEY` lida de `FLASK_SECRET_KEY` env var (fallback para dev com warning).
- **Breaking change menor**: rotas `/novo`, `/<id>/editar`, `/<id>/excluir` passam a requerer login. Usuário precisa criar o primeiro admin via `scripts/create_admin.py` antes de usar o sistema.
- **Depende de Change 0** (`add-school-directory`): `users.escola_id` faz FK para `schools.id`.
- **Pré-requisito para Change 2** (`add-loans-subsystem`): empréstimos precisam de `user_id` autenticado.
