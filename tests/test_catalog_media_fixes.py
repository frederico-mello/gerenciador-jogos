"""Testes de regressão para os 5 bugs do change fix-catalog-media-bugs.

Cobre: modal nativo (showModal/close), cache-busting ?v=updated_at,
persistência de manuais (commit), limpeza de páginas excedentes,
migração de mídias no rename/área, descrição com nl2br e rótulo "Objetivo".
"""

import io
from pathlib import Path

from PIL import Image


def _img_bytes(name="img.jpg"):
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="blue").save(buf, "JPEG")
    buf.seek(0)
    return (buf, name)


def _uploads(n=1):
    """Lista de (buffers, nomes) para o campo múltiplo manual_pages."""
    return [_img_bytes(f"manual_{i}.jpg") for i in range(1, n + 1)]


def _create_game_with_uploads(admin_client, nome="Jogo Fix", area="anatomia",
                              uploads=True, manual_pages=0):
    """Cria um jogo via POST /novo (form real) e retorna o game_id."""
    data = {
        "nome": nome,
        "area": area,
        "descricao": "linha um\nlinha dois",
    }
    if uploads:
        data["imagem_perfil"] = _img_bytes("perfil.jpg")
        data["imagem_componentes"] = _img_bytes("componentes.jpg")
    if manual_pages:
        data["manual_pages"] = _uploads(manual_pages)

    resp = admin_client.post("/novo", data=data, follow_redirects=True)
    assert resp.status_code == 200
    return _game_id_by_nome(admin_client, nome)


def _game_id_by_nome(admin_client, nome):
    from app.db import get_db
    app = admin_client.application
    with app.app_context():
        return get_db().execute(
            "SELECT id FROM games WHERE nome = ? ORDER BY id DESC LIMIT 1", (nome,)
        ).fetchone()["id"]


def _get_game_updated_at(app, game_id):
    from app.db import get_db
    with app.app_context():
        return get_db().execute(
            "SELECT updated_at FROM games WHERE id = ?", (game_id,)
        ).fetchone()["updated_at"]


class TestModalExclusao:
    def test_dialog_native_sem_hidden(self, admin_client, app):
        gid = _create_game_with_uploads(admin_client)
        html = admin_client.get(f"/{gid}").get_data(as_text=True)
        assert 'id="delete-modal"' in html
        assert 'id="delete-modal" hidden' not in html
        assert 'id="delete-modal" aria-modal' in html
        # handlers usam APIs nativas e não manipulam hidden; o JS hoje vive
        # no arquivo externo app/static/js/app.js (change fix-csp-inline-js)
        assert 'data-modal-open="delete-modal"' in html
        assert "data-modal-close" in html
        app_js = (Path(app.root_path) / "static" / "js" / "app.js").read_text(encoding="utf-8")
        assert "showModal()" in app_js
        assert "close()" in app_js
        assert "removeAttribute('hidden')" not in app_js
        assert "setAttribute('hidden'" not in app_js

    def test_excluir_rota_continua(self, admin_client, app):
        gid = _create_game_with_uploads(admin_client)
        resp = admin_client.post(f"/{gid}/excluir", follow_redirects=True)
        assert resp.status_code == 200
        from app.models import get_game
        with app.app_context():
            assert get_game(gid) is None


