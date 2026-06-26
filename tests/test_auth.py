"""Testes de autenticação: login, registro, autorização, CSRF."""

import pytest

from conftest import TEST_PASSWORD


class TestLogin:
    def test_success(self, admin_client):
        resp = admin_client.get("/")
        assert resp.status_code == 200

    def test_wrong_password(self, client, app):
        _seed_admin(app)
        resp = client.post("/login", data={"email": "admin@teste.com", "senha": "senha_errada"},
                           follow_redirects=True)
        assert b"Credenciais" in resp.data

    def test_nonexistent_email(self, client):
        resp = client.post("/login", data={"email": "naoexiste@teste.com", "senha": TEST_PASSWORD},
                           follow_redirects=True)
        assert b"Credenciais" in resp.data

    def test_inactive_user(self, client, app):
        with app.app_context():
            from app.models import create_user
            from werkzeug.security import generate_password_hash
            create_user({
                "nome": "Inativo",
                "email": "inativo@teste.com",
                "password_hash": generate_password_hash(TEST_PASSWORD),
                "role": "usuario",
                "ativo": 0,
            })
        resp = client.post("/login", data={"email": "inativo@teste.com", "senha": TEST_PASSWORD},
                           follow_redirects=True)
        assert b"inativa" in resp.data or b"inativo" in resp.data


