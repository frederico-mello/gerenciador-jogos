## MODIFIED Requirements

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

### Requirement: Tela de detalhe com carrossel de manuais
O sistema SHALL fornecer uma rota `GET /<id>` que renderiza `templates/detail.html` mostrando todos os campos do jogo, a imagem de componentes, a imagem de perfil, e o texto descritivo (Markdown renderizado). As páginas de manual (`manual_1.jpg`, `manual_2.jpg`, …) são exibidas em sequência, navegáveis via botões anterior/próximo (carrossel simples em JS). **A rota é pública (read-only). Botões de editar/excluir são exibidos apenas para `admin_sistema` e `admin_jogos`.**

#### Scenario: Detalhe de jogo com manual de 1 página (visitante)
- **WHEN** um visitante não logado acessa `GET /<id>` para um jogo com 1 página de manual
- **THEN** a página mostra a imagem do manual sem botões de navegação, e sem botões de editar/excluir

#### Scenario: Detalhe de jogo com manual de 2 páginas (admin_jogos)
- **WHEN** um `admin_jogos` logado acessa `GET /<id>` para um jogo com 2 páginas de manual
- **THEN** a página mostra a primeira página do manual, com botões "anterior" (desabilitado) e "próximo" (habilitado); clicar em próximo mostra a segunda página; botões "Editar" e "Excluir" são exibidos

## ADDED Requirements

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
