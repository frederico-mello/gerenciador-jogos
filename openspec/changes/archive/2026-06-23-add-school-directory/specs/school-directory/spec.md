## ADDED Requirements

### Requirement: Tabela schools com código INEP
O sistema SHALL manter um diretório de escolas em SQLite (tabela `schools`) com campos: `id` (PK), `codigo_inep` (TEXT, UNIQUE, pode ser NULL), `nome` (TEXT NOT NULL), `rede` (TEXT, em {federal, estadual, municipal, privada}), `endereco` (TEXT), `bairro` (TEXT), `cep` (TEXT), `ativo` (INTEGER DEFAULT 1), `created_at`, `updated_at`. O campo `codigo_inep` é a chave natural para idempotência de importação, mas permite NULL para escolas cadastradas manualmente sem INEP.

#### Scenario: Banco criado com tabela schools vazia
- **WHEN** o script `scripts/init_db.py` é executado
- **THEN** a tabela `schools` é criada vazia, além das tabelas `games` e `game_manual_pages` já existentes

#### Scenario: Escola com INEP
- **WHEN** uma escola com `codigo_inep = "35061274"` é inserida
- **THEN** a linha tem `id` autoincrement, `codigo_inep = "35061274"`, `nome` preenchido, `rede` em um dos valores permitidos, `ativo = 1`, e `created_at` preenchido

#### Scenario: Escola sem INEP (criada manualmente)
- **WHEN** uma escola é inserida com `codigo_inep = NULL`
- **THEN** a inserção é aceita (UNIQUE permite múltiplos NULLs no SQLite)

#### Scenario: INEP duplicado rejeitado
- **WHEN** tenta-se inserir uma escola com `codigo_inep` já existente
- **THEN** a inserção falha com violação de UNIQUE constraint

### Requirement: Importação do Censo Escolar INEP
O sistema SHALL fornecer um script CLI `scripts/import_schools.py` que lê um arquivo CSV dos microdados do Censo Escolar INEP, filtra por `CO_MUNICIPIO = 3549904` (São José dos Campos), e faz upsert idempotente na tabela `schools` usando `codigo_inep` (campo `CO_ENTIDADE` do CSV) como chave.

#### Scenario: Primeira importação
- **WHEN** o usuário executa `python scripts/import_schools.py --csv microdados_2024.csv` em um DB vazio
- **THEN** todas as escolas de SJC no CSV são inseridas, e o script imprime `[OK] <codigo_inep> <nome>` por escola, finalizando com "Total: X escolas importadas (federal: F, estadual: E, municipal: M, privada: P)"

#### Scenario: Re-importação (idempotência)
- **WHEN** o usuário re-executa o script com o mesmo CSV
- **THEN** nenhuma escola é duplicada; campos existentes são atualizados (nome, endereco, bairro, cep, rede); `id` e `ativo` são preservados

#### Scenario: CSV sem colunas esperadas
- **WHEN** o CSV não contém as colunas `CO_ENTIDADE`, `NO_ENTIDADE`, `CO_MUNICIPIO`, `TP_DEPENDENCIA`
- **THEN** o script aborta com mensagem de erro listando as colunas ausentes

#### Scenario: Mapeamento de rede
- **WHEN** o CSV tem `TP_DEPENDENCIA = 1` (federal), `2` (estadual), `3` (municipal), `4` (privada)
- **THEN** o campo `rede` em `schools` recebe o valor correspondente em inglês (`federal`, `estadual`, `municipal`, `privada`)

### Requirement: CRUD mínimo de escolas na UI
O sistema SHALL fornecer rotas para `admin_sistema` gerenciar escolas: `GET /admin/schools` (lista com filtro por rede e busca por nome), `GET /admin/schools/<id>/editar` (form de edição), `POST /admin/schools/<id>/editar` (atualiza), `POST /admin/schools/criar` (cria nova escola, opcionalmente sem INEP), `POST /admin/schools/<id>/inativar` (soft delete, `ativo=0`). Até a implementação do Change 1 (auth), estas rotas não terão proteção.

#### Scenario: Listar escolas
- **WHEN** o usuário acessa `GET /admin/schools`
- **THEN** a página mostra todas as escolas ativas, com filtro por rede e busca por nome, ordenadas por `nome`

#### Scenario: Editar endereço
- **WHEN** o admin edita o campo `endereco` de uma escola e submete
- **THEN** o registro é atualizado, `updated_at` muda, e a lista reflete o novo endereço

#### Scenario: Criar escola sem INEP
- **WHEN** o admin cria uma escola com nome "Escola Nova", rede "municipal", sem código INEP
- **THEN** uma nova linha é inserida com `codigo_inep = NULL` e `ativo = 1`

#### Scenario: Inativar escola
- **WHEN** o admin clica em "Inativar" para uma escola
- **THEN** o campo `ativo` muda para `0`, e a escola deixa de aparecer na listagem padrão (mas permanece no DB)

#### Scenario: Reativar escola
- **WHEN** o admin acessa o filtro "mostrar inativas" e clica em "Reativar"
- **THEN** o campo `ativo` volta para `1` e a escola reaparece na listagem padrão
