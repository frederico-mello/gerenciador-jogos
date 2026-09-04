# Capability: markdown-editor

## Purpose

Editor markdown EasyMDE integrado ao formulário admin de criação/edição de jogos, com toolbar e live preview, self-hosted.

## Requirements

### Requirement: Editor EasyMDE no campo descricao

O formulario de criacao e edicao de jogos SHALL substituir o `<textarea>` simples do campo `descricao` por um editor EasyMDE, carregado a partir de arquivos self-hosted em `app/static/vendor/`. O editor deve fornecer toolbar com botoes para bold, italic, headings (h1-h3), listas ordenadas e nao-ordenadas, citacao, link, imagem, e preview/live-preview com modo side-by-side.

#### Scenario: Formulario de novo jogo exibe editor

- **WHEN** um admin logado acessa `GET /novo`
- **THEN** o campo `descricao` e renderizado como editor EasyMDE com toolbar visivel e textarea vazio pronto para edicao

#### Scenario: Formulario de edicao carrega valor existente

- **WHEN** um admin logado acessa `GET /<id>/editar` para um jogo com `descricao` preenchida
- **THEN** o editor EasyMDE exibe o conteudo markdown existente no textarea, pronto para edicao

#### Scenario: Submit do form envia descricao normalmente

- **WHEN** o admin preenche o editor EasyMDE e submete o formulario
- **THEN** o valor do campo `descricao` e enviado no POST exatamente como no `<textarea>` original, com CSRF token preservado

### Requirement: Arquivos EasyMDE self-hosted

Os arquivos do EasyMDE SHALL ser armazenados em `app/static/vendor/easymde.min.css` e `app/static/vendor/easymde.min.js`, servidos via `url_for('static', filename='vendor/...')`. Nenhuma dependencia de CDN em runtime.

#### Scenario: Arquivos servidos pelo Flask

- **WHEN** o navegador requisita `/static/vendor/easymde.min.js`
- **THEN** o Flask retorna o arquivo com Content-Type `application/javascript`

#### Scenario: Acesso offline

- **WHEN** a aplicacao e executada sem acesso a internet
- **THEN** o editor EasyMDE funciona normalmente, pois todos os assets sao locais

### Requirement: Escopo de carregamento limitado ao formulario

Os assets do EasyMDE SHALL ser carregados apenas no `{% block scripts %}` de `form.html`, e NAO em `base.html`. Outras paginas (index, detail, login) NAO devem carregar os arquivos do editor.

#### Scenario: Pagina de formulario carrega editor

- **WHEN** um admin acessa `GET /novo` ou `GET /<id>/editar`
- **THEN** a pagina carrega `easymde.min.css` e `easymde.min.js` e inicializa o editor no campo `descricao`

#### Scenario: Pagina de detalhe nao carrega editor

- **WHEN** qualquer usuario acessa `GET /<id>`
- **THEN** a pagina NAO carrega arquivos do EasyMDE

### Requirement: Toolbar configurada para o contexto

A toolbar do EasyMDE SHALL incluir os botoes: bold, italic, heading, unordered-list, ordered-list, quote, link, image, preview, side-by-side, fullscreen, guide. Botoes ausentes no contexto (ex.: table) SHALL ser omitidos. O spellchecker nativo SHALL ser desabilitado.

#### Scenario: Toolbar visivel com botoes configurados

- **WHEN** o editor EasyMDE e renderizado
- **THEN** a toolbar exibe bold, italic, heading, listas, quote, link, image, preview, side-by-side, fullscreen e guide
- **THEN** a toolbar NAO exibe botao de tabela
