## Context

Com auth implementado (Change 1), temos `users` com 3 papéis. Este change adiciona o subsistema de empréstimos: `usuario` solicita, `admin_sistema`/`admin_jogos` gerenciam o fluxo. Cada jogo é uma cópia física única (decisão do explore mode: Opção A).

Stack: Flask + SQLite + Jinja2. Sem ORM, queries SQL diretas (padrão do projeto).

## Goals / Non-Goals

**Goals:**
- Fluxo completo de empréstimo: solicitado → reservado → emprestado → devolvido (+ cancelado).
- Devolução prevista com default 7 dias, usuário sugere, admin ajusta.
- Renovação: usuário pede, admin aprova/rejeita.
- Status "atrasado" derivado (não persistido).
- Badge de disponibilidade no catálogo.
- Dashboard admin com totais.
- Histórico por jogo.
- Auditoria de mudanças de status.
- Filtros na lista admin.

**Non-Goals:**
- Fila de reserva quando jogo emprestado (Change 3).
- Notificações por email (Change 3).
- Paginação (Change 3).
- Export CSV (Change 3).
- Múltiplas cópias/exemplares por jogo (decisão: 1 jogo = 1 cópia).

## Decisions

### 1. 1 jogo = 1 cópia física (Opção A)
**Por que:** Decidido no explore mode. O modelo atual não tem exemplares. Cada jogo é único por `(area, nome)`.
**Implicação:** Apenas um empréstimo ativo (solicitado/reservado/emprestado) por jogo por vez. A solicitação de um jogo já emprestado é rejeitada com mensagem "Jogo indisponível".

### 2. 5 estados do empréstimo
```
solicitado → reservado → emprestado → devolvido
    └→ cancelado (usuário, enquanto solicitado)
```
**Por que:** Decidido no explore mode. "Disponível" é estado do JOGO (derivado), não do empréstimo.

### 3. Modelo de dados
**Schema:**
```sql
CREATE TABLE loans (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  game_id               INTEGER NOT NULL,
  user_id               INTEGER NOT NULL,
  status                TEXT NOT NULL CHECK(status IN
                          ('solicitado','reservado','emprestado',
                           'devolvido','cancelado')),
  devolucao_prevista    DATE,
  renovacao_pendente    INTEGER DEFAULT 0,
  nova_devolucao_prevista DATE,
  observacoes           TEXT,
  solicitado_at         TEXT,
  reservado_at          TEXT,
  emprestado_at         TEXT,
  devolvido_at          TEXT,
  created_at            TEXT DEFAULT (datetime('now','localtime')),
  updated_at            TEXT DEFAULT (datetime('now','localtime')),
  FOREIGN KEY (game_id) REFERENCES games(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX idx_loans_game ON loans(game_id);
CREATE INDEX idx_loans_user ON loans(user_id);
CREATE INDEX idx_loans_status ON loans(status);

CREATE TABLE loan_status_history (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  loan_id         INTEGER NOT NULL,
  status_anterior TEXT,
  status_novo     TEXT NOT NULL,
  changed_by      INTEGER NOT NULL,
  changed_at      TEXT DEFAULT (datetime('now','localtime')),
  observacao      TEXT,
  FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE,
  FOREIGN KEY (changed_by) REFERENCES users(id)
);
CREATE INDEX idx_history_loan ON loan_status_history(loan_id);
```

**Decisões:**
- Timestamps por estado (`solicitado_at`, `reservado_at`, etc.) são preenchidos na transição. Permitem calcular duração de cada fase.
- `renovacao_pendente` + `nova_devolucao_prevista` são flags na própria tabela `loans` (não tabela separada). Mais simples para um sistema pequeno. Se precisar de histórico de renovações, adicionar tabela no Change 3.
- `devolucao_prevista` é DATE (não TIMESTAMP) — importa a data, não a hora.
- Não há `cancelado_at` porque cancelamento é refletido em `updated_at` + `loan_status_history`.

### 4. Disponibilidade derivada (não persistida)
**Por que:** Persistir `games.status` criaria inconsistência se o loan mudar. Melhor derivar em runtime.
**Implementação:**
```python
def get_game_availability(game_id):
    """Retorna (status, loan_id_ativo) ou ('disponivel', None)."""
    loan = get_db().execute(
        "SELECT id, status FROM loans WHERE game_id = ? AND status IN "
        "('solicitado','reservado','emprestado') ORDER BY id DESC LIMIT 1",
        (game_id,)
    ).fetchone()
    if not loan:
        return ('disponivel', None)
    return (loan['status'], loan['id'])
```

