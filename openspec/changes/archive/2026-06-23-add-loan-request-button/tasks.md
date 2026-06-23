## 1. Backend — Bloquear solicitação duplicada

- [x] 1.1 Em `routes.py`, na rota `solicitar_emprestimo` (linha ~643), adicionar verificação: se o usuário já possui loan ativo (status `solicitado`, `reservado` ou `emprestado`) para o mesmo `game_id`, redirecionar para `/emprestimos` com flash de erro
- [x] 1.2 Adicionar função auxiliar em `models.py` para verificar se usuário tem loan ativo para um jogo (ex: `user_has_active_loan(user_id, game_id) -> bool`)

## 2. Backend — Passar contexto adicional à página de detalhe

- [x] 2.1 Na rota `detalhe` (routes.py:204), quando o usuário está logado, verificar se já possui loan ativo para o jogo e passar `user_has_active_loan` (bool) ao template

## 3. Template — Botão na página de detalhe

- [x] 3.1 Em `detail.html`, no bloco `.detail-actions` (linha 15-21), adicionar bloco condicional para `usuario` com botão "Solicitar Empréstimo" (form POST) quando `availability_status == 'disponivel'` e `user_has_active_loan == False`
- [x] 3.2 Adicionar botão "Entrar na fila" (link para `/emprestimos/fila/confirmar/<game_id>`) quando `availability_status != 'disponivel'` e `user_has_active_loan == False`
- [x] 3.3 Adicionar link "Faça login para solicitar" (link para `/login`) quando `current_user` é None e `availability_status == 'disponivel'`
- [x] 3.4 Garantir que admins não veem botão de empréstimo (condicional já coberta pelo bloco existente de admin)

## 4. Template — Botão na página Meus Empréstimos

- [x] 4.1 Em `emprestimos.html`, adicionar botão "Solicitar novo empréstimo" (link para `GET /`) acima da tabela/lista, visível independentemente de haver loans

## 5. Testes

- [x] 5.1 Adicionar teste em `test_loans.py` para solicitação duplicada (usuário com loan ativo tenta solicitar mesmo jogo → redirecionamento com erro)
- [x] 5.2 Adicionar teste para verificar que a rota `detalhe` passa `user_has_active_loan` ao template
