# RESEARCH — fix-catalog-media-bugs (Flask 3 + SQLite + Pillow)

Repo alvo: `gerenciador-jogos` (Flask 3, Flask-WTF, Pillow, python-docx, markdown, bleach, SQLite, Jinja2 templates, EasyMDE 2.18.0 já vendorizado em `app/static/vendor/`).

Cinco bugs relatados:

1. Excluir jogo — nada acontece, sem mensagem (modal de confirmação não abre).
2. Foto de jogo existente não atualiza (upload sobrescreve?).
3. Fotos novas do manual não carregam / não são salvas.
4. Descrição salva sem quebras de parágrafo mesmo dando Enter no textarea.
5. Rótulo "Regras (resumo)" → "Objetivo" (só UI).

Pesquisa realizada via MCP `parallel_web_search` / `parallel_web_fetch` filtrada ao que o repo já usa e às restrições (Flask 3, Pillow, JS estático vendored, sem build pipeline).

---

## Opção A — Conserto mínimo dentro do stack atual (sem novas dependências)

- **Componentes**: Flask 3.0+, Flask-WTF (CSRF) + `request.files`, Pillow 10+ (`Image.verify`/`Image.open` + `Image.thumbnail` + `Path.replace` atômico), python-Markdown 3.5+ (já em uso via `extensions=["extra"]`), bleach 6+, `<dialog>` HTML nativo + `showModal()`, label edit em template Jinja2.
- **Versão/licença**: Flask BSD-3, Pillow HPND/MIT-CMU, python-Markdown BSD, bleach Apache-2.0, EasyMDE MIT.
- **Maturidade**: todos em produção há 5+ anos no repo.
- **Encaixe no repo**:
  - Bug 1: trocar `removeAttribute('hidden')` por `modal.showModal()` e `setAttribute('hidden','')` por `modal.close()`; ou simplesmente usar `<div class="modal-overlay" hidden>` (abandonar `<dialog>`). Nenhuma dep nova.
  - Bug 2/3: revisar `_save_uploaded` (`app/routes.py:293`) e `_save_manual_uploads` (`app/routes.py:311`). Quando o usuário escolhe arquivo, `file_storage.filename` está populado; o `if not file_storage or not file_storage.filename: return None` deve funcionar. O bug mais provável é: `imagem_perfil`/manual só é sobrescrito se `comp_path`/`manual_paths` vier truthy, mas no Edit com novo slug (nome mudou), o caminho armazenado aponta para a pasta NOVA (`<new_slug>`) enquanto o arquivo antigo fica órfão em `<old_slug>/perfil.jpg`. Para o manual, `set_manual_pages` faz DELETE+INSERT — então o problema costuma ser CSRF, multipart, ou o usuário não marcou "novo" arquivo (file input vazio fica como `""`).
  - Bug 4: EasyMDE usa `<textarea>` + preview CodeMirror; o `markdown.markdown(text, extensions=["extra"])` no `detalhe` (`app/routes.py:441`) já gera `<p>` para quebras de linha em branco, mas colapsa quebras simples. Adicionar `extensions=["extra","nl2br"]` (ou `"sane_lists"`) preserva Enter único como `<br>`. Não muda schema.
  - Bug 5: trocar string no template `app/templates/form.html:48` e `app/templates/detail.html:67`. Zero dep.
- **Tradeoffs**: zero risco de supply chain, zero custo de migração, fix puramente local.
- **Riscos**:
  - `nl2br` em modo "manutenção" (não recebe features novas, só bugfixes) — sem impacto aqui.
  - `<dialog>` + `showModal()` requer JS habilitado; OK porque o app já depende de JS (carousel manual, EasyMDE).
  - Sobrescrita atômica `Path.replace` no Pillow path precisa de `.tmp` no mesmo filesystem; já está sendo feito em `_save_uploaded`/`_save_manual_uploads`.
- **Fontes**:
  - MDN — `https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/showModal`
  - MDN — `https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog`
  - python-Markdown nl2br — `https://python-markdown.github.io/extensions/nl2br/`
  - python-Markdown extra — `https://github.com/Python-Markdown/markdown/blob/master/docs/extensions/extra.md`
  - Flask `Request.files` — `https://tedboy.github.io/flask/generated/generated/flask.Request.files.html`
  - Pillow Security — `https://github.com/python-pillow/Pillow/security/policy`
  - Pillow 10.0 release notes (decompression bomb guard) — `https://github.com/python-pillow/Pillow/blob/main/docs/releasenotes/10.0.0.rst`

