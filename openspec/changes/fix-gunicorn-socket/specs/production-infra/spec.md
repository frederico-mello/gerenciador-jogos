## MODIFIED Requirements

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