**Badges:**
- `disponivel` → verde
- `solicitado` → amarelo (alguém pediu, ainda não reservado)
- `reservado` → amarelo (reservado para alguém)
- `emprestado` → vermelho
- `emprestado` + atrasado → vermelho escuro + "ATRASADO"

### 5. Devolução prevista: default 7 dias, usuário sugere, admin ajusta
**Fluxo:**
1. Usuário solicita: form tem campo `devolucao_prevista` preenchido com `today + 7 dias` (default). Usuário pode alterar.
2. Admin marca "emprestar": pode sobrescrever `devolucao_prevista` antes de confirmar.
**Decisão:** O valor sugerido pelo usuário é gravado em `loans.devolucao_prevista` no momento da solicitação. O admin pode alterá-lo ao marcar "emprestar".

### 6. Renovação como flag na própria loans
**Por que:** Decidido no explore mode. Para um sistema pequeno, flag é mais simples que tabela separada.
**Fluxo:**
1. Usuário clica "Renovar" (só visível se status=emprestado): POST `/emprestimos/<id>/renovar` com `nova_devolucao_prevista`.
2. `loans.renovacao_pendente = 1`, `loans.nova_devolucao_prevista = X`.
3. Admin vê na lista de empréstimos um indicador "Renovação solicitada".
4. Admin aprova: `devolucao_prevista = nova_devolucao_prevista`, `renovacao_pendente = 0`, `nova_devolucao_prevista = NULL`. Registra em `loan_status_history` com observação "Renovação aprovada".
5. Admin rejeita: `renovacao_pendente = 0`, `nova_devolucao_prevista = NULL`. `devolucao_prevista` mantém. Registra com "Renovação rejeitada".

### 7. Restrição: 1 empréstimo ativo por jogo
**Por que:** 1 jogo = 1 cópia física.
**Implementação:** Ao solicitar, verificar se já existe loan ativo. Se sim, rejeitar com "Jogo indisponível".

### 8. Transições permitidas
```
solicitado → reservado (admin aprova)
solicitado → cancelado (usuário cancela)
reservado → emprestado (admin empresta, define devolucao_prevista)
reservado → cancelado (admin cancela, com observação)
emprestado → devolvido (admin devolve)
emprestado → reservado (admin reverte, se entregou por engano — caso edge)
cancelado → (terminal)
devolvido → (terminal)
```
**Implementação:** Cada rota de transição valida o estado atual antes de mudar. Transição inválida retorna 400.

### 9. Dashboard admin
**Rota:** `GET /admin/dashboard` — `@role_required('admin_sistema', 'admin_jogos')`.
**Conteúdo:**
- Total de jogos (por área)
- Empréstimos ativos (solicitado + reservado + emprestado)
- Empréstimos atrasados
- Empréstimos do mês (criados no mês corrente)
- Top 5 jogos mais emprestados (histórico)
- Top 5 usuários mais ativos

### 10. Histórico por jogo
**Onde:** `detail.html`, seção "Histórico de empréstimos" (só para admins).
**Conteúdo:** Lista de empréstimos passados do jogo, ordenados por `created_at DESC`, mostrando usuário, período, status final.

## Risks / Trade-offs

- **[Sem fila de reserva]** → Se jogo emprestado, solicitação é rejeitada. Fila fica para Change 3.
- **[Renovação como flag sem histórico]** → Se houver múltiplas renovações, só a última fica registrada. Histórico de renovações fica em `loan_status_history` (observação), mas não é estruturado. Aceitável para sistema pequeno.
- **[Race condition em solicitação simultânea]** → Dois usuários solicitam o mesmo jogo ao mesmo tempo. Mitigação: UNIQUE INDEX parcial em `(game_id, status)` não é suportado em SQLite antigo. Alternativa: validar no início do POST e usar transaction. Risco baixo em sistema local.
- **[Sem notificação de atraso]** → Usuário não é avisado que está atrasado. Email fica para Change 3. Dashboard admin mostra atrasados.

## Migration Plan

1. Adicionar tabelas `loans` e `loan_status_history` ao `app/schema.sql`.
2. Adicionar funções de loans em `app/models.py` (ou `app/loans_models.py`).
3. Adicionar rotas de empréstimos (usuário e admin) em `app/routes.py`.
4. Adicionar badge de disponibilidade em `index.html` e `detail.html`.
5. Criar `dashboard.html` e `emprestimos.html` / `emprestimos_admin.html`.
6. Adicionar histórico por jogo em `detail.html`.
7. **Rollback:** remover tabelas, rotas, templates. Catálogo volta ao estado anterior (sem badge, sem histórico).

## Open Questions

- Nenhuma pendente. Todas as decisões foram confirmadas durante o explore mode.
