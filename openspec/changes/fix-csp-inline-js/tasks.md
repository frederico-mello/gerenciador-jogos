## 1. JS da aplicação

- [x] 1.1 Criar `app/static/js/app.js` com seções modal/carousel/easymde/auto-submit/confirm conforme design (decisões 1-4): delegação global de `click` para `data-modal-open`/`data-modal-close`, `submit` (capture) para `data-confirm`, `change` para `data-autosubmit`, init condicional de EasyMDE em `#descricao` e carrossel em `#manual-carousel`. Verificar: sintaxe válida (`node --check app/static/js/app.js`).
- [x] 1.2 Carregar `app.js` em `base.html` após `<main>` com `<script defer src="{{ static_v('js/app.js') }}"></script>` (decisão 5). Verificar: `GET /` no client de teste contém `js/app.js` com query `?v=`.

## 2. Templates

- [x] 2.1 `detail.html`: trocar `onclick="openModal()"` (linha 18) por `data-modal-open="delete-modal"`, `onclick="closeModal()"` (linha 163) por `data-modal-close`, e remover todo o `{% block scripts %}` com o `<script>` inline (linhas 171-220). Verificar: HTML renderizado sem `onclick=` e sem `<script>` sem `src`.
- [x] 2.2 `admin_users.html`: remover os dois `onchange="this.form.submit()"` (linhas 8 e 45) e adicionar `data-autosubmit` nos selects. Verificar: HTML renderizado sem `onchange=`.
- [x] 2.3 `admin_schools.html`: remover `onchange="this.form.submit()"` (linha 9) e adicionar `data-autosubmit` no select `rede-filter`. Verificar: HTML renderizado sem `onchange=`.
- [x] 2.4 `emprestimos_admin.html`: remover `onsubmit="return confirm('Cancelar este empréstimo?')"` (linha 106) e adicionar `data-confirm="Cancelar este empréstimo?"` no form. Verificar: HTML renderizado sem `onsubmit=`.
- [x] 2.5 `form.html`: remover o `<script>` inline de init do EasyMDE (linhas 133-157), mantendo `<link>` + `<script src>` externos do EasyMDE (linhas 131-132) no `{% block scripts %}`. Verificar: `GET /novo` renderiza `easymde.min.js` antes de `app.js` na ordem do DOM e sem `<script>` inline.

## 3. Teste de regressão

- [x] 3.1 Criar `tests/test_csp_inline_js.py`: para cada rota renderizada (detalhe, `/novo`, `/admin/users`, `/admin/schools`, `/emprestimos/admin`, `/login`), assertar ausência de `on(click|change|submit|load|error|input|keydown)=` e de `<script(?![^>]*\bsrc=)`, e presença de `js/app.js` (decisão 6). Verificar: `pytest tests/test_csp_inline_js.py -v` verde.
- [x] 3.2 Incluir no teste o caso negativo: mutação sintética (adicionar `onclick=` a um template em memória) faz o detector falhar — valida que o regex pega o padrão. Verificar: teste do detector passa com mutação e sem ela.

## 4. Verificação

- [x] 4.1 Rodar a suíte completa `pytest` e confirmar que nada quebrou (testes existentes de rotas/estáticos/empréstimos permanecem verdes). Verificar: `pytest` verde.
- [x] 4.2 Smoke manual das 5 interações com o app rodando (`flask run`): abrir/fechar modal de exclusão, navegar carrossel, editor EasyMDE em `/novo`, auto-submit dos filtros de usuários/escolas, confirm de cancelamento de empréstimo. Verificar: nenhum erro de console; CSP do dev server não precisa mudar (bloqueio só existe sob Nginx).
- [x] 4.3 `openspec validate fix-csp-inline-js` verde e artefatos consistentes (proposal/specs/design/tasks).