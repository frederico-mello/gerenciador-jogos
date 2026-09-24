## MODIFIED Requirements

### Requirement: WSGI entry point para Gunicorn
O sistema SHALL fornecer um módulo `wsgi.py` na raiz do projeto que importa e expõe o objeto `app` criado por `create_app()`, servindo como entry point para o Gunicorn. A factory `create_app()` SHALL executar a inicialização/migração do banco de dados (`init_db` com o path configurado em `DATABASE_PATH`) durante a criação da aplicação, de forma idempotente: aplicar o schema declarado em `app/schema.sql` e as migrações de schema existentes (inclusive FKs `ON DELETE CASCADE` em `loans` e `reservation_queue`) sem destruir dados, de modo que o boot do Gunicorn torne o banco compatível com a versão deployada sem nenhum passo manual.

#### Scenario: Gunicorn carrega a aplicação via wsgi.py
- **WHEN** o Gunicorn é iniciado com `gunicorn wsgi:app`
- **THEN** a aplicação Flask é carregada corretamente e responde a requests HTTP

#### Scenario: wsgi.py funciona standalone para testes
- **WHEN** um desenvolvedor executa `python wsgi.py`
- **THEN** o servidor de desenvolvimento do Flask inicia em modo debug (apenas para desenvolvimento local)

#### Scenario: Boot do Gunicorn aplica o schema sem passo manual
- **WHEN** o serviço Gunicorn é reiniciado após um deploy (rsync + `systemctl restart`) com um `app/schema.sql` mais novo que o banco existente
- **THEN** o banco `instance/jogos.db` fica com o schema e as migrações aplicados ao final do boot, sem que nenhum comando de migração seja executado manualmente

#### Scenario: Inicialização é idempotente
- **WHEN** `create_app()` é chamado repetidamente (múltiplos workers do Gunicorn, reinicializações ou testes) sobre um banco já migrado
- **THEN** a execução de `init_db` não altera dados existentes nem falha (statements `IF NOT EXISTS` e migrações condicionais), e o banco permanece utilizável

#### Scenario: Banco inexistente é criado no boot
- **WHEN** `create_app()` roda em um ambiente onde `instance/jogos.db` ainda não existe (novo deploy ou ambiente limpo)
- **THEN** o banco é criado com o schema completo durante a factory, antes de qualquer request ser servido

#### Scenario: Migração de FKs ON DELETE CASCADE aplicada no boot
- **WHEN** o boot ocorre sobre um banco legado cujas FKs `loans.game_id` / `reservation_queue.game_id` não possuem `ON DELETE CASCADE`
- **THEN** ao final do boot as FKs referenciam `games(id) ON DELETE CASCADE` e as linhas existentes de `loans` e `reservation_queue` são preservadas