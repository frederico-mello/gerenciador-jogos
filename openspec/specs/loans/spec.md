# Capability: loans

## Purpose

TBD — Subsistema de empréstimos com 5 estados (solicitado, reservado, emprestado, devolvido, cancelado), renovação, auditoria, dashboard admin, histórico por jogo e badge de disponibilidade.

## Requirements

### Requirement: Tabelas loans e loan_status_history
O sistema SHALL manter duas novas tabelas em SQLite: `loans` (empréstimos) e `loan_status_history` (auditoria de mudanças de status). A tabela `loans` contém: `id` (PK), `game_id` (FK → games), `user_id` (FK → users), `status` (CHECK em 'solicitado', 'reservado', 'emprestado', 'devolvido', 'cancelado'), `devolucao_prevista` (DATE), `renovacao_pendente` (INTEGER DEFAULT 0), `nova_devolucao_prevista` (DATE), `observacoes` (TEXT), `solicitado_at`, `reservado_at`, `emprestado_at`, `devolvido_at`, `termos_aceite_at` (TEXT, timestamp ISO 8601 do aceite), `termos_versao` (TEXT, hash dos termos aceitos), `created_at`, `updated_at`. A tabela `loan_status_history` contém: `id` (PK), `loan_id` (FK → loans ON DELETE CASCADE), `status_anterior`, `status_novo`, `changed_by` (FK → users), `changed_at`, `observacao`.

#### Scenario: Loan criado com solicitado_at
- **WHEN** um usuário solicita um empréstimo via `POST /emprestimos/solicitar/<game_id>`
- **THEN** uma nova linha em `loans` é criada com `status='solicitado'`, `solicitado_at` preenchido, `termos_aceite_at` preenchido, `termos_versao` preenchido, e uma linha em `loan_status_history` registra `status_anterior=NULL`, `status_novo='solicitado'`, `changed_by=<user_id>`

#### Scenario: Histórico registra cada transição
- **WHEN** um empréstimo muda de `solicitado` para `reservado`
- **THEN** uma nova linha em `loan_status_history` é criada com `status_anterior='solicitado'`, `status_novo='reservado'`, `changed_by=<admin_id>`, `changed_at` preenchido

### Requirement: Solicitação de empréstimo pelo usuário
O sistema SHALL permitir que um `usuario` logado solicite um empréstimo. A solicitação requer duas etapas: (1) `GET /emprestimos/solicitar/<game_id>` exibe tela dedicada com termos de uso, campo de devolução prevista e checkbox de aceite; (2) `POST /emprestimos/solicitar/<game_id>` com `aceite_termos=1` e `devolucao_prevista` cria o empréstimo. O campo `devolucao_prevista` tem default hoje + 7 dias, editável pelo usuário. **Se o jogo já possui um empréstimo ativo, o sistema pergunta se o usuário deseja entrar na fila de reserva. Se sim, cria uma entrada em `reservation_queue` com a próxima posição disponível. Se o usuário já possui um empréstimo ativo (solicitado, reservado ou emprestado) para o mesmo jogo, o sistema rejeita a solicitação com mensagem "Você já possui uma solicitação ou empréstimo ativo para este jogo".**

#### Scenario: Solicitação válida
- **WHEN** um `usuario` logado envia `POST /emprestimos/solicitar/5` com `devolucao_prevista = 2026-07-15` e `aceite_termos = 1`
- **THEN** um novo loan é criado com `game_id=5`, `user_id=<id do usuario>`, `status='solicitado'`, `solicitado_at` preenchido, `termos_aceite_at` preenchido, `termos_versao` preenchido, e o usuário é redirecionado para `/emprestimos` com mensagem "Solicitação enviada"

#### Scenario: Solicitação sem aceite
- **WHEN** um `usuario` logado envia `POST /emprestimos/solicitar/5` sem `aceite_termos = 1`
- **THEN** o sistema reexibe a tela de solicitação com mensagem de erro "Você precisa aceitar os termos de empréstimo."

#### Scenario: Tela de solicitação exibe termos e dados
- **WHEN** um `usuario` logado acessa `GET /emprestimos/solicitar/5`
- **THEN** a página exibe o nome do jogo, termos de empréstimo renderizados, campo de data com default +7 dias, e checkbox "Li e aceito os termos"

