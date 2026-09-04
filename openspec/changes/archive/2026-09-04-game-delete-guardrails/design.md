## Context

O sistema exclui jogos em `app/routes.py:excluir`, chamando `models.delete_game()` e depois `_remove_game_files()`. Hoje não há verificação de empréstimos associados; além disso, o schema (`app/schema.sql`) define as FKs `loans.game_id` e `reservation_queue.game_id` **sem** `ON DELETE CASCADE`, o que causa `IntegrityError: FOREIGN KEY constraint failed` ao excluir um jogo que possua empréstimos, e os jogos permanecem no banco. O `PRAGMA foreign_keys` está ativado em `app/db.py`, portanto a restrição é efetiva.

Existem `slugify`/`resize_image` em `app/importer.py`, `slug = slugify(data["nome"])` nas rotas, e `_remove_game_files(area, slug)` em `app/routes.py:308`. Não há ainda migração de schema após a criação do banco.

## Goals / Non-Goals

**Goals:**
- Impedir exclusão de jogos com empréstimos ativos e exibir erro orientando a resolução.
- Garantir que a exclusão remova em cascata empréstimos/histórico e filas de reserva, sem orfãos.
- Migrar bancos pré-existentes para `ON DELETE CASCADE` preservando os dados.

**Non-Goals:**
- Reestruturar o fluxo de empréstimos, filas ou catálogo.
- Alterar rotas de devolução/cancelamento ou o status dos empréstimos.

## Decisions

- **Verificação em `models.delete_game()` via `SELECT COUNT(*)` por status ativo** em vez de delegar ao cascade do SQLite. Motivo: o cascade do SQLite apaga silenciosamente, sem dar ao admin a oportunidade de ver a mensagem de bloqueio; a verificação explícita permite levantar `GameHasActiveLoansError` e exibir flash de erro. Alternativa considerada — `DELETE ... WHERE NOT EXISTS loan` — foi descartada por não separar "ativo" de "histórico".
- **Statuses ativos = {solicitado, reservado, emprestado}.** Empréstimos `devolvido`/`cancelado` permitem exclusão (não impactam disponibilidade). Decisão derivada do comportamento de badge de disponibilidade já documentado.
- **Migração idempotente via `ALTER TABLE ... RENAME` + recriação.** SQLite não suporta `DROP CONSTRAINT`; a técnica padrão é renomear a tabela, recriar com a FK alterada e re-injetar os dados. Fazer isso sob `PRAGMA foreign_keys=OFF` para evitar falha durante a recriação. Alternativas (recriar schema do zero) foram rejeitadas por perda de dados.
- **Remoção em cascata via cascade do SQLite para `loans`/`reservation_queue`.** Não é necessário deletar manualmente essas linhas no model, pois o cascade do SQLite (após migração) remove as linhas filhas.

## Risks / Trade-offs

- **Perda de dados em migração (rename+recriar).** Risco de perda de linhas ou índices durante a migração. → Migração executada com `foreign_keys=OFF`, transação explícita, e recriação preservando dados existentes; testar contra um banco legado antes de aplicar.
- **`PRAGMA foreign_keys=OFF` na migração.** Desativa enforcement globalmente durante a migração. → Reativar imediatamente após; escopo limitado ao bloco de migração.
- **Slug de arquivo vs. slug de exclusão.** A rota já usa `slug = slugify(nome)` no momento da exclusão; se o nome do jogo mudou depois do upload, a pasta `data/<area>/<slug>/` pode não corresponder. → Fora do escopo desta mudança; preservada a lógica existente.

## Migration Plan

1. Adicionar `ensure_on_delete_cascade(conn)` em `app/db.py`, executada após `init_db()` (ou em `teardown_appcontext`/startup do app), preservando `foreign_keys=ON` fora do bloco de migração.
2. Atualizar `app/schema.sql` para declarar as FKs com `ON DELETE CASCADE`.
3. Atualizar `app/models.py:delete_game()` para validar status ativos e levantar `GameHasActiveLoansError`.
4. Atualizar `app/routes.py:excluir()` para capturar a exceção e exibir flash de erro.
5. Testes unitários para exclusão com empréstimo ativo/histórico e migração de banco legado.

## Open Questions

Nenhuma. Se houver dúvida sobre quais status contam como "ativos", confirmar com o admin antes de codificar.
