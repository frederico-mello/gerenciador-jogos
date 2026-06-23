## 1. Schema e banco de dados

- [x] 1.1 Adicionar tabelas `loans` e `loan_status_history` e índices a `app/schema.sql`
- [x] 1.2 Adicionar funções de loan em `app/models.py` (ou criar `app/loans_models.py`): `create_loan`, `get_loan`, `list_loans_by_user`, `list_loans_all` (c/ filtros), `list_loans_by_game`, `update_loan_status`, `set_renovacao_pendente`, `aprovar_renovacao`, `rejeitar_renovacao`, `get_game_availability`, `count_loans_by_status`
- [x] 1.3 Adicionar funções de histórico: `add_status_history`, `list_status_history`, `get_loan_history`

## 2. Rotas de usuário

- [x] 2.1 Implementar `POST /emprestimos/solicitar/<game_id>` (cria loan, valida disponibilidade, default devolucao_prevista = today+7d) — `@login_required`
- [x] 2.2 Implementar `GET /emprestimos` (lista do usuário logado) — `@login_required`
- [x] 2.3 Implementar `POST /emprestimos/<id>/cancelar` (só se status=solicitado e user_id = current_user) — `@login_required`
- [x] 2.4 Implementar `POST /emprestimos/<id>/renovar` (só se status=emprestado, define renovacao_pendente) — `@login_required`

## 3. Rotas de admin

- [x] 3.1 Implementar `GET /emprestimos/admin` (lista completa com filtros status/usuario/area/periodo) — `@role_required('admin_sistema', 'admin_jogos')`
- [x] 3.2 Implementar `POST /emprestimos/<id>/aprovar` (solicitado→reservado) — `@role_required('admin_sistema', 'admin_jogos')`
- [x] 3.3 Implementar `POST /emprestimos/<id>/emprestar` (reservado→emprestado, pode ajustar devolucao_prevista) — `@role_required('admin_sistema', 'admin_jogos')`
- [x] 3.4 Implementar `POST /emprestimos/<id>/devolver` (emprestado→devolvido) — `@role_required('admin_sistema', 'admin_jogos')`
- [x] 3.5 Implementar `POST /emprestimos/<id>/cancelar/admin` (qualquer estado p/ cancelado, com observação) — `@role_required('admin_sistema', 'admin_jogos')`
- [x] 3.6 Implementar `POST /emprestimos/<id>/renovar/aprovar` — `@role_required('admin_sistema', 'admin_jogos')`
- [x] 3.7 Implementar `POST /emprestimos/<id>/renovar/rejeitar` — `@role_required('admin_sistema', 'admin_jogos')`

## 4. Badge de disponibilidade no catálogo

- [x] 4.1 Criar função helper `get_games_with_availability()` que junta games + loan ativo para popular o badge
- [x] 4.2 Atualizar `app/routes.py` rota `GET /` para passar disponibilidade junto com os jogos
- [x] 4.3 Atualizar `app/routes.py` rota `GET /<id>` para passar disponibilidade do jogo
- [x] 4.4 Atualizar `templates/index.html` para exibir badge (verde/amarelo/vermelho) em cada card
- [x] 4.5 Atualizar `templates/detail.html` para exibir badge no topo do detalhe

## 5. Dashboard admin

- [x] 5.1 Implementar `GET /admin/dashboard` — `@role_required('admin_sistema', 'admin_jogos')`
- [x] 5.2 Criar consultas SQL agregadas: total jogos, empréstimos ativos, atrasados, do mês, top 5, por área
- [x] 5.3 Criar `templates/dashboard.html` com cards e tabelas

## 6. Templates de empréstimos

- [x] 6.1 Criar `templates/emprestimos.html` (lista do usuário com status, devolucao_prevista, botões cancelar/renovar)
- [x] 6.2 Criar `templates/emprestimos_admin.html` (tabela completa com filtros, indicador de atrasado, botões de ação por status)
- [x] 6.3 Criar `templates/_badge_disponibilidade.html` (partial reutilizável)
- [x] 6.4 Adicionar seção de histórico em `templates/detail.html` (só para admins)

## 7. Navegação (base.html)

- [x] 7.1 Adicionar "Meus empréstimos" ao nav para `usuario` logado
- [x] 7.2 Adicionar "Empréstimos (admin)" ao nav para `admin_sistema` e `admin_jogos`
- [x] 7.3 Adicionar "Dashboard" ao nav para `admin_sistema` e `admin_jogos`

## 8. Testes

- [x] 8.1 Criar `tests/test_loans.py` cobrindo: solicitação válida, jogo indisponível, cancelamento, renovação, transições de admin (cada uma), transição inválida, histórico registrado
- [x] 8.2 Adicionar testes de disponibilidade: game_availability após criar loan, após devolver
- [x] 8.3 Adicionar testes de dashboard: totais corretos, atrasado derivação
- [x] 8.4 Adicionar testes de autorização: usuario não acessa rotas admin, admin vê tudo
- [x] 8.5 Atualizar `tests/conftest.py` com fixtures para loans e diferentes estados
- [x] 8.6 Rodar `python -m pytest` e garantir todos os testes passando

## 9. Validação manual

- [x] 9.1 Rodar `python scripts/init_db.py` (recria DB com novas tabelas)
- [x] 9.2 Fazer login como usuario, solicitar empréstimo, ver badge no catálogo
- [x] 9.3 Fazer login como admin, aprovar, emprestar, devolver
- [x] 9.4 Testar renovação: usuario solicita, admin aprova/rejeita
- [x] 9.5 Testar filtros na lista admin
- [x] 9.6 Testar dashboard
- [x] 9.7 Verificar histórico por jogo

## 10. Finalização OpenSpec

- [x] 10.1 `/opsx:archive` da change `add-loans-subsystem` após tudo verificado
