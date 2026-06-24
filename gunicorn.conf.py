import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "unix:/run/gerenciador-jogos/gunicorn.sock")
workers = os.environ.get("GUNICORN_WORKERS")
if workers:
    workers = int(workers)
else:
    workers = multiprocessing.cpu_count() * 2 + 1

timeout = 30
graceful_timeout = 30

accesslog = "-"
errorlog = "-"
loglevel = "info"

capture_output = True
