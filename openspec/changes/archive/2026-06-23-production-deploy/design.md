## Context

O Gerenciador de Jogos é uma aplicação Flask + SQLite que hoje roda exclusivamente com o servidor de desenvolvimento integrado (`flask run`). O projeto está pronto para ir a produção: precisa ser acessível pela internet em um servidor Linux próprio.

Estado atual:
- Flask 3.x com factory pattern (`create_app`)
- SQLite como banco de dados
- Arquivos estáticos mínimos (CSS) + dados (imagens, markdown)
- Autenticação por sessão com CSRF protection
- Sem configuração de produção nem WSGI server

Restrições:
- Servidor Linux próprio (Ubuntu 22.04+)
- Acessível na internet (domínio + HTTPS obrigatório)
- SQLite permanece (não migrar para Postgres)
- Simplicidade operacional (equipe pequena)

## Goals / Non-Goals

**Goals:**
- Servir a aplicação com Gunicorn (WSGI server de produção)
- Proxy reverso Nginx com HTTPS (Let's Encrypt)
- Arquivos estáticos e de dados servidos pelo Nginx (não pelo Flask)
- Processo gerenciado por Systemd (auto-start, restart on failure)
- Script de deploy automatizado para instalação em servidor limpo
- Security headers em todas as respostas
- Logging estruturado para diagnóstico

**Non-Goals:**
- Migrar de SQLite para outro banco
- Containerização com Docker (futuro, não agora)
- CI/CD automatizado (deploy manual via script)
- Escalabilidade horizontal (single server é suficiente)
- CDN para arquivos estáticos

## Decisions

### 1. Gunicorn como WSGI server

**Escolha:** Gunicorn

**Alternativas consideradas:**
- **Waitress**: Funciona em Windows, mais simples, mas menos performático e menos adotado na comunidade
- **uWSGI**: Mais complexo de configurar, C extensions, overkill para este projeto

**Razão:** Gunicorn é o standard da indústria para Flask em produção. Puro Python, fácil de configurar, boa performance com workers pré-fork, documentação vasta. Como o servidor será Linux, a limitação de Windows não se aplica.

### 2. Socket Unix vs TCP para comunicação Nginx→Gunicorn

**Escolha:** Unix socket (`/run/gunicorn.sock`)

**Alternativas consideradas:**
- **TCP (127.0.0.1:8000)**: Funciona bem, mas adiciona overhead de rede mesmo em loopback

**Razão:** Unix socket tem menor latência e é a prática recomendada quando Nginx e Gunicorn estão na mesma máquina. Permissões de arquivo controlam o acesso.

### 3. Número de workers do Gunicorn

**Escolha:** `2 * CPU_cores + 1` (padrão recomendado), configurável via variável de ambiente

**Razão:** Fórmula padrão da comunidade. Para um servidor modesto (2 cores), são 5 workers. Suficiente para o volume esperado de tráfego.

### 4. Let's Encrypt para HTTPS

**Escolha:** Certbot com renovação automática via cron/systemd timer

**Alternativas consideradas:**
- **Certificado auto-assinado**: Inseguro para internet, browsers bloqueiam
- **Certificado pago**: Desnecessário para este caso

**Razão:** Gratuito, automático, amplamente suportado. Certbot renova sozinho antes da expiração.

### 5. Serving de arquivos estáticos e dados pelo Nginx

**Escolha:** Nginx serve diretamente `app/static/` e `data/`, com proxy para o Flask apenas nas rotas dinâmicas

**Razão:** Nginx é otimizado para servir arquivos estáticos. Desvia carga do Gunicorn, que se concentra na lógica da aplicação.

### 6. Security headers via Nginx

**Escolha:** Headers configurados no bloco `server` do Nginx

**Headers:**
- `Strict-Transport-Security` (HSTS) — força HTTPS
- `X-Content-Type-Options: nosniff` — previne MIME sniffing
- `X-Frame-Options: DENY` — previne clickjacking
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-XSS-Protection: 0` (desativado em favor de CSP moderno)
- `Content-Security-Policy` — baseline restritivo

### 7. FLASK_ENV=production obriga SECRET_KEY forte

**Escolha:** Quando `FLASK_ENV=production`, a aplicação MUST exigir `FLASK_SECRET_KEY` definida e com mínimo de 32 caracteres. Sem fallback para chave dev.

**Razão:** Em produção, uma chave fraca ou padrão é vulnerabilidade crítica de segurança (sessões podem ser forjadas).

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| SQLite com writes concorrentes sob carga | WAL mode + connection pooling mínimo. Volume esperado é baixo. |
| Certificado Let's Encrypt expira se renovação falhar | Monitorar via cron + alerta de email. Certbot timer verifica diariamente. |
| Servidor cai e não volta automaticamente | Systemd `Restart=always` + `StartLimitIntervalSec`. Monitoramento externo futuro. |
| Deploy manual é propenso a erros | Script `setup.sh` automatiza o máximo possível. Checklist no README. |
| Dados (SQLite + imagens) não têm backup automatizado | Documentar processo de backup. Backup automatizado é non-goal por agora. |

## Migration Plan

1. Preparar arquivos de configuração no repositório (este change)
2. No servidor: executar `deploy/setup.sh` que instala dependências, configura Nginx, Systemd, firewall e certificado
3. Transferir código para o servidor (git clone ou rsync)
4. Executar `scripts/init_db.py` e `scripts/import_from_downloads.py` se necessário
5. Iniciar serviço: `sudo systemctl start gunicorn`
6. Verificar: acessar `https://<domínio>` e confirmar HTTPS + login funcionando

**Rollback:** `sudo systemctl stop gunicorn` + restaurar backup do SQLite. O `flask run` pode ser usado como fallback temporário.

## Open Questions

- Qual domínio será usado? (necessário para configurar Nginx e Let's Encrypt — o setup.sh perguntará)
- Quantos cores tem o servidor? (afeta número de workers — default será 2 cores = 5 workers)
