## 1. Corrigir nginx.conf

- [x] 1.1 Substituir `listen 443 ssl;` + `http2 on;` por `listen 443 ssl http2;` no bloco HTTPS
- [x] 1.2 Substituir caminhos `/etc/letsencrypt/live/$host/` por `/etc/letsencrypt/live/__DOMAIN__/` no template

## 2. Corrigir setup.sh

- [x] 2.1 Adicionar `rsync` à lista de pacotes instalados via `apt`
- [x] 2.2 Adicionar comando `sed` para substituir `__DOMAIN__` pelo domínio informado no arquivo Nginx
- [x] 2.3 Corrigir `systemctl enable gunicorn` para `systemctl enable gerenciador-jogos`
- [x] 2.4 Corrigir `systemctl restart gunicorn` para `systemctl restart gerenciador-jogos`
- [x] 2.5 Atualizar mensagens finais com `sudo systemctl status gerenciador-jogos` e `journalctl -u gerenciador-jogos -f`
- [x] 2.6 Adicionar `nginx -t` após substituições de domínio/certificado para validar configuração

## 3. Resolver dependência circular de bootstrapping SSL

- [x] 3.1 Refatorar o bloco "Configurando Nginx" do `setup.sh` para implementar fluxo two-phase:
  - Fase 1: escrever config HTTP-only temporária em `/etc/nginx/sites-available/gerenciador-jogos`
  - Validar com `nginx -t` e recarregar Nginx
- [x] 3.2 Alterar `certbot --nginx` para `certbot certonly --nginx` (emitir cert sem modificar config)
- [x] 3.3 Envolver `certbot certonly` em `if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]` para idempotência
- [x] 3.4 Após certbot, copiar `nginx.conf` completo, substituir `__DOMAIN__` e `server_name`, validar com `nginx -t` e recarregar
- [x] 3.5 Tratar falha do certbot: se falhar, manter config HTTP-only e avisar (não instalar config SSL quebrada)

## 4. Testar e Documentar

- [ ] 4.1 Executar setup.sh corrigido em servidor de teste (se disponível)
- [ ] 4.2 Confirmar que `sudo nginx -t` passa sem erros em todas as fases
- [ ] 4.3 Confirmar que o serviço `gerenciador-jogos` inicia e o site é acessível via HTTPS
