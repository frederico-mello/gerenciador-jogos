## Context

Cinco bugs validados pelo EXPLORE, com causas-raiz provadas em código (âncoras verificadas neste worktree):

- **Modal de exclusão**: `detail.html:153` declara `<dialog ... hidden>`; os handlers `openModal`/`closeModal` (`detail.html:172-181`) manipulam o atributo `hidden` com `removeAttribute`/`setAttribute`. Um `<dialog hidden>` aberto dessa forma não se torna modal (sem `showModal()`, não entra no top layer), então o form de confirmação nunca fica usável.
- **Foto não atualiza**: `deploy/nginx.conf:36-40` emite `expires 7d; add_header Cache-Control "public"` para `/media/`. O re-upload sobrescreve o mesmo path (`data/<area>/<slug>/perfil.jpg`), a URL não muda e o browser continua servindo a cópia em cache por até 7 dias.
- **Manuais não salvam**: `app/models.py:91-99` (`set_manual_pages`) faz DELETE+INSERT sem `db.commit()`; o `close_db` descarta a transação ao encerrar o request. Todos os writers de `games`/`loans` (ex.: `create_game` em `models.py:122`) já chamam `db.commit()` — o bug é a omissão local, não a estratégia de transação.
- **Descrição sem parágrafos**: `app/routes.py:441` renderiza com `extensions=["extra"]`, que colapsa Enter único. `bleach.clean` já preserva `<br>` (`ALLOWED_TAGS` inclui `"br"`, `routes.py:53`), então `nl2br` não é neutralizado pelo sanitizer.
- **Rótulo**: `form.html:48` e `detail.html:67` exibem "Regras (resumo)" para o campo `regras_resumo`.

Restrições: Flask 3 + SQLite + Pillow + python-Markdown + bleach, JS vendored (EasyMDE 2.18.0), sem build pipeline. Baseline de testes: 154 passed, 1 skipped, 1 flaky de ambiente (`test_get_form_as_admin` — malloc libcrypto; passa isolado).

## Goals / Non-Goals

**Goals:**
- Corrigir os 5 bugs com mudanças locais mínimas (Opção A do `research.md`), sem dependências novas.
- Invalidação de mídia robusta: `no-cache` no Nginx **e** cache-busting `?v=updated_at` (decisão aceita pelo usuário).
- Persistência correta de manuais + limpeza de arquivos órfãos (páginas excedentes e pasta de slug antigo).

**Non-Goals:**
- Não migrar uploads para Flask-WTF `MultipleFileField` (Opção B: refinamento futuro, não necessário para estes bugs).
- Não trocar EasyMDE/CodeMirror nem bleach→nh3 (Opções C/D do research).
- Não mudar schema do banco, nomes de campo (`regras_resumo`) nem contrato de rotas.

## Decisions

1. **Modal: manter `<dialog>` e usar `showModal()`/`close()`** — o elemento já está no template e é o caminho nativo; trocar por `<div class="modal-overlay">` reintroduziria gerência manual de foco/fechamento. Remover a manipulação de `hidden` (o atributo passa a não ser necessário; `<dialog>` sem `open` já não renderiza). Alternativa descartada: overlay div (mais CSS, duplica o que o top layer dá de graça).
2. **Cache: dupla invalidação (aceita pelo usuário)** — `no-cache` no `location /media/` do Nginx (substitui `expires 7d`) **e** `?v=<updated_at>` nos 3 pontos de `url_for('games.media', ...)` (`index.html:42`, `detail.html:47`, `detail.html:54`, `detail.html:124`). O `no-cache` protege mesmo se um template esquecer o `?v=`; o `?v=` evita revalidação a cada load quando a imagem não mudou. `updated_at` já é atualizado em todo UPDATE (`models.py`, `SQL_UPDATED_AT`), não exige migração.
3. **Commit em `set_manual_pages`** — espelha o padrão dos demais writers (`create_game`/`update_game`/`delete_game`); `close_db` continua fechando a conexão sem commit implícito. Alternativa descartada: commit no chamador (routes) — espalharia a responsabilidade e deixaria o helper inseguro para reuso.
4. **Migração e limpeza de mídia na rota de edição** — após persistir: (a) se `manual_paths is not None`, remover do disco `manual_<n>.jpg` com `n > len(manual_paths)`; (b) se `area` ou `slug` mudou, **migrar** as mídias existentes: mover `data/<old_area>/<old_slug>/` para `data/<new_area>/<new_slug>/` (`shutil.move`) e reescrever o prefixo dos paths no banco (`games.imagem_componentes`, `games.imagem_perfil`, `game_manual_pages.path`) de `<old_area>/<old_slug>/` para `<new_area>/<new_slug>/` — remover a pasta antiga destruiria mídias existentes quando o usuário renomeia sem reenviar fotos. A migração roda ANTES de salvar uploads novos (que aterrissam na pasta nova e sobrescrevem os movidos); a pasta antiga deixa de existir por ter sido movida. Fica na route (não no model) porque depende de `request.files` e de paths em disco; o rewrite dos paths é função nova em `models.py` (com `db.commit()`).
5. **`nl2br` global (aceito pelo usuário)** — `extensions=["extra", "nl2br"]` em `routes.py:441`. `bleach` já permite `<br>`; sem mudança em `ALLOWED_TAGS`.
6. **Rótulo "Objetivo"** — troca de string em `form.html:48` e `detail.html:67`; sem renomear campo nem dado.

## Risks / Trade-offs

- [`nl2br` global] Altera a renderização de descrições existentes (todo Enter único passa a virar `<br>` na tela de detalhe) → aceito pelo usuário; não muda o texto armazenado.
- [`?v=updated_at` não muda quando só o arquivo muda] O `update_game` sempre toca `updated_at`, e todo caminho de re-upload passa por `update_game` → risco residual baixo.
- [Migração de pasta no rename] `shutil.move` entre áreas pode falhar em disco cheio/permissão após a transação → migração de disco roda após o `update_game` commitado e antes da limpeza de excedentes; se o move falhar, o flash de erro reporta e os paths antigos permanecem válidos (nenhum dado perdido).
- [Nginx `no-cache`] Revalidação a cada load (leve: 304 condicional) em troca de correção imediata de imagem → trade-off aceito; a carga é irrelevante para o tamanho do app (rede local).
- [Flaky `test_get_form_as_admin`] Falha de ambiente (malloc libcrypto), não dos fixes → registrar no run de teste; passa isolado.

## Migration Plan

- Deploy: recarregar Nginx (`nginx -s reload`) para o novo bloco `/media/` — sem downtime (reload graceful). Nenhuma migração de dados: `updated_at` já existe e manuais antigos continuam válidos.
- Rollback: reverter templates/routes/models e o bloco `/media/` do Nginx; a limpeza de órfãos é idempotente e sem efeito reverso (arquivos já removidos não retornam, mas nada os referencia no banco).

## Open Questions

(nenhuma — decisões de produto/cache foram fechadas com o usuário na fase EXPLORE: manter `<dialog>`, dupla invalidação, `nl2br` global, limpeza de órfãos em escopo.)