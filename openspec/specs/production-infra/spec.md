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
O sistema SHALL fornecer um arquivo `gunicorn.conf.py` na raiz do projeto com configurações de produção: bind via Unix socket, workers configuráveis via env var, logging para stdout/stderr, timeout de 30 segundos, e graceful shutdown.

#### Scenario: Gunicorn inicia com configuração padrão
- **WHEN** o Gunicorn é iniciado com `gunicorn -c gunicorn.conf.py wsgi:app`
- **THEN** ele escuta no socket `/run/gunicorn.sock` com `2 * CPU_cores + 1` workers

#### Scenario: Número de workers configurável via env var
- **WHEN** a variável `GUNICORN_WORKERS` está definida como `4`
- **THEN** o Gunicorn inicia com exatamente 4 workers

#### Scenario: Socket path configurável via env var
- **WHEN** a variável `GUNICORN_BIND` está definida como `0.0.0.0:8000`
- **THEN** o Gunicorn escuta em TCP em vez de Unix socket

### Requirement: Serviço Systemd para gerenciamento do processo
O sistema SHALL fornecer um unit file `deploy/gunicorn.service` que gerencia o processo Gunicorn como serviço do Systemd: auto-start no boot, restart automático em caso de falha, usuário dedicado `www-data`, e logs via journalctl.

#### Scenario: Serviço inicia automaticamente no boot
- **WHEN** o servidor Linux é reiniciado
- **THEN** o serviço Gunicorn inicia automaticamente após o boot

#### Scenario: Serviço reinicia após crash
- **WHEN** o processo Gunicorn morre inesperadamente
- **THEN** o Systemd reinicia o serviço automaticamente dentro de 10 segundos

#### Scenario: Logs acessíveis via journalctl
- **WHEN** um administrador executa `journalctl -u gunicorn`
- **THEN** os logs de acesso e erro do Gunicorn são exibidos

### Requirement: Configuração Nginx como proxy reverso com HTTPS
O sistema SHALL fornecer um arquivo `deploy/nginx.conf` com configuração de proxy reverso: redirect HTTP→HTTPS, proxy para o socket do Gunicorn, serving de arquivos estáticos e de dados, e security headers.

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

### Requirement: Script de setup automatizado para o servidor
O sistema SHALL fornecer um script `deploy/setup.sh` que automatiza a instalação em um servidor Ubuntu 22.04+ limpo: instala Python, Nginx, Certbot, cria usuário dedicado, copia configurações, solicita o domínio, gera certificado Let's Encrypt, e inicia os serviços.

#### Scenario: Setup completo em servidor limpo
- **WHEN** um administrador executa `sudo bash deploy/setup.sh` em um Ubuntu 22.04 limpo
- **THEN** todas as dependências são instaladas, Nginx configurado, certificado SSL gerado, e o serviço Gunicorn está rodando

#### Scenario: Setup solicita domínio
- **WHEN** o script é executado
- **THEN** ele pergunta "Qual é o domínio do servidor?" e usa a resposta para configurar Nginx e o certificado

#### Scenario: Setup é idempotente
- **WHEN** o script é executado novamente após setup bem-sucedido
- **THEN** ele atualiza as configurações sem erros e reinicia os serviços

### Requirement: Logging de produção
O sistema SHALL configurar logging do Gunicorn para stdout/stderr (capturado pelo journalctl) com formato contendo timestamp, nível, e mensagem. O Nginx SHALL logar acesso e erros em `/var/log/nginx/`.

#### Scenario: Log de request no journalctl
- **WHEN** um request é processado pelo Gunicorn
- **THEN** uma linha de log com timestamp, method, path, status code e tempo de resposta aparece no `journalctl -u gunicorn`

#### Scenario: Log de erro no journalctl
- **WHEN** uma exceção não tratada ocorre na aplicação
- **THEN** o traceback completo aparece no `journalctl -u gunicorn`

### Requirement: Firewall com UFW
O sistema SHALL configurar o UFW (Uncomplicated Firewall) para permitir apenas as portas 22 (SSH), 80 (HTTP) e 443 (HTTPS), negando todo o tráfego entrante por padrão.

#### Scenario: Apenas portas necessárias abertas
- **WHEN** o setup é concluído
- **THEN** `sudo ufw status` mostra apenas portas 22, 80 e 443 como ALLOW

#### Scenario: Porta do Gunicorn não exposta externamente
- **WHEN** um cliente tenta conectar diretamente na porta 8000 do servidor
- **THEN** a conexão é recusada pelo firewall
