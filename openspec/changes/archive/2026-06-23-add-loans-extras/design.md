## Context

Após implementar o subsistema de empréstimos (Change 2), temos o fluxo básico funcionando: solicitar, aprovar, emprestar, devolver, renovar, com auditoria e dashboard. Este change adiciona as funcionalidades extras que foram identificadas durante o explore mode como "posteriores", mas já em escopo:

1. **Fila de reserva** quando jogo emprestado (em vez de rejeitar).
2. **Notificações por email** (SMTP) para mudanças de status.
3. **Paginação** no catálogo principal e na lista admin de empréstimos.
4. **Export CSV** de empréstimos para relatórios.

Stack: Flask + SQLite + Jinja2. Para email, `smtplib` da stdlib ou `Flask-Mail`. Para paginação, implementação manual com `LIMIT/OFFSET`.

## Goals / Non-Goals

**Goals:**
- Fila de reserva: se jogo emprestado, usuário pode entrar em fila; admin libera na ordem ao devolver.
- Notificações por email: configurável, template por tipo de notificação, opt-out por usuário.
- Paginação: no catálogo (GET /), nos empréstimos do usuário, e na lista admin.
- Export CSV: de empréstimos (ativos e/ou por período), filtros exportáveis.

**Non-Goals:**
- WebSocket/notificações em tempo real (email é suficiente).
- Templates HTML de email elegantes (texto plano + opcional HTML simples).
- Paginação infinita / scroll infinito (paginação tradicional < 1, 2, 3 >).

## Decisions

### 1. Fila de reserva: tabela reservation_queue
**Por que:** Um jogo emprestado não deve simplesmente rejeitar novas solicitações. A fila permite que o próximo interessado seja notificado quando o jogo voltar.
**Implementação:**
```sql
CREATE TABLE reservation_queue (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  game_id    INTEGER NOT NULL REFERENCES games(id),
  user_id    INTEGER NOT NULL REFERENCES users(id),
  posicao    INTEGER NOT NULL,
  status     TEXT NOT NULL DEFAULT 'na_fila'
               CHECK(status IN ('na_fila','notificado','atendido','cancelado')),
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_queue_game ON reservation_queue(game_id);
```
**Fluxo:**
1. Ao solicitar empréstimo, se jogo já tem loan ativo, pergunta: "Jogo indisponível. Entrar na fila?".
2. Se sim, cria linha em `reservation_queue` com `posicao = MAX(posicao) + 1`.
3. Ao devolver jogo, admin vê "Há N reservas" e pode liberar para o primeiro da fila.
4. Admin clica "Notificar próximo": muda status para `notificado`, envia email (se configurado).
5. Se não houver email, o primeiro da fila pode ser promovido automaticamente ou manualmente.

### 2. Notificações por email: smtplib + thread separada
**Por que:** `smtplib` é stdlib (sem dependência extra). Para não travar o request, envio em background thread.
**Eventos que disparam notificação:**
- Empréstimo aprovado (solicitado→reservado) → notifica usuário
- Empréstimo emprestado (reservado→emprestado) → notifica usuário com devolucao_prevista
- Renovação aprovada/rejeitada → notifica usuário
- Atraso → notifica usuário e admin (ou só email diário de resumo)
- Próximo da fila → notifica "Jogo disponível!"
**Configuração:** via variáveis de ambiente:
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`
- Se não configurado, notificações são apenas in-app (flash message + observação no histórico).
- Usuário pode optar por `receber_emails=0` em seu perfil.

### 3. Paginação: LIMIT/OFFSET com parâmetro `?page=`
**Por que:** Simples, sem dependência extra. O catálogo hoje tem ~26 jogos, mas pode crescer. A lista admin de empréstimos pode ter centenas.
**Implementação:**
- Adicionar `page` e `per_page` (default 20) aos queries.
- Templates: `{% if pagination.pages > 1 %}` com links `?page=1&page=2&...`.
- `pagination` dict com: `page`, `per_page`, `total`, `pages`, `has_prev`, `has_next`, `prev_num`, `next_num`.
- Afeta: `GET /` (catálogo), `GET /emprestimos` (usuário), `GET /emprestimos/admin` (admin).

### 4. Export CSV de empréstimos
**Rota:** `GET /emprestimos/admin/export.csv` — `@role_required('admin_sistema', 'admin_jogos')`.
**Filtros:** mesmos filtros da lista admin + período. Exporta colunas: ID, Jogo, Área, Usuário, Email, Escola, Status, Solicitado em, Reservado em, Emprestado em, Devolvido em, Devolução Prevista, Atrasado, Observações.

### 5. Campo `receber_emails` em users
**Adicionar:** `users.receber_emails INTEGER DEFAULT 0` (opt-in para não poluir). Admin pode ativar/desativar para um usuário.

## Risks / Trade-offs

- **[Email sem thread separada pode travar request]** → Mitigação: enviar em thread (`threading.Thread`). Risco: se servidor SMTP lento, thread sobrevive ao request. Aceitável para sistema local.
- **[Configuração SMTP pode ser complexa para usuário não técnico]** → Mitigação: notificações são opcionais. Sem SMTP configurado, sistema funciona sem email. Mensagens são exibidas in-app.
- **[Fila de reserva vs. 1 cópia física]** → A fila só faz sentido se há um jogo e vários interessados. Como cada jogo é 1 cópia, a fila é FIFO. Se no futuro houver múltiplas cópias, a fila pode ser reavaliada.
- **[Paginação pode quebrar filtros existentes]** → Mitigação: filtros são preservados via query string (`?page=2&area=histologia`).

## Migration Plan

1. Adicionar `reservation_queue` ao schema.
2. Adicionar `users.receber_emails` ao schema.
3. Implementar paginação em queries de models (parâmetro page/per_page).
4. Atualizar templates com navegação de página.
5. Implementar fila de reserva: criação, listagem para admin, notificação do próximo.
6. Implementar notificações por email com `smtplib`.
7. Implementar export CSV.
8. **Rollback:** reverter tabelas, remover paginação, remover configs de email.

## Open Questions

- Nenhuma pendente. Todas as decisões foram exploradas durante o explore mode.