#### Scenario: Entrar na fila quando indisponível
- **WHEN** um `usuario` tenta solicitar um jogo já emprestado
- **THEN** o sistema exibe mensagem "Jogo indisponível no momento. Entrar na fila de reserva?" com botão "Sim, reservar"

#### Scenario: Confirmar fila
- **WHEN** o usuário clica em "Sim, reservar"
- **THEN** uma entrada é criada em `reservation_queue` com `game_id`, `user_id`, `posicao = MAX(posicao) + 1`, `status='na_fila'`

#### Scenario: Solicitação duplicada rejeitada
- **WHEN** um `usuario` que já possui um loan com `status='solicitado'` para o `game_id=5` envia `POST /emprestimos/solicitar/5`
- **THEN** o sistema redireciona para `/emprestimos` com mensagem de erro "Você já possui uma solicitação ou empréstimo ativo para este jogo"

### Requirement: Lista de empréstimos do usuário
O sistema SHALL fornecer `GET /emprestimos` para o `usuario` logado ver sua própria lista de empréstimos, ordenada por `created_at DESC`, mostrando jogo, status, devolucao_prevista, observações, e botões de ação disponíveis (cancelar se solicitado, renovar se emprestado).

#### Scenario: Usuário vê seus empréstimos
- **WHEN** um `usuario` acessa `GET /emprestimos`
- **THEN** a página mostra apenas os empréstimos do usuário logado, ordenados do mais recente para o mais antigo

### Requirement: Cancelamento pelo usuário
O sistema SHALL permitir que um `usuario` cancele seu próprio empréstimo via `POST /emprestimos/<id>/cancelar`, desde que o status seja `solicitado`. Se já estiver `reservado` ou `emprestado`, o cancelamento deve ser feito pelo admin (via rota admin).

#### Scenario: Cancelar solicitação própria
- **WHEN** um `usuario` clica em "Cancelar" em um empréstimo com `status='solicitado'`
- **THEN** o status muda para `cancelado`, o histórico registra a mudança, e o usuário é redirecionado para `/emprestimos`

#### Scenario: Cancelar empréstimo já reservado
- **WHEN** um `usuario` tenta cancelar um empréstimo com `status='reservado'`
- **THEN** o sistema rejeita com mensagem "Cancelamento deve ser feito por um administrador"

### Requirement: Renovação pelo usuário
O sistema SHALL permitir que um `usuario` com empréstimo em status `emprestado` solicite renovação via `POST /emprestimos/<id>/renovar`, informando `nova_devolucao_prevista`. O sistema marca `renovacao_pendente=1` e `nova_devolucao_prevista=<data informada>`. O admin deve aprovar ou rejeitar.

#### Scenario: Solicitar renovação
- **WHEN** um `usuario` clica em "Renovar" em um empréstimo emprestado, informando `nova_devolucao_prevista = 2026-07-30`
- **THEN** `renovacao_pendente` muda para `1`, `nova_devolucao_prevista` é preenchida, e o admin vê o indicador na lista admin

### Requirement: Admin gerencia empréstimos
O sistema SHALL fornecer `GET /emprestimos/admin` para admins (`admin_sistema`, `admin_jogos`) listarem todos os empréstimos com filtros por status, usuário, área, período. A página mostra indicador de renovação pendente, atrasados destacados, e botões de ação por status.

#### Scenario: Admin vê todos os empréstimos
- **WHEN** um `admin_jogos` acessa `GET /emprestimos/admin`
- **THEN** a página mostra todos os empréstimos, com filtros, ordenados por `created_at DESC`

#### Scenario: Admin filtra por status
- **WHEN** um admin seleciona o filtro "emprestado"
- **THEN** apenas empréstimos com `status='emprestado'` são exibidos

### Requirement: Transições de status (admin)
O sistema SHALL fornecer rotas de admin para cada transição de estado: `POST /emprestimos/<id>/aprovar` (solicitado→reservado), `POST /emprestimos/<id>/emprestar` (reservado→emprestado, admin pode sobrescrever `devolucao_prevista`), `POST /emprestimos/<id>/devolver` (emprestado→devolvido). Cada transição registra em `loan_status_history`. Transições inválidas retornam 400.

