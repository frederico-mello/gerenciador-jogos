## Why

A página de detalhes de cada jogo apresenta as informações como texto corrido. Os metadados (`regras_resumo`, `num_jogadores`, `duracao_min`) e a descrição em Markdown ficam empilhados em parágrafos dentro de um único bloco, dificultando a leitura e a rápida identificação das informações principais. Reorganizar visualmente essa página torna os dados mais claros para usuários que querem decidir se solicitam um empréstimo.

## What Changes

- Reestruturar o template `app/templates/detail.html` para separar a descrição do jogo dos metadados técnicos.
- Criar uma seção "Sobre o jogo" com a descrição em largura total.
- Criar uma seção "Detalhes técnicos" com os campos `regras_resumo`, `num_jogadores` e `duracao_min` dispostos em cards separados.
- Manter as imagens de componentes e perfil na coluna lateral, abaixo da descrição.
- Atualizar `app/static/style.css` com classes para as novas seções e cards de metadados.
- Ocultar automaticamente seções que não possuem conteúdo (descrição vazia ou todos os detalhes técnicos vazios).

## Capabilities

### New Capabilities
- `game-detail-page`: apresentação visual dos detalhes de um jogo, organizando descrição, imagens e metadados técnicos de forma clara.

### Modified Capabilities
<!-- Esta mudança não altera requisitos funcionais de capabilities existentes, apenas a implementação visual da página de detalhes. -->

## Impact

- `app/templates/detail.html`: reestruturação do conteúdo principal.
- `app/static/style.css`: novas classes de layout e estilo.
- Nenhuma alteração em rotas, modelos, banco de dados ou APIs.