---

## Opção B — Migrar o upload de imagem para Flask-WTF `MultipleFileField` + `FileAllowed`

- **Componentes**: Flask-WTF 1.2+ já disponível, expõe `MultipleFileField` (changelog 1.2.0) e validadores `FileAllowed`/`FileRequired` que suportam listas — substitui `request.files.getlist` manual.
- **Versão/licença**: Flask-WTF 1.2+ (BSD-3), já em `requirements.txt` (`Flask-WTF>=1.2`).
- **Maturidade**: `MultipleFileField` foi adicionado em 1.2.0 (changelog oficial), produção-ready.
- **Encaixe no repo**: refator de `app/routes.py` (`novo`/`editar`) para usar um `FlaskForm` com `FileField("imagem_componentes")`, `FileField("imagem_perfil")` e `MultipleFileField("manual_pages", validators=[FileAllowed(["jpg","jpeg","png"])])`. Mantém Pillow para resize, mantém EasyMDE para descrição, mantém bleach para sanitizar.
- **Tradeoffs**: dá validação + mensagens de erro consistentes (CSRF já vem do Flask-WTF), elimina o bug de "filename vazio" quando há ambiguidade entre `request.files` e `form.*`. Reduz código manual em `_save_uploaded`.
- **Riscos**:
  - Mudança toca formulários e exige migração de templates (`<form>` sem action explícito OK, mas precisa `{{ form.hidden_tag() }}` ou `{{ form.csrf_token }}`).
  - `FileAllowed` hoje depende de Flask-Uploads (deprecated) ou de uma lista simples — usar lista simples evita dep extra.
  - Pequena curva: nomes de campos devem bater entre template e form class.
- **Fontes**:
  - Flask-WTF Changes (1.2.0 MultipleFileField) — `https://flask-wtf.readthedocs.io/en/latest/changes`
  - Flask-WTF file.py source — `https://github.com/wtforms/flask-wtf/blob/main/src/flask_wtf/file.py`
  - Flask-WTF FileField docs — `https://pythonhosted.org/Flask-WTF/form.html`

---

## Opção C — Substituir EasyMDE por alternativa mais leve com textarea vanilla

- **Componentes candidatos**:
  - **EasyMDE 2.21.0** (MIT, fork do SimpleMDE, ~3k stars). Já vendored 2.18.0 — basta bumpar.
  - **CodeMirror 6** (MIT) — moderno, modular, mas requer build pipeline (esbuild/rollup) que o repo não tem.
  - **textarea vanilla + preview server-side** — sem JS de editor; usa só o textarea e renderiza markdown no `detalhe`.
- **Versão/licença**: EasyMDE 2.21.0 (MIT); CodeMirror 6 (MIT); textarea puro (n/a).
- **Maturidade**: EasyMDE mantido ativamente até 2026 (npm mostra 2.21.0 publicado em mai/2026); CodeMirror 6 ativo; textarea puro trivial.
- **Encaixe no repo**:
  - Bump EasyMDE 2.18.0 → 2.21.0 resolve bug menor de preview e garante compat com Chromium recentes; troca 2 arquivos em `app/static/vendor/`.
  - CodeMirror 6 exigiria introduzir build step (NPM/Vite/rollup) — fora do escopo.
  - Textarea vanilla elimina dependência JS de editor (bug 4 vira 100% server-side com `nl2br`).
- **Tradeoffs**: EasyMDE dá UX familiar com toolbar/buttons; vanilla é 0 JS mas perde preview lado-a-lado.
- **Riscos**: EasyMDE 2.x é MIT mas roda sobre CodeMirror 5 (deprecated upstream); trocar para CodeMirror 6 é reescrita. Textarea vanilla perde os botões de formatação (bold/italic/list) que usuários já esperam.
- **Fontes**:
  - EasyMDE npm — `https://www.npmjs.com/package/easymde`
  - EasyMDE GitHub — `https://github.com/ionaru/easy-markdown-editor`
  - EasyMDE jsDelivr — `https://www.jsdelivr.com/package/npm/easymde`

