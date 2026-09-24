## Context

CSP de produção `script-src 'self'` (`deploy/nginx.conf:28`) bloqueia os 8 pontos inline mapeados no EXPLORE (ver proposal.md — Why). O app já tem a infraestrutura necessária: helper `static_v` (change `fix-static-cache-busting`) em `base.html:7`, EasyMDE self-hosted em `static/vendor/` e modal nativo `<dialog>` (requisito "Modal de exclusão via dialog nativo"). Decisões de escopo já tomadas pelo coordenador: um único `app.js` via `static_v` + `defer`, listeners com `data-*`, CSP intocada, teste de regressão de templates e spec delta em `web-ui`.

## Goals / Non-Goals

**Goals:**
- Todas as 5 interações (modal, carrossel, EasyMDE, auto-submit, confirm) funcionando sob `script-src 'self'`, com semântica idêntica à atual.
- Um único ponto de JS de aplicação (`app/static/js/app.js`), sem build step, sem framework.
- Garantia estrutural contra reintrodução de inline: teste de regressão automatizado.

**Non-Goals:**
- Afrouxar a CSP (`unsafe-inline`, hashes, nonces) — decidido: CSP intocada.
- Migrar EasyMDE ou seus assets (`static/vendor/` permanece); os `<script src>` externos de `form.html` são permitidos pela CSP.
- Introduzir bundler/TypeScript/module loader; JS vanilla IIFE.
- Reescrever estilos, rotas ou backend.

## Decisions

1. **Delegação por `data-*` em um listener global por seção** (em vez de listeners individuais em cada elemento). `app.js` registra, uma vez, handlers nos containers `document`/`body` para `click` (`data-modal-open`, `data-modal-close`), `submit` (`data-confirm`, captive) e `change` (`data-autosubmit`). Vantagens: tolera conteúdo dinâmico sem re-binding, e o HTML dos templates só ganha um atributo declarativo. Alternativa descartada: listeners por elemento em `DOMContentLoaded` — mais acoplado a ids e frágil com múltiplos forms (tabelas de admin têm N forms idênticos).
   - `data-confirm`: listener `submit` em `document` com `capture: true`; se `form.hasAttribute('data-confirm')` e `!window.confirm(mensagem)`, `e.preventDefault()`. Mensagem extraída do valor do atributo (`data-confirm="Cancelar este empréstimo?"`), fallback para texto genérico. Preserva a semântica de `onsubmit="return confirm(...)"` (`emprestimos_admin.html:106`).
   - `data-autosubmit`: no `change`, `element.closest('form')?.requestSubmit()` com fallback `submit()`. `requestSubmit` respeita validação e botão submit implícito; os forms são GET simples, sem validação restritiva.
2. **Modal por seletor genérico, não por id fixo.** O listener de `click` resolve o `<dialog>` via `document.getElementById(el.getAttribute('data-modal-open'))` (ou `closest('dialog')` para close). Preserva o `<dialog>` nativo e o requisito existente do modal; `detail.html` ganha `data-modal-open="delete-modal"` / `data-modal-close` e perde `onclick`.
3. **EasyMDE condicionado à existência de `#descricao`.** Seção `easymde` de `app.js`: `document.getElementById('descricao')` → se ausente, return (index/detail/login não tocam no EasyMDE). Requer que os assets externos do EasyMDE carreguem antes de `app.js`: em `form.html`, `easymde.min.js` (externo, já versionado por `static_v`) fica antes do `app.js` herdado de `base.html` — `defer` preserva a ordem de execução. Alternativa descartada: mover o EasyMDE para `base.html` (viola o requisito "Escopo de carregamento limitado ao formulario").
4. **Carrossel por inicialização idempotente.** Seção `carousel`: procura `#manual-carousel`; sem slides > 1, return. Mantém ids existentes (`carousel-prev`, `carousel-next`, `carousel-status`) e o `noscript` fallback (`detail.html:95-97`), trocando apenas o IIFE inline por função de `app.js`.
5. **`app.js` carregado em `base.html` via `static_v` + `defer`**, dentro de `{% block scripts %}`? Não — no corpo do template após `<main>`, para que `{% block scripts %}` (usado por `form.html`) continue existindo e possa inserir scripts **antes** na ordem de execução. Como `defer` executa em ordem de documento e `form.html` injeta `easymde.min.js` no bloco (que aparece antes do `app.js` no DOM), a ordem fica correta sem flags extras.
6. **Teste de regressão por renderização de rotas**, não por leitura de arquivos de template. Reutiliza os fixtures de `tests/conftest.py` (client + roles): para cada rota renderizada (detalhe, `/novo`, `/admin/users`, `/admin/schools`, `/emprestimos/admin`, login), asserta que o HTML não casa com `on(click|change|submit|load|error|input|keydown)=` nem com `<script(?![^>]*\bsrc=)`, e que `js/app.js` aparece. Regex `<script(?!\ssrc)` com PCRE no HTML serializado; mensagem de erro inclui o template e o trecho. Complemento barato: varre também os arquivos `app/templates/*.html` por `on\w+=` (fora de comentários Jinja) para cobrir rotas não renderizadas no teste. Alternativa descartada: lint custom — mais infraestrutura que o necessário.
7. **CSP intocada.** `deploy/nginx.conf` não muda. Sem `unsafe-inline`, sem hashes, sem nonces: o objetivo é compatibilidade estrutural, não exceção.

## Risks / Trade-offs

- [Um `app.js` global carrega em todas as páginas] → Mitigação: cada seção retorna cedo quando seu gancho (`#descricao`, `#manual-carousel`, `data-*`) não existe; arquivo pequeno (~100 linhas), sem custo perceptível.
- [`requestSubmit` sem suporte em browsers antigos] → Mitigação: fallback `form.submit()`; usuários-alvo usam browsers modernos (intranet escolar).
- [Ordem de execução EasyMDE → app.js depende do posicionamento do `{% block scripts %}` em `base.html`] → Mitigação: decisão 5 fixa a ordem no DOM; teste de regressão verifica presença de `app.js`; smoke manual do formulário cobre o editor.
- [Regex de teste pode falso-positivar em texto de conteúdo com `onclick=`] → Mitigação: padrões ancorados em atributos HTML (`\son\w+=`) e nenhuma rota renderiza conteúdo de usuário dentro de atributos (Markdown é sanitizado e injetado como nós, não atributos).
- [Modal dependente de JS] (já era: `<dialog>.showModal()` só existe via JS) → Sem regressão; `noscript` do carrossel mostra todas as páginas, modal simplesmente não abre sem JS (comportamento igual ao atual em produção).

## Migration Plan

1. Criar `app/static/js/app.js` com as 5 seções (modal, carousel, easymde, auto-submit, confirm).
2. `base.html`: adicionar `<script defer src="{{ static_v('js/app.js') }}"></script>` após `<main>`.
3. Templates: trocar handlers inline por `data-*` (`detail.html`, `admin_users.html` ×2, `admin_schools.html`, `emprestimos_admin.html`) e remover os `<script>` inline de `detail.html`/`form.html` (mantendo os `<script src>` externos + `<link>` do EasyMDE em `form.html`).
4. Adicionar teste de regressão em `tests/` seguindo o padrão de `tests/test_static_v.py`.
5. Deploy: deploy normal (estáticos versionados por `static_v`, cache não é obstáculo). Rollback: `git revert` do commit único; sem schema, sem migração de dados.

## Open Questions

(nenhuma — decisões do coordenador fecham o escopo; detalhes nomeados em tasks.md)