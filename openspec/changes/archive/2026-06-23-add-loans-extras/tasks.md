## 1. Schema

- [x] 1.1 Adicionar tabela `reservation_queue` a `app/schema.sql` (game_id, user_id, posicao, status, timestamps + índices)
- [x] 1.2 Adicionar coluna `receber_emails INTEGER DEFAULT 0` à tabela `users` no schema

## 2. Fila de reserva

- [x] 2.1 Adicionar funções em `app/models.py` (ou `app/loans_models.py`): `add_to_queue(game_id, user_id)`, `get_queue(game_id)`, `get_next_in_queue(game_id)`, `notify_next_in_queue(game_id)`, `cancel_queue_entry(id)`, `count_queue(game_id)`
- [x] 2.2 Ao solicitar empréstimo, se jogo indisponível: perguntar "Entrar na fila?" (redirect para página de confirmação ou flash com form)
- [x] 2.3 Criar `POST /emprestimos/fila/entrar/<game_id>` (confirma entrada na fila)
- [x] 2.4 Criar `POST /emprestimos/fila/notificar/<game_id>` (admin notifica próximo) — `@role_required`
- [x] 2.5 Exibir contagem da fila na lista admin e no detalhe do jogo
- [x] 2.6 Exibir botão "Notificar próximo" ao devolver jogo se fila não vazia

## 3. Paginação

- [x] 3.1 Modificar `list_games()` em models para aceitar `page=1, per_page=20`, retornar `(results, pagination_dict)`
- [x] 3.2 Modificar `list_loans_by_user()` para aceitar `page, per_page`
- [x] 3.3 Modificar `list_loans_all()` para aceitar `page, per_page`
- [x] 3.4 Modificar rota `GET /` para usar page/per_page e passar pagination ao template
- [x] 3.5 Modificar rota `GET /emprestimos` para usar page/per_page
- [x] 3.6 Modificar rota `GET /emprestimos/admin` para usar page/per_page
- [x] 3.7 Criar template partial `_pagination.html` com navegação `< 1 2 3 >`
- [x] 3.8 Atualizar templates afetados com `{% include '_pagination.html' %}`

## 4. Export CSV

- [x] 4.1 Implementar `GET /emprestimos/admin/export.csv` — `@role_required`
- [x] 4.2 Usar `csv.writer` da stdlib, escrever cabeçalho + linhas com mesmos filtros da lista
- [x] 4.3 Adicionar link "Exportar CSV" na página `/emprestimos/admin` (botão ou link)

## 5. Notificações por email

- [x] 5.1 Criar `app/email.py` com funções: `send_email(to, subject, body)`, `send_notification(tipo, loan, user)`
- [x] 5.2 Implementar envio em thread separada (`threading.Thread`)
- [x] 5.3 Configurar: ler `SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM` de `app.config` / env vars
- [x] 5.4 Disparar notificações nos eventos: aprovação, empréstimo, renovação, atraso, fila
- [x] 5.5 Se SMTP não configurado: skip silencioso (sem erro), apenas notificação in-app
- [x] 5.6 Verificar `users.receber_emails` antes de enviar

## 6. Campo receber_emails

- [x] 6.1 Adicionar campo ao form de edição de usuário (admin e perfil próprio)
- [x] 6.2 Criar `GET/POST /perfil` para usuário alterar seus dados (nome, email, receber_emails) — `@login_required`

## 7. Testes

- [x] 7.1 Testes para fila de reserva: entrada, ordem, notificação, cancelamento
- [x] 7.2 Testes para paginação: página 1, página 2, página além do limite, filtros preservados
- [x] 7.3 Testes para export CSV: conteúdo do CSV, filtros aplicados
- [x] 7.4 Testes para email: envio em thread, opt-out, SMTP não configurado
- [x] 7.5 Rodar `python -m pytest` e garantir todos os testes passando

## 8. Validação manual

- [x] 8.1 Testar fila: solicitar jogo emprestado, confirmar fila, admin notificar próximo
- [x] 8.2 Testar paginação com DB populado (>20 jogos)
- [x] 8.3 Testar export CSV em várias combinações de filtro
- [x] 8.4 Se SMTP configurado, testar envio de email; se não, confirmar skip silencioso

## 9. Finalização OpenSpec

- [x] 9.1 `/opsx:archive` da change `add-loans-extras` após tudo verificado
