## Purpose

Define como a exclusão de jogos do catálogo interage com a vida útil dos empréstimos e das filas de reserva, garantindo que o catálogo reflita com precisão o estado de disponibilidade dos jogos e que a remoção de um jogo seja consistente.

## ADDED Requirements

### Requirement: Bloqueio de exclusão de jogos com empréstimos ativos
O sistema NÃO SHALL excluir um jogo que possua ao menos um empréstimo com status ativo (`solicitado`, `reservado` ou `emprestado`). Ao confirmar a exclusão via `POST /<id>/excluir`, o sistema deve verificar a existência de empréstimos ativos e, havendo algum, NÃO remover o jogo, exibir uma mensagem de erro orientando que o administrador deva devolver ou cancelar os empréstimos ativos antes, e redirecionar de volta para a página do jogo (`GET /<id>`). O sistema NÃO SHALL mover nem remover os arquivos de dados do jogo neste caso.

#### Scenario: Excluir jogo emprestado
- **WHEN** um administrador confirma a exclusão de um jogo que possui um empréstimo com `status='emprestado'` via `POST /<id>/excluir`
- **THEN** o jogo NÃO é removido do catálogo, aparece flash de erro informando que existem empréstimos ativos e o administrador é redirecionado para a página do jogo

#### Scenario: Excluir jogo com solicitação em aberto
- **WHEN** um administrador confirma a exclusão de um jogo que possui um empréstimo com `status='solicitado'` via `POST /<id>/excluir`
- **THEN** o jogo NÃO é removido, aparece flash de erro e o administrador é redirecionado para a página do jogo

#### Scenario: Excluir jogo após resolver empréstimos
- **WHEN** um administrador devolve ou cancela todos os empréstimos ativos de um jogo e só então confirma a exclusão
- **THEN** o jogo é removido do catálogo, os empréstimos históricos são removidos em cascata e os arquivos de dados são apagados

### Requirement: Remoção em cascata de empréstimos e filas
O sistema SHALL remover, em cascata, todas as linhas de `loans` e de `reservation_queue` cujo `game_id` aponte para um jogo excluído, de forma que nenhum empréstimo ou entrada de fique órfão após a exclusão. A exclusão do jogo via `POST /<id>/excluir` deve propagar a remoção para essas tabelas.

#### Scenario: Exclusão remove empréstimos e filas associados
- **WHEN** um jogo com empréstimos e entradas de fila é excluído
- **THEN** todas as linhas de `loans` e `reservation_queue` associadas a esse `game_id` são removidas simultaneamente
