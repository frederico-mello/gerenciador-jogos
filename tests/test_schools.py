"""Testes para app.models — CRUD de escolas."""

import pytest
from app.db import get_db


class TestSchools:
    def test_create_and_get(self, app):
        with app.app_context():
            sid = _create_school(app, codigo_inep="35061274")
            school = _get_school(app, sid)
            assert school["nome"] == "Escola Teste"
            assert school["rede"] == "municipal"
            assert school["codigo_inep"] == "35061274"
            assert school["ativo"] == 1

    def test_get_by_inep(self, app):
        with app.app_context():
            from app.models import get_school_by_inep
            sid = _create_school(app, codigo_inep="35061274")
            school = get_school_by_inep("35061274")
            assert school is not None
            assert school["id"] == sid
            assert get_school_by_inep("inep_invalido") is None

    def test_create_without_inep(self, app):
        with app.app_context():
            from app.models import create_school
            sid = create_school({
                "nome": "Escola Sem INEP",
                "rede": "privada",
                "endereco": "Rua A, 123",
            })
            school = _get_school(app, sid)
            assert school["codigo_inep"] is None
            assert school["ativo"] == 1

    def test_list_all(self, app):
        with app.app_context():
            _create_school(app, nome="A")
            _create_school(app, nome="B", rede="estadual")
            schools = _list_schools(app)
            assert len(schools) == 2

    def test_list_filter_rede(self, app):
        with app.app_context():
            _create_school(app, nome="A")
            _create_school(app, nome="B", rede="estadual")
            schools = _list_schools(app, rede="estadual")
            assert len(schools) == 1
            assert schools[0]["rede"] == "estadual"

    def test_list_filter_q(self, app):
        with app.app_context():
            _create_school(app, nome="Escola Municipal Centro")
            _create_school(app, nome="Colegio Estadual Sul")
            schools = _list_schools(app, q="centro")
            assert len(schools) == 1

    def test_list_ativo_only(self, app):
        with app.app_context():
            sid = _create_school(app)
            from app.models import set_school_ativo
            set_school_ativo(sid, 0)
            schools = _list_schools(app)
            assert len(schools) == 0
            schools_inactive = _list_schools(app, ativo_only=False)
            assert len(schools_inactive) == 1

    def test_update(self, app):
        with app.app_context():
            sid = _create_school(app)
            from app.models import update_school
            update_school(sid, {"nome": "Renomeada", "bairro": "Centro"})
            school = _get_school(app, sid)
            assert school["nome"] == "Renomeada"
            assert school["bairro"] == "Centro"

    def test_set_ativo(self, app):
        with app.app_context():
            sid = _create_school(app)
            from app.models import set_school_ativo
            set_school_ativo(sid, 0)
            assert _get_school(app, sid)["ativo"] == 0
            set_school_ativo(sid, 1)
            assert _get_school(app, sid)["ativo"] == 1

    def test_upsert_by_inep_insert(self, app):
        with app.app_context():
            from app.models import upsert_school_by_inep
            sid = upsert_school_by_inep("12345678", {"nome": "Nova Escola", "rede": "privada"})
            school = _get_school(app, sid)
            assert school["nome"] == "Nova Escola"

    def test_upsert_by_inep_update(self, app):
        with app.app_context():
            from app.models import upsert_school_by_inep
            sid1 = upsert_school_by_inep("12345678", {"nome": "Versao 1"})
            sid2 = upsert_school_by_inep("12345678", {"nome": "Versao 2"})
            assert sid1 == sid2
            school = _get_school(app, sid1)
            assert school["nome"] == "Versao 2"


def _create_school(app, nome="Escola Teste", rede="municipal", codigo_inep=None):
    from app.models import create_school
    return create_school({
        "nome": nome,
        "codigo_inep": codigo_inep or f"3506127{hash(nome) % 9000 + 1000}",
        "rede": rede,
        "endereco": "Rua Teste, 100",
        "bairro": "Centro",
        "cep": "12200-000",
    })


def _get_school(app, school_id):
    from app.models import get_school
    return get_school(school_id)


def _list_schools(app, rede=None, q=None, ativo_only=True):
    from app.models import list_schools
    return list_schools(rede=rede, q=q, ativo_only=ativo_only)
