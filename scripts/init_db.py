"""Inicializa o banco SQLite com o schema."""

import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Guarda de usuário: em produção, scripts admin DEVEM rodar como www-data
# (dono de .env, instance/, data/) via scripts/run-as-app.sh. Falhar fast
# aqui evita a criação de jogos.db com owner errado, que quebraria o Gunicorn.
_APP_USER = "www-data"
_SCRIPT_NAME = Path(__file__).name
if os.name == "nt":
    sys.stderr.write(
        f"AVISO: rodando em Windows. Em produção, use "
        f"'./scripts/run-as-app.sh scripts/{_SCRIPT_NAME}' (Linux). "
        f"Em dev local Windows, prossiga apenas se souber o que faz.\n"
    )
elif getpass.getuser() != _APP_USER:
    sys.exit(
        f"ERRO: este script deve ser rodado como '{_APP_USER}' para que os "
        f"arquivos gerados (.env, instance/, data/) tenham o owner correto. "
        f"Use: ./scripts/run-as-app.sh scripts/{_SCRIPT_NAME}\n"
    )

from app.db import init_db


def main():
    base = Path(__file__).resolve().parent.parent
    db_path = base / "instance" / "jogos.db"
    init_db(str(db_path))
    print(f"Banco inicializado em: {db_path}")


if __name__ == "__main__":
    main()
