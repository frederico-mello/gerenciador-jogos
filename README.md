# Gerenciador de Jogos

CRUD local de jogos educacionais (anatomia, histologia, microbiologia) com Flask + SQLite.

## Desenvolvimento Local

```powershell
pip install -r requirements.txt
```

### Variáveis de ambiente

Copie `.env.example` para `.env` e defina uma `FLASK_SECRET_KEY` segura:

```powershell
cp .env.example .env
```

Gere uma chave com:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Cole o valor gerado no `.env`:

```
FLASK_SECRET_KEY=seu-token-hex-aqui
```

### Inicializar banco

```powershell
python scripts\init_db.py
```

Cria `instance\jogos.db` (vazio).

### Importar jogos do Downloads

```powershell
python scripts\import_from_downloads.py
```

Varre `IMPORT_SOURCE_DIR` (definido no `.env`) para as 3 áreas, copia e redimensiona imagens para `data\<area>\<jogo-slug>\`, converte DOCX para Markdown, e popula o banco. **Idempotente**: re-executar não duplica.

### Rodar o servidor de desenvolvimento (Flask)

```powershell
flask run
```

Abra `http://localhost:5000`.

### Testes

```powershell
python -m pytest
```

---

## Deploy em Produção

### Pré-requisitos

- **Servidor Linux** (Ubuntu 22.04+ ou Debian 12+)
- **Domínio** apontando para o IP do servidor
- Acesso **root** (sudo) ao servidor

### Stack de Produção

```
Internet → UFW (443) → Nginx (HTTPS + static) → Gunicorn (socket) → Flask + SQLite
```

- **Gunicorn**: WSGI server com workers pré-fork
- **Nginx**: Proxy reverso, HTTPS (Let's Encrypt), serve arquivos estáticos
- **Systemd**: Gerencia o processo Gunicorn (auto-start, restart)
- **UFW**: Firewall — apenas portas 22, 80, 443

### Variáveis de Ambiente de Produção

| Variável | Obrigatória | Default | Descrição |
|----------|-------------|---------|-----------|
| `FLASK_ENV` | Não | `development` | Em produção, use `production` |
| `FLASK_SECRET_KEY` | **Sim** (produção) | — | Mínimo 32 caracteres. Gere com `python -c "import secrets; print(secrets.token_hex(32))"` |
| `GUNICORN_WORKERS` | Não | `2 * CPU_cores + 1` | Número de workers do Gunicorn |
| `GUNICORN_BIND` | Não | `unix:/run/gunicorn.sock` | Endereço do socket |
| `IMPORT_SOURCE_DIR` | Não | — | Diretório de origem para o importador |

Em **produção**, o sistema **recusa iniciar** se `FLASK_SECRET_KEY` não estiver definida ou tiver menos de 32 caracteres.

### Instalação Automática

No servidor Ubuntu/Debian:

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/gerenciador-jogos.git /opt/gerenciador-jogos
cd /opt/gerenciador-jogos

# Execute o script de deploy
sudo bash deploy/setup.sh
```

O script vai:
1. Instalar Python 3, pip, Nginx, Certbot e UFW
2. Solicitar o domínio do servidor
3. Criar ambiente virtual e instalar dependências
4. Gerar `FLASK_SECRET_KEY` automaticamente
5. Configurar Nginx com HTTPS (Let's Encrypt)
6. Configurar serviço Systemd para o Gunicorn
7. Configurar UFW (portas 22, 80, 443)
8. Configurar renovação automática do certificado SSL

### Instalação Manual

```bash
# 1. Copiar arquivos para /opt/gerenciador-jogos
# 2. Criar ambiente virtual
python3 -m venv /opt/gerenciador-jogos/venv
source /opt/gerenciador-jogos/venv/bin/activate
pip install -r /opt/gerenciador-jogos/requirements.txt

# 3. Configurar .env
cp .env.example /opt/gerenciador-jogos/.env
# Editar FLASK_SECRET_KEY e FLASK_ENV=production

# 4. Configurar Nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/gerenciador-jogos
sudo sed -i "s/server_name _;/server_name seu-dominio.com;/g" /etc/nginx/sites-available/gerenciador-jogos
sudo ln -s /etc/nginx/sites-available/gerenciador-jogos /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default 2>/dev/null
sudo certbot --nginx -d seu-dominio.com

# 5. Configurar serviço Systemd
sudo cp deploy/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn

# 6. Configurar firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Verificar Status dos Serviços

```bash
# Gunicorn
sudo systemctl status gunicorn
journalctl -u gunicorn -f   # logs em tempo real

# Nginx
sudo systemctl status nginx
sudo nginx -t               # testar configuração
```

### Backup do Banco SQLite

O banco fica em `instance/jogos.db`. Para backup:

```bash
cp /opt/gerenciador-jogos/instance/jogos.db /opt/gerenciador-jogos/instance/jogos.db.$(date +%Y%m%d)

# Restaurar:
cp /opt/gerenciador-jogos/instance/jogos.db.<data> /opt/gerenciador-jogos/instance/jogos.db
```

### Scripts administrativos em produção

Em produção, `.env`, `instance/`, e `data/` pertencem ao usuário `www-data` (configurado por `deploy/setup.sh` e usado pelo serviço Systemd do Gunicorn). **Scripts administrativos DEVEM ser invocados como `www-data`**, nunca diretamente como outro usuário.

Rodar um script admin como outro usuário causa dois problemas:

1. **`PermissionError` ao ler `.env`** (modo `640`, somente legível por `www-data`).
2. **Worse**: arquivos criados pelo script (`instance/jogos.db`, conteúdo em `data/`) ficam com owner errado, e o Gunicorn (rodando como `www-data`) então quebra em produção com erro de permissão no banco ou nos arquivos.

Use o wrapper `scripts/run-as-app.sh`, que executa o Python do venv como `www-data`:

```bash
cd /opt/gerenciador-jogos

# Criar admin inicial (interactive)
./scripts/run-as-app.sh scripts/create_admin.py

# Inicializar banco vazio
./scripts/run-as-app.sh scripts/init_db.py

# Importar jogos do diretório de Downloads
./scripts/run-as-app.sh scripts/import_from_downloads.py
```

Cada script tem um guarda embutido que termina com erro claro (`ERRO: este script deve ser rodado como 'www-data'...`) se invocado por outro usuário, antes de qualquer efeito colateral — então não é possível acidentalmente criar arquivos com owner errado.

#### Runbook: corrigir ownership de `jogos.db` após execução acidental

Se `scripts/create_admin.py` ou `scripts/init_db.py` foi executado diretamente (sem o wrapper) por outro usuário no passado, o `instance/jogos.db` pode ter owner errado. Verifique:

```bash
ls -la /opt/gerenciador-jogos/instance/jogos.db
# Esperado: -rw-r--r-- ... www-data www-data ... jogos.db
```

Se o owner NÃO for `www-data:www-data`, corrija:

```bash
sudo chown www-data:www-data /opt/gerenciador-jogos/instance/jogos.db
sudo systemctl restart gerenciador-jogos
```

---

## Estrutura do Projeto

- `app/` — aplicação Flask (db, models, routes, importer, templates, static)
- `data/` — imagens e descrições normalizadas (geradas pelo importer)
- `instance/jogos.db` — banco SQLite
- `deploy/` — arquivos de configuração para produção (nginx, systemd, setup)
- `wsgi.py` — entry point para o Gunicorn
- `gunicorn.conf.py` — configuração do Gunicorn
- `scripts/` — CLIs (init_db, import_from_downloads)
- `tests/` — pytest
- `openspec/` — specs e change proposals (OpenSpec)
