## MODIFIED Requirements

### Requirement: Solicitação de empréstimo pelo usuário
O sistema SHALL permitir que um `usuario` logado solicite um empréstimo via `POST /emprestimos/solicitar/<game_id>`. **Se o jogo já possui um empréstimo ativo, o sistema pergunta se o usuário deseja entrar na fila de reserva. Se sim, cria uma entrada em `reservation_queue` com a próxima posição disponível.**

#### Scenario: Entrar na fila quando indisponível
- **WHEN** um `usuario` tenta solicitar um jogo já emprestado
- **THEN** o sistema exibe mensagem "Jogo indisponível no momento. Entrar na fila de reserva?" com botão "Sim, reservar"

#### Scenario: Confirmar fila
- **WHEN** o usuário clica em "Sim, reservar"
- **THEN** uma entrada é criada em `reservation_queue` com `game_id`, `user_id`, `posicao = MAX(posicao) + 1`, `status='na_fila'`

### Requirement: Admin gerencia fila de reserva
O sistema SHALL exibir na lista admin de empréstimos a informação de quantas pessoas estão na fila de cada jogo. Ao devolver um jogo, o admin pode clicar "Notificar próximo da fila", que muda o status do primeiro `na_fila` para `notificado` e envia email (se configurado) informando que o jogo está disponível.

#### Scenario: Admin vê fila
- **WHEN** um admin acessa `GET /emprestimos/admin` para um jogo com 3 pessoas na fila
- **THEN** a linha do jogo exibe badge "3 na fila" com link para gerenciar

#### Scenario: Notificar próximo
- **WHEN** o admin devolve um jogo e clica em "Notificar próximo"
- **THEN** o primeiro `na_fila` muda para `notificado`, email é enviado (se configurado), e o admin vê confirmação

#### Scenario: Avançar fila automaticamente se email não configurado
- **WHEN** o admin devolve um jogo, clica em "Notificar próximo", mas SMTP não está configurado
- **THEN** o status muda para `notificado`, uma mensagem in-app é exibida, e o admin pode manualmente avisar o usuário

### Requirement: Paginação no catálogo e listas
O sistema SHALL adicionar paginação baseada em `LIMIT/OFFSET` nas rotas: `GET /` (catálogo), `GET /emprestimos` (usuário), `GET /emprestimos/admin` (admin). O parâmetro `?page=<n>` controla a página atual (default 1). `per_page` é 20 para o catálogo e 30 para listas de empréstimos. Os filtros existentes são preservados na navegação entre páginas.

#### Scenario: Navegar páginas do catálogo
- **WHEN** o catálogo tem 50 jogos e o visitante acessa `GET /?page=2`
- **THEN** os jogos 21-40 são exibidos, com links `<1 2 3>` no footer

#### Scenario: Filtros preservados
- **WHEN** o visitante acessa `GET /?area=histologia&page=2`
- **THEN** a página 2 dos jogos de histologia é exibida, filtro mantido

#### Scenario: Página além do limite
- **WHEN** o visitante acessa `GET /?page=999`
- **THEN** a última página disponível é exibida (não erro)

### Requirement: Export CSV de empréstimos
O sistema SHALL fornecer `GET /emprestimos/admin/export.csv` que retorna um arquivo CSV com todos os empréstimos (aplicando os mesmos filtros da lista admin). Colunas: ID, Jogo, Área, Usuário, Email, Escola, Status, Solicitado em, Reservado em, Emprestado em, Devolvido em, Devolução Prevista, Atrasado (Sim/Não), Observações.

#### Scenario: Export completo
- **WHEN** um admin acessa `GET /emprestimos/admin/export.csv`
- **THEN** o navegador baixa um CSV com cabeçalho e todas as linhas de empréstimos

#### Scenario: Export filtrado
- **WHEN** um admin acessa `GET /emprestimos/admin/export.csv?status=emprestado&area=anatomia`
- **THEN** o CSV contém apenas empréstimos emprestados de anatomia

### Requirement: Notificações por email (SMTP opcional)
O sistema SHALL enviar notificações por email quando SMTP está configurado (env vars `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`). Eventos: empréstimo aprovado (solicitado→reservado), emprestado com devolução prevista, renovação aprovada/rejeitada, atraso, disponibilidade na fila. Se SMTP não configurado, notificações são apenas in-app (flash + observação no histórico). Usuários com `receber_emails=0` não recebem (opt-in).

#### Scenario: Email ao aprovar empréstimo
- **WHEN** SMTP configurado e admin aprova solicitação
- **THEN** email é enviado ao usuário com assunto "Empréstimo reservado: <jogo>" contendo "Seu empréstimo de <jogo> foi reservado. Retire com o admin."

#### Scenario: SMTP não configurado
- **WHEN** admin aprova solicitação sem SMTP configurado
- **THEN** notificação in-app é exibida (flash "Empréstimo reservado" + observação no histórico)

#### Scenario: Usuário opt-out
- **WHEN** usuário tem `receber_emails=0` e admin aprova solicitação
- **THEN** email não é enviado (independente de SMTP estar configurado)

### Requirement: Campo receber_emails no perfil do usuário
O sistema SHALL adicionar o campo `receber_emails` (INTEGER DEFAULT 0) à tabela `users`. `admin_sistema` pode alterar via form de edição de usuário. `usuario` pode alterar em seu próprio perfil (rota `GET/POST /perfil` a ser criada).

#### Scenario: Admin ativa email para usuário
- **WHEN** admin edita um usuário e marca "Receber notificações por email"
- **THEN** `receber_emails` muda para `1`

### Requirement: Paginação nos models
O sistema SHALL modificar as funções `list_games`, `list_loans_by_user`, e `list_loans_all` em `app/models.py` para aceitar parâmetros `page` (int, default 1) e `per_page` (int, default 20 ou 30). O retorno inclui um dict `pagination` com: `page`, `per_page`, `total`, `pages`, `has_prev`, `has_next`, `prev_num`, `next_num`.

#### Scenario: Paginação com 3 páginas
- **WHEN** há 55 jogos e `list_games(page=2, per_page=20)` é chamado
- **THEN** retorna os jogos 21-40 e `pagination = {page: 2, per_page: 20, total: 55, pages: 3, has_prev: true, has_next: true, prev_num: 1, next_num: 3}`
