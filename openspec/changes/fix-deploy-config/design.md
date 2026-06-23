## Context

Após o deploy inicial do change `production-deploy`, identificaram-se três bugs nos arquivos `deploy/nginx.conf` e `deploy/setup.sh` que impedem o funcionamento em servidores Debian 12 com Nginx 1.22:

- `http2 on;` não é uma diretiva válida nessa versão do Nginx.
- Os caminhos dos certificados SSL utilizam `$host`, que o Nginx não expande em `ssl_certificate`.
- O script tenta habilitar/reiniciar o serviço `gunicorn` em vez de `gerenciador-jogos`, que é o nome do arquivo copiado para `/etc/systemd/system/`.

## Goals / Non-Goals

**Goals:**
- Corrigir `deploy/nginx.conf` para ser compatível com Nginx 1.22
- Fazer os caminhos dos certificados SSL dependerem do domínio configurado
- Fazer o script `deploy/setup.sh` usar o nome correto do serviço Systemd
- Validar a configuração do Nginx após ajustes

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

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Nova incompatibilidade com outra versão do Nginx | Documentar versões testadas no README |
| Certbot continua falhando se DNS não estiver apontando | Script mostra aviso e instruções para execução manual |
| Estado do servidor ficou inconsistente após falha | Limpar configuração antiga e reexecutar o setup |
