"""Importa jogos das pastas Downloads para data/ + SQLite."""

import getpass
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Guarda de usuário: em produção, scripts admin DEVEM rodar como www-data
# (dono de .env, instance/, data/) via scripts/run-as-app.sh. Falhar fast
# aqui evita tanto o PermissionError do load_dotenv() quanto a escrita de
# arquivos em data/ com owner errado, que quebrariam o Gunicorn/Nginx.
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

from app import create_app
from app.importer import import_all


def main():
    base = Path(__file__).resolve().parent.parent
    downloads_root = os.environ.get("IMPORT_SOURCE_DIR")
    if not downloads_root:
        print("Erro: IMPORT_SOURCE_DIR não definido no .env")
        sys.exit(1)
    downloads_root = Path(downloads_root)
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    app = create_app()
    with app.app_context():
        print(f"Origem: {downloads_root}")
        print(f"Destino: {data_dir}\n")
        import_all(downloads_root, str(data_dir))


if __name__ == "__main__":
    main()
