## MODIFIED Requirements

### Requirement: Tela de lista com filtro
O sistema SHALL fornecer uma rota `GET /` que renderiza `templates/index.html` listando todos os jogos (nome, área, imagem de perfil como thumbnail), com seletor de área (todas/anatomia/histologia/microbiologia) e campo de busca por nome. **Cada card de jogo mostra adicionalmente um badge de disponibilidade (verde = Disponível, amarelo = Reservado/Solicitado, vermelho = Emprestado) derivado da tabela `loans`.**

#### Scenario: Lista com badge de disponibilidade
- **WHEN** o visitante acessa `GET /`
- **THEN** cada card de jogo exibe o badge de disponibilidade ao lado do nome

### Requirement: Tela de detalhe com carrossel de manuais
O sistema SHALL fornecer uma rota `GET /<id>` que renderiza `templates/detail.html` mostrando todos os campos do jogo, a imagem de componentes, a imagem de perfil, e o texto descritivo (Markdown renderizado). As páginas de manual (`manual_1.jpg`, `manual_2.jpg`, …) são exibidas em sequência, navegáveis via botões anterior/próximo (carrossel simples em JS). **O badge de disponibilidade é exibido. Uma seção "Histórico de empréstimos" é exibida apenas para usuários com role `admin_sistema` ou `admin_jogos`, listando todos os empréstimos do jogo ordenados por data.**

#### Scenario: Admin vê badge + histórico
- **WHEN** um `admin_jogos` logado acessa `GET /<id>` para um jogo emprestado
- **THEN** o badge mostra "Emprestado" em vermelho, e a seção de histórico exibe os empréstimos passados

#### Scenario: Visitante vê badge sem histórico
- **WHEN** um visitante não logado acessa `GET /<id>` para um jogo disponível
- **THEN** o badge mostra "Disponível" em verde, e a seção de histórico não é exibida
