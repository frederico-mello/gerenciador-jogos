## Context

`create_app()` (app/__init__.py) hoje monta config, cria `instance/` e `data/`, chama `db.init_app(app)` (que só registra hooks de conexão/teardown) e registra o blueprint. Quem garante o schema é o passo manual `./scripts/run-as-app.sh scripts/init_db.py` durante o deploy (rsync + `systemctl restart`).

`db.init_db(db_path)` (app/db.py:29) já é idempotente e autocontido: cria o diretório pai se necessário, executa `app/schema.sql` (todo `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`), aplica `_apply_column_migrations` (ADD COLUMN idempotentes em `users`) e `_ensure_game_delete_cascade` (migração de FKs `loans.game_id` / `reservation_queue.game_id` para `ON DELETE CASCADE`, executada sob `PRAGMA foreign_keys=OFF` com recriação de tabela preservando dados). Abre e fecha a própria conexão — não depende de request/app context.

Ver proposta.md (Why) para a motivação; aqui tratamos apenas de onde e como ligar o `init_db` ao boot.

## Goals / Non-Goals

**Goals:**
- Migrar o schema automaticamente no boot da aplicação (Gunicorn em produção, `flask run`/testes localmente), sem passo manual no deploy.
- Reutilizar `init_db` existente sem alterá-lo — a mudança é apenas o ponto de chamada.

**Non-Goals:**
- Criar framework de migrations versionadas (down migrations, controle de revision) — o mecanismo idempotente atual continua sendo a fonte de verdade.
- Alterar `init_db`, `schema.sql` ou o conteúdo das migrações de FK.
- Paralelizar ou travar migração entre workers do Gunicorn (ver Riscos: carga é baixa e operações são idempotentes).
- Mudar o comportamento dos scripts administrativos, que continuam chamando `init_db` explicitamente.

## Decisions

- **Chamar `db.init_db(app.config["DATABASE_PATH"])` dentro de `create_app()`**, logo após a config final estar montada (após `test_config` ser aplicado e `DATA_DIR` criado) e antes de `db.init_app(app)`/registro do blueprint. Motivo: `init_db` recebe o path explícito, não depende de app context, e executar antes de qualquer request garante que nenhuma rota sirva dados com schema antigo. A config já define `DATABASE_PATH` para o arquivo em `instance/`; `test_config` pode sobrescrevê-la (usado pelos testes com `tmp_path`), então a chamada deve usar o valor final da config.
- **Chamar sempre, sem flag de ambiente.** `init_db` é idempotente e barato quando nada muda (leituras de `sqlite_master` + `executescript` de DDL `IF NOT EXISTS`); executar também em dev/testes mantém um único caminho de código e elimina a divergência entre ambientes. O fixture `tests/conftest.py` já chama `init_db` explicitamente; a chamada duplicada é inofensiva (idempotente).
- **Sem lock entre workers.** Com `2*CPU+1` workers do Gunicorn, todos executam `init_db` no boot. Operações são idempotentes e DDL `IF NOT EXISTS` é concorrência-segura na prática; a migração de recriação de tabela (`_recreate_table_with_cascade`) já roda em transação. Adicionar lock de arquivo (ex.: `fcntl`/portalocker) seria complexidade extra sem evidência de problema; se surgir `database is locked` esporádico, o `Restart=always` do systemd + idempotência cobrem a recuperação.
- **Falha de migração derruba o boot.** Se `init_db` levantar exceção (ex.: banco corrompido), `create_app()` propaga o erro e o Gunicorn não sobe; com `Restart=always` o systemd reinicia e o `journalctl` mostra o traceback. Preferível a subir servindo erros de schema mismatch.

## Risks / Trade-offs

- **Corrida entre workers no primeiro boot** (N workers recriando tabelas simultaneamente sobre um banco legado). Probabilidade baixa (janela de migração é curta e rara) e efeito limitado a erro de boot com restart automático; mitigação futura, se necessário, seria um `ExecStartPre` dedicado ou lock de arquivo — não agora.
- **Boot marginalmente mais lento**: `init_db` abre conexão extra e roda DDL/migrações a cada boot. Em banco pequeno (catálogo de jogos) é de milissegundos; aceitável.
- **Testes passam a depender do boot migrar o banco**: fixture que sobrescreve `DATABASE_PATH` via `test_config` recebe a migração de graça; o `init_db` explícito do fixture vira redundância — remover em implementação é opcional e seguro.

## Migration Plan

1. Em `app/__init__.py`, adicionar `db.init_db(app.config["DATABASE_PATH"])` após a definição da config final (incluindo `test_config`) e antes de `db.init_app(app)`.
2. Rodar a suíte de testes (`pytest`) — o fixture `app` de `tests/conftest.py` já cria banco físico via `tmp_path`; nenhuma alteração obrigatória.
3. Em produção, o próximo deploy (rsync + `systemctl restart gerenciador-jogos`) passa a migrar automaticamente; o passo manual `run-as-app.sh scripts/init_db.py` pode ser omitido (script continua disponível para uso ad-hoc).

## Open Questions

Nenhuma.