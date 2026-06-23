## MODIFIED Requirements

### Requirement: Solicitação de empréstimo pelo usuário
O sistema SHALL permitir que um `usuario` logado solicite um empréstimo via `POST /emprestimos/solicitar/<game_id>`. O form contém o campo `devolucao_prevista` (default hoje + 7 dias, usuário pode alterar). **Se o jogo já possui um empréstimo ativo, o sistema pergunta se o usuário deseja entrar na fila de reserva. Se sim, cria uma entrada em `reservation_queue` com a próxima posição disponível. Se o usuário já possui um empréstimo ativo (solicitado, reservado ou emprestado) para o mesmo jogo, o sistema rejeita a solicitação com mensagem "Você já possui uma solicitação ou empréstimo ativo para este jogo".**

#### Scenario: Solicitação válida
- **WHEN** um `usuario` logado envia `POST /emprestimos/solicitar/5` com `devolucao_prevista = 2026-07-15`
- **THEN** um novo loan é criado com `game_id=5`, `user_id=<id do usuario>`, `status='solicitado'`, `solicitado_at` preenchido, e o usuário é redirecionado para `/emprestimos` com mensagem "Solicitação enviada"

#### Scenario: Entrar na fila quando indisponível
- **WHEN** um `usuario` tenta solicitar um jogo já emprestado
- **THEN** o sistema exibe mensagem "Jogo indisponível no momento. Entrar na fila de reserva?" com botão "Sim, reservar"

#### Scenario: Confirmar fila
- **WHEN** o usuário clica em "Sim, reservar"
- **THEN** uma entrada é criada em `reservation_queue` com `game_id`, `user_id`, `posicao = MAX(posicao) + 1`, `status='na_fila'`

#### Scenario: Solicitação duplicada rejeitada
- **WHEN** um `usuario` que já possui um loan com `status='solicitado'` para o `game_id=5` envia `POST /emprestimos/solicitar/5`
- **THEN** o sistema redireciona para `/emprestimos` com mensagem de erro "Você já possui uma solicitação ou empréstimo ativo para este jogo"
