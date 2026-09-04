## Why

O sistema hoje exclui jogos via `POST /<id>/excluir` apenas removendo a linha de `games`, sem verificar se o jogo possui empréstimos (ou filas de reserva) associados. Jogos emprestados continuam aparecendo como disponíveis nas listas de admin e no catálogo, gerando divergência entre o estado persistido e o comportamento observado.

## What Changes

- A exclusão de um jogo passa a ser bloqueada enquanto houver empréstimos com status ativo (`solicitado`, `reservado`, `emprestado`), exibindo uma mensagem de erro orientando o administrador a devolver/cancelar antes de excluir.
- Empréstimos com status histórico (`devolvido`, `cancelado`) e entradas de fila de reserva (`reservation_queue`) são removidos em cascata junto com o jogo.
- As chaves estrangeiras `loans.game_id` e `reservation_queue.game_id` passam a ter `ON DELETE CASCADE`; bancos já existentes são migrados automaticamente preservando os dados.
- A exclusão move os arquivos de dados do jogo (`data/<area>/<slug>/`) e remove o registro do catálogo.
- Mensagem de sucesso/fail padronizada via flash, redirecionando para a página do jogo no caso de bloqueio.

## Capabilities

### New Capabilities
- (nenhuma — o comportamento é de guardrails sobre capacidades existentes)

### Modified Capabilities
- `game-catalog`: o requisito "Operação DELETE" passa a exigir bloqueio quando o jogo possui empréstimos ativos, cascade de histórico e arquivos, e feedback via flash.
- `loans`: a FK `loans.game_id` passa a ter `ON DELETE CASCADE`, com migração de bancos pré-existentes.

## Impact

- `app/models.py` — `delete_game()` passa a validar empréstimos ativos e levantar exceção específica.
- `app/db.py` — migração idempotente das FKs para `ON DELETE CASCADE`.
- `app/schema.sql` — definição das FKs com `ON DELETE CASCADE`.
- `app/routes.py` — rota `excluir` trata a exceção com flash e redirect.
- `app/models.py` — `_remove_game_files` / `slugify` já existentes preservados.
- Testes: cobertura de exclusão com empréstimo ativo/histórico e migração de banco legado.
