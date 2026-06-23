## Why

Hoje existem 26 jogos educacionais distribuídos em 3 áreas de conhecimento (anatomia, histologia, microbiologia), organizados como pastas soltas em `Downloads/Fotos <área>/Fotos <área>/<Jogo>/`, cada uma com 3 imagens (componentes, manual, perfil) e um DOCX descritivo. Não há catálogo pesquisável, os nomes dos arquivos são inconsistentes entre jogos, e as imagens chegam a ~5MB cada, inviáveis para navegação web. Precisamos de um gerenciador (CRUD) que padronize, redimensione e permita criar/consultar/editar/excluir jogos por área, servindo como catálogo local navegável.

## What Changes

- **Novo app Flask** servindo CRUD de jogos em `http://localhost:5000` com renderização server-side (Jinja2).
- **Banco SQLite local** (`instance/jogos.db`) com tabelas `games` e `game_manual_pages` (manuais multipágina).
- **Importador** (`importer.py` + CLI `scripts/import_from_downloads.py`) que varre `Downloads/Fotos <área>/Fotos <área>/`, classifica arquivos por substring no nome, normaliza para paths canônicos (`data/<área>/<slug>/`), converte DOCX→Markdown, e redimensiona JPGs para web (max 1600px, JPEG q=85). Idempotente via chave `(area, nome)`.
- **3 imagens por jogo** padronizadas: `componentes.jpg`, `perfil.jpg`, e `manual_1.jpg` [, `manual_2.jpg`, …] para manuais multipágina.
- **UI Jinja2**: lista com filtro por área, detalhe (carrossel simples de manuais), form criar/editar, confirmação de exclusão.
- **Upload de imagens** no form (substituir/editar imagens de um jogo), com redimensionamento on-the-fly via Pillow.
- **Testes pytest** cobrindo models, importer (em pasta temporária) e routes.

## Capabilities

### New Capabilities
- `game-catalog`: CRUD de jogos (listar, criar, editar, excluir) com filtros por área e persistência em SQLite.
- `media-importer`: Importação/normalização de jogos a partir das pastas em `Downloads` para `data/` no projeto, com classificação por substring, slug ASCII-safe, conversão DOCX→MD e redimensionamento de imagens.
- `web-ui`: Interface web (Flask + Jinja2) com telas de lista, detalhe, formulário e exclusão, incluindo carrossel de manuais multipágina.

### Modified Capabilities
<!-- Nenhuma — projeto novo, sem specs anteriores. -->

## Impact

- **Novo projeto** em `C:\Users\Frederico\workspace\gerenciador-jogos\` (atualmente vazio além do scaffold OpenSpec).
- **Dependências Python**: `flask`, `python-docx`, `Pillow` (em `requirements.txt`).
- **Sistema de arquivos**: cria `app/`, `data/`, `tests/`, `scripts/`, `static/`, `instance/` (SQLite). A pasta `data/` receberá cópias normalizadas — **Downloads permanece intacto** até validação manual posterior.
- **~26 jogos × 3 imagens** ≈ 78 JPGs redimensionados (~30–40MB em `data/`).
- **Encoding**: nomes de pastas em Downloads contêm caracteres acentuados; `importer.py` lê via `os.listdir` (UTF-8) e aplica slug ASCII-safe preservando o nome exibido com acentos.
- **Sem breaking changes** — projeto novo.
