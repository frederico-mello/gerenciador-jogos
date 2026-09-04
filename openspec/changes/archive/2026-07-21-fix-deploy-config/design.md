## Context

Após o deploy inicial do change `production-deploy`, identificaram-se cinco bugs nos arquivos `deploy/nginx.conf` e `deploy/setup.sh` que impedem o funcionamento em servidores Debian 12 com Nginx 1.22:

- `http2 on;` não é uma diretiva válida nessa versão do Nginx.
- Os caminhos dos certificados SSL utilizam `$host`, que o Nginx não expande em `ssl_certificate`.
- O script tenta habilitar/reiniciar o serviço `gunicorn` em vez de `gerenciador-jogos`, que é o nome do arquivo copiado para `/etc/systemd/system/`.
- **Dependência circular de bootstrapping SSL**: o script instala a config completa do Nginx (com diretivas `ssl_certificate` apontando para certificados inexistentes) *antes* de o certificado ser emitido. Como `nginx -t` carrega os certificados, ele falha. O `certbot --nginx` executa `nginx -t` internamente, então também falha.
- **Firewall externo bloqueia portas 80/443 da internet**: o servidor está atrás de um firewall institucional (UNESP) que bloqueia conexões inbound da internet. O Let's Encrypt HTTP-01 challenge não consegue validar o domínio. Resultado: mesmo com o fluxo two-phase corrigido, o certbot falha, e sem certificado a config completa do Nginx não pode ser deployada — o site fica inacessível.

Os bugs 1-3 já foram corrigidos (tasks 1.x e 2.x). O bug 4 foi corrigido com o fluxo two-phase (tasks 3.x). O bug 5 é o foco desta atualização: garantir que o site funcione mesmo sem Let's Encrypt, usando self-signed cert como fallback.

## Goals / Non-Goals

**Goals:**
- Corrigir `deploy/nginx.conf` para ser compatível com Nginx 1.22
- Fazer os caminhos dos certificados SSL serem configuráveis via placeholders genéricos
- Fazer o script `deploy/setup.sh` usar o nome correto do serviço Systemd
- Validar a configuração do Nginx após ajustes
- Resolver a dependência circular SSL com um fluxo two-phase no `setup.sh`
- **Garantir que o site funcione mesmo quando o Let's Encrypt falha, usando self-signed cert como fallback**

**Non-Goals:**
- Mudar a arquitetura de deploy
- Reescrever a aplicação Flask
- Trocar de Let's Encrypt para outro emissor de certificado (self-signed é fallback temporário, não substituto)

## Decisions

### 1. Formato do HTTP/2 no Nginx

**Escolha:** `listen 443 ssl http2;`

**Razão:** Diretiva padrão e suportada desde versões antigas do Nginx. A forma `http2 on;` só existe a partir do Nginx 1.25.1. Usar `listen 443 ssl http2;` garante compatibilidade com Debian 12 (Nginx 1.22).

### 2. Placeholders genéricos para certificados

**Escolha:** Usar placeholders `__SSL_CERT__` e `__SSL_KEY__` no template, substituídos por `sed` no script com o path apropriado (Let's Encrypt ou self-signed).

**Razão:** O template precisa funcionar tanto com Let's Encrypt (`/etc/letsencrypt/live/$DOMAIN/`) quanto com self-signed (`/etc/nginx/ssl/`). Placeholders genéricos permitem que o `setup.sh` decida o path correto com base no resultado do certbot. Anteriormente usávamos `__DOMAIN__` que sempre resolvia para paths do Let's Encrypt, mas isso não permite fallback.

### 3. Nome do serviço Systemd

**Escolha:** O arquivo unit copiado será `/etc/systemd/system/gerenciador-jogos.service` e todos os comandos `systemctl` usarão `gerenciador-jogos`.

**Razão:** Evita conflito com outros serviços chamados `gunicorn` e reflete o nome da aplicação.

### 4. Fluxo two-phase para bootstrapping SSL

**Escolha:** O `setup.sh` SHALL executar o deploy do Nginx em três fases:

```
FASE 1 — HTTP-only temporária
  • Escrever config mínima (listen 80, server_name $DOMAIN, location / { return 200 })
  • nginx -t && systemctl reload nginx

UFW — Abrir portas 80, 443, 22

FASE 2 — Emissão do certificado
  • Se /etc/letsencrypt/live/$DOMAIN não existe:
      certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
  • Se já existe: pular (idempotente)

FASE 3 — Config completa com SSL (SEMPRE executa)
  • Se certbot sucesso: SSL_CERT = /etc/letsencrypt/live/$DOMAIN/fullchain.pem
  • Se certbot falhou:  gerar self-signed, SSL_CERT = /etc/nginx/ssl/self-signed.crt
  • Copiar nginx.conf, substituir __SSL_CERT__, __SSL_KEY__, server_name
  • nginx -t && systemctl reload nginx
```

**Razão:** A fase 1 quebra o ciclo chicken-and-egg. A UFW abre portas antes do certbot. A fase 2 tenta Let's Encrypt. A fase 3 SEMPRE executa — com Let's Encrypt se disponível, ou self-signed como fallback. Isso garante que o site funcione mesmo quando o firewall bloqueia o Let's Encrypt.

### 5. Self-signed cert como fallback

**Escolha:** Quando o certbot falha, gerar um certificado self-signed com `openssl req -x509 -nodes -days 365` em `/etc/nginx/ssl/`.

**Razão:** O firewall da UNESP bloqueia portas 80/443 da internet, impedindo o Let's Encrypt. Sem um certificado qualquer, a config SSL do Nginx não valida (`nginx -t` falha). O self-signed permite que o site funcione internamente (com warning de browser) até que as portas sejam abertas.

**Fluxo de transição:**
1. Deploy inicial: certbot falha → self-signed gerado → site funciona internamente ⚠️
2. Portas abertas: re-executar setup.sh → certbot sucesso → Let's Encrypt substitui self-signed → site funciona externamente ✅

**Alternativas consideradas:**
- DNS-01 challenge: não precisa de porta 80, mas requer API de DNS (UNESP não provê)
- Cloudflare Tunnel: bypassa o firewall, mas muda a arquitetura (adiciona dependência)
- Esperar pelas portas: site fica inacessível por tempo indeterminado

O self-signed é a opção mais simples que faz o site funcionar imediatamente, com path claro para Let's Encrypt quando as portas abrirem.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Self-signed gera warning no browser | Documentar que é esperado;消失 quando Let's Encrypt for configurado |
| Usuário esquece de re-executar setup após portas abertas | Mensagem final do script indica certificado self-signed e como trocar |
| `openssl` não está instalado | Já vem com `nginx` no Debian 12 (dependência) |
| Self-signed expira em 365 dias | Script é idempotente; re-executar regenera |
| Nova incompatibilidade com versão do Nginx | Documentar versões testadas (Debian 12, Nginx 1.22) |
| Config HTTP-only temporária entre fases 1 e 3 | Janela é de segundos; aceitável para deploy inicial |
