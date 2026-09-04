## 1. Schema

- [ ] 1.1 Add `ON DELETE CASCADE` to the `loans.game_id` and `reservation_queue.game_id` foreign keys in `app/schema.sql` and verify the file parses
- [ ] 1.2 Verify the `games` table still allows deletion of a game without associated loans

## 2. Database migration

- [ ] 2.1 Implement `ensure_on_delete_cascade(conn)` in `app/db.py` that renames the table and recreates it with the FK carrying `ON DELETE CASCADE`, executed under `PRAGMA foreign_keys=OFF`, preserving existing rows
- [ ] 2.2 Verify the migration is idempotent and preserves data when run against a legacy database (no cascade)

## 3. Game deletion guardrails

- [ ] 3.1 Update `models.delete_game()` to raise `GameHasActiveLoansError` when the game has loans with active status (solicitado, reservado, emprestado)
- [ ] 3.2 Verify a loan with historical status (devolvido, cancelado) does not block deletion and is removed in cascade
- [ ] 3.3 Update `routes.excluir()` to catch `GameHasActiveLoansError`, show a flash error instructing to resolve active loans, and redirect back to the game page without deleting files

## 4. Tests

- [ ] 4.1 Add unit tests covering: active loan blocks deletion, historical loan allows deletion in cascade, legacy database migration preserves data, and the route returns the flash error
- [ ] 4.2 Run the full test suite and confirm all tests pass
