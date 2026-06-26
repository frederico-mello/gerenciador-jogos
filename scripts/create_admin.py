"""Cria o primeiro usuário administrador do sistema.

Uso:
    python scripts/create_admin.py --nome "Alice" --email admin@example.com --senha "123456"

Se o email já existir:
- Se for admin_sistema → oferece reset de senha.
- Se for outro papel → oferece promoção a admin_sistema + reset de senha.
"""

import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Guarda de usuário: em produção, scripts admin DEVEM rodar como www-data
# (dono de .env, instance/, data/) via scripts/run-as-app.sh. Falhar fast
# aqui evita tanto o PermissionError do load_dotenv() quanto a criação de
# arquivos (ex.: jogos.db) com owner errado, que quebrariam o Gunicorn.
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

from werkzeug.security import generate_password_hash
from app import create_app
from app.db import init_db, get_db


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Cria o primeiro administrador do sistema")
    parser.add_argument("--nome", help="Nome do administrador")
    parser.add_argument("--email", help="Email do administrador")
    parser.add_argument("--senha", help="Senha do administrador")
    args = parser.parse_args()

    nome = args.nome or input("Nome: ").strip()
    email = args.email or input("Email: ").strip()
    senha = args.senha or input("Senha: ").strip()

    if not nome or not email or not senha:
        print("ERRO: Nome, email e senha são obrigatórios.", file=sys.stderr)
        sys.exit(1)

    base_dir = Path(__file__).resolve().parent.parent
    db_path = base_dir / "instance" / "jogos.db"
    init_db(str(db_path))

    app = create_app({"DATABASE_PATH": str(db_path), "TESTING": True, "SECRET_KEY": "create-admin-secret"})
    with app.app_context():
        from app.models import count_admins_sistema, get_user_by_email, create_user, update_user

        user = get_user_by_email(email)
        if user:
            if user["role"] == "admin_sistema":
                print(f"Email '{email}' já cadastrado como admin_sistema.")
                resp = input("Deseja resetar a senha deste admin? (s/N): ").strip().lower()
                if resp != "s":
                    print("Cancelado.")
                    sys.exit(0)
                update_user(user["id"], {"senha": senha})
                print(f"Senha do admin '{email}' (ID: {user['id']}) atualizada.")
            else:
                print(f"Email '{email}' já cadastrado como '{user['role']}'.")
                resp = input(f"Deseja promover para admin_sistema e resetar a senha? (s/N): ").strip().lower()
                if resp != "s":
                    print("Cancelado.")
                    sys.exit(0)
                update_user(user["id"], {"role": "admin_sistema", "senha": senha})
                print(f"Usuário '{email}' (ID: {user['id']}) promovido a admin_sistema com senha atualizada.")
            return

        count = count_admins_sistema()
        if count > 0:
            resp = input(f"Já existe {count} admin_sistema. Criar outro? (s/N): ").strip().lower()
            if resp != "s":
                print("Cancelado.")
                sys.exit(0)

        user_id = create_user({
            "nome": nome,
            "email": email,
            "password_hash": generate_password_hash(senha),
            "role": "admin_sistema",
            "ativo": 1,
            "telefone": "",
            "whatsapp": 0,
            "consentimento": 0,
        })
        print(f"Admin criado: {email} (ID: {user_id})")


if __name__ == "__main__":
    main()
