"""Testes para rotas de admin de escolas (requerem login como admin_sistema)."""


class TestAdminSchools:
    def test_list_get(self, admin_client):
        resp = admin_client.get("/admin/schools")
        assert resp.status_code == 200

    def test_list_with_filter(self, admin_client, app):
        _seed_school(app)
        resp = admin_client.get("/admin/schools?rede=municipal")
        assert resp.status_code == 200

    def test_list_with_q(self, admin_client, app):
        _seed_school(app)
        resp = admin_client.get("/admin/schools?q=Escola")
        assert resp.status_code == 200

    def test_criar_get(self, admin_client):
        resp = admin_client.get("/admin/schools/criar")
        assert resp.status_code == 200

    def test_criar_post_valid(self, admin_client, app):
        resp = admin_client.post("/admin/schools/criar", data={
            "nome": "Nova Escola",
            "rede": "estadual",
            "codigo_inep": "12345678",
            "endereco": "Rua X",
            "bairro": "Centro",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_criar_post_missing_name(self, admin_client):
        resp = admin_client.post("/admin/schools/criar", data={"rede": "municipal"}, follow_redirects=True)
        assert resp.status_code in (200, 400)

    def test_editar_get(self, admin_client, app):
        sid = _seed_school(app)
        resp = admin_client.get(f"/admin/schools/{sid}/editar")
        assert resp.status_code == 200

    def test_editar_404(self, admin_client):
        resp = admin_client.get("/admin/schools/99999/editar")
        assert resp.status_code == 404

    def test_editar_post(self, admin_client, app):
        sid = _seed_school(app)
        resp = admin_client.post(f"/admin/schools/{sid}/editar", data={
            "nome": "Editada",
            "rede": "privada",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_inativar(self, admin_client, app):
        sid = _seed_school(app)
        resp = admin_client.post(f"/admin/schools/{sid}/inativar", follow_redirects=True)
        assert resp.status_code == 200

    def test_reativar(self, admin_client, app):
        sid = _seed_school(app)
        admin_client.post(f"/admin/schools/{sid}/inativar", follow_redirects=True)
        resp = admin_client.post(f"/admin/schools/{sid}/reativar", follow_redirects=True)
        assert resp.status_code == 200

    def test_inativar_404(self, admin_client):
        resp = admin_client.post("/admin/schools/99999/inativar", follow_redirects=True)
        assert resp.status_code == 404

    def test_unauthorized_user(self, app, client):
        """Usuario comum deve receber 403 ao acessar /admin/schools."""
        with app.app_context():
            from app.models import create_user
            from werkzeug.security import generate_password_hash
            create_user({
                "nome": "Usuario Comum",
                "email": "comum@teste.com",
                "password_hash": generate_password_hash("123456"),
                "role": "usuario",
                "ativo": 1,
                "telefone": "11999998888",
                "whatsapp": 0,
                "consentimento": 0,
            })
        client.post("/login", data={"email": "comum@teste.com", "senha": "123456"})
        resp = client.get("/admin/schools")
        assert resp.status_code == 403


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
