## Why

O deploy de produção (rsync + `systemctl restart`) não migra o schema do banco automaticamente: hoje quem garante `instance/jogos.db` atualizado é o passo manual `./scripts/run-as-app.sh scripts/init_db.py`. Se esse passo for esquecido, o app sobe com schema desatualizado (ex.: FKs `loans.game_id` / `reservation_queue.game_id` sem `ON DELETE CASCADE`) e comportamentos dependentes de migração falham em produção. Como o `init_db` já existe, é idempotente e executa as migrações (`_apply_column_migrations`, `_ensure_game_delete_cascade`), basta executá-lo automaticamente no boot da aplicação.

## What Changes

- `create_app()` passa a chamar `db.init_db(app.config["DATABASE_PATH"])` durante a factory, antes de registrar blueprint e rotas.
- Com isso, o boot do Gunicorn (`wsgi.py` → `create_app()`) aplica o schema e as migrações idempotentes sem passo manual.
- Scripts administrativos (`scripts/init_db.py`, `create_admin.py`, `import_schools.py`) continuam chamando `init_db` normalmente — comportamento inalterado.

## Capabilities

### New Capabilities
- (nenhuma)

### Modified Capabilities
- `production-infra`: o requisito "WSGI entry point para Gunicorn" passa a exigir que `create_app()` inicialize/migre o banco (`init_db`) no boot, de forma idempotente, sem passo manual no deploy.

## Impact

- `app/__init__.py` — `create_app()` ganha a chamada `db.init_db(app.config["DATABASE_PATH"])` (idempotente; segura para múltiplos workers e reexecuções).
- Sem mudanças em `app/db.py`, `app/schema.sql`, rotas ou scripts — `init_db` e as migrações de FKs ON DELETE CASCADE já existem.
- Testes: confirmar que `create_app()` já executa `init_db` (o fixture `tests/conftest.py` chama `init_db` explicitamente; passa a ser redundante, mas inofensivo).