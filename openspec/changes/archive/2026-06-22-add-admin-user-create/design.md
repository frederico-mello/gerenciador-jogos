## Context

O painel administrativo já possui uma página `/admin/users` que lista todos os usuários com opções de filtro, edição, alteração de papel e inativação/reativação. Faltava uma interface para que administradores pudessem criar novos usuários diretamente, sem depender do registro público (`/registrar`) que é auto-serviço e restrito a papel "usuario".

A rota `admin_users_criar` foi implementada em `routes.py` seguindo o mesmo padrão das demais rotas admin (e.g., `admin_schools_criar`, `admin_users_editar`). O template `admin_user_create.html` é independente do template de edição (`admin_user_form.html`) porque os campos e validações diferem significativamente.

## Goals / Non-Goals

**Goals:**
- Administradores com papel admin_sistema podem criar usuários com nome, email, senha, papel, escola (opcional) e status ativo/inativo
- Validação completa dos campos no backend
- CSRF protection via Flask-WTF
- Testes automatizados para a funcionalidade

**Non-Goals:**
- Importação em lote de usuários
- Envio de e-mail de boas-vindas ou notificação
- Log de auditoria de criação
- Criação de usuário via API REST
- Alteração de papel de usuário na criação (já coberto pela rota `/admin/users/<id>/role`)

## Decisions

1. **Template separado do de edição**
   - Alternativa: reaproveitar `admin_user_form.html` com lógica condicional
   - Decisão: criar template dedicado `admin_user_create.html` porque criação tem fluxo diferente (confirmação de senha, seleção de papel) e evita complexidade condicional
   
2. **escola_id opcional na criação admin (vs obrigatório no registro público)**
   - Alternativa: exigir escola sempre
   - Decisão: admin pode criar usuários genéricos sem vínculo escolar; o registro público exige escola porque o contexto é diferente (aluno se vinculando a sua escola)
   
3. **Papel selecionável na criação**
   - Alternativa: criar sempre como "usuario"
   - Decisão: admin pode definir o papel diretamente, pois já tem privilégio para alterar papel via `/admin/users/<id>/role`
   
4. **Reutilização de `models.create_user()`**
   - A função já suporta todos os campos necessários, incluindo hash de senha via `senha` ou `password_hash`
   
5. **CSRF via Flask-WTF**
   - Consistente com o resto do projeto; o token é injetado via `{{ csrf_token() }}` no template

## Risks / Trade-offs

- [Risco] Template `admin_user_create.html` duplica HTML do formulário → Mitigação: aceitável pela diferença de comportamento e simplicidade; extração de partial só se houver terceiro formulário de usuário
- [Risco] Escola opcional pode criar usuários "órfãos" sem vínculo → Mitigação: decisão intencional, administrador sabe o que está fazendo