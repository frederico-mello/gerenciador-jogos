## Why

A página `/admin/users` apresenta problemas visuais: os botões de ação (Editar, alternância de papel e Inativar/Reativar) estão grudados uns nos outros na coluna "Ações", e o toolbar superior também não respeita os padrões de espaçamento usados no restante do projeto. Sem espaçamento consistente, a interface fica apertada e difícil de usar.

## What Changes

- Adicionar estilos dedicados para a coluna de ações da tabela de usuários, com `gap` consistente entre botões, links e formulários inline.
- Refatorar o toolbar da página `/admin/users` para usar os padrões visuais existentes do projeto (`list-header` + `list-actions` / `filter-form`), garantindo espaçamento e consistência.
- Ajustar a responsividade da coluna de ações para telas pequenas, mantendo a usabilidade.
- Garantir que as alterações afetem apenas `admin_users.html` e `style.css`, sem mudanças de comportamento funcional.

## Capabilities

### New Capabilities
- `admin-users-actions-spacing`: Estilização da coluna de ações da tabela de usuários e do toolbar superior, introduzindo espaçamento consistente entre controles.

### Modified Capabilities
- (nenhum — mudança puramente visual/UX, sem alteração de requisitos funcionais)

## Impact

- `app/templates/admin_users.html`: reformatação do toolbar e envoltória da coluna de ações.
- `app/static/style.css`: adição de regras de estilo para `.actions-cell` e `.toolbar-users`.
- Nenhum impacto em APIs, banco de dados ou permissões.
