## ADDED Requirements

### Requirement: Tabelas loans e loan_status_history
O sistema SHALL manter duas novas tabelas em SQLite: `loans` (empréstimos) e `loan_status_history` (auditoria de mudanças de status). A tabela `loans` contém: `id` (PK), `game_id` (FK → games), `user_id` (FK → users), `status` (CHECK em 'solicitado', 'reservado', 'emprestado', 'devolvido', 'cancelado'), `devolucao_prevista` (DATE), `renovacao_pendente` (INTEGER DEFAULT 0), `nova_devolucao_prevista` (DATE), `observacoes` (TEXT), `solicitado_at`, `reservado_at`, `emprestado_at`, `devolvido_at`, `created_at`, `updated_at`. A tabela `loan_status_history` contém: `id` (PK), `loan_id` (FK → loans ON DELETE CASCADE), `status_anterior`, `status_novo`, `changed_by` (FK → users), `changed_at`, `observacao`.

#### Scenario: Loan criado com solicitado_at
- **WHEN** um usuário solicita um empréstimo via `POST /emprestimos/solicitar/<game_id>`
- **THEN** uma nova linha em `loans` é criada com `status='solicitado'`, `solicitado_at` preenchido, e uma linha em `loan_status_history` registra `status_anterior=NULL`, `status_novo='solicitado'`, `changed_by=<user_id>`

#### Scenario: Histórico registra cada transição
- **WHEN** um empréstimo muda de `solicitado` para `reservado`
- **THEN** uma nova linha em `loan_status_history` é criada com `status_anterior='solicitado'`, `status_novo='reservado'`, `changed_by=<admin_id>`, `changed_at` preenchido

### Requirement: Solicitação de empréstimo pelo usuário
O sistema SHALL permitir que um `usuario` logado solicite um empréstimo via `POST /emprestimos/solicitar/<game_id>`. O form contém o campo `devolucao_prevista` (default hoje + 7 dias, usuário pode alterar). Se o jogo já possui um empréstimo ativo (solicitado/reservado/emprestado), a solicitação é rejeitada com mensagem "Jogo indisponível".

#### Scenario: Solicitação válida
- **WHEN** um `usuario` logado envia `POST /emprestimos/solicitar/5` com `devolucao_prevista = 2026-07-15`
- **THEN** um novo loan é criado com `game_id=5`, `user_id=<id do usuario>`, `status='solicitado'`, `solicitado_at` preenchido, e o usuário é redirecionado para `/emprestimos` com mensagem "Solicitação enviada"

#### Scenario: Jogo indisponível
- **WHEN** um `usuario` tenta solicitar um jogo que já está emprestado
- **THEN** o sistema rejeita com flash "Jogo indisponível" e redireciona para `/` sem criar loan

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
