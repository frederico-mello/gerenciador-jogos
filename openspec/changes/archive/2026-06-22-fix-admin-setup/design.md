## Context

A aplicação Flask utiliza `FLASK_SECRET_KEY` para sessions e tokens CSRF. Atualmente, `app/__init__.py` lê essa variável de `os.environ`, mas não carrega um arquivo `.env`, o que gera o warning sobre chave insegura quando a variável está ausente. Além disso, o script `scripts/create_admin.py` foi pensado apenas para criar o primeiro administrador; quando um email já cadastrado é informado, ele encerra com erro, impedindo resets de senha ou promoções durante o setup.

## Goals / Non-Goals

**Goals:**
- Permitir configuração local via arquivo `.env` sem necessidade de exportar variáveis de ambiente manualmente.
- Eliminar o warning de `FLASK_SECRET_KEY` insegura em ambientes onde `.env` está corretamente configurado.
- Tornar `create_admin.py` robusto para cenários de recuperação/reconfiguração de acesso admin.
- Fornecer um `.env.example` versionável como template.

**Non-Goals:**
- Alterar o fluxo de login ou registro via interface web.
- Implementar um sistema completo de "esqueci minha senha".
- Mudar o banco de dados ou schema.
- Criar interface administrativa para reset de senha.

## Decisions

1. **Usar `python-dotenv` para carregar `.env`**
   - É a biblioteca padrão e leve para Flask.
   - Será chamada no topo de `app/__init__.py`, antes da leitura de `FLASK_SECRET_KEY`.
   - O fallback de chave insegura com warning será mantido apenas para desenvolvimento sem `.env`.

2. **Carregar `.env` apenas na factory `create_app()`**
   - Mantém o carregamento lazy e evita side-effects na importação do módulo `app`.
   - Assim testes continuam funcionando com `test_config` explícito.

3. **Reset/promoção no `create_admin.py` interativo**
   - Se o email existir e `role == 'admin_sistema'`: perguntar se deseja resetar a senha.
   - Se o email existir e `role != 'admin_sistema'`: perguntar se deseja promover para admin_sistema e resetar a senha.
   - O script nunca cria duplicatas nem altera dados sem confirmação explícita.

4. **Não criar o `.env` real automaticamente**
   - Por segurança, versionamos apenas `.env.example`.
   - O setup local continua demandando cópia manual para `.env`.

## Risks / Trade-offs

- [Risk] `load_dotenv()` pode sobrescrever variáveis já definidas no ambiente se não configurado corretamente. → Mitigation: usar `override=False` (comportamento padrão do `load_dotenv`) para dar prioridade às variáveis de ambiente reais.
- [Risk] O script `create_admin.py` continuará emitindo warning se rodado sem `.env`. → Mitigation: esse é o comportamento desejado — o warning incentiva configuração segura.
- [Risk] `python-dotenv` não é encontrado se o script for executado sem o venv ativado. → Mitigation: documentado no `README.md` e no `.env.example` que todo comando deve rodar com `.\.venv\Scripts\Activate.ps1` primeiro.

## Migration Plan

Não há migração de dados. Após o deploy:
1. Copiar `.env.example` para `.env`.
2. Definir um valor seguro para `FLASK_SECRET_KEY`.
3. Reexecutar `scripts/create_admin.py` conforme necessário.

## Open Questions

- Nenhuma.
