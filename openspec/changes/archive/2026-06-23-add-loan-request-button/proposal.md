## Why

A rota `POST /emprestimos/solicitar/<game_id>` já existe e funciona, mas nenhum botão no UI a aciona. Usuários não conseguem solicitar empréstimos porque não há como chegar à rota — nem na página de detalhe do jogo, nem na página "Meus Empréstimos".

## What Changes

- Adicionar botão "Solicitar Empréstimo" na página de detalhe do jogo (`detail.html`), visível para `usuario` logado quando o jogo está disponível
- Quando o jogo estiver indisponível, o botão muda para "Entrar na fila" e leva à página de confirmação de fila
- Usuários não logados veem um botão "Faça login para solicitar" que redireciona para `/login`
- Adicionar botão "Solicitar novo empréstimo" na página "Meus Empréstimos" (`emprestimos.html`) que leva ao catálogo

## Capabilities

### New Capabilities

_(nenhuma nova capability)_

### Modified Capabilities

- `web-ui`: Adição de botões de solicitação de empréstimo nas páginas de detalhe do jogo e de "Meus Empréstimos"
- `loans`: O requirement "Badge de disponibilidade no catálogo" será estendido para incluir o botão de ação na página de detalhe

## Impact

- `app/templates/detail.html` — adicionar bloco de botões de empréstimo no `.detail-actions`
- `app/templates/emprestimos.html` — adicionar botão/link para solicitar novo empréstimo
- `app/routes.py` — a rota `detalhe` já passa `availability_status` e `active_loan_id`; pode precisar passar contexto adicional (ex: se o usuário já tem solicitação ativa para o jogo)
- `app/templates/_badge_disponibilidade.html` — sem alterações (já funciona)
- Nenhuma mudança de schema ou dependência
