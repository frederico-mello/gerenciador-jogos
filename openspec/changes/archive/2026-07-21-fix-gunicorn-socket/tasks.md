## 1. Atualizar gunicorn.service

- [x] 1.1 Adicionar `RuntimeDirectory=gerenciador-jogos` ao bloco `[Service]`
- [x] 1.2 Adicionar `ExecStartPre=/bin/rm -f /run/gerenciador-jogos/gunicorn.sock` antes do `ExecStart`

## 2. Atualizar gunicorn.conf.py

- [x] 2.1 Alterar bind default de `unix:/run/gunicorn.sock` para `unix:/run/gerenciador-jogos/gunicorn.sock`

## 3. Atualizar nginx.conf

- [x] 3.1 Alterar upstream de `unix:/run/gunicorn.sock` para `unix:/run/gerenciador-jogos/gunicorn.sock`

## 4. Testar

- [x] 4.1 No servidor: `sudo systemctl daemon-reload && sudo systemctl restart gerenciador-jogos`
- [x] 4.2 Confirmar que o serviço está ativo: `sudo systemctl status gerenciador-jogos` (sem crash loop)
- [x] 4.3 Confirmar que o socket existe: `ls -la /run/gerenciador-jogos/gunicorn.sock`
