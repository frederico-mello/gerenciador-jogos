## Context

A página `/admin/users` (`app/templates/admin_users.html`) lista usuários com colunas fixas (Nome, Email, Papel, Escola, Ativo, Ações). A coluna "Ações" contém um link "Editar", um `<select>` de papel dentro de um `<form>`, e um botão "Inativar"/"Reativar" dentro de outro `<form>`. Todos os elementos são `display:inline` sem wrapper flexível, resultando em botões encostados.

O toolbar superior (`<div class="toolbar">`) usa um `<form class="filters">` seguido de um link "Novo usuário", ambos sem o padrão visual do projeto. O CSS existente já define `.list-header`, `.list-actions` e `.filter-form` com espaçamento adequado, mas `admin_users.html` não os utiliza.

## Goals / Non-Goals

**Goals:**
- Espaçamento consistente entre os controles da coluna "Ações" usando `display: flex; gap`.
- Toolbar superior reutiliza os padrões visuais existentes (`.list-header` / `.filter-form`).
- Quebra de linha limpa em telas menores.

**Non-Goals:**
- Alterar a estrutura semântica da tabela ou colunas.
- Mudar comportamento funcional (filtros, CSRF, submissão de formulários).
- Refatorar outros templates ou rotas.

## Decisions

1. **Usar flexbox com gap na coluna de ações**
   - Alternativa: `margin-right` em cada botão → Rejeitada por ser menos consistente e mais difícil de manter.
   - Decisão: envolver os elementos da coluna "Ações" em um wrapper com `display: flex; flex-wrap: wrap; gap: 8px; align-items: center;`.

2. **Reutilizar classes existentes no toolbar**
   - Alternativa: criar novas classes `.toolbar`, `.toolbar-filters` → Rejeitada por introduzir padrão duplicado.
   - Decisão: trocar `<div class="toolbar">` por `<div class="list-header">` e `<form class="filters">` por `<form class="filter-form">`. O link "Novo usuário" entra em um wrapper com `.list-actions`.

3. **Adicionar CSS mínimo para a coluna de ações**
   - Criar seletor `.actions` com regras de flexbox. Não há conflito porque nenhuma outra tabela usa essa classe no template.

## Risks / Trade-offs

- [Risco] O `<select>` dentro de `<form style="display:inline">` pode não herdar o gap corretamente → Mitigação: o wrapper flex controla o espaçamento entre filhos, independentemente do `display` interno.
- [Risco] Alterar a classe do toolbar pode afetar a aparência se outros templates usarem `.toolbar` → Mitigação: `.toolbar` não é definido no CSS atual; apenas `admin_users.html` usa esse nome.

## Migration Plan

- Alterar `app/templates/admin_users.html` e `app/static/style.css`.
- Testar visualmente em `/admin/users` após salvar.
- Rollback: reverter as duas alterações.
