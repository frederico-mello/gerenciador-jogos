## MODIFIED Requirements

### Requirement: Configuração Nginx como proxy reverso com HTTPS
O sistema SHALL fornecer um arquivo `deploy/nginx.conf` com configuração de proxy reverso: redirect HTTP→HTTPS, `listen 443 ssl http2;` (compatível com Nginx 1.22+), caminhos de certificado SSL com placeholders genéricos `__SSL_CERT__` e `__SSL_KEY__` substituíveis pelo script de setup (Let's Encrypt ou self-signed), proxy para o socket do Gunicorn, serving de arquivos estáticos e de dados, e security headers. O location `/media/` SHALL emitir respostas com `Cache-Control: no-cache` (sem `expires` longo), de modo que a validade de uma imagem em cache fique sob controle da aplicação via cache-busting (`?v=updated_at`), e não de um TTL fixo.

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

#### Scenario: Resposta de /media/ não é cacheável por TTL longo
- **WHEN** o Nginx responde um request para `/media/<area>/<slug>/perfil.jpg`
- **THEN** a resposta contém `Cache-Control` com `no-cache` e NÃO contém `expires 7d` (nem outro TTL longo), permitindo revalidação imediata após re-upload

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