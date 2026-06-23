## Why

Administradores do sistema precisam criar usuários diretamente pelo painel administrativo, sem depender do fluxo de registro público. O registro público (`/registrar`) só cria usuários com papel "usuario" e exige escola. Já um administrador precisa poder atribuir papéis (admin_sistema, admin_jogos, usuario), definir status ativo/inativo e opcionalmente vincular a uma escola — tudo em uma interface dedicada.

## What Changes

- Nova rota `GET /admin/users/criar` que renderiza formulário de criação de usuário
- Rota `POST /admin/users/criar` que valida os dados e persiste o usuário
- Template `admin_user_create.html` com formulário contendo: nome, email, senha, confirmação, papel, escola (opcional), ativo
- Link "Novo usuário" no toolbar de `/admin/users` apontando para a nova rota
- Testes automatizados para a funcionalidade

## Capabilities

### New Capabilities
- `admin-user-create`: Criação de usuários pelo administrador, com suporte a definição de papel, escola e status ativo/inativo

### Modified Capabilities


## Impact

- `app/routes.py`: nova rota `admin_users_criar` (já implementada)
- `app/templates/admin_user_create.html`: novo template de formulário (já implementado)
- `app/templates/admin_users.html`: adicionado link "Novo usuário" no toolbar (já implementado)
- `tests/test_auth.py`: testes para a funcionalidade (já implementados)
- Nenhum impacto em banco de dados, APIs ou dependências