class TestRegistro:
    def test_valid(self, client, app):
        _seed_school(app)
        resp = client.post("/registrar", data={
            "nome": "Novo Usuario",
            "email": "novo@teste.com",
            "senha": "123456",
            "confirmacao": "123456",
            "escola_id": "1",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Conta criada" in resp.data

    def test_passwords_dont_match(self, client, app):
        _seed_school(app)
        resp = client.post("/registrar", data={
            "nome": "Usuario",
            "email": "u@teste.com",
            "senha": "123456",
            "confirmacao": "654321",
            "escola_id": "1",
        }, follow_redirects=True)
        assert b"n\xc3\xa3o conferem" in resp.data

    def test_duplicate_email(self, client, app):
        _seed_admin(app)
        _seed_school(app)
        # primeiro registro ok
        client.post("/registrar", data={
            "nome": "Primeiro",
            "email": "dup@teste.com",
            "senha": "123456",
            "confirmacao": "123456",
            "escola_id": "1",
        })
        # segundo com mesmo email
        resp = client.post("/registrar", data={
            "nome": "Segundo",
            "email": "dup@teste.com",
            "senha": "123456",
            "confirmacao": "123456",
            "escola_id": "1",
        }, follow_redirects=True)
        assert b"j\xc3\xa1 cadastrado" in resp.data

    def test_missing_school(self, client):
        resp = client.post("/registrar", data={
            "nome": "Sem Escola",
            "email": "sem@teste.com",
            "senha": "123456",
            "confirmacao": "123456",
        }, follow_redirects=True)
        assert b"Escola" in resp.data


class TestAutorizacao:
    def test_protected_redirects_anonymous(self, client):
        resp = client.get("/novo")
        assert resp.status_code == 302

    def test_insufficient_role_returns_403(self, client, app):
        with app.app_context():
            from app.models import create_user
            from werkzeug.security import generate_password_hash
            create_user({
                "nome": "Comum",
                "email": "comum@teste.com",
                "password_hash": generate_password_hash(TEST_PASSWORD),
                "role": "usuario",
                "ativo": 1,
            })
        client.post("/login", data={"email": "comum@teste.com", "senha": TEST_PASSWORD})
        resp = client.get("/novo")
        assert resp.status_code == 403

    def test_admin_jogos_access(self, client, app):
        with app.app_context():
            from app.models import create_user
            from werkzeug.security import generate_password_hash
            create_user({
                "nome": "Admin Jogos",
                "email": "adminj@teste.com",
                "password_hash": generate_password_hash(TEST_PASSWORD),
                "role": "admin_jogos",
                "ativo": 1,
            })
        client.post("/login", data={"email": "adminj@teste.com", "senha": TEST_PASSWORD})
        resp = client.get("/novo")
        assert resp.status_code == 200

    def test_admin_sistema_access_admin_users(self, admin_client):
        resp = admin_client.get("/admin/users")
        assert resp.status_code == 200

    def test_usuario_cannot_access_admin_users(self, client, app):
        with app.app_context():
            from app.models import create_user
            from werkzeug.security import generate_password_hash
            create_user({
                "nome": "Comum",
                "email": "comum2@teste.com",
                "password_hash": generate_password_hash(TEST_PASSWORD),
                "role": "usuario",
                "ativo": 1,
            })
        client.post("/login", data={"email": "comum2@teste.com", "senha": TEST_PASSWORD})
        resp = client.get("/admin/users")
        assert resp.status_code == 403


class TestCSRF:
    @pytest.mark.skip(reason="CSRF enabled only in non-test config")
    def test_post_without_token_returns_400(self):
        pass


class TestAdminUserCreate:
    def test_admin_can_access_form(self, admin_client):
        resp = admin_client.get("/admin/users/criar")
        assert resp.status_code == 200
        assert b"Novo" in resp.data

    def test_admin_creates_user(self, admin_client):
        resp = admin_client.post("/admin/users/criar", data={
            "nome": "Novo User",
            "email": "[EMAIL]",
            "senha": "1234",
            "confirmacao": "1234",
            "role": "usuario",
            "ativo": "1",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"criado" in resp.data

    def test_duplicate_email(self, admin_client):
        admin_client.post("/admin/users/criar", data={
            "nome": "Primeiro",
            "email": "[EMAIL]",
            "senha": "1234",
            "confirmacao": "1234",
            "role": "usuario",
        })
        resp = admin_client.post("/admin/users/criar", data={
            "nome": "Segundo",
            "email": "[EMAIL]",
            "senha": "1234",
            "confirmacao": "1234",
            "role": "usuario",
        }, follow_redirects=True)
        assert b"j\xc3\xa1 cadastrado" in resp.data

    def test_short_password(self, admin_client):
        resp = admin_client.post("/admin/users/criar", data={
            "nome": "User",
            "email": "[EMAIL]",
            "senha": "12",
            "confirmacao": "12",
            "role": "usuario",
        }, follow_redirects=True)
        assert b"4 caracteres" in resp.data

    def test_passwords_dont_match(self, admin_client):
        resp = admin_client.post("/admin/users/criar", data={
            "nome": "User",
            "email": "[EMAIL]",
            "senha": "1234",
            "confirmacao": "5678",
            "role": "usuario",
        }, follow_redirects=True)
        assert b"n\xc3\xa3o conferem" in resp.data

    def test_non_admin_gets_403(self, client, app):
        with app.app_context():
            from app.models import create_user
            from werkzeug.security import generate_password_hash
            create_user({
                "nome": "Comum",
                "email": "[EMAIL]",
                "password_hash": generate_password_hash(TEST_PASSWORD),
                "role": "usuario",
                "ativo": 1,
            })
        client.post("/login", data={"email": "[EMAIL]", "senha": TEST_PASSWORD})
        resp = client.get("/admin/users/criar")
        assert resp.status_code == 403


class TestAdminUserRoleChange:
    def test_promote_usuario_to_admin_jogos(self, admin_client, app):
        """Bugfix: promover um usuario a admin_jogos deve funcionar com um
        unico admin_sistema no sistema (a guarda so aplica a democao de
        admin_sistema)."""
        with app.app_context():
            from app.models import create_user
            from werkzeug.security import generate_password_hash
            user_id = create_user({
                "nome": "Usuario",
                "email": "[EMAIL]",
                "password_hash": generate_password_hash(TEST_PASSWORD),
                "role": "usuario",
                "ativo": 1,
            })
        resp = admin_client.post(f"/admin/users/{user_id}/role", data={
            "role": "admin_jogos",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"alterado" in resp.data
        with app.app_context():
            from app.models import get_user
            assert get_user(user_id)["role"] == "admin_jogos"

    def test_self_demote_blocked(self, client, app):
        """Um admin_sistema nao pode rebaixar a si mesmo."""
        with app.app_context():
            from app.models import create_user
            from werkzeug.security import generate_password_hash
            user_id = create_user({
                "nome": "Unico Admin",
                "email": "[EMAIL]",
                "password_hash": generate_password_hash(TEST_PASSWORD),
                "role": "admin_sistema",
                "ativo": 1,
            })
        client.post("/login", data={"email": "[EMAIL]", "senha": TEST_PASSWORD},
                    follow_redirects=True)
        resp = client.post(f"/admin/users/{user_id}/role", data={
            "role": "admin_jogos",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert "próprio papel" in resp.data.decode("utf-8").lower()
        with app.app_context():
            from app.models import get_user
            assert get_user(user_id)["role"] == "admin_sistema"

    def test_demote_admin_sistema_when_other_exists(self, admin_client, app):
        """Democao e permitida quando existe outro admin_sistema."""
        with app.app_context():
            from app.models import create_user, get_user_by_email
            from werkzeug.security import generate_password_hash
            create_user({
                "nome": "Segundo Admin",
                "email": "[EMAIL]",
                "password_hash": generate_password_hash(TEST_PASSWORD),
                "role": "admin_sistema",
                "ativo": 1,
            })
            first_id = get_user_by_email("[EMAIL]")["id"]
        resp = admin_client.post(f"/admin/users/{first_id}/role", data={
            "role": "admin_jogos",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"alterado" in resp.data
        with app.app_context():
            from app.models import get_user
            assert get_user(first_id)["role"] == "admin_jogos"


def _seed_admin(app):
    with app.app_context():
        from app.models import create_user, get_user_by_email
        from werkzeug.security import generate_password_hash
        if not get_user_by_email("admin@teste.com"):
            create_user({
                "nome": "Admin Teste",
                "email": "admin@teste.com",
                "password_hash": generate_password_hash(TEST_PASSWORD),
                "role": "admin_sistema",
                "ativo": 1,
            })


def _seed_school(app):
    with app.app_context():
        from app.models import create_school
        return create_school({
            "nome": "Escola Teste",
            "codigo_inep": "35061274",
            "rede": "municipal",
            "endereco": "Rua Teste, 100",
            "bairro": "Centro",
        })