class TestCacheBusting:
    def test_urls_com_v_updated_at(self, admin_client, app):
        gid = _create_game_with_uploads(admin_client)
        updated_at = _get_game_updated_at(app, gid)
        assert updated_at

        html = admin_client.get(f"/{gid}").get_data(as_text=True)
        assert f"?v={updated_at.replace(' ', '+')}" in html
        assert "/media/anatomia/jogo-fix/perfil.jpg?v=" in html
        assert "/media/anatomia/jogo-fix/componentes.jpg?v=" in html

        index = admin_client.get("/").get_data(as_text=True)
        assert "/media/anatomia/jogo-fix/perfil.jpg?v=" in index

    def test_reupload_muda_v(self, admin_client, app):
        gid = _create_game_with_uploads(admin_client, nome="Reup Fix")
        v1 = _get_game_updated_at(app, gid)
        html1 = admin_client.get(f"/{gid}").get_data(as_text=True)
        assert f"?v={v1.replace(' ', '+')}" in html1

        # Re-upload da imagem de perfil via edição
        resp = admin_client.post(
            f"/{gid}/editar",
            data={
                "nome": "Reup Fix",
                "area": "anatomia",
                "imagem_perfil": _img_bytes("perfil2.jpg"),
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        v2 = _get_game_updated_at(app, gid)
        assert v2 != v1, "updated_at deveria mudar após re-upload"
        html2 = admin_client.get(f"/{gid}").get_data(as_text=True)
        assert f"?v={v2.replace(' ', '+')}" in html2
        assert f"?v={v1.replace(' ', '+')}" not in html2


class TestManuais:
    def test_set_manual_pages_persiste(self, admin_client, app):
        gid = _create_game_with_uploads(admin_client, nome="Persiste Manual",
                                        manual_pages=2)
        # Re-upload com 1 página nova: deve persistir (commit) e aparecer
        # em leitura posterior via GET.
        resp = admin_client.post(
            f"/{gid}/editar",
            data={
                "nome": "Persiste Manual",
                "area": "anatomia",
                "manual_pages": _uploads(1),
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        from app.models import list_manual_pages
        with app.app_context():
            pages = list_manual_pages(gid)
        assert len(pages) == 1
        assert pages[0]["ordem"] == 1
        assert pages[0]["path"].endswith("manual_1.jpg")

        html = admin_client.get(f"/{gid}").get_data(as_text=True)
        assert "manual_1.jpg" in html

    def test_reupload_menor_remove_excedentes(self, admin_client, app):
        gid = _create_game_with_uploads(admin_client, nome="Exc Fix",
                                        manual_pages=3)
        data_dir = Path(app.config["DATA_DIR"])
        pasta = data_dir / "anatomia" / "exc-fix"
        assert (pasta / "manual_1.jpg").exists()
        assert (pasta / "manual_2.jpg").exists()
        assert (pasta / "manual_3.jpg").exists()

        resp = admin_client.post(
            f"/{gid}/editar",
            data={
                "nome": "Exc Fix",
                "area": "anatomia",
                "manual_pages": _uploads(1),
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert (pasta / "manual_1.jpg").exists()
        assert not (pasta / "manual_2.jpg").exists()
        assert not (pasta / "manual_3.jpg").exists()

        from app.models import list_manual_pages
        with app.app_context():
            assert len(list_manual_pages(gid)) == 1

    def test_rename_migra_medias_sem_reupload(self, admin_client, app):
        # Jogo com perfil + 2 manuais; renomear (slug e área mudam) sem
        # reenviar fotos: pasta antiga some, nova existe com os arquivos,
        # paths do banco reescritos e GET /<id> aponta para a pasta nova.
        gid = _create_game_with_uploads(admin_client, nome="Anato Mach",
                                        area="anatomia", manual_pages=2)
        data_dir = Path(app.config["DATA_DIR"])
        antiga = data_dir / "anatomia" / "anato-mach"
        assert antiga.exists()

        resp = admin_client.post(
            f"/{gid}/editar",
            data={"nome": "Histo Mach Novo", "area": "histologia"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        nova = data_dir / "histologia" / "histo-mach-novo"
        assert nova.exists(), "pasta nova deveria existir com as mídias migradas"
        assert (nova / "perfil.jpg").exists()
        assert (nova / "componentes.jpg").exists()
        assert (nova / "manual_1.jpg").exists()
        assert (nova / "manual_2.jpg").exists()
        assert not antiga.exists(), "pasta antiga deveria ter sido movida"

        from app.models import get_game, list_manual_pages
        with app.app_context():
            game = get_game(gid)
            assert game["imagem_perfil"] == "histologia/histo-mach-novo/perfil.jpg"
            assert game["imagem_componentes"] == "histologia/histo-mach-novo/componentes.jpg"
            for p in list_manual_pages(gid):
                assert p["path"].startswith("histologia/histo-mach-novo/")

        html = admin_client.get(f"/{gid}").get_data(as_text=True)
        assert "histologia/histo-mach-novo/perfil.jpg?v=" in html
        assert "histologia/histo-mach-novo/manual_1.jpg" in html

    def test_rename_com_reupload_de_perfil_consolida(self, admin_client, app):
        # Renomear E reenviar a foto de perfil: o upload novo (pasta nova)
        # deve prevalecer e as demais mídias migram.
        gid = _create_game_with_uploads(admin_client, nome="Migra Reup",
                                        manual_pages=1)
        data_dir = Path(app.config["DATA_DIR"])
        resp = admin_client.post(
            f"/{gid}/editar",
            data={
                "nome": "Migra Reup 2",
                "area": "anatomia",
                "imagem_perfil": _img_bytes("perfil_novo.jpg"),
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        nova = data_dir / "anatomia" / "migra-reup-2"
        assert (nova / "perfil.jpg").exists()
        assert (nova / "componentes.jpg").exists()
        assert (nova / "manual_1.jpg").exists()
        assert not (data_dir / "anatomia" / "migra-reup").exists()

        from app.models import get_game
        with app.app_context():
            assert get_game(gid)["imagem_perfil"] == "anatomia/migra-reup-2/perfil.jpg"
            assert get_game(gid)["imagem_componentes"] == "anatomia/migra-reup-2/componentes.jpg"


class TestDescricao:
    def test_nl2br_enter_unico(self, admin_client, app):
        gid = _create_game_with_uploads(admin_client, nome="Nl2br Fix")
        html = admin_client.get(f"/{gid}").get_data(as_text=True)
        assert "<br>" in html
        assert "linha um<br>" in html
        assert "linha dois" in html

    def test_markdown_continue_sanitizado(self, admin_client, app):
        gid = _create_game_with_uploads(admin_client, nome="Md Fix")
        admin_client.post(
            f"/{gid}/editar",
            data={
                "nome": "Md Fix",
                "area": "anatomia",
                "descricao": "**negrito**\nlinha\n\n- item a\n- item b\n\n<script>alert('x')</script>",
            },
            follow_redirects=True,
        )
        html = admin_client.get(f"/{gid}").get_data(as_text=True)
        assert "<strong>negrito</strong>" in html
        assert "<br>" in html
        assert "<li>" in html
        # sanitização: conteúdo perigoso não vira tag viva
        assert "<script>alert('x')</script>" not in html


class TestRotuloObjetivo:
    def test_form_exibe_objetivo(self, admin_client):
        html = admin_client.get("/novo").get_data(as_text=True)
        assert "Objetivo" in html
        assert "Regras (resumo)" not in html

    def test_detalhe_exibe_objetivo(self, admin_client, app):
        gid = _create_game_with_uploads(admin_client, nome="Obj Fix")
        admin_client.post(
            f"/{gid}/editar",
            data={"nome": "Obj Fix", "area": "anatomia",
                  "regras_resumo": "Descobrir o mistério"},
            follow_redirects=True,
        )
        html = admin_client.get(f"/{gid}").get_data(as_text=True)
        assert "Objetivo" in html
        assert "Regras (resumo)" not in html
