## ADDED Requirements

### Requirement: Cache-busting de assets estáticos
As templates que referenciam assets estáticos do app via `url_for('static', ...)` SHALL acrescentar query string de versão `?v=<fingerprint>` ao atributo `href`/`src`, espelhando o padrão de "Cache-busting de mídias de jogo" (`?v=<updated_at>`). O fingerprint SHALL refletir o conteúdo corrente do arquivo no servidor (derivado de `mtime_ns` + `size` do arquivo), de forma que a URL mude automaticamente quando o arquivo é substituído no deploy. O fingerprint SHALL ser computado sob demanda com cache no processo (um `stat` por arquivo por processo), sem constantes de versão mantidas manualmente. Um asset servido com `expires 30d` immutable (`/static/` no Nginx) SHALL ser invalidado pela mudança da URL, não pela redução do TTL.

#### Scenario: style.css versionado na página base
- **WHEN** qualquer página é renderizada a partir de `base.html`
- **THEN** o `<link rel="stylesheet">` aponta para `style.css?v=<fingerprint>`, onde `?v=` muda quando o arquivo `static/style.css` é substituído

#### Scenario: Assets do EasyMDE versionados no formulário
- **WHEN** a página de formulário (`form.html`) é renderizada
- **THEN** `vendor/easymde.min.css` e `vendor/easymde.min.js` são referenciados com `?v=<fingerprint>`

#### Scenario: Re-deploy com CSS novo invalida o cache
- **WHEN** `static/style.css` é substituído no deploy (mtime/size alterados) e o processo de app reinicia
- **THEN** a URL servida para `style.css` contém `?v=` diferente do deploy anterior, forçando o browser a buscar o CSS novo apesar do `expires 30d` immutable do Nginx

#### Scenario: Fingerprint ausente não quebra o render
- **WHEN** o helper de versão não consegue resolver o fingerprint de um arquivo (ex.: arquivo ausente)
- **THEN** a template renderiza a URL sem `?v=` e a página não falha

#### Scenario: Helper disponível globalmente nas templates
- **WHEN** qualquer template do app referencia um asset estático
- **THEN** o helper de versão está disponível no contexto de template sem import explícito (helper global registrado na factory da aplicação)