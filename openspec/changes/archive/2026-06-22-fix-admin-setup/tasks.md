## 1. Dependências e configuração de ambiente

- [x] 1.1 Adicionar `python-dotenv` a `requirements.txt`
- [x] 1.2 Instalar dependências atualizadas (`pip install -r requirements.txt`)
- [x] 1.3 Criar arquivo `.env.example` na raiz do projeto com `FLASK_SECRET_KEY=` em branco e comentários
- [x] 1.4 Atualizar `README.md` com instruções para copiar `.env.example` para `.env` e definir `FLASK_SECRET_KEY`

## 2. Carregamento de .env na aplicação

- [x] 2.1 Importar `load_dotenv` de `dotenv` no topo de `app/__init__.py`
- [x] 2.2 Chamar `load_dotenv()` no início da factory `create_app()`, antes de ler `FLASK_SECRET_KEY`
- [x] 2.3 Manter o fallback de chave dev insegura com `RuntimeWarning` apenas quando `FLASK_SECRET_KEY` não estiver definida
- [x] 2.4 Verificar que `tests/conftest.py` continua passando `test_config` e não é afetado pelo `.env`

## 3. Melhorias no script de bootstrap de admin

- [x] 3.1 Refatorar `scripts/create_admin.py` para buscar usuário por email antes de tentar criar
- [x] 3.2 Se usuário existir com `role='admin_sistema'`, perguntar se deseja resetar a senha
- [x] 3.3 Se usuário existir com papel diferente de `admin_sistema'`, perguntar se deseja promover a `admin_sistema` e resetar a senha
- [x] 3.4 Implementar função `reset_admin_password(user_id, senha)` usando `update_user` com `data={"senha": senha}`
- [x] 3.5 Implementar função `promote_to_admin_sistema(user_id, senha)` atualizando `role` e senha
- [x] 3.6 Preservar o comportamento atual de confirmação quando já existe algum `admin_sistema` e o email é novo
- [x] 3.7 Garantir que o script encerra sem alterar dados se o usuário cancelar a ação

## 4. Testes

- [x] 4.1 Adicionar/ajustar testes em `tests/` para cobrir carregamento de `.env` via `python-dotenv` (se viável sem poluir ambiente de teste)
- [x] 4.2 Criar testes para `create_admin.py` cobrindo: novo admin, reset de senha de admin existente, promoção de usuário comum, cancelamento de ação
- [x] 4.3 Rodar `python -m pytest` e garantir que todos os testes existentes continuam passando

## 5. Validação manual

- [x] 5.1 Criar `.env` a partir de `.env.example` com uma `FLASK_SECRET_KEY` definida
- [x] 5.2 Executar `python scripts/create_admin.py` com email inexistente e confirmar criação sem warning de chave insegura
- [x] 5.3 Executar `python scripts/create_admin.py` com email já cadastrado como `admin_sistema` e confirmar reset de senha
- [x] 5.4 Executar `python scripts/create_admin.py` com email de usuário comum e confirmar promoção + reset
- [x] 5.5 Confirmar login na aplicação com as senhas atualizadas

## 6. Finalização OpenSpec

- [x] 6.1 Revisar artefatos da change `fix-admin-setup`
- [x] 6.2 `/opsx-archive` da change após validação
