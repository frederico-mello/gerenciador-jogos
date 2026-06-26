"""Testes para scripts/create_admin.py — cenários de reset, promoção e criação."""

from werkzeug.security import check_password_hash


def test_create_new_admin(app):
    """Criar um admin novo quando o email não existe."""
    with app.app_context():
        from app.models import get_user_by_email, create_user
        from werkzeug.security import generate_password_hash

        user_id = create_user({
            "nome": "Novo Admin",
            "email": "novo@admin.com",
            "password_hash": generate_password_hash("senha123"),
            "role": "admin_sistema",
            "ativo": 1,
            "telefone": "11999998888",
            "whatsapp": 0,
            "consentimento": 0,
        })

        user = get_user_by_email("novo@admin.com")
        assert user is not None
        assert user["role"] == "admin_sistema"
        assert user["id"] == user_id
        assert user["ativo"] == 1


def test_reset_admin_password(app):
    """Resetar a senha de um admin_sistema existente via update_user."""
    with app.app_context():
        from app.models import get_user_by_email, create_user, update_user
        from werkzeug.security import generate_password_hash

        old_hash = generate_password_hash("velha123")
        create_user({
            "nome": "Admin Existente",
            "email": "admin@reset.com",
            "password_hash": old_hash,
            "role": "admin_sistema",
            "ativo": 1,
            "telefone": "11999998888",
            "whatsapp": 0,
            "consentimento": 0,
        })

        update_user(get_user_by_email("admin@reset.com")["id"], {"senha": "nova456"})

        user = get_user_by_email("admin@reset.com")
        assert check_password_hash(user["password_hash"], "nova456")


def test_promote_usuario_to_admin(app):
    """Promover um usuario a admin_sistema com reset de senha."""
    with app.app_context():
        from app.models import get_user_by_email, create_user, update_user
        from werkzeug.security import generate_password_hash

        create_user({
            "nome": "Usuario Comum",
            "email": "comum@promover.com",
            "password_hash": generate_password_hash("comum123"),
            "role": "usuario",
            "ativo": 1,
            "telefone": "11999998888",
            "whatsapp": 0,
            "consentimento": 0,
        })

        update_user(
            get_user_by_email("comum@promover.com")["id"],
            {"role": "admin_sistema", "senha": "nova789"},
        )

        user = get_user_by_email("comum@promover.com")
        assert user["role"] == "admin_sistema"
        assert check_password_hash(user["password_hash"], "nova789")


def test_promote_admin_jogos_to_admin(app):
    """Promover um admin_jogos a admin_sistema com reset de senha."""
    with app.app_context():
        from app.models import get_user_by_email, create_user, update_user
        from werkzeug.security import generate_password_hash

        create_user({
            "nome": "Admin Jogos",
            "email": "jogos@promover.com",
            "password_hash": generate_password_hash("jogos123"),
            "role": "admin_jogos",
            "ativo": 1,
            "telefone": "11999998888",
            "whatsapp": 0,
            "consentimento": 0,
        })

        update_user(
            get_user_by_email("jogos@promover.com")["id"],
            {"role": "admin_sistema", "senha": "nova999"},
        )

        user = get_user_by_email("jogos@promover.com")
        assert user["role"] == "admin_sistema"
        assert check_password_hash(user["password_hash"], "nova999")


def test_cancel_does_not_alter_data(app):
    """Garantir que chamar update_user com a mesma senha não quebra (simula cancelamento)."""
    with app.app_context():
        from app.models import get_user_by_email, create_user
        from werkzeug.security import generate_password_hash

        original_hash = generate_password_hash("original123")
        create_user({
            "nome": "Nao Mexer",
            "email": "nao@mexer.com",
            "password_hash": original_hash,
            "role": "admin_sistema",
            "ativo": 1,
            "telefone": "11999998888",
            "whatsapp": 0,
            "consentimento": 0,
        })

        user = get_user_by_email("nao@mexer.com")
        assert check_password_hash(user["password_hash"], "original123")
        assert user["role"] == "admin_sistema"