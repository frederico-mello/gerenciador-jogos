## 1. Setup do projeto

- [x] 1.1 Criar `requirements.txt` com `flask`, `python-docx`, `Pillow`, `markdown`, `pytest`
- [x] 1.2 Criar `app/__init__.py` com factory `create_app()` (hello world em `/` temporÃ¡rio)
- [x] 1.3 Criar `.gitignore` (ignora `venv/`, `__pycache__/`, `instance/`, `data/`)
- [x] 1.4 Criar `README.md` com passos de setup (venv, install, init_db, import, flask run)
- [x] 1.5 Verificar `python --version` e criar venv (`python -m venv venv`); instalar deps

## 2. Banco de dados (game-catalog)

- [x] 2.1 Criar `app/schema.sql` com DDL de `games` e `game_manual_pages` (FK + ON DELETE CASCADE)
- [x] 2.2 Criar `app/db.py` com `get_db()` (sqlite3.Row), `init_db()`, e fechamento em teardown
- [x] 2.3 Criar `scripts/init_db.py` que cria `instance/jogos.db` a partir de `schema.sql`
- [x] 2.4 Criar `app/models.py` com funÃ§Ãµes: `list_games(area=None, q=None)`, `get_game(id)`, `create_game(data)`, `update_game(id, data)`, `delete_game(id)`, `list_manual_pages(game_id)`, `set_manual_pages(game_id, paths)`

## 3. Importador (media-importer)

- [x] 3.1 Criar `app/importer.py` com função `slugify(nome)` (NFKD + ASCII + lowercase + `[^a-z0-9]+`→`-`)
- [x] 3.2 Implementar `classify_file(filename)` retornando categoria (componentes/manual/perfil/descricao) por substring case-insensitive
- [x] 3.3 Implementar `resize_image(src_path, dst_path)` com Pillow (max 1600px, JPEG q=85, optimize)
- [x] 3.4 Implementar `convert_docx_to_md(docx_path)` via `python-docx` (parágrafos separados por linha em branco)
- [x] 3.5 Implementar `import_game(origem_dir, area, nome_jogo)` que classifica, copia+redimensiona para `data/<area>/<slug>/`, converte DOCX→`descricao.md`, faz upsert em `games` e `game_manual_pages`
- [x] 3.6 Implementar `import_all(downloads_root)` que itera as 3 áreas e chama `import_game` por subpasta; idempotente por `(area, nome)`; logs `[OK] <area>/<nome>`
- [x] 3.7 Criar `scripts/import_from_downloads.py` (CLI wrapper) com resumo final "Total: X jogos (anatomia: A, histologia: H, microbiologia: M)"

## 4. Rotas Flask (web-ui + game-catalog)

- [x] 4.1 Implementar `GET /` em `app/routes.py` (lista com filtros `?area=` e `?q=`) renderizando `index.html`
- [x] 4.2 Implementar `GET /novo` e `POST /novo` (valida nome+area, redimensiona uploads, persiste, redirect `/<id>`)
- [x] 4.3 Implementar `GET /<id>` (detalhe, busca manual pages ordenadas por `ordem`, renderiza Markdown) renderizando `detail.html`
- [x] 4.4 Implementar `GET /<id>/editar` e `POST /<id>/editar` (preenche form, atualiza, substitui imagens se houver upload, redirect `/<id>`)
- [x] 4.5 Implementar `POST /<id>/excluir` (remove do DB, remove pasta `data/<area>/<slug>/`, redirect `/`)
- [x] 4.6 Implementar `GET /media/<path:filename>` servindo de `data/` via `send_from_directory`
- [x] 4.7 Registrar `routes` blueprint na factory `create_app()`

## 5. Templates (web-ui)

- [x] 5.1 Criar `app/templates/base.html` (header, nav, bloco content, link para `/static/style.css`)
- [x] 5.2 Criar `app/templates/index.html` (lista de cards com thumbnail de perfil, seletor de Ã¡rea, campo de busca, botÃ£o "Novo jogo")
- [x] 5.3 Criar `app/templates/form.html` (form criar/editar com campos nome/area/descricao/regras_resumo/num_jogadores/duracao_min + uploads; exibe erros de validaÃ§Ã£o)
- [x] 5.4 Criar `app/templates/detail.html` (todos os campos, imagem componentes, imagem perfil, descriÃ§Ã£o renderizada, carrossel JS para manuais multipÃ¡gina, botÃ£o excluir com modal de confirmaÃ§Ã£o)
- [x] 5.5 Criar `app/static/style.css` (estilo mÃ­nimo e limpo, grid de cards, carrossel)

## 6. Testes (pytest)

- [x] 6.1 Criar `tests/conftest.py` com fixtures: `app` (create_app em modo testing com DB temporÃ¡rio), `client`, `tmp_data_dir`
- [x] 6.2 Criar `tests/test_models.py` cobrindo create/read/update/delete + manual pages cascade
- [x] 6.3 Criar `tests/test_importer.py` cobrindo `slugify`, `classify_file`, `resize_image`, `import_game` (em pasta temporÃ¡ria com DOCX fake)
- [x] 6.4 Criar `tests/test_routes.py` cobrindo `GET /`, filtros, `GET/POST /novo`, `GET /<id>`, editar, excluir, `/media/`
- [x] 6.5 Rodar `python -m pytest` e garantir todos os testes passando

## 7. ValidaÃ§Ã£o e smoke test

- [x] 7.1 Rodar `python scripts/init_db.py` para criar o DB
- [x] 7.2 Rodar `python scripts/import_from_downloads.py` e verificar os 26 jogos importados
- [x] 7.3 Rodar `flask run` e navegar manualmente: listar, filtrar por Ã¡rea, abrir detalhe (verificar carrossel de manual multipÃ¡gina), criar jogo novo, editar, excluir
- [x] 7.4 Verificar que a pasta Downloads permanece intacta apÃ³s importaÃ§Ã£o

## 8. FinalizaÃ§Ã£o OpenSpec

- [ ] 8.1 `/opsx:archive` da change `criar-gerenciador-jogos` apÃ³s tudo verificado








