## 1. Dependências e Entry Point

- [x] 1.1 Adicionar `gunicorn` ao `requirements.txt`
- [x] 1.2 Criar `wsgi.py` na raiz do projeto com `app = create_app()` e bloco `if __name__` para dev
- [x] 1.3 Atualizar `.env.example` com variáveis `FLASK_ENV`, `GUNICORN_WORKERS`, `GUNICORN_BIND`

## 2. Hardening da Aplicação

- [x] 2.1 Em `app/__init__.py`: quando `FLASK_ENV=production`, exigir `FLASK_SECRET_KEY` definida com mínimo de 32 caracteres (abortar startup se inválida)
- [x] 2.2 Em `app/__init__.py`: adicionar security headers via `@app.after_request` (X-Content-Type-Options, X-Frame-Options, Referrer-Policy) — fallback caso Nginx não esteja na frente
- [x] 2.3 Em `app/__init__.py`: garantir que `DEBUG` nunca é True em produção

## 3. Configuração do Gunicorn

- [x] 3.1 Criar `gunicorn.conf.py` na raiz: bind Unix socket (`/run/gunicorn.sock`), workers via `GUNICORN_WORKERS` env var (default: `2 * cores + 1`), timeout 30s, graceful timeout 30s, access log e error log para stdout/stderr
- [x] 3.2 Testar localmente: `gunicorn -c gunicorn.conf.py wsgi:app` deve iniciar sem erros (testar no servidor Linux — não roda em Windows)

## 4. Configuração do Nginx

- [x] 4.1 Criar `deploy/nginx.conf`: bloco server HTTP com redirect 301 para HTTPS, bloco server HTTPS com proxy_pass para socket do Gunicorn, location blocks para `/static/` e `/data/` servindo arquivos direto do disco
- [x] 4.2 Adicionar security headers no Nginx: HSTS (1 ano, includeSubDomains), X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Content-Security-Policy baseline
- [x] 4.3 Configurar `client_max_body_size` para 32M (compatível com MAX_CONTENT_LENGTH do Flask)

## 5. Serviço Systemd

- [x] 5.1 Criar `deploy/gunicorn.service`: User=www-data, ExecStart com gunicorn -c gunicorn.conf.py wsgi:app, Restart=always, RestartSec=5, WorkingDirectory apontando para o diretório do projeto
- [x] 5.2 Configurar EnvironmentFile para carregar `.env` do projeto

## 6. Script de Deploy

- [x] 6.1 Criar `deploy/setup.sh`: instalar Python 3, pip, Nginx, Certbot via apt
- [x] 6.2 No setup.sh: criar diretório do projeto em `/opt/gerenciador-jogos`, clonar repositório ou copiar arquivos
- [x] 6.3 No setup.sh: criar venv, instalar requirements, configurar permissões (www-data dono de instance/ e data/)
- [x] 6.4 No setup.sh: perguntar domínio, copiar nginx.conf para sites-available, gerar certificado com certbot, habilitar site
- [x] 6.5 No setup.sh: copiar gunicorn.service para /etc/systemd/, habilitar e iniciar serviço
- [x] 6.6 No setup.sh: configurar UFW (allow 22, 80, 443, deny default incoming)
- [x] 6.7 No setup.sh: configurar renovação automática do certificado (certbot renew --quiet via systemd timer ou cron)

## 7. Documentação

- [x] 7.1 Atualizar README.md com seção "Deploy em Produção" contendo: pré-requisitos, passos de instalação, variáveis de ambiente de produção, como verificar status dos serviços, processo de backup do SQLite
- [x] 7.2 Adicionar seção "Desenvolvimento Local" no README (flask run continua funcionando normalmente)
