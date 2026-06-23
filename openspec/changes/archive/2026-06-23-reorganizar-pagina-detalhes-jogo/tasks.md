## 1. Estruturar seções no template

- [x] 1.1 Em `app/templates/detail.html`, mover a descrição Markdown para uma nova seção "Sobre o jogo" com largura total, abaixo do cabeçalho de ações.
- [x] 1.2 Criar a seção "Detalhes técnicos" à direita das imagens, contendo os cards de `regras_resumo`, `num_jogadores` e `duracao_min`.
- [x] 1.3 Manter as imagens de componentes e perfil na coluna lateral esquerda, abaixo da seção "Sobre o jogo".
- [x] 1.4 Adicionar condicionais para ocultar a seção "Sobre o jogo" quando `descricao_html` estiver vazio.
- [x] 1.5 Adicionar condicionais para ocultar a seção "Detalhes técnicos" quando todos os metadados técnicos estiverem vazios.

## 2. Adicionar estilos no CSS

- [x] 2.1 Criar classes `.game-about` e `.game-specs` com fundo branco, borda sutil, cantos arredondados e espaçamento interno consistente com os cards existentes.
- [x] 2.2 Criar classes `.specs-grid` e `.spec-card` para dispor os metadados em cards verticais (rótulo no topo, valor abaixo).
- [x] 2.3 Criar classes `.two-column-section` ou ajustar `.detail-grid` para manter imagens à esquerda e detalhes técnicos à direita.
- [x] 2.4 Adicionar media query para empilhar as colunas e os cards em telas menores que 860px.

## 3. Verificar e ajustar responsividade

- [x] 3.1 Validar que em telas largas a descrição ocupa a largura total e os detalhes técnicos ficam ao lado das imagens.
- [x] 3.2 Validar que em telas estreitas as seções se empilham verticalmente e os cards de metadados ocupam a largura total.

## 4. Testes e validação

- [x] 4.1 Executar testes existentes do projeto (`pytest`) para garantir que nenhuma rota ou funcionalidade quebrou.
- [x] 4.2 Renderizar a página de detalhes para jogos com todos os campos preenchidos e confirmar a separação visual.
- [x] 4.3 Renderizar a página de detalhes para jogos sem descrição e sem metadados técnicos e confirmar que as seções vazias não aparecem.
