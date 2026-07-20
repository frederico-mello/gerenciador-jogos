import pytest

from app import create_app
from app.db import init_db

TEST_PASSWORD = "123"  # NOSONAR: test-only password for deterministic assertions


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "jogos.db"
    data_dir = tmp_path / "data"

    app = create_app(
        {
            "DATABASE_PATH": str(db_path),
            "DATA_DIR": str(data_dir),
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
        }
    )

    # `init_db` precisa gravar o schema em um arquivo físico, pois abre
    # novas conexões; por isso não usamos `:memory:`.
    with app.app_context():
        init_db(app.config["DATABASE_PATH"])

    return app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def tmp_data_dir(app):
    # Mantém o mesmo DATA_DIR configurado na app, para upload/importer.
    return app.config["DATA_DIR"]


@pytest.fixture()
def admin_client(app, client):
    """Retorna um client logado como admin_sistema."""
    with app.app_context():
        from app.models import create_user
        from werkzeug.security import generate_password_hash
        create_user({
            "nome": "Admin Teste",
            "email": "admin@teste.com",
            "password_hash": generate_password_hash(TEST_PASSWORD),
            "role": "admin_sistema",
            "ativo": 1,
        })
    client.post("/login", data={"email": "admin@teste.com", "senha": TEST_PASSWORD},
                follow_redirects=True)
    return client
