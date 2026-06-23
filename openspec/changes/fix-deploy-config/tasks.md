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

## 3. Testar e Documentar

- [ ] 3.1 Executar setup.sh corrigido em servidor de teste (se disponível)
- [ ] 3.2 Confirmar que `sudo nginx -t` passa sem erros
- [ ] 3.3 Confirmar que o serviço `gerenciador-jogos` inicia e o site é acessível via HTTPS
