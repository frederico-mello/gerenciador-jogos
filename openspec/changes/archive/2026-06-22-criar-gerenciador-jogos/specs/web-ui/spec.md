## ADDED Requirements

### Requirement: Servidor Flask local
O sistema SHALL expor uma aplicação Flask servindo em `http://localhost:5000` quando executado via `flask run` (ou `python -m flask run`). A factory `create_app()` está em `app/__init__.py`.

#### Scenario: Subir o servidor
- **WHEN** o usuário executa `flask run` na raiz do projeto
- **THEN** o servidor sobe em `http://localhost:5000` e responde 200 na rota `/`

### Requirement: Tela de lista com filtro
O sistema SHALL fornecer uma rota `GET /` que renderiza `templates/index.html` listando todos os jogos (nome, área, imagem de perfil como thumbnail), com seletor de área (todas/anatomia/histologia/microbiologia) e campo de busca por nome.

#### Scenario: Lista sem filtro
- **WHEN** o usuário acessa `GET /`
- **THEN** a página mostra todos os jogos ordenados por nome, com o seletor de área em "todas"

#### Scenario: Lista com filtro de área
- **WHEN** o usuário acessa `GET /?area=histologia`
- **THEN** a página mostra apenas jogos de histologia, com o seletor de área em "histologia"

### Requirement: Tela de detalhe com carrossel de manuais
O sistema SHALL fornecer uma rota `GET /<id>` que renderiza `templates/detail.html` mostrando todos os campos do jogo, a imagem de componentes, a imagem de perfil, e o texto descritivo (Markdown renderizado). As páginas de manual (`manual_1.jpg`, `manual_2.jpg`, …) são exibidas em sequência, navegáveis via botões anterior/próximo (carrossel simples em JS).

#### Scenario: Detalhe de jogo com manual de 1 página
- **WHEN** o usuário acessa `GET /<id>` para um jogo com 1 página de manual
- **THEN** a página mostra a imagem do manual sem botões de navegação

#### Scenario: Detalhe de jogo com manual de 2 páginas
- **WHEN** o usuário acessa `GET /<id>` para um jogo com 2 páginas de manual
- **THEN** a página mostra a primeira página do manual, com botões "anterior" (desabilitado) e "próximo" (habilitado); clicar em próximo mostra a segunda página

### Requirement: Formulário de criação
O sistema SHALL fornecer rotas `GET /novo` (renderiza `templates/form.html` vazio) e `POST /novo` (valida, persiste, redireciona para `/<id>`). O form contém campos: nome, área (select), descricao (textarea), regras_resumo, num_jogadores, duracao_min, e uploads opcionais de imagem_componentes, imagem_perfil e 1+ páginas de manual.

#### Scenario: Criar jogo válido
- **WHEN** o usuário preenche nome "Novo Jogo", área "anatomia" e submete
- **THEN** o jogo é criado e o navegador redireciona para `/<novo-id>` mostrando o detalhe

#### Scenario: Upload de imagens na criação
- **WHEN** o usuário anexa uma imagem em `imagem_perfil` ao criar
- **THEN** o arquivo é redimensionado (max 1600px, JPEG q=85) e salvo em `data/anatomia/<slug>/perfil.jpg`, e o path é persistido em `games.imagem_perfil`

### Requirement: Formulário de edição
O sistema SHALL fornecer rotas `GET /<id>/editar` (renderiza `templates/form.html` preenchido) e `POST /<id>/editar` (valida, atualiza, redireciona para `/<id>`). Uploads opcionais substituem as imagens existentes.

#### Scenario: Editar descrição
- **WHEN** o usuário altera o campo `descricao` e submete
- **THEN** o registro é atualizado em `games`, `updated_at` muda, e o navegador redireciona para `/<id>` mostrando o novo texto

#### Scenario: Substituir imagem de perfil
- **WHEN** o usuário anexa nova imagem em `imagem_perfil` ao editar
- **THEN** o arquivo anterior é substituído em `data/.../perfil.jpg` e o path persistido permanece o mesmo

### Requirement: Exclusão com confirmação
O sistema SHALL fornecer um botão "Excluir" na tela de detalhe que abre um modal/página de confirmação, e a rota `POST /<id>/excluir` que remove o jogo do DB, remove os arquivos de `data/<area>/<slug>/` do disco, e redireciona para `/`.

#### Scenario: Confirmar exclusão
- **WHEN** o usuário clica em "Excluir" no detalhe de um jogo e confirma
- **THEN** o registro é removido de `games`, as páginas associadas removidas em cascade, a pasta `data/<area>/<slug>/` é removida do disco, e o navegador redireciona para `/`

#### Scenario: Cancelar exclusão
- **WHEN** o usuário clica em "Cancelar" no modal de confirmação
- **THEN** nada é removido e o usuário permanece na tela de detalhe

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