#### Scenario: Aprovar solicitação
- **WHEN** um admin clica em "Aprovar" em um empréstimo com `status='solicitado'`
- **THEN** o status muda para `reservado`, `reservado_at` é preenchido, histórico registrado

#### Scenario: Marcar como emprestado
- **WHEN** um admin clica em "Emprestar" em um empréstimo com `status='reservado'`
- **THEN** o status muda para `emprestado`, `emprestado_at` é preenchido, e o admin pode ajustar `devolucao_prevista`

#### Scenario: Devolver jogo
- **WHEN** um admin clica em "Devolver" em um empréstimo com `status='emprestado'`
- **THEN** o status muda para `devolvido`, `devolvido_at` é preenchido, histórico registrado

#### Scenario: Transição inválida
- **WHEN** um admin tenta "Aprovar" um empréstimo com `status='devolvido'`
- **THEN** o sistema retorna 400 Bad Request

### Requirement: Admin aprova ou rejeita renovação
O sistema SHALL fornecer `POST /emprestimos/<id>/renovar/aprovar` e `POST /emprestimos/<id>/renovar/rejeitar` para admins. Ao aprovar, `devolucao_prevista` é atualizada para `nova_devolucao_prevista`, e os flags são limpos. Ao rejeitar, apenas os flags são limpos. Ambas registram no histórico.

#### Scenario: Aprovar renovação
- **WHEN** um admin clica em "Aprovar renovação"
- **THEN** `devolucao_prevista = nova_devolucao_prevista`, `renovacao_pendente = 0`, `nova_devolucao_prevista = NULL`, histórico registra "Renovação aprovada"

#### Scenario: Rejeitar renovação
- **WHEN** um admin clica em "Rejeitar renovação"
- **THEN** `renovacao_pendente = 0`, `nova_devolucao_prevista = NULL`, `devolucao_prevista` mantém a data original, histórico registra "Renovação rejeitada"

### Requirement: Status "atrasado" derivado
O sistema SHALL derivar o status "atrasado" em runtime: um empréstimo com `status='emprestado'` e `devolucao_prevista < data_atual` é considerado atrasado. O atraso é exibido como badge vermelho nas listas admin e na dashboard, não é persistido em tabela.

#### Scenario: Exibir atrasado na lista admin
- **WHEN** um admin acessa `/emprestimos/admin` e há um empréstimo emprestado com devolução prevista para ontem
- **THEN** a linha do empréstimo mostra badge "ATRASADO" em vermelho

### Requirement: Badge de disponibilidade no catálogo
O sistema SHALL exibir no catálogo (`GET /`) e no detalhe (`GET /<id>`) um badge indicando se o jogo está disponível (verde), solicitado (amarelo), reservado (amarelo), ou emprestado (vermelho). O status é derivado da tabela `loans` em runtime.

#### Scenario: Jogo disponível no catálogo
- **WHEN** um visitante acessa `GET /` e um jogo não tem nenhum empréstimo ativo
- **THEN** o card do jogo mostra badge verde "Disponível"

#### Scenario: Jogo emprestado no catálogo
- **WHEN** um jogo tem um empréstimo com `status='emprestado'`
- **THEN** o card do jogo mostra badge vermelho "Emprestado"

### Requirement: Dashboard admin
O sistema SHALL fornecer `GET /admin/dashboard` para admins, com cards mostrando: total de jogos (por área), empréstimos ativos (total e por status), empréstimos atrasados, empréstimos do mês, top 5 jogos mais emprestados.

#### Scenario: Dashboard exibe totais
- **WHEN** um admin acessa `GET /admin/dashboard`
- **THEN** a página mostra cards com números agregados

### Requirement: Histórico de empréstimos por jogo
O sistema SHALL exibir no detalhe do jogo (`GET /<id>`) uma seção "Histórico de empréstimos" (apenas para admins), listando todos os empréstimos do jogo (passados e ativos) ordenados por data, com usuário, período, status.

#### Scenario: Admin vê histórico
- **WHEN** um `admin_jogos` logado acessa `GET /<id>` para um jogo com 3 empréstimos anteriores
- **THEN** a seção mostra os 3 empréstimos listados do mais recente para o mais antigo, com nome do usuário, período e status final

#### Scenario: Usuario não vê histórico
- **WHEN** um `usuario` logado acessa `GET /<id>`
- **THEN** a seção de histórico não é exibida

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
