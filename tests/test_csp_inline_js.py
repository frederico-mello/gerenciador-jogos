"""Testes de regressão: templates sem JS inline (CSP `script-src 'self'`).

O Nginx de produção emite `script-src 'self'`, que bloqueia handlers de
evento inline (`onclick=`, `onchange=`, ...) e `<script>` sem atributo `src`.
Este módulo garante que as páginas renderizadas e os arquivos de template não
reintroduzam código inline, e que `app.js` (único ponto de JS da aplicação)
seja servido e presente em todas as páginas.
"""

import re
from pathlib import Path

import pytest

from app.models import create_game

APP_DIR = Path(__file__).resolve().parent.parent / "app"
TEMPLATES_DIR = APP_DIR / "templates"

# Atributos de handler de evento inline bloqueados pela CSP.
EVENT_ATTR_RE = re.compile(
    r"\son(?:click|change|submit|load|error|input|keydown)\s*=",
    re.IGNORECASE,
)
# <script> sem atributo src: casa `<script` e falha a lookahead se houver
# `src` em qualquer ponto antes do fim da tag de abertura.
INLINE_SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)", re.IGNORECASE)
# Varredura bruta dos arquivos .html (cobre rotas não renderizadas no teste).
RAW_EVENT_ATTR_RE = re.compile(r"\son\w+\s*=", re.IGNORECASE)
JINJA_COMMENT_RE = re.compile(r"\{#.*?#\}", re.DOTALL)


def _context(html, match, radius=50):
    """Trecho ao redor da ocorrência para a mensagem de erro."""
    start = max(0, match.start() - radius)
    end = min(len(html), match.end() + radius)
    return html[start:end].replace("\n", " ")


def _assert_no_inline_js(html, label):
    """Detector central: falha se `html` tem handler inline ou <script> sem src."""
    m = EVENT_ATTR_RE.search(html)
    if m:
        raise AssertionError(
            f"[{label}] handler de evento inline detectado: ...{_context(html, m)}..."
        )
    m = INLINE_SCRIPT_RE.search(html)
    if m:
        raise AssertionError(
            f"[{label}] <script> sem atributo src detectado: ...{_context(html, m)}..."
        )


def _create_game(app):
    with app.app_context():
        return create_game(
            {
                "nome": "Jogo CSP Teste",
                "area": "anatomia",
                "descricao": "RPG de mesa com regras simples",
                "regras_resumo": "Cooperativo",
                "num_jogadores": "2-6",
            }
        )


class TestPaginasRenderizadasSemJsInline:
    """Cada rota renderizada não pode conter inline e deve carregar app.js."""

    @pytest.mark.parametrize(
        "path",
        [
            "/novo",
            "/admin/users",
            "/admin/schools",
            "/emprestimos/admin",
        ],
    )
    def test_rota_admin_sem_js_inline(self, admin_client, path):
        resp = admin_client.get(path)
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        _assert_no_inline_js(html, path)
        assert "js/app.js?v=" in html

    def test_login_sem_js_inline(self, client):
        path = "/login"
        resp = client.get(path)
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        _assert_no_inline_js(html, path)
        assert "js/app.js?v=" in html

    def test_detalhe_sem_js_inline(self, admin_client, app):
        gid = _create_game(app)
        path = f"/{gid}"
        resp = admin_client.get(path)
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        _assert_no_inline_js(html, path)
        assert "js/app.js?v=" in html

    def test_editar_sem_js_inline(self, admin_client, app):
        """form.html renderizado via rota de edição também fica limpo."""
        gid = _create_game(app)
        path = f"/{gid}/editar"
        resp = admin_client.get(path)
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        _assert_no_inline_js(html, path)
        assert "js/app.js?v=" in html
        assert "easymde.min.js?v=" in html

    def test_ordem_easymde_antes_de_app_js(self, admin_client):
        """`defer` executa em ordem de documento: EasyMDE precisa vir antes."""
        html = admin_client.get("/novo").get_data(as_text=True)
        pos_easymde = html.find("easymde.min.js?v=")
        pos_app = html.find("js/app.js?v=")
        assert pos_easymde != -1 and pos_app != -1
        assert pos_easymde < pos_app


class TestAppJsServidoComoEstatico:
    def test_static_app_js_retorna_200_com_content_type_js(self, client):
        resp = client.get("/static/js/app.js")
        assert resp.status_code == 200
        assert "application/javascript" in resp.content_type


class TestArquivosDeTemplateSemHandlersInline:
    def test_templates_sem_on_evento(self):
        """Varre os arquivos .html por on<evento>= (fora de comentários Jinja),
        cobrindo também rotas não renderizadas no teste acima."""
        offenders = []
        for tpl in sorted(TEMPLATES_DIR.glob("*.html")):
            text = JINJA_COMMENT_RE.sub("", tpl.read_text(encoding="utf-8"))
            m = RAW_EVENT_ATTR_RE.search(text)
            if m:
                offenders.append((tpl.name, _context(text, m)))
        assert not offenders, f"handlers inline em templates: {offenders}"


class TestDetectorSintetico:
    """Valida que o detector realmente pega os padrões (mutação sintética)."""

    def test_html_limpo_passa_no_detector(self, client):
        html = client.get("/login").get_data(as_text=True)
        _assert_no_inline_js(html, "/login")  # não deve levantar

    def test_mutacao_onclick_faz_detector_falhar(self, client):
        base = client.get("/login").get_data(as_text=True)
        mutado = base.replace("<body>", '<body onclick="handler()">', 1)
        assert "onclick" in mutado
        with pytest.raises(AssertionError) as excinfo:
            _assert_no_inline_js(mutado, "mutação")
        assert "onclick" in str(excinfo.value)

    def test_mutacao_onsubmit_faz_detector_falhar(self):
        html = '<form onsubmit="return confirm(\'ok?\')"></form>'
        with pytest.raises(AssertionError) as excinfo:
            _assert_no_inline_js(html, "mutação")
        assert "onsubmit" in str(excinfo.value)

    def test_mutacao_script_inline_faz_detector_falhar(self):
        html = "<html><body><script>alert(1)</script></body></html>"
        with pytest.raises(AssertionError) as excinfo:
            _assert_no_inline_js(html, "mutação")
        assert "<script>" in str(excinfo.value)

    def test_script_com_src_e_permitido(self):
        html = '<script defer src="/static/js/app.js?v=abc"></script>'
        _assert_no_inline_js(html, "permitido")  # não deve levantar