---

## Opção D — Sanitização de markdown + imagem via biblioteca única (Bleach + nh3)

- **Componentes**: bleach 6.1+ (Apache-2.0) já em uso; alternativa moderna **nh3** (Mozilla, MIT) — usa html5ever (Rust) — mais rápida e alinhada com WHATWG, drop-in para `bleach.clean(..., tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)` na maior parte dos casos.
- **Versão/licena**: nh3 0.2.x (MIT); bleach 6.1+ (Apache-2.0).
- **Maturidade**: nh3 maduro (mantido pela Mozilla); bleach maduro mas com issues conhecidas (parser html5lib lento).
- **Encaixe no repo**: troca em `app/routes.py:442` (uma linha) e mantém compat com `ALLOWED_TAGS`/`ALLOWED_ATTRIBUTES`.
- **Tradeoffs**: nh3 mais rápido (≈5-10x), alinhado com WHATWG; bleach mais permissivo (atributos `style`, `class`).
- **Riscos**: nh3 tem allowlist padrão diferente de bleach — exige auditar `ALLOWED_TAGS`/`ALLOWED_ATTRIBUTES` para garantir paridade; bug 4 não é resolvido por sanitizer, é resolvido pelo `nl2br` do python-markdown.
- **Fontes**:
  - bleach docs — `https://bleach.readthedocs.io/`
  - nh3 PyPI — `https://pypi.org/project/nh3/` (busca complementar; placeholder)

---

## Recomendação

**Opção A como base** (consertar o que já existe) + **Opção B como refinamento opcional**.

Justificativa:

- Os cinco bugs são todos corrigíveis sem dependência nova. Bug 1 é puramente HTML/JS (usar `showModal()` no `<dialog>` ou trocar por `<div>` com a classe `.modal-overlay`); bugs 2/3 são validação do fluxo `request.files.getlist` no backend; bug 4 é uma extensão faltante do python-Markdown; bug 5 é string no template.
- Pillow 10+ já lida com decompression bomb e threat model; manter a versão pinned em `requirements.txt` é o bastante.
- EasyMDE 2.18.0 vendored cumpre o papel; bumpar para 2.21.0 (MIT) é trivial e opcional.
- Migrar para Flask-WTF `MultipleFileField` (Opção B) reduz código ad-hoc e dá validação de tipo/tamanho uniforme — útil se houver mais uploads no futuro; pode entrar como segunda task do change.
- **Não** recomendo trocar bleach → nh3 agora (Opção D): bug 4 não depende do sanitizer e o ganho de performance é desprezível num app local com SQLite.
- **Não** recomendo trocar EasyMDE por CodeMirror 6 (Opção C, segundo item): exige pipeline de build que o repo não tem.

Próximas tasks do change (alto nível, para o `propose`):

1. **Bug 5** — string pura: trocar label em `form.html:48` e `detail.html:67`.
2. **Bug 1** — `detail.html:172-181`: `openModal`/`closeModal` → `modal.showModal()`/`modal.close()` (ou trocar `<dialog>` por `<div class="modal-overlay" hidden>`).
3. **Bug 4** — `routes.py:441`: `extensions=["extra","nl2br"]` e validar `bleach.clean` continua aceitando `<br>`.
4. **Bug 2** — `routes.py:293` (`_save_uploaded`): garantir sobrescrita atômica, garantir que `comp_path`/`perfil_path` truthy sobrescreve, e remover arquivo antigo se o slug mudou.
5. **Bug 3** — `routes.py:311` (`_save_manual_uploads`) + `models.set_manual_pages`: garantir que `request.files.getlist("manual_pages")` retorna FileStorages mesmo com EasyMDE presente; remover páginas antigas em disco; persistir ordem.

Notas de risco operacional:

- EasyMDE monta sobre o `<textarea id="descricao">`. Se o `name` do textarea mudar, o POST para de enviar o markdown.
- O `<form>` em `form.html` não usa `{{ form.csrf_token }}` se virar Flask-WTF Form — precisa incluir.
- Em produção (Gunicorn/Nginx), `client_max_body_size` precisa estar ≥ alguns MB para upload de imagem; já está no Nginx de `deploy/`.