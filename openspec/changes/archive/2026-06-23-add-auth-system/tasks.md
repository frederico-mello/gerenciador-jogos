## 1. Schema e dependências

- [x] 1.1 Adicionar tabela `users` e índices a `app/schema.sql` (email UNIQUE, role CHECK, escola_id FK, ativo, timestamps)
- [x] 1.2 Adicionar `Flask-WTF` a `requirements.txt` e instalar (`pip install -r requirements.txt`)
- [x] 1.3 Atualizar `app/__init__.py` para ler `SECRET_KEY` de `FLASK_SECRET_KEY` env var (com fallback dev + warning)
- [x] 1.4 Inicializar `CSRFProtect` na factory `create_app()`

## 2. Módulo de auth (app/auth.py)

- [x] 2.1 Criar `app/auth.py` com `current_user()` (lê `session['user_id']`, busca em models)
- [x] 2.2 Implementar `@login_required` (redirect para `/login` se não logado)
- [x] 2.3 Implementar `@role_required(*roles)` (HTTP 403 se role insuficiente)
- [x] 2.4 Implementar `@active_required` (rejeita login de `ativo=0`)

## 3. Models de usuário (app/models.py)

- [x] 3.1 Adicionar `get_user(user_id)` (busca por id, retorna Row ou None)
- [x] 3.2 Adicionar `get_user_by_email(email)`
- [x] 3.3 Adicionar `create_user(data)` (data: nome, email, password_hash, role, escola_id, ativo=1)
- [x] 3.4 Adicionar `update_user(user_id, data)` (atualiza nome, email, escola_id; senha só se fornecida)
- [x] 3.5 Adicionar `set_user_role(user_id, role)` (promote/demote)
- [x] 3.6 Adicionar `set_user_ativo(user_id, ativo)` (soft delete toggle)
- [x] 3.7 Adicionar `list_users(role=None, escola_id=None, ativo_only=True)` (lista com filtros)
- [x] 3.8 Adicionar `count_admins_sistema()` (para o create_admin.py validar)

## 4. Rotas de auth (app/routes.py)

- [x] 4.1 Implementar `GET/POST /login` (form com email+senha, valida com `check_password_hash`, define `session['user_id']`, redirect `/`)
- [x] 4.2 Implementar `GET/POST /registrar` (form com nome, email, senha, confirmação, escola via datalist; cria `role='usuario'`, `ativo=1`)
- [x] 4.3 Implementar `GET /logout` (limpa session, redirect `/`)
- [x] 4.4 Validar no registro: senhas conferem, email não existe, escola obrigatória

## 5. Rotas admin de usuários

- [x] 5.1 Implementar `GET /admin/users` (lista com filtros `?role=` e `?escola_id=`, ordenada por nome) — `@role_required('admin_sistema')`
- [x] 5.2 Implementar `GET /admin/users/<id>/editar` (form preenchido) — `@role_required('admin_sistema')`
- [x] 5.3 Implementar `POST /admin/users/<id>/editar` (atualiza nome, email, escola_id, senha opcional, ativo) — `@role_required('admin_sistema')`
- [x] 5.4 Implementar `POST /admin/users/<id>/role` (muda role) — `@role_required('admin_sistema')`
- [x] 5.5 Implementar `POST /admin/users/<id>/inativar` e `POST /admin/users/<id>/reativar` (soft delete toggle) — `@role_required('admin_sistema')`

## 6. Proteger rotas existentes

- [x] 6.1 Adicionar `@role_required('admin_sistema', 'admin_jogos')` em `GET/POST /novo`
- [x] 6.2 Adicionar `@role_required('admin_sistema', 'admin_jogos')` em `GET/POST /<id>/editar`
- [x] 6.3 Adicionar `@role_required('admin_sistema', 'admin_jogos')` em `POST /<id>/excluir`
- [x] 6.4 Adicionar `@role_required('admin_sistema')` em todas as rotas `/admin/schools*` (do Change 0)
- [x] 6.5 Manter `GET /`, `GET /<id>`, `GET /media/` públicas (sem decorator)

## 7. Templates

- [x] 7.1 Criar `app/templates/login.html` (form email+senha, link para registrar)
- [x] 7.2 Criar `app/templates/registrar.html` (form nome, email, senha, confirmação, escola com `<select>`)
- [x] 7.3 Criar `app/templates/admin_users.html` (tabela com filtros, botões editar/inativar/reativar/mudar role)
- [x] 7.4 Criar `app/templates/admin_user_form.html` (form editar usuário)
- [x] 7.5 Atualizar `app/templates/base.html` com nav dinâmico por role (usa `current_user()`)
- [x] 7.6 Atualizar `app/templates/index.html` para esconder botão "Novo jogo" se não tem permissão
- [x] 7.7 Atualizar `app/templates/detail.html` para esconder botões editar/excluir se não tem permissão
- [x] 7.8 Adicionar `{{ csrf_token() }}` em todos os forms existentes

## 8. Script de bootstrap (scripts/create_admin.py)

- [x] 8.1 Criar `scripts/create_admin.py` que aceita `--nome`, `--email`, `--senha` ou prompta interativamente
- [x] 8.2 Se já existe `admin_sistema`, pedir confirmação antes de criar outro
- [x] 8.3 Criar usuário com `role='admin_sistema'`, `ativo=1`, `escola_id=NULL`, hash via `generate_password_hash`
- [x] 8.4 Imprimir "Admin criado: <email>" ao final

## 9. Testes

- [x] 9.1 Criar `tests/test_auth.py` cobrindo login (sucesso, senha errada, email inexistente, inativo), logout, registro (válido, senhas não conferem, email duplicado, sem escola)
- [x] 9.2 Adicionar testes de autorização: rota protegida sem login (redirect), com role insuficiente (403), com role suficiente (200)
- [x] 9.3 Adicionar testes para CRUD de usuários (apenas admin_sistema pode; admin_jogos e usuario recebem 403)
- [x] 9.4 Adicionar teste para autorização (admin_sistema acessa admin/users, usuario recebe 403)
- [x] 9.5 Testes de CSRF (skipped — CSRF desabilitado em TESTING mode)
- [x] 9.6 Atualizar `tests/conftest.py` com fixture `admin_client` (cria admin_sistema + login)
- [x] 9.7 Rodar `python -m pytest` — **83 testes passando, 1 skipped**

## 10. Validação manual

- [x] 10.1 Rodar `python scripts/init_db.py` e confirmar tabela `users` criada
- [x] 10.2 Rodar `python scripts/create_admin.py` e criar o primeiro admin
- [x] 10.3 Fazer login como admin_sistema, navegar `/admin/users`, `/admin/schools`
- [x] 10.4 Registrar um novo usuario via `/registrar`, confirmar login e que não vê botões de admin
- [x] 10.5 Promover usuario a admin_jogos, confirmar que vê `/novo` e `/<id>/editar` (bugfix aplicado: guarda de last-admin agora só bloqueia democao real de admin_sistema)
- [x] 10.6 Confirmar que visitante não logado vê catálogo mas não vê botões de ação
- [x] 10.7 Testar CSRF: inspecionar forms têm token; tentar POST sem token retorna 400

## 11. Finalização OpenSpec

- [x] 11.1 `/opsx:archive` da change `add-auth-system` após tudo verificado
