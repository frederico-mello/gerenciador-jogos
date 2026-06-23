## Why

Com auth implementado (Change 1), temos 3 papéis distinguindo quem pode gerenciar jogos (`admin_sistema`, `admin_jogos`) de quem apenas os consome (`usuario`). Falta o fluxo de empréstimo: um `usuario` solicita um jogo, um admin aprova/reserva/entrega/devolve, e o sistema rastreia tudo.

Hoje não há tabela de empréstimos, nem noção de disponibilidade, nem histórico. Um jogo emprestado fisicamente desaparece do radar do sistema. O subsistema de empréstimos resolve isso com:
- **5 estados**: solicitado → reservado → emprestado → devolvido (+ cancelado como ramo de saída).
- **Disponibilidade derivada**: um jogo está "disponível" quando não há empréstimo ativo (solicitado, reservado ou emprestado).
- **Devolução prevista**: default 7 dias, usuário sugere ao solicitar, admin pode ajustar ao marcar "emprestado".
- **Status "atrasado" derivado**: `emprestado` + `devolucao_prevista < hoje`.
- **Renovação**: usuário pede (flag `renovacao_pendente`), admin aprova/rejeita.
- **Auditoria**: tabela `loan_status_history` rastreia quem mudou o quê e quando.
- **Badge de disponibilidade** no catálogo (verde/amarelo/vermelho).
- **Dashboard admin**: totais, ativos, atrasados, por área.
- **Histórico por jogo**: empréstimos passados.

## What Changes

- **Nova tabela `loans`** com `id`, `game_id` (FK), `user_id` (FK), `status` (CHECK em 5 valores), `devolucao_prevista` (DATE), `renovacao_pendente` (INTEGER), `nova_devolucao_prevista` (DATE), `observacoes`, timestamps de cada transição de estado, `created_at`, `updated_at`.
- **Nova tabela `loan_status_history`** com `id`, `loan_id` (FK CASCADE), `status_anterior`, `status_novo`, `changed_by` (FK → users), `changed_at`, `observacao`.
- **Rotas de usuário**: `POST /emprestimos/solicitar/<game_id>` (cria loan `solicitado` com devolucao_prevista sugerida), `GET /emprestimos` (lista próprios empréstimos), `POST /emprestimos/<id>/cancelar` (cancela enquanto `solicitado`), `POST /emprestimos/<id>/renovar` (pede renovação).
- **Rotas de admin**: `GET /emprestimos/admin` (lista todos com filtros), `POST /emprestimos/<id>/aprovar` (solicitado→reservado), `POST /emprestimos/<id>/emprestar` (reservado→emprestado, define devolucao_prevista), `POST /emprestimos/<id>/devolver` (emprestado→devolvido), `POST /emprestimos/<id>/renovar/aprovar` e `/renovar/rejeitar`.
- **Badge de disponibilidade** em `index.html` e `detail.html` (verde=disponível, amarelo=reservado, vermelho=emprestado).
- **Dashboard** `GET /admin/dashboard` (totais, ativos, atrasados, por área).
- **Histórico por jogo** em `detail.html` (lista de empréstimos passados, só visível para admins).
- **Filtros** em `/emprestimos/admin`: por status, usuário, área, período.
- **Novo capability** `loans` + deltas em `web-ui` e `game-catalog`.

## Capabilities

### New Capabilities
- `loans`: Subsistema de empréstimos com 5 estados, renovação, auditoria, dashboard admin, histórico por jogo, badge de disponibilidade.

### Modified Capabilities
- `web-ui`: Adiciona rotas de empréstimos (usuário e admin), dashboard, badge de disponibilidade no catálogo, histórico por jogo no detalhe.
- `game-catalog`: Adiciona noção de "disponibilidade" derivada do empréstimo ativo (não persistida em `games`, calculada em runtime).

## Impact

- **Schema**: novas tabelas `loans` e `loan_status_history` em `app/schema.sql`.
- **Novas rotas** em `app/routes.py` (ou novo blueprint `app/loans_routes.py`).
- **Novos templates**: `emprestimos.html` (lista do usuário), `emprestimos_admin.html` (lista admin com filtros), `dashboard.html`, parcial `_badge_disponibilidade.html`.
- **Depende de Change 1** (`add-auth-system`): empréstimos precisam de `user_id` autenticado.
- **Sem breaking changes** para o catálogo existente — apenas adição de badge visual e novas rotas.
