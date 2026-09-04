# Capability: game-catalog

## Purpose

TBD — Persistência do catálogo de jogos em SQLite local, incluindo manuais multipágina, filtros e validação.

## Requirements

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
### Requirement: Bloqueio de exclusão de jogos com empréstimos ativos
O sistema NÃO SHALL excluir um jogo que possua ao menos um empréstimo com status ativo (`solicitado`, `reservado` ou `emprestado`). Ao confirmar a exclusão via `POST /<id>/excluir`, o sistema deve verificar a existência de empréstimos ativos e, havendo algum, NÃO remover o jogo, exibir uma mensagem de erro orientando que o administrador deva devolver ou cancelar os empréstimos ativos antes, e redirecionar de volta para a página do jogo (`GET /<id>`). O sistema NÃO SHALL mover nem remover os arquivos de dados do jogo neste caso.

#### Scenario: Excluir jogo emprestado
- **WHEN** um administrador confirma a exclusão de um jogo que possui um empréstimo com `status='emprestado'` via `POST /<id>/excluir`
- **THEN** o jogo NÃO é removido do catálogo, aparece flash de erro informando que existem empréstimos ativos e o administrador é redirecionado para a página do jogo

#### Scenario: Excluir jogo com solicitação em aberto
- **WHEN** um administrador confirma a exclusão de um jogo que possui um empréstimo com `status='solicitado'` via `POST /<id>/excluir`
- **THEN** o jogo NÃO é removido, aparece flash de erro e o administrador é redirecionado para a página do jogo

#### Scenario: Excluir jogo após resolver empréstimos
- **WHEN** um administrador devolve ou cancela todos os empréstimos ativos de um jogo e só então confirma a exclusão
- **THEN** o jogo é removido do catálogo, os empréstimos históricos são removidos em cascata e os arquivos de dados são apagados

### Requirement: Remoção em cascata de empréstimos e filas
O sistema SHALL remover, em cascata, todas as linhas de `loans` e de `reservation_queue` cujo `game_id` aponte para um jogo excluído, de forma que nenhum empréstimo ou entrada de fique órfão após a exclusão. A exclusão do jogo via `POST /<id>/excluir` deve propagar a remoção para essas tabelas.

#### Scenario: Exclusão remove empréstimos e filas associados
- **WHEN** um jogo com empréstimos e entradas de fila é excluído
- **THEN** todas as linhas de `loans` e `reservation_queue` associadas a esse `game_id` são removidas simultaneamente


### Requirement: Manuais multipágina
O sistema SHALL suportar manuais com múltiplas páginas, armazenadas na tabela `game_manual_pages` com campos: `id` (PK), `game_id` (FK → games(id) ON DELETE CASCADE), `ordem` (INTEGER), `path` (TEXT, relativo a `data/`). Cada jogo pode ter zero ou mais páginas de manual, ordenadas por `ordem`.

#### Scenario: Jogo com manual de 2 páginas
- **WHEN** o jogo "Trunfo citologia" tem `manual_1.jpg` e `manual_2.jpg`
- **THEN** existem 2 linhas em `game_manual_pages` com `game_id` correspondente, `ordem` 1 e 2, e paths `histologia/trunfo-citologia/manual_1.jpg` e `histologia/trunfo-citologia/manual_2.jpg`

#### Scenario: Excluir jogo com manuais
- **WHEN** um jogo com manuais é excluído
- **THEN** todas as linhas em `game_manual_pages` com o `game_id` correspondente são removidas automaticamente por cascade

### Requirement: Filtro por área e busca textual
O sistema SHALL permitir filtrar a lista de jogos por área e buscar por texto nos campos `nome`, `descricao` e `regras_resumo`, via query string `?area=<area>&q=<texto>`.

A busca SHALL ser:
- **Insensível a acentos**: uma consulta digitada sem acento (ex.: "mucosa") deve encontrar registros que contenham o termo com ou sem acento (ex.: "mucósa").
- **Multi-termo com lógica AND**: quando `q` contiver múltiplas palavras separadas por espaço, todas devem aparecer em pelo menos um dos campos pesquisados (nome, descricao ou regras_resumo), em qualquer ordem.
- **Insensível a maiúsculas/minúsculas**: a comparação deve ignorar capitalização.

#### Scenario: Filtro por área
- **WHEN** o usuário acessa `GET /?area=anatomia`
- **THEN** apenas jogos com `area = 'anatomia'` são listados

#### Scenario: Busca por nome
- **WHEN** o usuário acessa `GET /?q=memotomia`
- **THEN** apenas jogos cujo `nome` contém "memotomia" (case-insensitive) são listados

#### Scenario: Busca por texto na descrição
- **WHEN** o usuário acessa `GET /?q=mitose`
- **THEN** jogos cujo campo `descricao` ou `regras_resumo` contém "mitose" são listados, mesmo que o termo não apareça no `nome`

#### Scenario: Busca insensível a acentos na descrição
- **WHEN** o usuário acessa `GET /?q=mucosa`
- **THEN** jogos cujo campo `descricao` contém "mucósa" (com acento) são listados

#### Scenario: Busca insensível a acentos no nome
- **WHEN** o usuário acessa `GET /?q=joao`
- **THEN** jogos cujo `nome` contém "João" são listados

#### Scenario: Busca com múltiplos termos
- **WHEN** o usuário acessa `GET /?q=anatomia celula`
- **THEN** apenas jogos que contenham tanto "anatomia" quanto "celula" (em qualquer combinação dos campos nome, descricao ou regras_resumo) são listados

#### Scenario: Filtro combinado
- **WHEN** o usuário acessa `GET /?area=histologia&q=celula`
- **THEN** apenas jogos de histologia cujo nome, descricao ou regras_resumo contêm "celula" são listados

### Requirement: Validação de campos obrigatórios
O sistema SHALL validar que `nome` e `area` são obrigatórios no form de criar/editar. `area` deve ser um dos três valores permitidos.

#### Scenario: Nome ausente
- **WHEN** o usuário submete o form `/novo` com campo `nome` vazio
- **THEN** o sistema retorna o form com mensagem de erro "Nome é obrigatório" e não persiste

#### Scenario: Área inválida
- **WHEN** o usuário submete com `area = "quimica"`
- **THEN** o sistema retorna o form com mensagem "Área inválida" e não persiste
