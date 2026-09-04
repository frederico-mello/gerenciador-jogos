## MODIFIED Requirements

### Requirement: Configuração Nginx como proxy reverso com HTTPS
O sistema SHALL fornecer um arquivo `deploy/nginx.conf` com configuração de proxy reverso: redirect HTTP→HTTPS, `listen 443 ssl http2;` (compatível com Nginx 1.22+), caminhos de certificado SSL com placeholders genéricos `__SSL_CERT__` e `__SSL_KEY__` substituíveis pelo script de setup (Let's Encrypt ou self-signed), proxy para o socket do Gunicorn, serving de arquivos estáticos e de dados, e security headers.

#### Scenario: Request HTTP é redirecionado para HTTPS
- **WHEN** um cliente faz `GET http://exemplo.com/`
- **THEN** o Nginx responde com HTTP 301 para `https://exemplo.com/`

#### Scenario: Request HTTPS para rota dinâmica é proxied para Gunicorn
- **WHEN** um cliente faz `GET https://exemplo.com/`
- **THEN** o Nginx proxya o request para o socket do Gunicorn e retorna a resposta

#### Scenario: Request para arquivo estático é servido diretamente pelo Nginx
- **WHEN** um cliente faz `GET https://exemplo.com/static/style.css`
- **THEN** o Nginx serve o arquivo diretamente do disco, sem envolver o Gunicorn

#### Scenario: Request para arquivo de dados (imagem) é servido pelo Nginx
- **WHEN** um cliente faz `GET https://exemplo.com/media/anatomia/jogo-slug/foto.jpg`
- **THEN** o Nginx serve a imagem diretamente do diretório `data/`

#### Scenario: Security headers presentes em todas as respostas
- **WHEN** o Nginx responde qualquer request
- **THEN** os headers `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e `Content-Security-Policy` estão presentes

#### Scenario: Configuração compatível com Nginx 1.22
- **WHEN** o template `deploy/nginx.conf` é processado pelo Nginx 1.22.1
- **THEN** a diretiva `listen 443 ssl http2;` é aceita sem erro de "unknown directive"

#### Scenario: Caminhos do certificado usam placeholders genéricos
- **WHEN** o template `deploy/nginx.conf` é examinado
- **THEN** as diretivas `ssl_certificate` e `ssl_certificate_key` usam os placeholders `__SSL_CERT__` e `__SSL_KEY__`, que são substituídos pelo script de setup com os paths reais

#### Scenario: Config funciona com Let's Encrypt
- **WHEN** o setup emite certificado via Let's Encrypt
- **THEN** os placeholders são substituídos por `/etc/letsencrypt/live/$DOMAIN/fullchain.pem` e `/etc/letsencrypt/live/$DOMAIN/privkey.pem`

#### Scenario: Config funciona com self-signed cert
- **WHEN** o Let's Encrypt falha e o setup gera self-signed cert
- **THEN** os placeholders são substituídos por `/etc/nginx/ssl/self-signed.crt` e `/etc/nginx/ssl/self-signed.key`

### Requirement: Script de setup automatizado para o servidor
O sistema SHALL fornecer um script `deploy/setup.sh` que automatiza a instalação em um servidor Ubuntu 22.04+ limpo: instala Python, Nginx, Certbot, rsync, cria usuário dedicado, copia configurações, substitui os placeholders `__SSL_CERT__` e `__SSL_KEY__` pelo path do certificado apropriado, gera certificado Let's Encrypt (ou self-signed como fallback), inicia os serviços e usa o nome correto do serviço Systemd (`gerenciador-jogos`). O script SHALL usar um fluxo two-phase para bootstrapping SSL: primeiro deploya uma config Nginx HTTP-only temporária, emite o certificado, e só então instala a config completa com SSL.

#### Scenario: Setup completo em servidor limpo
- **WHEN** um administrador executa `sudo bash deploy/setup.sh` em um Ubuntu 22.04 limpo
- **THEN** todas as dependências são instaladas, Nginx configurado, certificado SSL gerado, e o serviço `gerenciador-jogos` está rodando

#### Scenario: Setup solicita domínio
- **WHEN** o script é executado
- **THEN** ele pergunta "Qual é o domínio do servidor?" e usa a resposta para configurar Nginx e o certificado

#### Scenario: Setup é idempotente
- **WHEN** o script é executado novamente após setup bem-sucedido
- **THEN** ele atualiza as configurações sem erros, reinicia os serviços e mantém certificados existentes

#### Scenario: Nome correto do serviço Systemd
- **WHEN** o setup configura o Systemd
- **THEN** o arquivo `/etc/systemd/system/gerenciador-jogos.service` é criado e os comandos `systemctl` usam `gerenciador-jogos`

#### Scenario: Bootstrapping SSL em duas fases
- **WHEN** o setup é executado em um servidor sem certificado SSL existente
- **THEN** o script primeiro instala uma config Nginx HTTP-only (sem diretivas `ssl_certificate`), valida com `nginx -t`, emite o certificado via `certbot certonly --nginx`, e só então instala a config completa com SSL

#### Scenario: nginx -t passa em todas as fases
- **WHEN** o setup executa `nginx -t` durante o bootstrapping SSL
- **THEN** `nginx -t` passa sem erros tanto na fase HTTP-only (sem certificados referenciados) quanto na fase final (com certificados já emitidos)

#### Scenario: Certbot não modifica a config do Nginx
- **WHEN** o setup emite o certificado
- **THEN** o script usa `certbot certonly --nginx` (não `certbot --nginx`), para que o Certbot apenas emita o certificado sem alterar a config do Nginx

#### Scenario: Reexecução quando certificado já existe
- **WHEN** o setup é reexecutado e `/etc/letsencrypt/live/$DOMAIN` já existe
- **THEN** o script pula a emissão do certificado e prossegue direto para a instalação da config completa

#### Scenario: Fallback para self-signed cert quando Let's Encrypt falha
- **WHEN** o `certbot certonly --nginx` falha (ex: firewall bloqueia porta 80 da internet)
- **THEN** o script gera um certificado self-signed com `openssl` em `/etc/nginx/ssl/` e deploya a config completa do Nginx usando os paths do self-signed — o site funciona internamente com HTTPS (browser mostra warning de certificado não confiável)

#### Scenario: Transição de self-signed para Let's Encrypt
- **WHEN** o setup é reexecutado após as portas serem abertas na rede
- **THEN** o script detecta que `/etc/letsencrypt/live/$DOMAIN` não existe, roda o certbot com sucesso, e a config completa passa a usar o certificado Let's Encrypt — o warning do browser desaparece

#### Scenario: Aviso sobre certificado self-signed
- **WHEN** o setup gera um self-signed cert como fallback
- **THEN** o script exibe uma mensagem informando que o certificado é autoassinado, que o site funcionará internamente com warning de browser, e como obter um certificado Let's Encrypt quando as portas forem abertas

### Requirement: Logging de produção
O sistema SHALL configurar logging do Gunicorn para stdout/stderr (capturado pelo journalctl) com formato contendo timestamp, nível, e mensagem. O Nginx SHALL logar acesso e erros em `/var/log/nginx/`.

#### Scenario: Log de request no journalctl
- **WHEN** um request é processado pelo Gunicorn
- **THEN** uma linha de log com timestamp, method, path, status code e tempo de resposta aparece no `journalctl -u gerenciador-jogos`

#### Scenario: Log de erro no journalctl
- **WHEN** uma exceção não tratada ocorre na aplicação
- **THEN** o traceback completo aparece no `journalctl -u gerenciador-jogos`

## ADDED Requirements

*(nenhuma)*

## REMOVED Requirements

*(nenhuma)*
