## Why

O script `deploy/setup.sh` e o template `deploy/nginx.conf` gerados no change `production-deploy` contêm bugs que impedem o deploy de funcionar corretamente em servidores Debian 12: (1) o Nginx não aceita `http2 on;` na versão 1.22; (2) os caminhos dos certificados SSL usam a variável `$host`, que o Nginx não expande em `ssl_certificate`; (3) o script referencia o serviço Systemd como `gunicorn` mas o arquivo copiado é `gerenciador-jogos.service`; (4) **dependência circular (chicken-and-egg)**: a config completa do Nginx (com SSL) é instalada *antes* do certificado existir, fazendo `nginx -t` falhar, o que por sua vez impede o `certbot --nginx` de emitir o certificado — o erro persiste mesmo após as correções 1-3. Esses erros causam falha na geração do certificado SSL e erro `SSL_ERROR_INTERNAL_ERROR_ALERT` no navegador.

## What Changes

- Corrigir `deploy/nginx.conf`: usar `listen 443 ssl http2;` ao invés de `http2 on;`
- Corrigir caminhos dos certificados SSL em `deploy/nginx.conf` usando placeholder `__DOMAIN__` substituível pelo script
- Corrigir `deploy/setup.sh` para substituir `__DOMAIN__` no arquivo do Nginx
- Corrigir todos os comandos Systemd de `gunicorn` para `gerenciador-jogos`
- Adicionar teste/validação de `nginx -t` após ajustar certificados
- **Resolver a dependência circular SSL**: o `setup.sh` SHALL deployar uma config Nginx HTTP-only temporária antes de rodar o certbot, e só depois instalar a config completa com SSL — garantindo que `nginx -t` passe em todas as fases

## Capabilities

### New Capabilities
- *(nenhuma)*

### Modified Capabilities
- `production-infra`: Ajustar requisitos do Nginx e do script de deploy para refletir a configuração corrigida e o fluxo two-phase de bootstrapping SSL

## Impact

- Arquivos alterados: `deploy/nginx.conf`, `deploy/setup.sh`
- Sem impacto na aplicação Flask — só corrige a infraestrutura de deploy
- O próximo deploy deverá funcionar sem erros SSL no Debian 12
