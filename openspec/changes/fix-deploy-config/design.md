## Context

Após o deploy inicial do change `production-deploy`, identificaram-se quatro bugs nos arquivos `deploy/nginx.conf` e `deploy/setup.sh` que impedem o funcionamento em servidores Debian 12 com Nginx 1.22:

- `http2 on;` não é uma diretiva válida nessa versão do Nginx.
- Os caminhos dos certificados SSL utilizam `$host`, que o Nginx não expande em `ssl_certificate`.
- O script tenta habilitar/reiniciar o serviço `gunicorn` em vez de `gerenciador-jogos`, que é o nome do arquivo copiado para `/etc/systemd/system/`.
- **Dependência circular de bootstrapping SSL**: o script instala a config completa do Nginx (com diretivas `ssl_certificate` apontando para `/etc/letsencrypt/live/$DOMAIN/`) *antes* de o certificado existir. Como `nginx -t` tenta carregar os certificados referenciados na config, ele falha. O `certbot --nginx` executa `nginx -t` internamente antes de emitir o certificado, então também falha. Resultado: o certificado nunca é emitido e o Nginx nunca carrega a config de SSL.

Os três primeiros bugs já foram corrigidos nas tasks 1.x e 2.x. O quarto bug é o foco desta atualização do change.

## Goals / Non-Goals

**Goals:**
- Corrigir `deploy/nginx.conf` para ser compatível com Nginx 1.22
- Fazer os caminhos dos certificados SSL dependerem do domínio configurado
- Fazer o script `deploy/setup.sh` usar o nome correto do serviço Systemd
- Validar a configuração do Nginx após ajustes
- **Resolver a dependência circular SSL com um fluxo two-phase no `setup.sh`**

**Non-Goals:**
- Mudar a arquitetura de deploy
- Reescrever a aplicação Flask
- Trocar de Let's Encrypt para outro emissor de certificado

## Decisions

### 1. Formato do HTTP/2 no Nginx

**Escolha:** `listen 443 ssl http2;`

**Razão:** Diretiva padrão e suportada desde versões antigas do Nginx. A forma `http2 on;` só existe a partir do Nginx 1.25.1. Usar `listen 443 ssl http2;` garante compatibilidade com Debian 12 (Nginx 1.22).

### 2. Caminhos dos certificados

**Escolha:** Usar placeholder `__DOMAIN__` no template e substituir por `sed` no script.

**Razão:** `ssl_certificate` não aceita variáveis Nginx como `$host`. Substituir pelo domínio real durante o setup resolve isso. Também mantém o template genérico caso o Certbot falhe ou precise ser reexecutado manualmente.

### 3. Nome do serviço Systemd

**Escolha:** O arquivo unit copiado será `/etc/systemd/system/gerenciador-jogos.service` e todos os comandos `systemctl` usarão `gerenciador-jogos`.

**Razão:** Evita conflito com outros serviços chamados `gunicorn` e reflete o nome da aplicação. O template `deploy/gunicorn.service` pode continuar com esse nome interno; o arquivo final no sistema recebe o nome `gerenciador-jogos.service`.

### 4. Fluxo two-phase para bootstrapping SSL

**Escolha:** O `setup.sh` SHALL executar o deploy do Nginx em três fases:

```
FASE 1 — HTTP-only temporária
  • Escrever config mínima (listen 80, server_name $DOMAIN, location / { return 200 })
  • nginx -t && systemctl reload nginx

FASE 2 — Emissão do certificado
  • Se /etc/letsencrypt/live/$DOMAIN não existe:
      certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
  • Se já existe: pular (idempotente)

FASE 3 — Config completa com SSL
  • Copiar nginx.conf, substituir __DOMAIN__ por $DOMAIN e server_name _ por $DOMAIN
  • nginx -t && systemctl reload nginx
```

**Razão:** `nginx -t` carrega e valida os certificados referenciados em `ssl_certificate`. Se os certificados não existem, `nginx -t` falha. O `certbot --nginx` executa `nginx -t` internamente, então também falha. A fase 1 quebra o ciclo: uma config HTTP-only não referencia certificados, então `nginx -t` passa, o Nginx sobe na porta 80, e o `certbot certonly --nginx` consegue emitir o certificado via HTTP-01 challenge. Na fase 3, os certificados já existem, então a config completa valida sem erro.

**Alternativas consideradas:**
- `certbot --standalone`: funciona sem Nginx, mas precisa parar o Nginx (downtime) e ocupar a porta 80.
- Self-signed placeholder: feio, confunde operadores, e alguns browsers rejeitam.
- `certbot --webroot`: exige servir arquivos do challenge via Nginx, mais complexo.

O `certbot certonly --nginx` foi escolhido porque não modifica a config do Nginx (apenas emite o cert), e funciona com a config HTTP-only da fase 1.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Nova incompatibilidade com outra versão do Nginx | Documentar versões testadas no README |
| Certbot continua falhando se DNS não estiver apontando | Script mostra aviso e instruções para execução manual |
| Estado do servidor ficou inconsistente após falha | Limpar configuração antiga e reexecutar o setup |
| Config HTTP-only temporária deixa o site vulnerável entre fases 1 e 3 | Janela é de segundos; script roda de forma síncrona; aceitável para deploy inicial |
| Reexecutar o script quando cert já existe | Fase 2 verifica `if [ ! -d ... ]` antes de chamar certbot — idempotente |
