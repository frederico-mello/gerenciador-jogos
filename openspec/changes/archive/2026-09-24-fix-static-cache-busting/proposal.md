## Why

O modal "Confirmar exclusão" abre sozinho na página do jogo: o PR #226 corrigiu o CSS do modal (`<dialog>` nativo), mas `base.html:7` carrega `style.css` sem query de versão e o Nginx emite `expires 30d` immutable para `/static/` — browsers com o CSS antigo em cache mantêm o comportamento quebrado por até 30 dias após cada deploy. As referências a `vendor/easymde.min.css`/`vendor/easymde.min.js` (`form.html:131-132`) têm o mesmo problema: assets estáticos versionados apenas pelo conteúdo do arquivo, sem mecanismo de invalidação em URL. A infraestrutura já resolve o caso análogo de mídias de jogo com cache-busting `?v=<updated_at>`; faltam estaticos do app.

## What Changes

- Helper global de template `static_v(filename)` (context processor em `app/__init__.py`): retorna URL de estático com query `?v=<fingerprint>`, onde o fingerprint é derivado de `mtime_ns` + `size` do arquivo, computado sob demanda com cache no processo (hash curto, ex. primeiros 10 hex de sha256 de `"{mtime_ns}:{size}"`).
- As 3 referências existentes a estáticos passam pelo helper: `base.html:7` (`style.css`) e `form.html:131-132` (`vendor/easymde.min.css`, `vendor/easymde.min.js`).
- Spec delta em `web-ui` espelhando o padrão já estabelecido de cache-busting de mídias (`?v=game.updated_at`): novo requisito de cache-busting de estáticos com versionamento por fingerprint de conteúdo.
- Nginx intocado: `deploy/nginx.conf` continua emitindo `expires 30d` immutable para `/static/`; a invalidação passa a ser garantida pela URL versionada.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `web-ui`: novo requisito de cache-busting de assets estáticos (`style.css`, assets do EasyMDE) via query `?v=<fingerprint de conteúdo>` resolvida por helper global de template; espelha o requisito existente "Cache-busting de mídias de jogo" (`?v=updated_at`).

## Impact

- Código: `app/__init__.py` (helper `static_v` + registro no contexto de template), `app/templates/base.html` (1 linha), `app/templates/form.html` (2 linhas).
- Sem mudança de Nginx, sem dependências novas, sem mudança de schema, sem breaking changes. Assets terceiros em `static/vendor/` recebem a mesma query `?v=`.