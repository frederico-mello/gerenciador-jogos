"""Importa jogos das pastas Downloads para data/ + SQLite."""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.importer import import_all


def main():
    base = Path(__file__).resolve().parent.parent
    downloads_root = Path.home() / "Downloads"
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    app = create_app()
    with app.app_context():
        print(f"Origem: {downloads_root}")
        print(f"Destino: {data_dir}\n")
        import_all(downloads_root, str(data_dir))


if __name__ == "__main__":
    main()
