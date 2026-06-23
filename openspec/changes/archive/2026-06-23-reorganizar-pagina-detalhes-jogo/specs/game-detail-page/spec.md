## ADDED Requirements

### Requirement: Descrição separada em seção própria
A página de detalhes do jogo SHALL apresentar a descrição renderizada em Markdown em uma seção distinta intitulada "Sobre o jogo", ocupando a largura total disponível.

#### Scenario: Jogo possui descrição
- **WHEN** o jogo possuir descrição preenchida
- **THEN** a página exibe a seção "Sobre o jogo" com o conteúdo Markdown renderizado abaixo do cabeçalho de ações

#### Scenario: Jogo não possui descrição
- **WHEN** o jogo não possuir descrição
- **THEN** a seção "Sobre o jogo" NÃO é renderizada

### Requirement: Metadados técnicos em cards separados
A página de detalhes do jogo SHALL apresentar os metadados `regras_resumo`, `num_jogadores` e `duracao_min` em cards individuais dentro de uma seção intitulada "Detalhes técnicos".

#### Scenario: Todos os metadados preenchidos
- **WHEN** o jogo possui regras resumidas, número de jogadores e duração mínima
- **THEN** a página exibe três cards lado a lado, cada um com rótulo no topo e valor abaixo

#### Scenario: Apenas alguns metadados preenchidos
- **WHEN** apenas alguns dos três metadados estão preenchidos
- **THEN** apenas os cards correspondentes aos metadados preenchidos são exibidos

#### Scenario: Nenhum metadado preenchido
- **WHEN** nenhum dos três metadados está preenchido
- **THEN** a seção "Detalhes técnicos" NÃO é renderizada

### Requirement: Manter posição das imagens
A página de detalhes do jogo SHALL continuar a exibir as imagens de componentes e perfil na coluna lateral, abaixo da seção "Sobre o jogo".

#### Scenario: Imagens existentes
- **WHEN** o jogo possui imagens de componentes e/ou perfil
- **THEN** as imagens são renderizadas na coluna esquerda, abaixo da seção "Sobre o jogo", enquanto os cards de "Detalhes técnicos" ocupam a coluna direita

### Requirement: Layout responsivo
A página de detalhes do jogo SHALL manter apresentação legível em telas estreitas, empilhando as colunas e os cards verticalmente.

#### Scenario: Visualização em dispositivo móvel
- **WHEN** a página é visualizada em uma tela com largura menor ou igual ao breakpoint de 860px
- **THEN** as colunas de imagens e detalhes técnicos se empilham verticalmente e os cards de metadados se ajustam a uma única coluna

### Requirement: Estilos consistentes com o design system existente
Os novos elementos da página de detalhes do jogo SHALL usar os tokens visuais existentes do projeto (cores, bordas arredondadas e espaçamentos) e NÃO SHALL introduzir bibliotecas CSS/JS externas.

#### Scenario: Renderização dos novos elementos
- **WHEN** as seções "Sobre o jogo" e "Detalhes técnicos" são renderizadas
- **THEN** elas usam fundo branco, borda sutil, cantos arredondados e tipografia consistente com os cards já existentes
