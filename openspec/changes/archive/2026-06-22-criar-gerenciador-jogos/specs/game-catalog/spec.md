## ADDED Requirements

### Requirement: Catálogo de jogos persistido em SQLite
O sistema SHALL manter um catálogo de jogos em um banco SQLite local (`instance/jogos.db`), com tabela `games` contendo os campos: `id` (PK), `nome` (NOT NULL), `area` (NOT NULL, em {anatomia, histologia, microbiologia}), `descricao` (texto longo), `regras_resumo`, `num_jogadores` (texto livre como "2–6"), `duracao_min` (INTEGER), `imagem_componentes` (path relativo a `data/`), `imagem_perfil` (path relativo), `created_at` (TIMESTAMP default CURRENT_TIMESTAMP), `updated_at` (TIMESTAMP atualizado em toda operação UPDATE).

#### Scenario: Banco criado vazio
- **WHEN** o script `scripts/init_db.py` é executado pela primeira vez
- **THEN** o arquivo `instance/jogos.db` é criado com a tabela `games` vazia e a tabela `game_manual_pages` (ver requisito "Manuais multipágina")

#### Scenario: Operação CREATE
- **WHEN** o usuário cria um jogo via form `/novo` com nome "Memotomia" e área "anatomia"
- **THEN** uma nova linha é inserida em `games` com `id` autoincrement, `created_at` preenchido, e `updated_at` igual a `created_at`

#### Scenario: Operação READ (lista)
- **WHEN** o usuário acessa `GET /`
- **THEN** todos os jogos são listados ordenados por `nome`, mostrando nome, área, e imagem de perfil

#### Scenario: Operação UPDATE
- **WHEN** o usuário edita um jogo via `POST /<id>/editar`
- **THEN** os campos modificados são persistidos e `updated_at` é atualizado para o timestamp corrente

#### Scenario: Operação DELETE
- **WHEN** o usuário confirma exclusão via `POST /<id>/excluir`
- **THEN** a linha correspondente é removida de `games` e suas páginas de manual são removidas em cascata de `game_manual_pages` (ON DELETE CASCADE)

### Requirement: Manuais multipágina
O sistema SHALL suportar manuais com múltiplas páginas, armazenadas na tabela `game_manual_pages` com campos: `id` (PK), `game_id` (FK → games(id) ON DELETE CASCADE), `ordem` (INTEGER), `path` (TEXT, relativo a `data/`). Cada jogo pode ter zero ou mais páginas de manual, ordenadas por `ordem`.

#### Scenario: Jogo com manual de 2 páginas
- **WHEN** o jogo "Trunfo citologia" tem `manual_1.jpg` e `manual_2.jpg`
- **THEN** existem 2 linhas em `game_manual_pages` com `game_id` correspondente, `ordem` 1 e 2, e paths `histologia/trunfo-citologia/manual_1.jpg` e `histologia/trunfo-citologia/manual_2.jpg`

#### Scenario: Excluir jogo com manuais
- **WHEN** um jogo com manuais é excluído
- **THEN** todas as linhas em `game_manual_pages` com o `game_id` correspondente são removidas automaticamente por cascade

### Requirement: Filtro por área e busca por nome
O sistema SHALL permitir filtrar a lista de jogos por área e buscar por texto no nome, via query string `?area=<area>&q=<texto>`.

#### Scenario: Filtro por área
- **WHEN** o usuário acessa `GET /?area=anatomia`
- **THEN** apenas jogos com `area = 'anatomia'` são listados

#### Scenario: Busca por nome
- **WHEN** o usuário acessa `GET /?q=memotomia`
- **THEN** apenas jogos cujo `nome` contém "memotomia" (case-insensitive) são listados

#### Scenario: Filtro combinado
- **WHEN** o usuário acessa `GET /?area=histologia&q=celula`
- **THEN** apenas jogos de histologia cujo nome contém "celula" são listados

### Requirement: Validação de campos obrigatórios
O sistema SHALL validar que `nome` e `area` são obrigatórios no form de criar/editar. `area` deve ser um dos três valores permitidos.

#### Scenario: Nome ausente
- **WHEN** o usuário submete o form `/novo` com campo `nome` vazio
- **THEN** o sistema retorna o form com mensagem de erro "Nome é obrigatório" e não persiste

#### Scenario: Área inválida
- **WHEN** o usuário submete com `area = "quimica"`
- **THEN** o sistema retorna o form com mensagem "Área inválida" e não persiste
