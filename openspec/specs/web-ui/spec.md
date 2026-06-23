# Capability: web-ui

## Purpose

TBD — Interface web Flask para o catálogo de jogos: lista, detalhe, formulários de criação/edição, exclusão e servir mídias.

## Requirements

### Requirement: Servidor Flask local
O sistema SHALL expor uma aplicação Flask servindo em `http://localhost:5000` quando executado via `flask run` (ou `python -m flask run`). A factory `create_app()` está em `app/__init__.py`.

#### Scenario: Subir o servidor
- **WHEN** o usuário executa `flask run` na raiz do projeto
- **THEN** o servidor sobe em `http://localhost:5000` e responde 200 na rota `/`

### Requirement: Tela de lista com filtro
O sistema SHALL fornecer uma rota `GET /` que renderiza `templates/index.html` listando todos os jogos (nome, área, imagem de perfil como thumbnail), com seletor de área (todas/anatomia/histologia/microbiologia) e campo de busca por nome. **Cada card de jogo mostra adicionalmente um badge de disponibilidade (verde = Disponível, amarelo = Reservado/Solicitado, vermelho = Emprestado) derivado da tabela `loans`.**

#### Scenario: Lista sem filtro
- **WHEN** o usuário acessa `GET /`
- **THEN** a página mostra todos os jogos ordenados por nome, com o seletor de área em "todas"

#### Scenario: Lista com filtro de área
- **WHEN** o usuário acessa `GET /?area=histologia`
- **THEN** a página mostra apenas jogos de histologia, com o seletor de área em "histologia"

#### Scenario: Lista com badge de disponibilidade
- **WHEN** o visitante acessa `GET /`
- **THEN** cada card de jogo exibe o badge de disponibilidade ao lado do nome

### Requirement: Tela de detalhe com carrossel de manuais
O sistema SHALL fornecer uma rota `GET /<id>` que renderiza `templates/detail.html` mostrando todos os campos do jogo, a imagem de componentes, a imagem de perfil, e o texto descritivo (Markdown renderizado). As páginas de manual (`manual_1.jpg`, `manual_2.jpg`, …) são exibidas em sequência, navegáveis via botões anterior/próximo (carrossel simples em JS). **A rota é pública (read-only). O badge de disponibilidade é exibido. Uma seção "Histórico de empréstimos" é exibida apenas para usuários com role `admin_sistema` ou `admin_jogos`, listando todos os empréstimos do jogo ordenados por data. Botões de editar/excluir são exibidos apenas para `admin_sistema` e `admin_jogos`. Um botão de ação de empréstimo é exibido conforme o role do usuário e a disponibilidade do jogo (ver requirement "Botão de solicitar empréstimo na página de detalhe").**

#### Scenario: Detalhe de jogo com manual de 1 página (visitante)
- **WHEN** um visitante não logado acessa `GET /<id>` para um jogo com 1 página de manual
- **THEN** a página mostra a imagem do manual sem botões de navegação, sem botões de editar/excluir, e o badge de disponibilidade é exibido

#### Scenario: Detalhe de jogo com manual de 2 páginas (admin_jogos)
- **WHEN** um `admin_jogos` logado acessa `GET /<id>` para um jogo com 2 páginas de manual
- **THEN** a página mostra a primeira página do manual, com botões "anterior" (desabilitado) e "próximo" (habilitado); clicar em próximo mostra a segunda página; botões "Editar" e "Excluir" são exibidos; a seção de histórico mostra os empréstimos passados

#### Scenario: Admin vê badge + histórico
- **WHEN** um `admin_jogos` logado acessa `GET /<id>` para um jogo emprestado
- **THEN** o badge mostra "Emprestado" em vermelho, e a seção de histórico exibe os empréstimos passados

#### Scenario: Visitante vê badge sem histórico
- **WHEN** um visitante não logado acessa `GET /<id>` para um jogo disponível
- **THEN** o badge mostra "Disponível" em verde, e a seção de histórico não é exibida

### Requirement: Formulário de criação
O sistema SHALL fornecer rotas `GET /novo` (renderiza `templates/form.html` vazio) e `POST /novo` (valida, persiste, redireciona para `/<id>`). O form contém campos: nome, área (select), descricao (textarea), regras_resumo, num_jogadores, duracao_min, e uploads opcionais de imagem_componentes, imagem_perfil e 1+ páginas de manual. **Ambas as rotas requerem `@role_required('admin_sistema', 'admin_jogos')`.** Visitantes não logados são redirecionados para `/login`.

#### Scenario: Criar jogo válido
- **WHEN** um `admin_jogos` logado preenche nome "Novo Jogo", área "anatomia" e submete
- **THEN** o jogo é criado e o navegador redireciona para `/<novo-id>` mostrando o detalhe

