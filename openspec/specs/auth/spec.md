# Capability: auth

## Purpose

TBD — Autenticação por sessão Flask, 3 papéis (admin_sistema, admin_jogos, usuario), self-registration com escola, CRUD de usuários para admin_sistema, hash de senha, CSRF protection.

## Requirements

### Requirement: Tabela users com hash de senha e 3 papéis
O sistema SHALL manter uma tabela `users` em SQLite com campos: `id` (PK), `nome` (TEXT NOT NULL), `email` (TEXT UNIQUE NOT NULL), `password_hash` (TEXT NOT NULL), `role` (TEXT NOT NULL, CHECK em {'admin_sistema', 'admin_jogos', 'usuario'}), `escola_id` (INTEGER FK → schools(id), pode ser NULL para admins), `ativo` (INTEGER DEFAULT 1), `created_at`, `updated_at`. Senhas são armazenadas como hash via `werkzeug.security.generate_password_hash` (PBKDF2 com salt), nunca em texto plano.

#### Scenario: Usuário criado com hash
- **WHEN** um usuário é criado com senha "minhasenha123"
- **THEN** `password_hash` contém um hash PBKDF2 (não o texto plano), e `check_password_hash(password_hash, "minhasenha123")` retorna True

#### Scenario: Email duplicado rejeitado
- **WHEN** tenta-se criar um usuário com email já existente
- **THEN** a inserção falha com violação de UNIQUE constraint

#### Scenario: Role inválida rejeitada
- **WHEN** tenta-se inserir um usuário com `role = 'superuser'`
- **THEN** a inserção falha com violação de CHECK constraint

#### Scenario: Usuário sem escola (admin)
- **WHEN** um `admin_sistema` é criado via `scripts/create_admin.py`
- **THEN** `escola_id` é NULL e `role = 'admin_sistema'`

#### Scenario: Usuário com escola (usuario comum)
- **WHEN** um `usuario` se auto-registra indicando escola_id=5
- **THEN** `escola_id = 5`, `role = 'usuario'`, `ativo = 1`

### Requirement: Sessão Flask com SECRET_KEY via env var
O sistema SHALL usar sessões Flask (cookie assinado) para manter o usuário autenticado entre requests. A `SECRET_KEY` é lida da variável de ambiente `FLASK_SECRET_KEY`. Se não definida, o sistema usa uma chave dev insegura com warning no log.

#### Scenario: Login bem-sucedido
- **WHEN** o usuário submete `/login` com email e senha corretos
- **THEN** `session['user_id']` é definido, e o navegador redireciona para `/`

#### Scenario: Login com senha incorreta
- **WHEN** o usuário submete `/login` com senha incorreta
- **THEN** o sistema re-renderiza o form com mensagem "Credenciais inválidas" e `session` permanece vazia

#### Scenario: Login com email inexistente
- **WHEN** o usuário submete `/login` com email não cadastrado
- **THEN** o sistema re-renderiza o form com mensagem "Credenciais inválidas" (não revela que o email não existe)

#### Scenario: Login de usuário inativo
- **WHEN** o usuário tem `ativo = 0` e tenta fazer login com senha correta
- **THEN** o login é rejeitado com mensagem "Conta inativa. Contate um administrador."

#### Scenario: Logout
- **WHEN** o usuário clica em "Logout"
- **THEN** `session` é limpa e o navegador redireciona para `/`

#### Scenario: SECRET_KEY não definida
- **WHEN** a env var `FLASK_SECRET_KEY` não está definida
- **THEN** o sistema usa chave dev insegura e registra warning no log

### Requirement: Decorators de autorização
O sistema SHALL fornecer decorators `@login_required` (exige usuário logado) e `@role_required(*roles)` (exige usuário logado com um dos papéis especificados) em `app/auth.py`. Usuário não logado é redirecionado para `/login`. Usuário logado sem permissão recebe HTTP 403.

#### Scenario: Rota protegida sem login
- **WHEN** um visitante não logado acessa `GET /novo`
- **THEN** é redirecionado para `/login` com mensagem "Login necessário"

#### Scenario: Rota protegida com role insuficiente
- **WHEN** um `usuario` logado acessa `POST /<id>/excluir`
- **THEN** recebe HTTP 403 Forbidden

#### Scenario: Rota protegida com role suficiente
- **WHEN** um `admin_jogos` logado acessa `GET /novo`
- **THEN** o form de criação é renderizado normalmente

### Requirement: Self-registration com escola
O sistema SHALL permitir que visitantes se cadastrem em `GET/POST /registrar`. O form coleta: nome, email, senha, confirmação de senha, e escola (via `<datalist>` autocomplete com todas as escolas ativas de `schools`). Após cadastro, `role = 'usuario'`, `ativo = 1`, e o usuário pode fazer login imediatamente.

