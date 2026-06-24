## Why

O serviço Systemd `gerenciador-jogos.service` entra em crash loop imediatamente após iniciar. O Gunicorn roda como `www-data` mas tenta criar o socket Unix em `/run/gunicorn.sock` — um diretório owned by root onde `www-data` não tem permissão de escrita. O erro é `[Errno 13] Permission denied` e o systemd reinicia o serviço indefinidamente (246+ restarts observados).

## What Changes

- Adicionar `RuntimeDirectory=gerenciador-jogos` ao `deploy/gunicorn.service` — o systemd cria `/run/gerenciador-jogos/` com owner `www-data:www-data` automaticamente antes de iniciar o serviço e remove ao parar
- Alterar o bind do Gunicorn de `unix:/run/gunicorn.sock` para `unix:/run/gerenciador-jogos/gunicorn.sock` em `gunicorn.conf.py`
- Atualizar o upstream do Nginx em `deploy/nginx.conf` para apontar para o novo caminho do socket
- Adicionar `ExecStartPre` para remover socket stale antes de iniciar (defesa contra sockets órfãos de execuções manuais como root)

## Capabilities

### New Capabilities
- *(nenhuma)*

### Modified Capabilities
- `production-infra`: O requisito de serviço Systemd muda para usar `RuntimeDirectory` e o caminho do socket Unix muda de `/run/gunicorn.sock` para `/run/gerenciador-jogos/gunicorn.sock`

## Impact

- Arquivos alterados: `deploy/gunicorn.service`, `gunicorn.conf.py`, `deploy/nginx.conf`
- Sem impacto na aplicação Flask — apenas na infraestrutura de deploy
- O serviço `gerenciador-jogos` para de crashar e o Gunicorn passa a responder no socket corretamente
- O `deploy/setup.sh` não precisa mudar (já copia os arquivos e habilita o serviço)
