## Why

O script `scripts/create_admin.py` falha silenciosamente com um alerta de `FLASK_SECRET_KEY` ausente e encerra com erro quando o email do administrador já existe. Isso dificulta o setup inicial e a recuperação de acesso de um admin existente. Precisamos garantir que a variável de ambiente seja carregada corretamente e que o script ofereça ações úteis (reset de senha ou promoção a admin) quando o usuário já estiver cadastrado.

## What Changes

- Adicionar carregamento automático de variáveis de ambiente a partir de um arquivo `.env` na raiz do projeto, eliminando o alerta de chave insegura em ambientes configurados.
- Melhorar o script `scripts/create_admin.py` para detectar quando o email informado já existe e oferecer:
  - **Resetar a senha** se o usuário já for `admin_sistema`.
  - **Promover a admin_sistema e resetar a senha** se o usuário tiver outro papel.
- Criar `.env.example` como template seguro versionável.
- Atualizar `requirements.txt` incluindo `python-dotenv`.
- Atualizar as instruções de setup no `README.md`.

## Capabilities

### New Capabilities
- `env-config`: Carregamento de variáveis de ambiente via `.env` para configuração local do Flask.
- `admin-reset`: Permitir reset de senha ou promoção de um administrador existente pelo script de bootstrap.

### Modified Capabilities
- *(nenhuma alteração de requisito em capabilities existentes)*

## Impact

- `app/__init__.py`: carregará `FLASK_SECRET_KEY` (e futuras variáveis) de `.env` usando `python-dotenv`.
- `scripts/create_admin.py`: passará a verificar duplicidade de email e oferecer reset/promoção.
- `requirements.txt`: nova dependência `python-dotenv`.
- `README.md`: instruções para criar `.env` a partir de `.env.example`.
