## Context

O repo servia 3 assets estáticos sem versão em URL: `style.css` em `base.html:7` e os assets do EasyMDE em `form.html:131-132`. O PR #226 já estabeleceu o padrão de cache-busting para mídias de jogo (`?v=game.updated_at` em `url_for('games.media', ...)`) e a spec `web-ui` já o descreve no requisito "Cache-busting de mídias de jogo". O Nginx (`deploy/nginx.conf`) emite `expires 30d` immutable para `/static/` — por decisão do coordenador, permanece intocado; a invalidação passa a ser responsabilidade da URL. A factory `create_app()` em `app/__init__.py` já registra `after_request` inline, ou seja, é o lugar natural para registrar também um context processor.

## Goals / Non-Goals

**Goals:**
- Garantir que alterações em `static/*.css`/`*.js` (e `static/vendor/*`) sejam percebidas pelos browsers no primeiro acesso após o deploy, sem intervenção manual.
- Reusar o padrão de query `?v=` já aceito e documentado para mídias.
- Helper único e generalizado, usado por todas as templates atuais e futuras.

**Non-Goals:**
- Alterar `deploy/nginx.conf` (TTL de 30d immutable permanece).
- Implementar o change (fase apply cuida disso).
- Versionar rotas dinâmicas (`/media/`) — já cobertas pelo requisito existente.

## Decisions

**D1 — Versionamento por fingerprint de conteúdo (mtime_ns + size), não constante manual.**
O helper computa `f"{mtime_ns}:{size}"`, gera sha256 e usa os primeiros 10 hex como `?v=`. Rationale: constante manual (`?v=2`) esquecida em deploy é a causa raiz deste bug; fingerprint de arquivo se atualiza sozinho. Alternativas descartadas: constante incrementada à mão (sujeita a esquecimento, recaída do mesmo bug); `?v=<deploy_id>` global (invalida todo o cache a cada deploy, desperdiçando cache de assets não alterados); hash do conteúdo do arquivo (leitura completa a cada miss de cache, custo maior sem ganho prático sobre mtime_ns+size, que muda em qualquer escrita).

**D2 — Cache do fingerprint no processo.**
`os.stat` é barato, mas cada render de `base.html` faria 1 stat; com cache em dict no escopo do módulo/helper, o stat acontece 1× por arquivo por processo (gunicorn worker) e é refeito só quando o processo reinicia. Rationale: suficiente — deploys reiniciam o Gunicorn, e `mtime_ns` de arquivo novo difere. Trade-off aceito: um deploy que substitui arquivo **sem** reiniciar o processo (edição manual em produção) não invalida o cache do helper; isso não ocorre no fluxo de deploy atual (`deploy/setup.sh` reinicia o serviço).

**D3 — Helper global via context processor em `app/__init__.py`.**
`static_v(filename)` retorna `url_for('static', filename=filename, v=fingerprint)`. Registrado com `@app.context_processor` dentro de `create_app()`, disponível em todas as templates sem import. Alternativa `app.template_global` tem o mesmo efeito; context processor segue o padrão Flask canônico para helpers de template. Fallback: se `os.stat` falhar (arquivo ausente), o helper retorna a URL sem `?v=` — nunca quebra o render.

**D4 — Migração das 3 referências existentes.**
`base.html:7` → `static_v('style.css')`; `form.html:131-132` → `static_v('vendor/easymde.min.css')` e `static_v('vendor/easymde.min.js')`. Nenhuma outra referência a `url_for('static', ...)` existe nos templates (verificado por busca). Templates futuras devem usar `static_v`.

## Risks / Trade-offs

- [mtime de arquivo depende do filesystem/deploy preservar timestamps] → Mitigação: `mtime_ns` é capturado no boot/primeiro acesso após reinício do processo; deploys reescrevem o arquivo (mtime novo). Se um deploy copiar com timestamp idêntico E mesmo size, a URL não muda — cenário raro e auto-corrigido no deploy seguinte com reinício.
- [Cache do helper fica obsoleto se o processo não reiniciar no deploy] → Mitigação: fluxo de deploy atual (`deploy/gunicorn.service` + `setup.sh`) reinicia o serviço; documentado como precondição.
- [Assets de vendor com fingerprint estranho em URL] → Mitigação: nenhuma restrição do Nginx sobre query strings; serving é inalterado.

## Migration Plan

Deploy padrão: subir o código (templates + `app/__init__.py`) e reiniciar o Gunicorn (passo já obrigatório no fluxo). Rollback: reverter o commit — URLs voltam a ser sem `?v=`, cache antigo volta a valer por até 30d (mesmo comportamento de hoje). Sem migração de dados.

## Open Questions

(nenhuma — decisões do coordenador já ancoradas: fingerprint por mtime_ns+size com cache no processo, helper global em `app/__init__.py`, Nginx intocado.)