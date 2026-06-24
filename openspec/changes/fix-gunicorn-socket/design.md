## Context

O `deploy/gunicorn.service` executa o Gunicorn como `User=www-data`. O `gunicorn.conf.py` configura `bind = "unix:/run/gunicorn.sock"`. No Debian 12, `/run/` tem permissões `drwxr-xr-x root:root` — `www-data` pode traversar mas não pode criar arquivos. Resultado: o Gunicorn tenta criar o socket, recebe `Permission denied`, e entra em crash loop.

Adicionalmente, se alguém rodar Gunicorn manualmente como root (debug), o socket fica owned by root. Quando o serviço Systemd inicia como `www-data`, encontra o socket stale e também falha.

## Goals / Non-Goals

**Goals:**
- Fazer o serviço `gerenciador-jogos` iniciar sem erros de permissão
- Garantir que sockets stale não impedem o início do serviço
- Manter o socket em um local consistente entre Gunicorn e Nginx

**Non-Goals:**
- Mudar a arquitetura de deploy (continua Gunicorn + Nginx via Unix socket)
- Trocar Unix socket por TCP socket
- Mudar o usuário do Gunicorn (continua `www-data`)

## Decisions

### 1. RuntimeDirectory do Systemd

**Escolha:** Adicionar `RuntimeDirectory=gerenciador-jogos` ao service file.

**Razão:** O systemd cria `/run/gerenciador-jogos/` com owner `www-data:www-data` e mode `0755` antes de iniciar o processo, e remove automaticamente quando o serviço para. Isso resolve o problema de permissão sem precisar de scripts de init customizados ou `chown` manual.

**Alternativas consideradas:**
- ExecStartPre com `mkdir + chown`: funciona mas é mais frágil, não limpa no stop
- Mudar bind para TCP `127.0.0.1:8000`: elimina o problema do socket mas adiciona overhead de TCP e perde a simplicidade do Unix socket
- Rodar Gunicorn como root: inseguro, não recomendado

### 2. Caminho do socket

**Escolha:** `/run/gerenciador-jogos/gunicorn.sock`

**Razão:** Segue a convenção `RuntimeDirectory` (`/run/<service-name>/`). O Nginx upstream precisa apontar para o mesmo caminho.

### 3. Limpeza de socket stale

**Escolha:** Adicionar `ExecStartPre=/bin/rm -f /run/gerenciador-jogos/gunicorn.sock`

**Razão:** Se o Gunicorn foi rodado manualmente (como root) e criou o socket, o `RuntimeDirectory` pode não limpá-lo corretamente. O `ExecStartPre` garante que qualquer socket stale seja removido antes de iniciar. O `-f` evita erro se o arquivo não existir.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Socket em path novo não corresponde ao Nginx configurado | Nginx.conf atualizado no mesmo change |
| Servidor em produção com socket antinho precisa de restart manual | `systemctl daemon-reload && systemctl restart gerenciador-jogos nginx` após aplicar |
| `RuntimeDirectory` remove `/run/gerenciador-jogos/` no stop — se alguém colocar outros arquivos ali, somem | Documentar que o diretório é gerenciado pelo systemd |
