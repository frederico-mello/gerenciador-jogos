## 1. Boot da aplicação

- [ ] 1.1 Em `app/__init__.py`, adicionar `db.init_db(app.config["DATABASE_PATH"])` em `create_app()` após a montagem da config final (incluindo `test_config`) e antes de `db.init_app(app)`/registro do blueprint
- [ ] 1.2 Verificar que `python -c "from app import create_app; app = create_app(); print('ok')"` executa sem erro e cria/mantém `instance/jogos.db`

## 2. Idempotência e migração

- [ ] 2.1 Confirmar com teste/manual que chamar `create_app()` duas vezes seguidas sobre o mesmo `DATABASE_PATH` não altera dados nem falha (schema `IF NOT EXISTS` + migrações condicionais)
- [ ] 2.2 Confirmar que boot sobre banco legado (FKs sem `ON DELETE CASCADE` em `loans`/`reservation_queue`) termina com FKs em cascade e linhas preservadas — cobrir com teste que cria banco pré-migração, chama `create_app()` e inspeciona `sqlite_master`/dados

## 3. Testes

- [ ] 3.1 Ajustar `tests/conftest.py` se necessário (o `init_db` explícito do fixture `app` torna-se redundante; remover é opcional e seguro) e rodar `pytest` completo, garantindo que nenhum teste depende de o banco NÃO ter sido migrado no boot
- [ ] 3.2 Rodar a suíte completa (`pytest`) e confirmar todos os testes passando

## 4. Documentação de deploy

- [ ] 4.1 Verificar se `README.md`/`deploy/` mencionam o passo manual de migração (`run-as-app.sh scripts/init_db.py`) e atualizar o texto para indicar que a migração ocorre automaticamente no boot (o script permanece disponível para uso ad-hoc)