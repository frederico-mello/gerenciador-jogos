"""Testes do helper global de cache-busting de estáticos (`static_v`).

Cobre o fingerprint (estável, muda com mtime_ns/size, None para arquivo
ausente) e o helper de template (URL com `?v=`, fallback sem `?v=`, e a
página base renderizando `style.css?v=<hex10>`).
"""

import os

import pytest
from flask import render_template_string

from app import _static_fingerprint, _static_fingerprint_cache


def _clear_cache():
    _static_fingerprint_cache.clear()


class TestStaticFingerprint:
    def test_fingerprint_estavel_para_arquivo_inalterado(self, tmp_path):
        p = tmp_path / "asset.css"
        p.write_text("body { color: red; }\n")
        h1 = _static_fingerprint(str(p))
        h2 = _static_fingerprint(str(p))
        assert h1 == h2
        assert h1 is not None
        assert len(h1) == 10
        # hex
        int(h1, 16)

    def test_fingerprint_muda_quando_mtime_muda(self, tmp_path):
        p = tmp_path / "asset.css"
        p.write_text("body { color: red; }\n")
        h1 = _static_fingerprint(str(p))
        st = os.stat(p)
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 10**9))
        _clear_cache()
        h2 = _static_fingerprint(str(p))
        assert h1 != h2

    def test_fingerprint_muda_quando_size_muda(self, tmp_path):
        p = tmp_path / "asset.css"
        p.write_text("abc")
        h1 = _static_fingerprint(str(p))
        st = os.stat(p)
        p.write_text("abc def")  # muda o size...
        # ...mas restaura o mtime original, isolando o efeito de size.
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
        _clear_cache()
        h2 = _static_fingerprint(str(p))
        assert h1 != h2

    def test_fingerprint_none_para_arquivo_inexistente(self, tmp_path):
        assert _static_fingerprint(str(tmp_path / "nao-existe.css")) is None


class TestStaticVTemplateHelper:
    def test_url_versionada_com_fingerprint(self, app):
        with app.test_request_context():
            html = render_template_string("{{ static_v('style.css') }}")
        assert "style.css?v=" in html

    def test_url_sem_v_quando_arquivo_nao_existe(self, app):
        with app.test_request_context():
            html = render_template_string("{{ static_v('nao-existe.css') }}")
        assert "nao-existe.css" in html
        assert "?v=" not in html

    def test_base_html_renderiza_style_css_versionado(self, app, client):
        html = client.get("/").get_data(as_text=True)
        assert "style.css?v=" in html

    def test_form_html_versiona_assets_do_easymde(self, app, admin_client):
        html = admin_client.get("/novo").get_data(as_text=True)
        assert "easymde.min.css?v=" in html
        assert "easymde.min.js?v=" in html
