## Why

O botão "Excluir" está morto em produção: o Nginx emite `Content-Security-Policy` com `script-src 'self'` (`deploy/nginx.conf:28`), que bloqueia todo handler inline (`onclick=`, `onchange=`, `onsubmit=`) e todo `<script>` sem `src` — conforme a spec `script-src` do MDN. A página de detalhe define `openModal()`/`closeModal()` em `<script>` inline (`detail.html:172-181`) e os botões usam `onclick="openModal()"`/`onclick="closeModal()"` (`detail.html:18,163`), então o modal nunca abre. O mesmo padrão inline derruba outras 7 funcionalidades mapeadas no EXPLORE: carrossel do manual (`detail.html:172-219`), init do EasyMDE (`form.html:133-157`), auto-submit dos filtros de role e troca de papel na linha da tabela (`admin_users.html:8,45`), auto-submit do filtro de rede (`admin_schools.html:9`) e o confirm de cancelamento de empréstimo (`emprestimos_admin.html:106`).

## What Changes

- **Novo arquivo único `app/static/js/app.js`** (servido via `static_v` de `base.html` com `defer`), organizado em seções: modal, carousel, easymde, auto-submit, confirm.
- **Substituição dos handlers inline por listeners delegados** acionados por atributos `data-*`:
  - `data-modal-open` / `data-modal-close` → `<dialog>` nativo via `showModal()`/`close()` (requisito "Modal de exclusão via dialog nativo" preservado);
  - `data-confirm` → substitui `onsubmit="return confirm(...)"` via evento `submit` (captive) com `confirm()`; submit cancelado quando o usuário rejeita;
  - `data-autosubmit` → substitui `onchange="this.form.submit()"` nos selects de filtro.
- **Init do EasyMDE movido para `app.js`**, condicionado à existência de `#descricao` na página; os assets `vendor/easymde.min.css`/`vendor/easymde.min.js` continuam carregados apenas em `form.html` (requisito "Escopo de carregamento limitado ao formulario" preservado).
- **Templates limpos**: `detail.html` (botões Excluir/Cancelar + `<script>` inline removido), `form.html` (init inline removido), `admin_users.html` (2 `onchange`), `admin_schools.html` (1 `onchange`), `emprestimos_admin.html` (1 `onsubmit`).
- **CSP do Nginx INTOCADO**: `deploy/nginx.conf` permanece com `script-src 'self'`, sem `unsafe-inline`; a compatibilidade vem do JS externo, não de afrouxar a política.
- **Teste de regressão** que renderiza os templates e falha se existir `onclick=`, `onchange=`, `onsubmit=` ou `<script>` sem atributo `src` no HTML produzido.
- **Spec delta em `web-ui`**: novo requisito de JS compatível com `script-src 'self'` (nenhum inline), sem alterar os requisitos existentes de modal/carrossel/EasyMDE/auto-submit.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `web-ui`: novo requisito "JavaScript compatível com CSP" — templates SHALL renderizar sem handlers de evento inline e sem `<script>` inline; todo JS de página vem de `app/static/js/app.js` (carregado em `base.html` via `static_v` + `defer`) e usa listeners com atributos `data-*` (`data-modal-open`, `data-modal-close`, `data-confirm`, `data-autosubmit`).

## Impact

- **Templates**: `app/templates/base.html` (+1 `<script defer src=...>`), `detail.html`, `form.html`, `admin_users.html`, `admin_schools.html`, `emprestimos_admin.html` (remoção de handlers inline/scripts inline; `form.html` mantém os dois `<script src=...>` externos do EasyMDE).
- **JS**: novo `app/static/js/app.js` (~80-120 linhas, vanilla, sem build step); nada em `static/vendor/` muda.
- **Testes**: novo teste de regressão em `tests/` (padrão dos testes existentes de renderização, ex. `tests/test_static_v.py`).
- **Sem mudança** em `deploy/nginx.conf`, rotas Flask, schema, dependências; sem breaking changes. Risco de comportamento: baixo — as 5 interações (modal, carrossel, EasyMDE, auto-submit, confirm) mantêm semântica idêntica, agora acionadas por listeners.