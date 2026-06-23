# Capability: media-importer

## Purpose

TBD — Importação de mídias (imagens e descrições DOCX) das pastas de Downloads para o catálogo, com classificação, slug, redimensionamento e idempotência.

## Requirements

### Requirement: Varredura das pastas de origem
O sistema SHALL varrer recursivamente as pastas `C:\Users\Frederico\Downloads\Fotos <area>\Fotos <area>\` para cada área em {anatomia, histologia, microbiologia}, considerando cada subpasta como um jogo.

#### Scenario: Estrutura esperada
- **WHEN** o importer é executado
- **THEN** ele identifica todas as subpastas sob `Downloads/Fotos anatomia/Fotos anatomia/`, `Downloads/Fotos Histologia/Fotos Histologia/`, e `Downloads/Fotos microbiologia/Fotos microbiologia/` como jogos a importar

#### Scenario: Pasta de origem ausente
- **WHEN** uma das três pastas de origem não existe
- **THEN** o importer registra um warning e continua com as demais, sem abortar

### Requirement: Classificação de arquivos por substring no nome
O sistema SHALL classificar cada arquivo de uma pasta de jogo em uma das categorias canônicas (componentes, manual, perfil, descricao) com base em substrings case-insensitive no nome do arquivo:
- `componentes|conteúdo|conteudo|caixa` → `componentes.jpg`
- `manual` → `manual_<n>.jpg` (multipágina)
- `perfil|foto perfil` → `perfil.jpg` (se ausente, fallback para arquivo com `caixa` não usado como componentes)
- extensão `.docx` → `descricao.md`

#### Scenario: Classificação de componentes
- **WHEN** a pasta contém `Componentes.jpg` (ou `Conteúdo - X.jpg`, ou `Caixa - X.jpg`)
- **THEN** o arquivo é classificado como componentes

#### Scenario: Classificação de manual multipágina
- **WHEN** a pasta contém `Manual parte 1.jpg` e `Manual parte 2.jpg`
- **THEN** são classificados como `manual_1.jpg` e `manual_2.jpg`, ordenados por sufixo numérico

#### Scenario: Manual sem sufixo numérico
- **WHEN** a pasta contém apenas `Manual.jpg`
- **THEN** é classificado como `manual_1.jpg`

#### Scenario: Classificação de DOCX
- **WHEN** a pasta contém `Texto.docx` (ou `Resumo- X.docx`, ou `Documento sem título.docx`)
- **THEN** o arquivo é convertido para `descricao.md` via `python-docx`

### Requirement: Slug ASCII-safe para nomes de pastas
O sistema SHALL gerar um slug ASCII-safe para cada nome de jogo, preservando o nome exibido (com acentos) no campo `nome` do DB. O slug resulta de: `unicodedata.normalize('NFKD')` → remover acentos → lowercase → substituir `[^a-z0-9]+` por `-` → trim de hífens.

#### Scenario: Nome com acento
- **WHEN** o jogo se chama "Células em jogo - tabuleiro"
- **THEN** o slug é `celulas-em-jogo-tabuleiro` e o campo `nome` no DB é "Células em jogo - tabuleiro"

#### Scenario: Nome com caracteres especiais
- **WHEN** o jogo se chama "Anato mach"
- **THEN** o slug é `anato-mach`

### Requirement: Cópia (não movimentação) com redimensionamento
O sistema SHALL copiar (não mover) os arquivos de imagem da origem para `data/<area>/<jogo-slug>/`, redimensionando cada JPG para no máximo 1600px no maior lado (mantendo proporção) e salvando como JPEG quality=85 com otimização. A pasta de origem em Downloads permanece intacta.

#### Scenario: Redimensionamento de imagem grande
- **WHEN** a imagem de origem é 4000x3000px e 5MB
- **THEN** a imagem em `data/` é 1600x1200px e entre 200KB e 800KB

#### Scenario: Imagem menor que o limite
- **WHEN** a imagem de origem é 800x600px
- **THEN** a imagem em `data/` mantém 800x600px (não é ampliada)

### Requirement: Conversão DOCX para Markdown
O sistema SHALL converter o DOCX descritivo de cada jogo para um arquivo `descricao.md` na pasta de destino, extraindo o texto dos parágrafos via `python-docx`. O conteúdo é também armazenado no campo `descricao` do registro em `games`.

#### Scenario: DOCX com múltiplos parágrafos
- **WHEN** o DOCX contém 5 parágrafos
- **THEN** `descricao.md` contém os 5 parágrafos separados por linha em branco, e o campo `games.descricao` contém o mesmo texto

#### Scenario: Pasta sem DOCX
- **WHEN** uma pasta de jogo não contém nenhum `.docx`
- **THEN** o importer registra um warning, `descricao` fica NULL, e a importação do jogo continua

### Requirement: Idempotência por (area, nome)
O sistema SHALL ser idempotente: re-executar o importer não duplica registros. A chave de idempotência é `(area, nome)`. Se um jogo já existe, seus dados e arquivos são atualizados (substituídos).

#### Scenario: Primeira execução
- **WHEN** o importer é executado em um DB vazio
- **THEN** todos os jogos das 3 áreas são inseridos

#### Scenario: Segunda execução
- **WHEN** o importer é re-executado
- **THEN** nenhum jogo é duplicado; arquivos em `data/` são substituídos; registros existentes são atualizados

### Requirement: CLI de importação
O sistema SHALL fornecer um script CLI `scripts/import_from_downloads.py` que executa a importação completa, com output de progresso (um log por jogo importado) e resumo final (total importado por área).

#### Scenario: Execução bem-sucedida
- **WHEN** o usuário executa `python scripts/import_from_downloads.py`
- **THEN** o script percorre as 3 áreas, importa cada jogo, imprime `[OK] <area>/<nome>` por jogo, e ao final imprime "Total: X jogos (anatomia: A, histologia: H, microbiologia: M)"
