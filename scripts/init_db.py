"""Inicializa o banco SQLite com o schema."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import init_db


def main():
    base = Path(__file__).resolve().parent.parent
    db_path = base / "instance" / "jogos.db"
    init_db(str(db_path))
    print(f"Banco inicializado em: {db_path}")


if __name__ == "__main__":
    main()