#### Scenario: Upload de imagens na criação
- **WHEN** o `admin_jogos` anexa uma imagem em `imagem_perfil` ao criar
- **THEN** o arquivo é redimensionado (max 1600px, JPEG q=85) e salvo em `data/anatomia/<slug>/perfil.jpg`, e o path é persistido em `games.imagem_perfil`

#### Scenario: Visitante não logado tenta criar
- **WHEN** um visitante não logado acessa `GET /novo`
- **THEN** é redirecionado para `/login` com mensagem "Login necessário"

#### Scenario: Usuario comum tenta criar
- **WHEN** um `usuario` logado acessa `POST /novo`
- **THEN** recebe HTTP 403 Forbidden

### Requirement: Formulário de edição
O sistema SHALL fornecer rotas `GET /<id>/editar` (renderiza `templates/form.html` preenchido) e `POST /<id>/editar` (valida, atualiza, redireciona para `/<id>`). Uploads opcionais substituem as imagens existentes. **Ambas as rotas requerem `@role_required('admin_sistema', 'admin_jogos')`.**

#### Scenario: Editar descrição
- **WHEN** um `admin_jogos` logado altera o campo `descricao` e submete
- **THEN** o registro é atualizado em `games`, `updated_at` muda, e o navegador redireciona para `/<id>` mostrando o novo texto

#### Scenario: Substituir imagem de perfil
- **WHEN** o `admin_jogos` anexa nova imagem em `imagem_perfil` ao editar
- **THEN** o arquivo anterior é substituído em `data/.../perfil.jpg` e o path persistido permanece o mesmo

#### Scenario: Usuario comum tenta editar
- **WHEN** um `usuario` logado acessa `GET /<id>/editar`
- **THEN** recebe HTTP 403 Forbidden

### Requirement: Exclusão com confirmação
O sistema SHALL fornecer um botão "Excluir" na tela de detalhe que abre um modal/página de confirmação, e a rota `POST /<id>/excluir` que remove o jogo do DB, remove os arquivos de `data/<area>/<slug>/` do disco, e redireciona para `/`. **A rota `POST /<id>/excluir` requer `@role_required('admin_sistema', 'admin_jogos')`. O botão "Excluir" só é exibido para usuários com permissão.**

#### Scenario: Confirmar exclusão
- **WHEN** o `admin_jogos` logado clica em "Excluir" no detalhe de um jogo e confirma
- **THEN** o registro é removido de `games`, as páginas associadas removidas em cascade, a pasta `data/<area>/<slug>/` é removida do disco, e o navegador redireciona para `/`

#### Scenario: Cancelar exclusão
- **WHEN** o usuário clica em "Cancelar" no modal de confirmação
- **THEN** nada é removido e o usuário permanece na tela de detalhe

#### Scenario: Usuario comum não vê botão excluir
- **WHEN** um `usuario` logado acessa `GET /<id>`
- **THEN** o botão "Excluir" não é exibido

### Requirement: Servir arquivos estáticos de imagens
O sistema SHALL servir as imagens de `data/` via uma rota `GET /media/<path:filename>` que usa `flask.send_from_directory('data', filename)`, para que templates possam referenciar `<img src="/media/<game.imagem_perfil>">`.

#### Scenario: Acessar imagem de perfil
- **WHEN** o navegador requisita `GET /media/anatomia/memotomia/perfil.jpg`
- **THEN** o Flask retorna o arquivo JPEG com content-type `image/jpeg`

### Requirement: Renderização de Markdown na descrição
O sistema SHALL renderizar o campo `descricao` (Markdown) como HTML na tela de detalhe, usando a biblioteca `markdown` (ou `mistune`). A conversão acontece em runtime no template via filtro Jinja2 ou no route handler.

#### Scenario: Descrição com Markdown
- **WHEN** o jogo tem `descricao` contendo "# Título\n\nTexto em **negrito**"
- **THEN** a tela de detalhe mostra "Título" como h1 e "Texto em **negrito**" com a palavra em negrito

### Requirement: Nav dinâmico por role
O sistema SHALL exibir links de navegação diferentes em `base.html` conforme o role do usuário logado: visitante não logado vê "Login" e "Registrar"; `usuario` vê "Meus empréstimos" (no Change 2) e "Logout"; `admin_jogos` vê "Novo jogo", "Empréstimos (admin)" (no Change 2) e "Logout"; `admin_sistema` vê tudo de `admin_jogos` mais "Usuários" e "Escolas".

