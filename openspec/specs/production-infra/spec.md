# Capability: production-infra

## Purpose

Infraestrutura de produção para servir a aplicação Flask: WSGI server (Gunicorn), proxy reverso (Nginx) com HTTPS (Let's Encrypt), gerenciamento de processo (Systemd), script de setup automatizado, firewall (UFW), e logging.

## Requirements

### Requirement: WSGI entry point para Gunicorn
O sistema SHALL fornecer um módulo `wsgi.py` na raiz do projeto que importa e expõe o objeto `app` criado por `create_app()`, servindo como entry point para o Gunicorn.

#### Scenario: Gunicorn carrega a aplicação via wsgi.py
- **WHEN** o Gunicorn é iniciado com `gunicorn wsgi:app`
- **THEN** a aplicação Flask é carregada corretamente e responde a requests HTTP

#### Scenario: wsgi.py funciona standalone para testes
- **WHEN** um desenvolvedor executa `python wsgi.py`
- **THEN** o servidor de desenvolvimento do Flask inicia em modo debug (apenas para desenvolvimento local)

### Requirement: Configuração dedicada do Gunicorn
O sistema SHALL fornecer um arquivo `gunicorn.conf.py` na raiz do projeto com configurações de produção: bind via Unix socket em `/run/gerenciador-jogos/gunicorn.sock`, workers configuráveis via env var, logging para stdout/stderr, timeout de 30 segundos, e graceful shutdown.

#### Scenario: Gunicorn inicia com configuração padrão
- **WHEN** o Gunicorn é iniciado com `gunicorn -c gunicorn.conf.py wsgi:app`
- **THEN** ele escuta no socket `/run/gerenciador-jogos/gunicorn.sock` com `2 * CPU_cores + 1` workers

#### Scenario: Número de workers configurável via env var
- **WHEN** a variável `GUNICORN_WORKERS` está definida como `4`
- **THEN** o Gunicorn inicia com exatamente 4 workers

#### Scenario: Socket path configurável via env var
- **WHEN** a variável `GUNICORN_BIND` está definida como `0.0.0.0:8000`
- **THEN** o Gunicorn escuta em TCP em vez de Unix socket

### Requirement: Serviço Systemd para gerenciamento do processo
O sistema SHALL fornecer um unit file `deploy/gunicorn.service` que gerencia o processo Gunicorn como serviço do Systemd: auto-start no boot, restart automático em caso de falha, usuário dedicado `www-data`, logs via journalctl, `RuntimeDirectory=gerenciador-jogos` para criar `/run/gerenciador-jogos/` com permissões corretas, e `ExecStartPre` para remover sockets stale antes de iniciar.

#### Scenario: Serviço inicia automaticamente no boot
- **WHEN** o servidor Linux é reiniciado
- **THEN** o serviço Gunicorn inicia automaticamente após o boot

#### Scenario: Serviço reinicia após crash
- **WHEN** o processo Gunicorn morre inesperadamente
- **THEN** o Systemd reinicia o serviço automaticamente dentro de 10 segundos

#### Scenario: Logs acessíveis via journalctl
- **WHEN** um administrador executa `journalctl -u gunicorn`
- **THEN** os logs de acesso e erro do Gunicorn são exibidos

#### Scenario: RuntimeDirectory cria diretório do socket com permissões corretas
- **WHEN** o serviço Systemd inicia
- **THEN** o diretório `/run/gerenciador-jogos/` é criado com owner `www-data:www-data` antes do Gunicorn iniciar, permitindo a criação do socket sem erro de permissão

#### Scenario: Socket stale é removido antes de iniciar
- **WHEN** existe um socket `/run/gerenciador-jogos/gunicorn.sock` residual de uma execução anterior
- **THEN** o `ExecStartPre` remove o socket antes de iniciar o Gunicorn, evitando conflito

#### Scenario: RuntimeDirectory é limpo quando o serviço para
- **WHEN** o serviço Systemd para
- **THEN** o diretório `/run/gerenciador-jogos/` e seu conteúdo são removidos automaticamente pelo systemd

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

### Requirement: Firewall com UFW
O sistema SHALL configurar o UFW (Uncomplicated Firewall) para permitir apenas as portas 22 (SSH), 80 (HTTP) e 443 (HTTPS), negando todo o tráfego entrante por padrão.

#### Scenario: Apenas portas necessárias abertas
- **WHEN** o setup é concluído
- **THEN** `sudo ufw status` mostra apenas portas 22, 80 e 443 como ALLOW

#### Scenario: Porta do Gunicorn não exposta externamente
- **WHEN** um cliente tenta conectar diretamente na porta 8000 do servidor
- **THEN** a conexão é recusada pelo firewall

### Requirement: Wrapper para invocação de scripts administrativos como o usuário da aplicação

O sistema SHALL fornecer um script `scripts/run-as-app.sh` (bash) que executa um script Python arbitrário passado como argumento usando o interpretador do venv do projeto, como o usuário `www-data` (via `sudo -u www-data`), derivando o diretório-raiz do projeto a partir da localização do próprio wrapper (não hardcoded).

#### Scenario: Invocação canônica de script administrativo
- **WHEN** um operador executa `./scripts/run-as-app.sh scripts/create_admin.py` no servidor de produção
- **THEN** o wrapper invoca `sudo -u www-data "$APP_DIR/venv/bin/python" scripts/create_admin.py`, onde `$APP_DIR` é resolvido como o diretório-pai do diretório que contém o wrapper

#### Scenario: Argumentos do script são repassados
- **WHEN** um operador executa `./scripts/run-as-app.sh scripts/create_admin.py --nome "Alice" --email a@b.c --senha "123"`
- **THEN** todos os argumentos após o nome do script são repassados intactos ao Python

#### Scenario: Wrapper funciona independente do path de produção
- **WHEN** o projeto está clonado em `/opt/meu-staging/gerenciador-jogos` e o operador executa `./scripts/run-as-app.sh scripts/init_db.py` a partir desse clone
- **THEN** o wrapper resolve `APP_DIR=/opt/meu-staging/gerenciador-jogos` e usa `/opt/meu-staging/gerenciador-jogos/venv/bin/python`, sem depender de path hardcoded

#### Scenario: Falha explícita quando sudo não está disponível
- **WHEN** o wrapper é executado e o `sudo` não consegue escalar para `www-data` (ex.: usuário sem permissão sudo)
- **THEN** o wrapper termina com código não-zero, propagando a mensagem de erro do `sudo` (sem swallowing silencioso)

### Requirement: Guarda de usuário com falha rápida e mensagem acionável em scripts administrativos

Cada script administrativo (`scripts/create_admin.py`, `scripts/init_db.py`, `scripts/import_from_downloads.py`) SHALL verificar, antes de qualquer import da aplicação ou chamada a `init_db()`/`create_app()`, que está sendo executado como o usuário `www-data`, terminando com código de saída não-zero e mensagem indicando o uso do wrapper caso contrário.

#### Scenario: Script invocado por usuário não-www-data falha com mensagem acionável
- **WHEN** um usuário que não seja `www-data` (ex.: `frederico`) executa `python scripts/create_admin.py`
- **THEN** o script termina imediatamente com código de saída 1 e imprime uma mensagem em stderr mencionando o uso de `./scripts/run-as-app.sh scripts/create_admin.py`, sem executar `init_db()`, `create_app()`, nem qualquer acesso a `.env` ou banco de dados

#### Scenario: Script invocado via wrapper como www-data prossegue normalmente
- **WHEN** o script é executado via `./scripts/run-as-app.sh scripts/create_admin.py`
- **THEN** o guarda detecta usuário `www-data` e permite que o script continue sua execução normal (prompt por credenciais, criação de admin, etc.)

#### Scenario: Guarda executa antes de qualquer side-effect persistente
- **WHEN** um usuário não-`www-data` executa o script
- **THEN** nenhum arquivo é criado ou modificado em `instance/` ou `data/` (em particular, `init_db()` não é chamado, evitando criação de `jogos.db` com owner errado)

#### Scenario: Comportamento funcional dos scripts é preservado
- **WHEN** qualquer um dos três scripts administrativos é executado como `www-data` (diretamente ou via wrapper)
- **THEN** seu comportamento funcional (criar admin, inicializar banco, importar jogos) é idêntico ao comportamento anterior a esta mudança

### Requirement: Documentação no README sobre scripts administrativos em produção

O `README.md` SHALL incluir uma seção documentando que scripts administrativos em produção devem ser invocados via `scripts/run-as-app.sh`, com a justificativa (ownership de `.env`, `instance/`, `data/` pelo usuário `www-data`) e exemplos para cada um dos três scripts.

#### Scenario: Seção presente e indexada
- **WHEN** um operador lê o `README.md`
- **THEN** encontra uma seção "Scripts administrativos em produção" (ou título equivalente) listando os três scripts e o comando canônico para cada um via `run-as-app.sh`

#### Scenario: Justificativa do ownership é explicada
- **WHEN** um operador lê a seção
- **THEN** a documentação explica que `.env`, `instance/`, e `data/` pertencem a `www-data` em produção, e que rodar scripts como outro usuário causa erros de permissão e/ou ownership incorreto de arquivos
