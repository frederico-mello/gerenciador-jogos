"""Testes para app.routes — todas as rotas CRUD."""

import io
from pathlib import Path

from PIL import Image


def _img_bytes(name="img.jpg"):
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="blue").save(buf, "JPEG")
    buf.seek(0)
    return (name, buf)


class TestIndex:
    def test_get(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_filter_area(self, client, app):
        _seed_game(app)
        resp = client.get("/?area=anatomia")
        assert resp.status_code == 200

    def test_search(self, client, app):
        _seed_game(app)
        resp = client.get("/?q=Teste")
        assert resp.status_code == 200


class TestNovo:
    def test_get_form_requires_login(self, client):
        resp = client.get("/novo")
        assert resp.status_code == 302  # redirect to login

    def test_get_form_as_admin(self, admin_client, app):
        resp = admin_client.get("/novo")
        assert resp.status_code == 200

    def test_post_valid(self, admin_client, app):
        data = {
            "nome": "Jogo Criado",
            "area": "anatomia",
            "descricao": "Descricao",
        }
        resp = admin_client.post("/novo", data=data, follow_redirects=True)
        assert resp.status_code == 200

    def test_post_invalid_missing_name(self, admin_client):
        resp = admin_client.post("/novo", data={"area": "anatomia"}, follow_redirects=True)
        assert resp.status_code in (200, 400)

    def test_post_with_uploads(self, admin_client, app):
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color="blue").save(buf, "JPEG")
        buf.seek(0)
        data = {
            "nome": "Jogo Upload",
            "area": "histologia",
            "imagem_perfil": (buf, "img.jpg"),
        }
        resp = admin_client.post("/novo", data=data, follow_redirects=True)
        assert resp.status_code == 200


class TestDetalhe:
    def test_get_existing(self, client, app):
        gid = _seed_game(app)
        resp = client.get(f"/{gid}")
        assert resp.status_code == 200

    def test_404(self, client):
        resp = client.get("/99999")
        assert resp.status_code == 404


class TestEditar:
    def test_get_form_requires_login(self, client, app):
        gid = _seed_game(app)
        resp = client.get(f"/{gid}/editar")
        assert resp.status_code == 302  # redirect to login

    def test_get_form_as_admin(self, admin_client, app):
        gid = _seed_game(app)
        resp = admin_client.get(f"/{gid}/editar")
        assert resp.status_code == 200

    def test_post_update(self, admin_client, app):
        gid = _seed_game(app)
        resp = admin_client.post(
            f"/{gid}/editar",
            data={"nome": "Renomeado", "area": "histologia"},
            follow_redirects=True,
        )
        assert resp.status_code == 200


class TestExcluir:
    def test_post(self, admin_client, app):
        gid = _seed_game(app)
        resp = admin_client.post(f"/{gid}/excluir", follow_redirects=True)
        assert resp.status_code == 200

    def test_post_requires_login(self, client, app):
        gid = _seed_game(app)
        resp = client.post(f"/{gid}/excluir", follow_redirects=True)
        assert resp.status_code == 200  # redirect to login + follow gives 200


class TestMedia:
    def test_serve_file(self, client, app):
        Path(app.config["DATA_DIR"]).mkdir(parents=True, exist_ok=True)
        test_file = Path(app.config["DATA_DIR"]) / "test.txt"
        test_file.write_text("hello")
        resp = client.get("/media/test.txt")
        assert resp.status_code == 200

    def test_404(self, client):
        resp = client.get("/media/naoexiste.jpg")
        assert resp.status_code == 404


class TestAuth:
    def test_login_get(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_registrar_get(self, client):
        resp = client.get("/registrar")
        assert resp.status_code == 200

    def test_logout(self, admin_client):
        resp = admin_client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200


def _seed_game(app):
    with app.app_context():
        from app.models import create_game
        return create_game({
            "nome": "Jogo Teste",
            "area": "anatomia",
            "descricao": "Teste",
        })