#### Scenario: Nav para visitante
- **WHEN** um visitante não logado acessa qualquer página
- **THEN** o nav mostra "Login" e "Registrar", sem links de admin

#### Scenario: Nav para admin_sistema
- **WHEN** um `admin_sistema` logado acessa qualquer página
- **THEN** o nav mostra "Novo jogo", "Usuários", "Escolas", "Logout"

### Requirement: Rotas de autenticação
O sistema SHALL fornecer `GET/POST /login` (form de login com email e senha), `GET/POST /registrar` (form de self-registration), e `GET /logout` (encerra sessão). Estas rotas são públicas (exceto `/logout` que requer login).

#### Scenario: Acessar página de login
- **WHEN** um visitante acessa `GET /login`
- **THEN** o form de login é renderizado com campos email e senha

#### Scenario: Acessar página de registro
- **WHEN** um visitante acessa `GET /registrar`
- **THEN** o form de registro é renderizado com campos nome, email, senha, confirmação, e escola (datalist)

### Requirement: Rotas admin de usuários
O sistema SHALL fornecer `GET /admin/users` (lista), `GET/POST /admin/users/<id>/editar`, e `POST /admin/users/<id>/role` — todas protegidas com `@role_required('admin_sistema')`.

#### Scenario: Acessar lista de usuários
- **WHEN** o `admin_sistema` acessa `GET /admin/users`
- **THEN** a página mostra tabela de usuários com filtros por role e escola

### Requirement: Botão de solicitar empréstimo na página de detalhe
O sistema SHALL exibir na página de detalhe do jogo (`GET /<id>`) um botão de ação de empréstimo dentro do bloco `.detail-actions`, com comportamento condicional:

- **Usuário `usuario` logado + jogo disponível + sem loan ativo próprio**: botão "Solicitar Empréstimo" (form POST para `/emprestimos/solicitar/<game_id>`)
- **Usuário `usuario` logado + jogo indisponível**: botão "Entrar na fila" (link para `/emprestimos/fila/confirmar/<game_id>`)
- **Usuário `usuario` logado + já possui loan ativo para este jogo**: nenhum botão exibido
- **Usuário não logado + jogo disponível**: botão/link "Faça login para solicitar" (link para `/login`)
- **Admin (`admin_sistema` ou `admin_jogos`)**: nenhum botão de empréstimo (admins não solicitam empréstimos)

#### Scenario: Usuário vê botão solicitar em jogo disponível
- **WHEN** um `usuario` logado acessa `GET /<id>` para um jogo com `availability_status = 'disponivel'` e sem loan ativo próprio
- **THEN** a página exibe um botão "Solicitar Empréstimo" que envia `POST /emprestimos/solicitar/<game_id>` com CSRF token

#### Scenario: Usuário vê botão entrar na fila em jogo indisponível
- **WHEN** um `usuario` logado acessa `GET /<id>` para um jogo com `availability_status != 'disponivel'` e sem loan ativo próprio
- **THEN** a página exibe um botão "Entrar na fila" que linka para `/emprestimos/fila/confirmar/<game_id>`

#### Scenario: Usuário com loan ativo não vê botão
- **WHEN** um `usuario` logado acessa `GET /<id>` para um jogo para o qual já possui um loan ativo (solicitado, reservado ou emprestado)
- **THEN** nenhum botão de empréstimo é exibido na página

#### Scenario: Visitante vê link para login
- **WHEN** um visitante não logado acessa `GET /<id>` para um jogo disponível
- **THEN** a página exibe um link "Faça login para solicitar" que redireciona para `/login`

#### Scenario: Admin não vê botão de empréstimo
- **WHEN** um `admin_jogos` logado acessa `GET /<id>`
- **THEN** nenhum botão de solicitar emprestimo é exibido (apenas botões Editar/Excluir)

### Requirement: Botão de solicitar empréstimo na página Meus Empréstimos
O sistema SHALL exibir na página "Meus Empréstimos" (`GET /emprestimos`) um botão/link "Solicitar novo empréstimo" que redireciona para o catálogo (`GET /`). O botão deve estar visível independentemente de haver loans na lista.

#### Scenario: Usuário vê botão com lista vazia
- **WHEN** um `usuario` acessa `GET /emprestimos` e não possui nenhum empréstimo
- **THEN** a página mostra a mensagem "Nenhum empréstimo encontrado" e um botão "Solicitar novo empréstimo" que linka para `GET /`

#### Scenario: Usuário vê botão com lista populada
- **WHEN** um `usuario` acessa `GET /emprestimos` e possui empréstimos
- **THEN** a página mostra a tabela de empréstimos e um botão "Solicitar novo empréstimo" que linka para `GET /`
