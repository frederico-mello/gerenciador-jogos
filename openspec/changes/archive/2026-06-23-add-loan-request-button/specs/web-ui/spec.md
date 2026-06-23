## MODIFIED Requirements

### Requirement: Tela de detalhe com carrossel de manuais
O sistema SHALL fornecer uma rota `GET /<id>` que renderiza `templates/detail.html` mostrando todos os campos do jogo, a imagem de componentes, a imagem de perfil, e o texto descritivo (Markdown renderizado). As páginas de manual (`manual_1.jpg`, `manual_2.jpg`, …) são exibidas em sequência, navegáveis via botões anterior/próximo (carrossel simples em JS). **A rota é pública (read-only). O badge de disponibilidade é exibido. Uma seção "Histórico de empréstimos" é exibida apenas para usuários com role `admin_sistema` ou `admin_jogos`, listando todos os empréstimos do jogo ordenados por data, com usuário, período, status. Botões de editar/excluir são exibidos apenas para `admin_sistema` e `admin_jogos`. Um botão de ação de empréstimo é exibido conforme o role do usuário e a disponibilidade do jogo (ver requirement "Botão de solicitar empréstimo na página de detalhe").**

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

## ADDED Requirements

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
