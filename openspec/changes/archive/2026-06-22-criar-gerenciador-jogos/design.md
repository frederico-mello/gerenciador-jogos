## Context

Projeto novo em `C:\Users\Frederico\workspace\gerenciador-jogos\`. Hoje existem 26 jogos em 3 áreas (anatomia, histologia, microbiologia) sob `Downloads/Fotos <área>/Fotos <área>/<Jogo>/`. Cada pasta de jogo contém aproximadamente 3 JPGs (componentes, manual, perfil/caixa — com nomes variados) e 1 DOCX descritivo (Texto/Resumo/Documento sem título). Imagens têm ~5MB cada. Não há catálogo pesquisável.

Stack escolhida: **Python 3 + Flask + SQLite** (server-side rendering com Jinja2), com OpenSpec para spec-driven development. Requisito do ambiente: rodar localmente em Windows, Node v26.3.1 já atende ao OpenSpec; Python 3 presumido disponível.

## Goals / Non-Goals

**Goals:**
- CRUD completo de jogos via interface web local.
- Importação idempotente dos 26 jogos das pastas Downloads para `data/`, com nomes normalizados.
- Conversão DOCX → Markdown para texto descritivo.
- Redimensionamento de imagens para web (max 1600px, JPEG q=85).
- Suporte a manuais multipágina (`manual_1.jpg`, `manual_2.jpg`, …).
- Testes automatizados (pytest) para models, importer e routes.

**Non-Goals:**
- Autenticação / multiusuário (app local de uso único).
- Deploy em produção / nuvem.
- Busca full-text avançada (apenas filtro por área + busca simples por nome).
- Edição avançada de DOCX (somente conversão para exibição).
- Migração de outros formatos de imagem além de JPG.

## Decisions

### 1. Stack: Flask + SQLite + Jinja2 (server-side rendering)
**Por que:** App local simples, sem necessidade de SPA. SQLite elimina servidor de DB. Jinja2 evita build frontend.
**Alternativas consideradas:** Electron (mais pesado, empacotamento complexo), Node+Express (stack diferente do desejado pelo usuário), HTML puro+JSON (limitado para upload/consultas).
**Decisão:** Flask com templates Jinja2 e SQLite via `sqlite3` da stdlib (sem ORM para manter simples).

### 2. Modelo de dados: tabelas `games` + `game_manual_pages`
**Por que:** Manuais podem ter múltiplas páginas (caso "Trunfo citologia" com manual parte 1/2). Uma tabela separada com FK + `ON DELETE CASCADE` + `ordem` é mais flexível que um campo JSON.
**Alternativas:** Campo `manuais TEXT` com JSON serializado — descartado por dificultar queries/ordenação.
**Schema:**
```sql
games(id PK, nome, area, descricao, regras_resumo, num_jogadores, duracao_min,
      imagem_componentes, imagem_perfil, created_at, updated_at)
game_manual_pages(id PK, game_id FK→games CASCADE, ordem INT, path TEXT)
```
Paths são relativos a `data/` (ex.: `anatomia/memotomia/manual_1.jpg`).

### 3. Armazenamento de imagens: arquivos no disco, path no DB
**Por que:** SQLite não é ideal para BLOBs grandes. Disco permite servir diretamente via `Flask.send_from_directory`. Redimensionamento on-the-fly no upload/importação, não no request.
**Alternativas:** BLOBs em SQLite — descartado.

### 4. Normalização dos nomes (importer.py)
- **Origem:** `C:\Users\Frederico\Downloads\Fotos <área>\Fotos <área>\<Jogo>\`
- **Destino:** `data/<area-slug>/<jogo-slug>/`
- **Classificação por substring no nome do arquivo** (case-insensitive):
  - `componentes|conteúdo|conteudo|caixa` → `componentes.jpg`
  - `manual` → `manual_<n>.jpg` (n=1..N, ordenado por sufixo "parte X" ou alfabético)
  - `perfil|foto perfil` → `perfil.jpg` (se ausente, fallback para arquivo `caixa`)
  - `.docx` (qualquer nome) → `descricao.md` via `python-docx`
- **Slug ASCII-safe:** `unicodedata.normalize('NFKD')` + remove acentos + lowercase + `[^a-z0-9]+` → `-`. Nome exibido preserva acentos.
- **Idempotência:** upsert por `(area, nome)`; re-executar não duplica. Se a pasta de destino já existe, substitui arquivos.

### 5. Redimensionamento de imagens: Pillow, max 1600px, JPEG q=85
**Por que:** Reduz ~5MB → ~300-500KB, mantém qualidade legível para web.
**Implementação:** `Image.thumbnail((1600, 1600))` mantém proporção; salva com `quality=85, optimize=True`.

### 6. Importação como cópia (não move)
**Por que:** Preserva Downloads intacto até validação. Após confirmar que `data/` está correto, usuário apaga Downloads manualmente.
**Implementação:** `shutil.copy2` depois redimensiona in-place no destino.

### 7. Estrutura de rotas Flask (RESTful simplificado)
```
GET  /                  → lista (com ?area= e ?q=)
GET  /novo              → form criar
POST /novo              → cria + redirect /<id>
GET  /<id>              → detalhe (com carrossel de manuais)
GET  /<id>/editar       → form editar
POST /<id>/editar       → atualiza + redirect /<id>
POST /<id>/excluir      → exclui + redirect /
POST /<id>/imagens      → upload substituto de imagem (multipart)
```

### 8. Encoding dos nomes em Downloads
PowerShell mostra `?` nos acentos (renderização), mas `os.listdir` em Python lê UTF-8 corretamente no Windows. Se houver mojibake real, manter tabela de correção manual — **não necessário a priori**.

### 9. OpenSpec CLI como ferramenta de spec-driven
OpenSpec 1.4.1 instalado globalmente; `openspec init --tools opencode` criou `.opencode/` com skills/commands. Change `criar-gerenciador-jogos` seguindo fluxo `/opsx:propose → /opsx:apply → /opsx:archive`.

## Risks / Trade-offs

- **[Encoding de nomes quebrados]** → Mitigação: `importer.py` usa `os.listdir` (UTF-8); se houver mojibake real, mapear via tabela de correção manual por área.
- **[Jogos com nomes duplicados entre áreas (Salus, Baralho)]** → Mitigação: chave de idempotência é `(area, nome)`, não só `nome`. São registros distintos.
- **[DOCX "Documento sem título.docx"]** → Mitigação: heurística captura por exclusão (único `.docx` na pasta).
- **[Manuais sem sufixo "parte N"]** → Mitigação: ordenar alfabeticamente como fallback; documento no README.
- **[Downloads não movido]** → Trade-off aceito: cópia idempotente preserva original; usuário limpa depois.
- **[Sem upload de DOCX editável]** → Trade-off: DOCX vira Markdown apenas para exibição; não é editável na UI.
- **[App local sem auth]** → Trade-off aceito para uso pessoal.

## Migration Plan

1. Setup: `python -m venv venv`, `pip install -r requirements.txt`.
2. `python scripts/init_db.py` cria `instance/jogos.db`.
3. `python scripts/import_from_downloads.py` popula DB + copia/redimensiona para `data/`.
4. `flask run` serve em `http://localhost:5000`.
5. **Rollback:** deletar `instance/jogos.db` + `data/`; Downloads permanece intacto.

## Open Questions

- Nenhuma pendente. Todas as decisões foram confirmadas pelo usuário (manuais multipágina, redimensionamento web, cópia via importer, nome do projeto).
