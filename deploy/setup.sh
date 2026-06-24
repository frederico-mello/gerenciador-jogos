#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/gerenciador-jogos"
REPO_URL="${REPO_URL:-}"

echo "============================================"
echo "  Gerenciador de Jogos — Deploy Automatizado"
echo "============================================"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "Execute como root: sudo bash deploy/setup.sh"
    exit 1
fi

if ! grep -qi 'ubuntu\|debian' /etc/os-release 2>/dev/null; then
    echo "Este script foi testado no Ubuntu 22.04+ e Debian 12+."
    read -rp "Deseja continuar mesmo assim? (s/N) " answer
    if [[ ! "$answer" =~ ^[sS]$ ]]; then
        exit 1
    fi
fi

echo ">>> Atualizando pacotes..."
apt update -qq
apt upgrade -y -qq

echo ">>> Instalando dependências do sistema..."
apt install -y -qq python3 python3-pip python3-venv nginx certbot python3-certbot-nginx ufw rsync

echo ""
read -rp "Qual é o domínio do servidor? (ex: jogos.exemplo.com) " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo "Domínio é obrigatório. Abortando."
    exit 1
fi

echo ">>> Criando diretório do projeto em $APP_DIR..."
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/instance"
mkdir -p "$APP_DIR/data"

if [ -n "$REPO_URL" ]; then
    echo ">>> Clonando repositório..."
    if [ -d "$APP_DIR/.git" ]; then
        git -C "$APP_DIR" pull
    else
        git clone "$REPO_URL" "$APP_DIR"
    fi
else
    echo ">>> Copiando arquivos do diretório atual para $APP_DIR..."
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
    rsync -a --exclude='.git' --exclude='venv' --exclude='__pycache__' --exclude='.pytest_cache' "$PROJECT_DIR/" "$APP_DIR/"
fi

echo ">>> Configurando ambiente virtual..."
python3 -m venv "$APP_DIR/venv"
source "$APP_DIR/venv/bin/activate"
pip install -U pip -q
pip install -r "$APP_DIR/requirements.txt" -q

if [ ! -f "$APP_DIR/.env" ]; then
    echo ">>> Criando .env..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > "$APP_DIR/.env" <<EOF
FLASK_SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
IMPORT_SOURCE_DIR=
EOF
    echo "    FLASK_SECRET_KEY gerada automaticamente."
    echo ""
    echo "    ATENÇÃO: Configure IMPORT_SOURCE_DIR e verifique .env se necessário."
    echo ""
else
    echo ">>> .env já existe — mantendo configuração atual."
fi

echo ">>> Ajustando permissões..."
chown -R www-data:www-data "$APP_DIR/instance" "$APP_DIR/data"
chown www-data:www-data "$APP_DIR/.env"
chmod 640 "$APP_DIR/.env"

echo ">>> Configurando Nginx (fase 1/3 — HTTP-only para bootstrapping)..."
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    rm /etc/nginx/sites-enabled/default
fi

cat > "/etc/nginx/sites-available/gerenciador-jogos" <<NGINX_HTTP
server {
    listen 80;
    server_name $DOMAIN;
    location / {
        return 200 'Gerenciador de Jogos — deploy em andamento...';
    }
}
NGINX_HTTP

if [ ! -L "/etc/nginx/sites-enabled/gerenciador-jogos" ]; then
    ln -s "/etc/nginx/sites-available/gerenciador-jogos" "/etc/nginx/sites-enabled/"
fi

nginx -t && systemctl reload nginx

echo ">>> Configurando firewall (UFW)..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable

echo ">>> Gerando certificado SSL com Let's Encrypt (fase 2/3)..."
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    certbot certonly --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN" || {
        echo ""
        echo "    AVISO: A geração do certificado falhou."
        echo "    Mantendo config HTTP-only para troubleshooting."
        echo "    Execute manualmente após configurar o DNS:"
        echo "      sudo certbot certonly --nginx -d $DOMAIN"
        echo "      sudo cp /opt/gerenciador-jogos/deploy/nginx.conf /etc/nginx/sites-available/gerenciador-jogos"
        echo "      sudo sed -i 's/server_name _;/server_name $DOMAIN;/g' /etc/nginx/sites-available/gerenciador-jogos"
        echo "      sudo sed -i 's/__DOMAIN__/$DOMAIN/g' /etc/nginx/sites-available/gerenciador-jogos"
        echo "      sudo nginx -t && sudo systemctl reload nginx"
        echo ""
        CERT_FAILED=1
    }
else
    echo "    Certificado já existe — pulando emissão."
fi

echo ">>> Instalando serviço Systemd..."
cp "$APP_DIR/deploy/gunicorn.service" "/etc/systemd/system/gerenciador-jogos.service"
systemctl daemon-reload
systemctl enable gerenciador-jogos
systemctl restart gerenciador-jogos

if [ -z "${CERT_FAILED:-}" ]; then
    echo ">>> Instalando config completa com SSL (fase 3/3)..."
    cp "$APP_DIR/deploy/nginx.conf" "/etc/nginx/sites-available/gerenciador-jogos"
    sed -i "s/server_name _;/server_name $DOMAIN;/g" "/etc/nginx/sites-available/gerenciador-jogos"
    sed -i "s/__DOMAIN__/$DOMAIN/g" "/etc/nginx/sites-available/gerenciador-jogos"
    nginx -t && systemctl reload nginx
fi

echo ">>> Configurando renovação automática do certificado..."
if systemctl list-units --type=timer | grep -q certbot.timer; then
    systemctl enable certbot.timer
    systemctl start certbot.timer
else
    (crontab -l 2>/dev/null || true; echo "0 3 * * * /usr/bin/certbot renew --quiet --no-self-upgrade") | crontab -
fi

echo ""
echo "============================================"
echo "  Deploy concluído!"
echo "============================================"
echo ""
echo "  Acesse: https://$DOMAIN"
echo ""
echo "  Serviços:"
echo "    sudo systemctl status gerenciador-jogos"
echo "    sudo systemctl status nginx"
echo ""
echo "  Logs:"
echo "    journalctl -u gerenciador-jogos -f"
echo "    tail -f /var/log/nginx/access.log"
echo ""
echo "  Backup do banco:"
echo "    cp $APP_DIR/instance/jogos.db $APP_DIR/instance/jogos.db.\$(date +%Y%m%d)"
echo ""
