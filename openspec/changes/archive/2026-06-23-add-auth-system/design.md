## Context

O sistema `gerenciador-jogos` hoje é single-user sem auth. O Change 0 (`add-school-directory`) introduziu a tabela `schools`. Este change adiciona a tabela `users` e o sistema de autenticação, preparando o terreno para empréstimos (Change 2).

Stack: Flask + SQLite + Jinja2 (server-side rendering). Sessões Flask já são embutidas (usam `SECRET_KEY`). Para hash de senha, `werkzeug.security` (já vem com Flask). Para CSRF, `Flask-WTF`.

## Goals / Non-Goals

**Goals:**
- 3 papéis com permissões distintas: `admin_sistema`, `admin_jogos`, `usuario`.
- Self-registration de usuários com indicação de escola (lista controlada do Change 0).
- Hash de senha seguro (werkzeug).
- Sessão Flask com `SECRET_KEY` via env var.
- CSRF protection em todos os forms.
- CRUD de usuários para `admin_sistema` (incluindo promote/demote de role).
- Soft delete de usuários (`ativo=0`) para preservar histórico de empréstimos.
- Bootstrap do primeiro admin via CLI.
- Proteção das rotas existentes de jogos (criar/editar/excluir) e de `/admin/schools`.

**Non-Goals:**
- OAuth / login social (fora de escopo).
- Recuperação de senha por email (será no Change 3 com notificações).
- Two-factor authentication (fora de escopo).
- Lockout por tentativas falhas (nice-to-have futuro).
- Logs de auditoria de login (pode ser adicionado depois).

## Decisions

### 1. Hash de senha: `werkzeug.security`
**Por que:** Já vem com Flask, sem dependência extra. `generate_password_hash` usa PBKDF2 com salt aleatório por padrão.
**Alternativas:** `bcrypt` (requer compilador C no Windows), `argon2` (requer instalador extra). Werkzeug é suficiente para um sistema local.

### 2. Sessão Flask (não Flask-Login)
**Por que:** Flask sessions já são embutidas. Para um sistema simples com 3 papéis, um helper `current_user()` que lê `session['user_id']` + decorators `@login_required` / `@role_required` são suficientes. Flask-Login adiciona complexidade desnecessária.
**Alternativas:** Flask-Login — descartado por overkill.

**Implementação:**
```python
# app/auth.py
from functools import wraps
from flask import session, redirect, url_for, abort, flash
from . import models

def current_user():
    uid = session.get('user_id')
    if uid is None:
        return None
    return models.get_user(uid)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash('Login necessário.', 'error')
            return redirect(url_for('games.login'))
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user or user['role'] not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator
```

### 3. Modelo de dados: tabela `users`
**Schema:**
```sql
CREATE TABLE users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  nome          TEXT NOT NULL,
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL CHECK(role IN
                  ('admin_sistema','admin_jogos','usuario')),
  escola_id     INTEGER,
  ativo         INTEGER DEFAULT 1,
  created_at    TEXT DEFAULT (datetime('now','localtime')),
  updated_at    TEXT DEFAULT (datetime('now','localtime')),
  FOREIGN KEY (escola_id) REFERENCES schools(id)
);
CREATE INDEX idx_users_escola ON users(escola_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_ativo ON users(ativo);
```

**Decisões:**
- `escola_id` é NULL para `admin_sistema` e `admin_jogos` (admins não precisam indicar escola). Para `usuario`, é NOT NULL em runtime (validado no form, não no schema).
- `ativo = 0` é soft delete. Login de usuário inativo é rejeitado. Histórico de empréstimos preservado.

### 4. Self-registration: usuário ativo imediatamente
**Por que:** Decidido no explore mode — sem fricção de aprovação. Usuário recém-cadastrado pode pedir empréstimo imediatamente.
**Risco aceito:** Spam/abuso possível, mas sistema é para uso controlado em SJC.
**Implementação:** `POST /registrar` cria usuário com `role='usuario'`, `ativo=1`, e redireciona para `/login`.

