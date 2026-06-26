# Capability: loan-terms

## Purpose

Exibição e aceite de termos de uso no fluxo de solicitação de empréstimo e reserva, com persistência do aceite e versionamento simples dos termos.

## Requirements

### Requirement: Termos de empréstimo carregados de arquivo Markdown
O sistema SHALL carregar os termos de uso de empréstimo do arquivo `terms_emprestimo.md` na raiz do projeto. O conteúdo é renderizado como HTML (via markdown) e exibido na tela de solicitação de empréstimo e na tela de confirmação de fila. Se o arquivo não existir, o sistema SHALL exibir um texto padrão informando que os termos não foram configurados.

#### Scenario: Arquivo de termos existe
- **WHEN** o servidor inicia e o arquivo `terms_emprestimo.md` existe na raiz
- **THEN** o conteúdo é carregado e disponibilizado para renderização nas telas de solicitação

#### Scenario: Arquivo de termos não existe
- **WHEN** o servidor inicia e o arquivo `terms_emprestimo.md` NÃO existe
- **THEN** um warning é registrado no log e as telas exibem "Termos de uso não configurados. Entre em contato com o administrador."

### Requirement: Versionamento dos termos por hash
O sistema SHALL derivar a versão dos termos como o hash SHA-256 do conteúdo do arquivo, truncado para os primeiros 8 caracteres. Esta versão é armazenada no campo `termos_versao` da tabela `loans` no momento do aceite.

#### Scenario: Hash gerado
- **WHEN** o conteúdo do arquivo `terms_emprestimo.md` é "Ao retirar um jogo, comprometo-me a devolvê-lo em perfeito estado."
- **THEN** `termos_versao` é um hash SHA-256 truncado para 8 caracteres hexadecimais

#### Scenario: Hash muda com conteúdo
- **WHEN** o arquivo `terms_emprestimo.md` é alterado
- **THEN** o valor de `termos_versao` para novos aceites reflete o novo hash, e aceites anteriores preservam o hash da época

### Requirement: Tela dedicada de solicitação de empréstimo
O sistema SHALL fornecer `GET /emprestimos/solicitar/<game_id>` que exibe: nome do jogo, área, badge de disponibilidade, os termos de empréstimo renderizados em HTML, um campo de data de devolução prevista (default hoje + 7 dias, editável), e um checkbox "Li e aceito os termos de empréstimo" obrigatório. O formulário faz POST para a mesma rota.

#### Scenario: Usuário acessa tela de solicitação
- **WHEN** um `usuario` logado acessa `GET /emprestimos/solicitar/5` para um jogo disponível
- **THEN** a página exibe o nome do jogo, os termos renderizados, campo de data com default +7 dias, checkbox de aceite, e botão "Confirmar solicitação"

#### Scenario: Usuário não logado
- **WHEN** um visitante não autenticado acessa `GET /emprestimos/solicitar/5`
- **THEN** é redirecionado para `/login` com `next` apontando para a tela de solicitação

#### Scenario: Jogo inexistente
- **WHEN** um usuário logado acessa `GET /emprestimos/solicitar/9999`
- **THEN** retorna 404

### Requirement: Aceite obrigatório validado no servidor
O sistema SHALL rejeitar `POST /emprestimos/solicitar/<game_id>` se o campo `aceite_termos` não for igual a `1`. O servidor retorna mensagem de erro "Você precisa aceitar os termos de empréstimo." e reexibe a tela de solicitação com os dados preenchidos.

#### Scenario: POST sem aceite
- **WHEN** um usuário envia `POST /emprestimos/solicitar/5` sem o campo `aceite_termos` ou com valor diferente de `1`
- **THEN** o servidor retorna a tela de solicitação com mensagem de erro e o empréstimo NÃO é criado

#### Scenario: POST com aceite
- **WHEN** um usuário envia `POST /emprestimos/solicitar/5` com `aceite_termos=1` e `devolucao_prevista=2026-07-15`
- **THEN** o empréstimo é criado com `termos_aceite_at` preenchido e `termos_versao` igual ao hash atual dos termos

### Requirement: Registro de aceite na tabela loans
O sistema SHALL persistir o aceite dos termos no momento da criação do empréstimo, preenchendo as colunas `termos_aceite_at` (timestamp ISO 8601) e `termos_versao` (hash dos termos vigentes) na tabela `loans`.

#### Scenario: Aceite registrado
- **WHEN** um empréstimo é criado via `POST /emprestimos/solicitar/5` com `aceite_termos=1`
- **THEN** a linha em `loans` contém `termos_aceite_at` com a data/hora do aceite e `termos_versao` com o hash vigente dos termos

### Requirement: Aceite dos termos na confirmação de fila
O sistema SHALL exigir que o usuário aceite os termos de empréstimo também ao entrar na fila de reserva. A tela `GET /confirmar_fila/<game_id>` deve incluir os termos renderizados e o checkbox de aceite. O POST `/confirmar_fila/<game_id>` deve validar `aceite_termos=1`.

#### Scenario: Confirmação de fila com aceite
- **WHEN** um usuário acessa `GET /confirmar_fila/5` e envia `POST /confirmar_fila/5` com `aceite_termos=1`
- **THEN** a reserva é criada na fila

#### Scenario: Confirmação de fila sem aceite
- **WHEN** um usuário envia `POST /confirmar_fila/5` sem `aceite_termos=1`
- **THEN** o servidor reexibe a tela de confirmação com mensagem de erro e a reserva NÃO é criada
