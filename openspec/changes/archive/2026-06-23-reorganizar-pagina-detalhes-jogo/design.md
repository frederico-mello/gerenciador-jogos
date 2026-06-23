## Context

A página de detalhes de um jogo (`detail.html`) exibe nome, área, disponibilidade, ações, imagens, metadados técnicos (`regras_resumo`, `num_jogadores`, `duracao_min`), descrição em Markdown, manual e histórico de empréstimos. Atualmente, os metadados e a descrição ficam dentro de um único blanco lateral com parágrafos simples, deixando o conteúdo denso e difícil de escanear. O CSS já possui classes para cards (`card`, `card-stat`) e grids, mas não há estrutura dedicada para a página de detalhes.

## Goals / Non-Goals

**Goals:**
- Separar semanticamente a descrição do jogo dos metadados técnicos.
- Apresentar cada metadado técnico como um campo visualmente isolado (card).
- Manter a descrição em Markdown como seção de destaque, em largura total.
- Ocultar seções sem conteúdo para evitar espaço vazio.
- Preservar layout responsivo e acessível.

**Non-Goals:**
- Alterar o formulário de criação/edição de jogos.
- Adicionar novos campos ao modelo de dados.
- Mudar rotas, controllers ou lógica de negócio de empréstimos.
- Usar ícones, emojis ou bibliotecas de componentes externas.

## Decisions

1. **Layout em duas seções principais**: "Sobre o jogo" (descrição em Markdown, largura total) seguida de um grid abaixo com imagens à esquerda e "Detalhes técnicos" à direita.
   - *Rationale*: a descrição costuma ser o texto mais longo e merece destaque; os metadados são curtos e funcionam bem ao lado das imagens.
   - *Alternativa considerada*: colocar descrição e imagens lado a lado. Rejeitado porque a descrição perderia destaque quando longa.

2. **Metadados em cards verticais**: cada campo (`regras_resumo`, `num_jogadores`, `duracao_min`) vira um card com rótulo no topo e valor abaixo.
   - *Rationale*: facilita leitura rápida e escaneamento visual sem depender de ícones.
   - *Alternativa considerada*: lista horizontal com rótulo à esquerda. Rejeitado porque valores de tamanhos diferentes desalinhariam.

3. **Ocultar seções vazias**: "Sobre o jogo" só aparece se `descricao_html` existir; "Detalhes técnicos" só aparece se pelo menos um dos três campos estiver preenchido.
   - *Rationale*: evita que o usuário veja títulos soltos sem informação.

4. **Reutilizar estilos existentes**: a paleta e as bordas seguem os cards já usados no projeto (`--card`, `--border`, `border-radius: 16px`).
   - *Rationale*: mantém consistência visual e reduz CSS novo ao mínimo.

## Risks / Trade-offs

- [Risk] A descrição em largura total pode empurrar os metadados para bem abaixo da dobra em textos muito longos. → Mitigação: manter a descrição como Markdown renderizado normalmente; se futuramente percebermos que ela fica longa demais, podemos limitar altura ou adicionar "ler mais".
- [Risk] Telas muito estreitas podem fazer os cards de metadados empilharem e ocupar muita altura. → Mitigação: grid com `auto-fit` e `minmax` para que cards se ajustem a uma coluna em mobile.
- [Trade-off] Não usamos ícones para tornar os campos ainda mais escaneáveis; como a preferência é texto puro, confiamos no espaçamento e no contraste entre rótulo e valor.
