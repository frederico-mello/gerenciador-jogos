## ADDED Requirements

### Requirement: FK loans.game_id com cascade
O sistema SHALL declarar a chave estrangeira `game_id` da tabela `loans` como `game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE`. Bancos criados antes dessa mudança mantêm a FK sem cascade até que a migração `ensure_on_delete_cascade` seja executada; após a migração, a exclusão de um jogo remove em cascata os empréstimos (`loans`) e as entradas de fila (`reservation_queue`) associados.

#### Scenario: FK loans aponta para games com cascade
- **WHEN** o schema é aplicado ou a migração `ensure_on_delete_cascade` é executada
- **THEN** a coluna `game_id` da tabela `loans` referencia `games(id)` com `ON DELETE CASCADE`

#### Scenario: Migração preserva dados existentes
- **WHEN** um banco pré-existente (sem cascade na FK `loans.game_id`) é aberto e a migração é executada
- **THEN** as linhas de `loans` e `reservation_queue` existentes são preservadas e a definição passa a incluir `ON DELETE CASCADE`
