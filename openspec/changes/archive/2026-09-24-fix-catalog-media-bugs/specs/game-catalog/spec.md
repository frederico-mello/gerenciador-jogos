## MODIFIED Requirements

### Requirement: Manuais multipágina
O sistema SHALL suportar manuais com múltiplas páginas, armazenadas na tabela `game_manual_pages` com campos: `id` (PK), `game_id` (FK → games(id) ON DELETE CASCADE), `ordem` (INTEGER), `path` (TEXT, relativo a `data/`). Cada jogo pode ter zero ou mais páginas de manual, ordenadas por `ordem`. A substituição das páginas SHALL ser persistida com commit explícito da transação antes do fim do request. Ao reenviar um manual com menos páginas, os arquivos excedentes da pasta do jogo SHALL ser removidos do disco. Ao editar um jogo cujo slug ou área mudou, as mídias existentes SHALL ser migradas: a pasta `data/<old_area>/<old_slug>/` SHALL ser movida para `data/<new_area>/<new_slug>/` e os paths de `games.imagem_componentes`, `games.imagem_perfil` e `game_manual_pages.path` SHALL ser reescritos para a pasta nova, preservando as imagens quando o usuário renomeia sem reenviar fotos.

#### Scenario: Jogo com manual de 2 páginas
- **WHEN** o jogo "Trunfo citologia" tem `manual_1.jpg` e `manual_2.jpg`
- **THEN** existem 2 linhas em `game_manual_pages` com `game_id` correspondente, `ordem` 1 e 2, e paths `histologia/trunfo-citologia/manual_1.jpg` e `histologia/trunfo-citologia/manual_2.jpg`

#### Scenario: Excluir jogo com manuais
- **WHEN** um jogo com manuais é excluído
- **THEN** todas as linhas em `game_manual_pages` com o `game_id` correspondente são removidas automaticamente por cascade

#### Scenario: Re-upload de manual persiste no banco
- **WHEN** um administrador edita um jogo enviando novo(s) arquivo(s) de manual
- **THEN** as linhas em `game_manual_pages` são substituídas e visíveis em leituras subsequentes (transação persistida por commit explícito), em vez de descartadas no fechamento da conexão

#### Scenario: Re-upload menor remove páginas excedentes
- **WHEN** um jogo com 3 páginas de manual é editado com re-upload de apenas 1 página
- **THEN** a tabela passa a ter 1 linha (`ordem` 1) e os arquivos `manual_2.jpg` e `manual_3.jpg` são removidos do disco

#### Scenario: Renomear jogo migra as mídias para a pasta nova
- **WHEN** um jogo "Anato mach" (`data/anatomia/anato-mach/`) é renomeado para "Anato mach 2" (novo slug `anato-mach-2`), com ou sem novos uploads
- **THEN** os arquivos passam a existir em `data/anatomia/anato-mach-2/`, os paths no banco (imagem de perfil/componentes e páginas de manual) apontam para a pasta nova e a pasta `data/anatomia/anato-mach/` não existe mais — as mídias existentes permanecem acessíveis quando não há reenvio de fotos