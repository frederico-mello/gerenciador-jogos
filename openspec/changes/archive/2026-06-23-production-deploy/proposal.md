## Why

A aplicação roda atualmente com o servidor de desenvolvimento do Flask (`flask run`), que é single-threaded, inseguro e impróbil para uso em produção. O warning "Do not use it in a production deployment" aparece a cada execução. Para colocar o sistema acessível na internet em um servidor Linux próprio, precisamos de uma stack de produção robusta com WSGI server, proxy reverso HTTPS e hardening de segurança.

## What Changes

- Adicionar **Gunicorn** como servidor WSGI de produção (substitui `flask run`)
- Criar **entry point WSGI** (`wsgi.py`) para o Gunicorn carregar a aplicação
- Configurar **Nginx** como proxy reverso com HTTPS (Let's Encrypt), serving de arquivos estáticos e headers de segurança
- Criar **serviço Systemd** para gerenciar o processo Gunicorn (auto-start, restart on failure)
- Adicionar **configuração dedicada do Gunicorn** (`gunicorn.conf.py`) com workers, logging e socket
- Adicionar **script de setup automatizado** (`deploy/setup.sh`) para instalação no servidor
- Endurecer a aplicação: forçar `FLASK_SECRET_KEY` obrigatória em produção, desabilitar debug, adicionar security headers
- Documentar processo de deploy no README

## Capabilities

### New Capabilities
- `production-infra`: Configuração de infraestrutura de produção — Gunicorn, Nginx, Systemd, firewall, HTTPS, script de deploy automatizado

### Modified Capabilities
- `env-config`: Adicionar variáveis de ambiente específicas de produção (FLASK_ENV, GUNICORN_WORKERS, domínio)

## Impact

- **Dependências novas**: `gunicorn` adicionado ao `requirements.txt`
- **Arquivos novos**: `wsgi.py`, `gunicorn.conf.py`, `deploy/nginx.conf`, `deploy/gunicorn.service`, `deploy/setup.sh`
- **Arquivos modificados**: `app/__init__.py` (security headers, validação de produção), `requirements.txt`, `.env.example`, `README.md`
- **Sistema**: Requer servidor Linux (Ubuntu 22.04+) com sudo, domínio apontando para o IP do servidor
- **Sem breaking changes**: O `flask run` continua funcionando para desenvolvimento local
