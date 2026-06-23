## Why

O subsistema de empréstimos (Change 2) implementa o fluxo básico: solicitar, aprovar, emprestar, devolver, renovar. Mas à medida que o catálogo e o número de usuários crescem, algumas funcionalidades se tornam necessárias:

- **Fila de reserva**: hoje, se um jogo está emprestado, o usuário é simplesmente rejeitado. Com fila, o usuário pode entrar em uma lista de espera e ser notificado quando o jogo voltar.
- **Notificações por email**: sem elas, o usuário precisa ficar verificando o sistema para saber se seu empréstimo foi aprovado, se está atrasado, etc.
- **Paginação**: o catálogo tem ~26 jogos hoje, mas pode crescer. A lista admin de empréstimos pode chegar a centenas. Paginação evita páginas gigantes.
- **Export CSV**: admins precisam gerar relatórios para coordenação/supervisão.

## What Changes

- **Nova tabela `reservation_queue`** com `game_id`, `user_id`, `posicao`, `status` (na_fila/notificado/atendido/cancelado).
- **Campo `users.receber_emails`** (INTEGER DEFAULT 0, opt-in).
- **Configuração SMTP** via env vars (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`).
- **Notificações por email** via `smtplib` em background thread para: aprovação, empréstimo, renovação, atraso, fila.
- **Paginação** no catálogo (`GET /`), empréstimos do usuário (`GET /emprestimos`), e lista admin (`GET /emprestimos/admin`).
- **Export CSV** dos empréstimos com mesmos filtros da lista admin.
- **Deltas** em `loans` (fila, email, paginação, CSV).

## Capabilities

### New Capabilities
- Nenhuma (extensões do capability `loans`).

### Modified Capabilities
- `loans`: Adiciona fila de reserva (`reservation_queue`), notificações por email (thread com smtplib), paginação (LIMIT/OFFSET), CSV export.
- `web-ui`: Paginação no catálogo e listas de empréstimos. Botões para gerenciar fila. Link para export CSV.
- `auth`: Adiciona campo `receber_emails` (opt-in) na tabela `users` e form de perfil/edição.

## Impact

- **Schema**: nova tabela `reservation_queue` + coluna `users.receber_emails`.
- **Config**: novas env vars (`SMTP_*`), documentadas no `.env.example` ou README.
- **Dependências Python**: nenhuma nova (`smtplib` é stdlib).
- **Depende de Change 2** (`add-loans-subsystem`): estende o subsistema de empréstimos.
- **Sem breaking changes** — apenas adições. Fluxo existente de empréstimos continua funcionando sem email, sem fila.
