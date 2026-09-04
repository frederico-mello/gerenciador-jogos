## Why

O script `deploy/setup.sh` e o template `deploy/nginx.conf` gerados no change `production-deploy` contêm bugs que impedem o deploy de funcionar corretamente em servidores Debian 12: (1) o Nginx não aceita `http2 on;` na versão 1.22; (2) os caminhos dos certificados SSL usam a variável `$host`, que o Nginx não expande em `ssl_certificate`; (3) o script referencia o serviço Systemd como `gunicorn` mas o arquivo copiado é `gerenciador-jogos.service`; (4) **dependência circular (chicken-and-egg)**: a config completa do Nginx (com SSL) é instalada *antes* do certificado existir, fazendo `nginx -t` falhar, o que por sua vez impede o `certbot --nginx` de emitir o certificado; (5) **firewall externo bloqueia portas 80/443 da internet**, impedindo o Let's Encrypt de validar via HTTP-01 challenge — o site precisa funcionar internamente com self-signed cert enquanto as portas não são abertas.

## What Changes

- Corrigir `deploy/nginx.conf`: usar `listen 443 ssl http2;` ao invés de `http2 on;`
- Corrigir caminhos dos certificados SSL em `deploy/nginx.conf` usando placeholders genéricos `__SSL_CERT__` e `__SSL_KEY__` substituíveis pelo script
- Corrigir `deploy/setup.sh` para substituir os placeholders no arquivo do Nginx
- Corrigir todos os comandos Systemd de `gunicorn` para `gerenciador-jogos`
- Adicionar teste/validação de `nginx -t` após ajustar certificados
- **Resolver a dependência circular SSL**: o `setup.sh` SHALL deployar uma config Nginx HTTP-only temporária antes de rodar o certbot, e só depois instalar a config completa com SSL
- **Fallback de self-signed cert**: quando o Let's Encrypt falha (ex: firewall bloqueia portas), o `setup.sh` SHALL gerar um certificado self-signed com `openssl` e deployar a config completa mesmo assim — o site funciona internamente (com warning de browser), e quando as portas forem abertas, re-executar o setup obtém um certificado Let's Encrypt válido

## Capabilities

### New Capabilities
- *(nenhuma)*

### Modified Capabilities
- `production-infra`: Ajustar requisitos do Nginx e do script de deploy para refletir a configuração corrigida, o fluxo two-phase de bootstrapping SSL, e o fallback de self-signed cert

## Impact

- Arquivos alterados: `deploy/nginx.conf`, `deploy/setup.sh`
- Sem impacto na aplicação Flask — só corrige a infraestrutura de deploy
- O deploy funciona internamente com self-signed cert imediatamente
- Quando as portas forem abertas, re-executar o setup troca para Let's Encrypt automaticamente
