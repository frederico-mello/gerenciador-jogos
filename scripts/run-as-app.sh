#!/usr/bin/env bash
# Wrapper para executar scripts administrativos como o usuário da aplicação
# (www-data) em produção, garantindo leitura de .env e ownership correto
# dos arquivos gerados em instance/ e data/.
#
# Uso:
#   ./scripts/run-as-app.sh scripts/create_admin.py [--nome X --email Y ...]
#   ./scripts/run-as-app.sh scripts/init_db.py
#   ./scripts/run-as-app.sh scripts/import_from_downloads.py

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$#" -lt 1 ]]; then
    echo "Uso: $0 <caminho-para-script.py> [argumentos...]" >&2
    exit 64
fi

exec sudo -u www-data "$APP_DIR/venv/bin/python" "$@"
