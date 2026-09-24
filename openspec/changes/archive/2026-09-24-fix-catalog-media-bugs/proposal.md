## Why

Cinco bugs validados na fase EXPLORE degradam o fluxo administrativo do catálogo: o modal de exclusão não abre (jogo aparentemente não pode ser removido), a foto de um jogo existente não atualiza após re-upload (cache de 7 dias do Nginx em `/media/`), páginas novas de manual não são salvas (transação descartada por falta de `db.commit()` em `set_manual_pages`), a descrição salva perde quebras de parágrafo simples dadas com Enter (extensão `nl2br` ausente na renderização Markdown) e o rótulo "Regras (resumo)" não comunica o propósito do campo ("Objetivo"). Detalhes e alternativas em `research.md` (Opção A: conserto mínimo, sem dependências novas).

## What Changes

- Modal de exclusão: `<dialog>` passa a ser aberto/fechado com as APIs nativas `showModal()`/`close()` em `app/templates/detail.html` (removendo a manipulação manual de `hidden` que não abre o modal).
- Cache de mídia: invalidação dupla aceita pelo usuário — `no-cache` no location `/media/` de `deploy/nginx.conf` **e** cache-busting via query `?v=<updated_at>` nas templates que usam `url_for('games.media', ...)`.
- Persistência de manuais: `models.set_manual_pages` passa a executar `db.commit()` (como `create_game`/`update_game` já fazem), corrigindo a perda silenciosa da transação pelo `close_db`.
- Limpeza e migração de mídia (aceito pelo usuário): páginas de manual excedentes removidas do disco em re-upload menor e, ao mudar `area`/`slug`, a pasta de mídia é **migrada** (movida) e os paths reescritos no banco — preservando mídias existentes quando não há reenvio de fotos.
- Descrição: `nl2br` adicionado às extensões do python-Markdown em `app/routes.py` (global, aceito pelo usuário); `bleach` já preserva `<br>` em `ALLOWED_TAGS`.
- Rótulo "Regras (resumo)" → "Objetivo" em `form.html` e `detail.html`; campo `regras_resumo` e dados existentes permanecem inalterados.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `web-ui`: o requisito "Exclusão com confirmação" passa a exigir modal `<dialog>` funcional via APIs nativas `showModal()`/`close()`; o requisito "Servir arquivos estáticos de imagens" passa a exigir cache-busting `?v=updated_at` nos templates; o requisito "Renderização de Markdown na descrição" passa a exigir `nl2br` (Enter único vira `<br>`); rótulo do campo `regras_resumo` na UI passa a ser "Objetivo".
- `game-catalog`: o requisito "Manuais multipágina" passa a exigir que a substituição de páginas seja persistida com commit explícito e que arquivos excedentes no re-upload menor sejam removidos do disco; ao renomear um jogo (slug muda), a pasta antiga não pode ficar órfã.
- `production-infra`: o requisito "Configuração Nginx como proxy reverso com HTTPS" passa a exigir `no-cache` nas respostas de `/media/` para imagens de jogo.

## Impact

- Código: `app/templates/detail.html` (modal, rótulo, `?v=`), `app/templates/form.html` (rótulo), `app/templates/index.html` (thumbnail com `?v=`), `app/models.py` (`set_manual_pages`), `app/routes.py` (extensões do Markdown, limpeza de orfãos na edição).
- Deploy: `deploy/nginx.conf` (bloco `/media/`); exige recarga do Nginx no próximo deploy.
- Sem dependências novas, sem mudança de schema, sem breaking changes. Baseline de testes: 154 passed, 1 skipped, 1 flaky de ambiente (`test_get_form_as_admin`, passa isolado).