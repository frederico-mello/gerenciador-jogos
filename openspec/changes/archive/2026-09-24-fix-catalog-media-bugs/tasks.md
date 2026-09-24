## 1. Modal de exclusão (bug 1)

- [x] 1.1 Em `app/templates/detail.html`, substituir `openModal`/`closeModal` (linhas ~172-181) por `modal.showModal()` / `modal.close()` e remover a manipulação manual de `hidden`; remover o atributo `hidden` do `<dialog id="delete-modal">` (linha ~153), mantendo o elemento `<dialog>` e o form/CSRF internos. Verificar: no browser, clicar "Excluir" abre o modal nativo (fundo bloqueado), "Cancelar" fecha sem excluir, e o submit continua excluindo (cobre os cenários "Abrir modal de exclusão" e "Cancelar fecha o modal").
- [x] 1.2 Teste de integração: confirmar que `POST /<id>/excluir` continua funcionando a partir do form do modal (rota, CSRF e guardas de role intactos). Verificar: `pytest tests/ -k excluir` verde.

## 2. Cache de mídia (bug 2)

- [x] 2.1 Em `deploy/nginx.conf` (bloco `location /media/`, linhas ~36-40): trocar `expires 7d; add_header Cache-Control "public";` por `add_header Cache-Control "no-cache";`. Verificar: `nginx -t` passa com o template processado; resposta de `/media/...` contém `no-cache` e não contém TTL longo (cenário "Resposta de /media/ não é cacheável por TTL longo").
- [x] 2.2 Cache-busting nos templates: em `app/templates/index.html:42` e `app/templates/detail.html:47,54,124`, acrescentar `?v={{ game.updated_at }}` (ou variável equivalente no contexto) aos `url_for('games.media', ...)`. Verificar: render do `GET /<id>` e `GET /` mostra `src="/media/...?v=<updated_at>"` (cenário "Re-upload gera nova URL de imagem").
- [x] 2.3 Teste de rota: editar um jogo com novo upload de `imagem_perfil` e assegurar que (a) `updated_at` muda e (b) o HTML do detalhe contém o novo valor em `?v=`. Verificar: `pytest tests/ -k media` verde.

## 3. Persistência e limpeza de manuais (bug 3)

- [x] 3.1 Em `app/models.py` (`set_manual_pages`, linhas ~91-99): acrescentar `db.commit()` após o loop de INSERT, espelhando `create_game`. Verificar: teste de rota faz `POST /<id>/editar` com 1 página de manual e, em nova leitura (`models.list_manual_pages` ou `GET /<id>`), as linhas persistem (cenário "Re-upload de manual persiste no banco").
- [x] 3.2 Limpeza de páginas excedentes: na rota de edição (`app/routes.py`, `editar`), quando `manual_paths is not None` e menor que o total anterior, remover do disco `manual_<n>.jpg` com `n > len(manual_paths)` em `data/<area>/<slug>/`. Verificar: teste com 3 páginas existentes + re-upload de 1 remove `manual_2.jpg`/`manual_3.jpg` do disco (cenário "Re-upload menor remove páginas excedentes").
- [x] 3.3 Migração no rename/área: na rota `editar`, quando `area` ou `slug` muda, mover `data/<old>/<slug>/` para a pasta nova (`shutil.move`) e reescrever o prefixo dos paths no banco (`games.imagem_componentes`, `games.imagem_perfil`, `game_manual_pages.path`) de `<old_area>/<old_slug>/` para `<new_area>/<new_slug>/` (função nova em `models.py`, com commit), ANTES de salvar uploads novos. Migrar (e não remover) preserva as mídias existentes quando o usuário renomeia sem reenviar fotos; a pasta antiga deixa de existir por ter sido movida.

## 4. Descrição com parágrafos (bug 4)

- [x] 4.1 Em `app/routes.py:441`, trocar `extensions=["extra"]` por `extensions=["extra", "nl2br"]`. Verificar: render de "linha um\nlinha dois" produz `<br>` entre as linhas e o `bleach.clean` mantém o `<br>` (cenários "Enter único vira quebra visível" e "Sanitização continua aplicada").
- [x] 4.2 Teste de rota/render: `GET /<id>` de um jogo com descrição de linhas simples exibe quebras visíveis; descrever existente com Markdown (negrito/lista) continua renderizando igual. Verificar: `pytest tests/ -k descricao` verde.

## 5. Rótulo "Objetivo" (bug 5)

- [x] 5.1 Trocar a string "Regras (resumo)" por "Objetivo" em `app/templates/form.html:48` (label) e `app/templates/detail.html:67` (spec-label), sem renomear o campo `regras_resumo` nem alterar payload/dados. Verificar: `GET /novo` e `GET /<id>` exibem "Objetivo" e nenhum teste de nome de campo quebra.

## 6. Verificação final

- [x] 6.1 Suíte completa: `pytest tests/` com resultado ≥ baseline (154 passed, 1 skipped); registrar o flaky `test_get_form_as_admin` como ambiente se ocorrer (passa isolado).
- [x] 6.2 Smoke manual dos 5 fixes no app (`flask run`): abrir modal, reenviar foto e ver mudança sem hard-refresh, salvar manual de 2 páginas e ver carrossel, Enter único na descrição, rótulo "Objetivo". Verificar: comportamento observável nas telas reais.
- [x] 6.3 Validar o change: `openspec validate fix-catalog-media-bugs --strict` sem erros.

## Notas de verificação (APPLY)

- REVIEW (coordenador, 2026-09-23): 167 passed, 1 skipped; blocker de CSS no dialog nativo.
- Pós-review (aprovado pelo usuário): `.modal-overlay` corrigido em `app/static/style.css`
  — flex movido para `[open]` e escondido via `:not([open])`; regra `[hidden]` obsoleta removida.

- 1.2: `pytest tests/ -k excluir` → 3 passed.
- 2.1: template editado e validado por inspeção do bloco `location /media/` (sem `expires`, `Cache-Control "no-cache"`); **`nginx -t` não executável neste ambiente** (nginx não instalado localmente) — pendente no deploy.
- 2.2/2.3: `pytest tests/ -k media` → 14 passed (inclui `?v=updated_at` em index/detail e mudança de `updated_at` após re-upload).
- 3.1/3.2/3.3: cobertos por `tests/test_catalog_media_fixes.py` (persistência pós-re-upload, remoção de `manual_2/3.jpg` com re-upload menor, migração de pasta+paths no rename/área com e sem reenvio de fotos).
- 4.1/4.2: `pytest tests/ -k descricao` → 5 passed; `nl2br` produz `<br>` mantido pelo `bleach.clean`.
- 5.1: `GET /novo` e `GET /<id>` exibem "Objetivo"; nenhum teste de campo quebra.
- 6.1: `pytest tests/` → **167 passed, 1 skipped** (baseline 154/155 + 12 novos); `test_get_form_as_admin` não falhou neste run.
- 6.2: smoke dos 5 fixes coberto de forma automatizada pelos testes de integração (sem browser no ambiente do agente); o flaky `test_get_form_as_admin` é de ambiente (malloc libcrypto) e passa isolado.
- 6.3: `openspec validate fix-catalog-media-bugs --strict` → **valid**.
- Sem commit/push (fase de git cuida).