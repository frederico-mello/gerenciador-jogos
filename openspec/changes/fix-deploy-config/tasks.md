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

## 4. Mover UFW antes do certbot

- [x] 4.1 Reordenar setup.sh: UFW (abrir portas 80, 443, 22) antes de rodar certbot

## 5. Fallback de self-signed cert

- [x] 5.1 Trocar placeholders `__DOMAIN__` no nginx.conf por `__SSL_CERT__` e `__SSL_KEY__` (genéricos)
- [x] 5.2 Atualizar setup.sh: Phase 3 SEMPRE executa (remover guarda `if CERT_FAILED`)
- [x] 5.3 Atualizar setup.sh: determinar paths do certificado baseado no resultado do certbot
- [x] 5.4 Adicionar geração de self-signed cert com `openssl req -x509` quando certbot falha (path: `/etc/nginx/ssl/`)
- [x] 5.5 Atualizar comandos `sed` para usar `__SSL_CERT__`/`__SSL_KEY__` com delimiter `|` (paths contêm `/`)
- [x] 5.6 Simplificar mensagem de falha do certbot (indicar self-signed, como trocar depois)

## 6. Testar internamente

- [ ] 6.1 Commit, pull no servidor, e re-executar `setup.sh`
- [ ] 6.2 Confirmar que `curl -k https://localhost/` retorna a aplicação (ignorando warning SSL)
- [ ] 6.3 Confirmar que `curl http://localhost/` redireciona para HTTPS
- [ ] 6.4 Confirmar que o site abre no browser internamente (com warning de cert self-signed)
