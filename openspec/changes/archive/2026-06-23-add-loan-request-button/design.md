## Context

O sistema de empréstimos já está completo no backend. A rota `POST /emprestimos/solicitar/<game_id>` (routes.py:643) cria um loan com status `solicitado` e redireciona para `/emprestimos`. Quando o jogo está indisponível, redireciona para `/emprestimos/fila/confirmar/<game_id>`.

Porém, a UI não expõe nenhum botão para acionar essa rota. O usuário precisa saber a URL manualmente. A página de detalhe (`detail.html`) mostra o badge de disponibilidade e botões de admin (editar/excluir), mas nada para o `usuario`. A página "Meus Empréstimos" (`emprestimos.html`) lista loans existentes mas não oferece caminho para solicitar um novo.

**Templates afetados:**
- `detail.html:15-21` — bloco `.detail-actions` (atualmente só para admins)
- `emprestimos.html:53-55` — mensagem "Nenhum empréstimo encontrado" (quando vazio)

**Contexto já disponível no template `detail.html`:**
- `availability_status` — string: `disponivel`, `solicitado`, `reservado`, `emprestado`
- `active_loan_id` — ID do loan ativo (ou None)
- `current_user` — dict do usuário logado (ou None)

## Goals / Non-Goals

**Goals:**
- Usuário logado (`usuario`) vê botão "Solicitar Empréstimo" na página de detalhe quando jogo está disponível
- Quando jogo está indisponível, botão muda para "Entrar na fila"
- Usuário não logado vê link para login
- Página "Meus Empréstimos" oferece caminho para solicitar novo empréstimo

**Non-Goals:**
- Não alterar a rota `solicitar_emprestimo` (backend já funciona)
- Não alterar o catálogo (`index.html`) — cards já têm badge, adicionar botão em cada card poluiria o grid
- Não adicionar solicitação inline via AJAX — manter fluxo POST tradicional

## Decisions

### 1. Botão na página de detalhe, não no catálogo

**Decisão:** O botão de solicitar fica na página de detalhe do jogo (`detail.html`), não nos cards do catálogo.

**Rationale:** O catálogo mostra 20 cards por página com grid responsivo. Adicionar um botão em cada card polui visualmente e o card já é um link (`<a class="card">`) — aninhar formulários dentro de links é inválido HTML. A página de detalhe é o local natural para ações sobre um jogo específico.

**Alternativa considerada:** Botão flutuante por card com formulário separado. Rejeitado por complexidade de layout e conflito com o link do card.

### 2. Lógica condicional no template, não no backend

**Decisão:** O template `detail.html` decide qual botão mostrar baseado em `current_user`, `current_user.role` e `availability_status`. Nenhuma mudança no route handler `detalhe()`.

**Rationale:** O route handler já passa todos os dados necessários (`availability_status`, `current_user`). Adicionar lógica de apresentação no backend seria over-engineering. O template Jinja2 suporta condicionais facilmente.

### 3. Formulário POST para solicitar, não link

**Decisão:** O botão "Solicitar Empréstimo" é um `<form method="post">` com CSRF token, não um link `<a>`.

**Rationale:** A rota `solicitar_emprestimo` aceita apenas POST (cria recurso). Links devem ser idempotentes (GET). Manter POST com CSRF é consistente com os outros botões de ação no sistema (cancelar, renovar, etc).

### 4. Bloquear solicitação duplicada no backend

**Decisão:** Verificar na rota `solicitar_emprestimo` se o usuário já possui um loan ativo para o mesmo jogo antes de criar.

**Rationale:** Atualmente a rota não verifica duplicatas. Um usuário poderia clicar o botão múltiplas vezes e criar loans duplicados. Essa verificação é simples (uma query) e previne dados inconsistentes.

## Risks / Trade-offs

- **[Race condition]** Dois cliques rápidos podem criar loans duplicados antes da verificação → Mitigação: verificar duplicata dentro da mesma transição do `create_loan`, ou usar redirect PRG pattern (já feito — a rota redireciona após criar)
- **[Usuário com loan ativo vê botão]** Se o usuário já tem um loan ativo para o jogo, o botão não deve aparecer → Mitigação: a rota `detalhe` pode verificar se o usuário atual já tem loan ativo para esse jogo e passar essa info ao template
- **[UX da fila]** O botão "Entrar na fila" leva para uma página de confirmação separada (`confirmar_fila.html`), não diretamente para a fila — isso é consistente com o fluxo existente e dá ao usuário a chance de reconsiderar