### 5. Bootstrap do primeiro admin: `scripts/create_admin.py`
**Por que:** Chicken-and-egg: tabela `users` vazia, só `admin_sistema` pode criar usuários, mas não existe admin ainda. CLI resolve explicitamente.
**Uso:** `python scripts/create_admin.py` (prompt interativo para nome, email, senha) ou com args `--nome --email --senha`.
**Alternativas consideradas:** auto-promoção do primeiro registro (perigoso), seed no `init_db.py` com senha default (inseguro). CLI é explícito e auditável.

### 6. CSRF via Flask-WTF
**Por que:** Padrão multi-user. `Flask-WTF` fornece `CSRFProtect` que protege todos os POSTs. Forms passam a herdar de `FlaskForm` ou usar `{{ csrf_token() }}` nos templates.
**Alternativas:** implementar CSRF manualmente — descartado, Flask-WTF é padrão e bem testado.

### 7. SECRET_KEY via env var
**Por que:** Hoje é hardcoded `"dev-local-key"` em `app/__init__.py`. Com login real, isso é inaceitável.
**Implementação:**
```python
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
if not app.config['SECRET_KEY']:
    # Dev fallback com warning
    app.config['SECRET_KEY'] = 'dev-insecure-key'
    app.logger.warning('FLASK_SECRET_KEY não definida — usando chave dev insegura')
```

### 8. Nav dinâmico por role
**Implementação:** `base.html` verifica `current_user()['role']` e mostra links condicionalmente:
- Visitante não logado: "Login", "Registrar"
- `usuario`: "Meus empréstimos", "Logout"
- `admin_jogos`: "Novo jogo", "Empréstimos (admin)", "Logout"
- `admin_sistema`: tudo de `admin_jogos` + "Usuários", "Escolas", "Logout"

### 9. Campo escola no registro: `<select>` com busca
**Por que:** ~400 escolas é muito para um `<select>` simples. Opções:
- `<select>` com `<datalist>` (autocomplete nativo HTML5) — simples, sem JS.
- `<select>` com AJAX (busca incremental via API) — mais UX, mas requer endpoint.

**Decisão:** Começar com `<datalist>` (autocomplete nativo). Se UX for insuficiente, migrar para AJAX no Change 3.

## Risks / Trade-offs

- **[Self-registration sem verificação]** → Trade-off aceito: conveniência > segurança em ambiente escolar controlado. Risco mitigado pelo fato de empréstimos exigirem aprovação manual de admin.
- **[SECRET_KEY em dev fallback]** → Mitigação: warning no log. Em produção, definir `FLASK_SECRET_KEY` via variável de ambiente.
- **[Sem recuperação de senha]** → Trade-off: admin_sistema pode redefinir senha de qualquer usuário via `/admin/users/<id>/editar`. Recuperação por email fica para Change 3.
- **[Datalist pode não funcionar em browsers antigos]** → Mitigação: fallback para `<select>` simples com scroll.
- **[Janela entre Change 0 e Change 1 onde /admin/schools é público]** → Resolvido neste change.

## Migration Plan

1. Adicionar tabela `users` ao `app/schema.sql`.
2. Atualizar `scripts/init_db.py` (valida criação de `users`).
3. Adicionar `Flask-WTF` a `requirements.txt`.
4. Criar `app/auth.py` (decorators, `current_user`).
5. Adicionar funções de usuário em `app/models.py`.
6. Adicionar rotas de auth + admin/users em `app/routes.py`.
7. Proteger rotas existentes com decorators.
8. Criar `scripts/create_admin.py`.
9. Criar templates (login, registrar, admin_users, admin_user_form).
10. Atualizar `base.html` com nav dinâmico.
11. Após deploy: rodar `python scripts/create_admin.py` para criar o primeiro admin.
12. **Rollback:** remover tabela `users`, reverter rotas ao estado anterior, remover `auth.py`, reverter `SECRET_KEY` para dev.

## Open Questions

- Nenhuma pendente. Todas as decisões foram confirmadas durante o explore mode.