#### Scenario: Cadastro válido
- **WHEN** o visitante preenche nome "Maria Silva", email "[EMAIL]", senha "****", escola "EE Prof. Alceu Maynard Araujo" e submete
- **THEN** um novo usuário é criado com `role='usuario'`, `ativo=1`, `escola_id` correspondente, e o navegador redireciona para `/login` com mensagem de sucesso

#### Scenario: Senhas não conferem
- **WHEN** o visitante preenche senha e confirmação diferentes
- **THEN** o form é re-renderizado com erro "Senhas não conferem"

#### Scenario: Email já cadastrado
- **WHEN** o visitante usa email já existente no DB
- **THEN** o form é re-renderizado com erro "Email já cadastrado"

#### Scenario: Escola obrigatória para usuario
- **WHEN** o visitante não seleciona nenhuma escola
- **THEN** o form é re-renderizado com erro "Escola é obrigatória"

### Requirement: CRUD de usuários para admin_sistema
O sistema SHALL fornecer rotas para `admin_sistema` gerenciar usuários: `GET /admin/users` (lista com filtros por role, escola, ativo), `GET /admin/users/<id>/editar` (form), `POST /admin/users/<id>/editar` (atualiza nome, email, escola, senha opcional, ativo), `POST /admin/users/<id>/role` (promote/demote role). Apenas `admin_sistema` pode acessar estas rotas. `admin_jogos` e `usuario` recebem 403.

#### Scenario: Listar usuários
- **WHEN** o `admin_sistema` acessa `GET /admin/users`
- **THEN** a página mostra todos os usuários (nome, email, role, escola, ativo) com filtros por role e escola

#### Scenario: Editar usuário
- **WHEN** o `admin_sistema` edita o nome de um usuário e submete
- **THEN** o registro é atualizado e `updated_at` muda

#### Scenario: Redefinir senha
- **WHEN** o `admin_sistema` preenche o campo "nova senha" no form de edição
- **THEN** `password_hash` é atualizado com o hash da nova senha

#### Scenario: Promover usuario a admin_jogos
- **WHEN** o `admin_sistema` muda o role de um usuário de `usuario` para `admin_jogos` via `POST /admin/users/<id>/role`
- **THEN** `role` muda para `admin_jogos` e `escola_id` pode ser mantido ou definido como NULL

#### Scenario: Inativar usuário (soft delete)
- **WHEN** o `admin_sistema` clica em "Inativar" para um usuário
- **THEN** `ativo` muda para `0`, o usuário não pode mais fazer login, mas seus empréstimos históricos são preservados

#### Scenario: admin_jogos tenta acessar CRUD de usuários
- **WHEN** um `admin_jogos` acessa `GET /admin/users`
- **THEN** recebe HTTP 403

### Requirement: Bootstrap do primeiro admin via CLI
O sistema SHALL fornecer um script CLI `scripts/create_admin.py` que cria o primeiro usuário com `role='admin_sistema'`. Aceita argumentos `--nome`, `--email`, `--senha` ou prompta interativamente. Se já existe algum `admin_sistema`, o script pede confirmação antes de criar outro.

#### Scenario: Criar primeiro admin
- **WHEN** o usuário executa `python scripts/create_admin.py --nome "Alice" --email "[EMAIL]" --senha "****"` em um DB sem admins
- **THEN** um usuário é criado com `role='admin_sistema'`, `ativo=1`, `escola_id=NULL`, e o script imprime "Admin criado: [EMAIL]"

#### Scenario: Já existe admin
- **WHEN** o script é executado e já existe um `admin_sistema`
- **THEN** o script pede confirmação: "Já existe um admin_sistema. Criar outro? (s/N)"

### Requirement: CSRF protection em todos os forms
O sistema SHALL proteger todos os forms POST com CSRF token via `Flask-WTF` (`CSRFProtect`). O token é injetado nos templates via `{{ csrf_token() }}` ou `{{ form.csrf_token }}`. Requests POST sem token válido recebem HTTP 400.

#### Scenario: Form com CSRF token
- **WHEN** o usuário submete o form de login
- **THEN** o token CSRF é validado e o request é processado

#### Scenario: CSRF token inválido
- **WHEN** um request POST é enviado sem token CSRF ou com token inválido
- **THEN** o sistema retorna HTTP 400 Bad Request

### Requirement: Catálogo público read-only
O sistema SHALL manter as rotas `GET /`, `GET /<id>`, `GET /media/<path:filename>` públicas (acessíveis sem login). Apenas as rotas de ação (criar, editar, excluir) requerem login.

#### Scenario: Visitante não logado vê catálogo
- **WHEN** um visitante não logado acessa `GET /`
- **THEN** a lista de jogos é exibida normalmente, sem botões de criar/editar/excluir

#### Scenario: Visitante não logado vê detalhe
- **WHEN** um visitante não logado acessa `GET /<id>`
- **THEN** o detalhe do jogo é exibido, sem botões de editar/excluir
