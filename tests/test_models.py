"""Testes para app.models — CRUD + manual pages cascade."""

import pytest
from app.db import get_db


class TestGames:
    def test_create_and_get(self, app):
        with app.app_context():
            gid = _create_jogo(app)
            game = _get_game(app, gid)
            assert game["nome"] == "Jogo Teste"
            assert game["area"] == "anatomia"
            assert game["duracao_min"] == 30

    def test_list_all(self, app):
        with app.app_context():
            _create_jogo(app, nome="A")
            _create_jogo(app, nome="B", area="histologia")
            games = _list_games(app)
            assert len(games) == 2

    def test_list_filter_area(self, app):
        with app.app_context():
            _create_jogo(app, nome="A")
            _create_jogo(app, nome="B", area="histologia")
            games = _list_games(app, area="histologia")
            assert len(games) == 1
            assert games[0]["area"] == "histologia"

    def test_list_filter_q(self, app):
        with app.app_context():
            _create_jogo(app, nome="Anatomia Divertida")
            _create_jogo(app, nome="Histo Max")
            games = _list_games(app, q="anatomia")
            assert len(games) == 1

    def test_update(self, app):
        with app.app_context():
            gid = _create_jogo(app)
            from app.models import update_game
            update_game(gid, {"nome": "Renomeado", "num_jogadores": "4"})
            game = _get_game(app, gid)
            assert game["nome"] == "Renomeado"
            assert game["num_jogadores"] == "4"

    def test_delete(self, app):
        with app.app_context():
            gid = _create_jogo(app)
            from app.models import delete_game
            delete_game(gid)
            assert _get_game(app, gid) is None

    def test_set_manual_pages_and_cascade(self, app):
        with app.app_context():
            gid = _create_jogo(app)
            from app.models import set_manual_pages, list_manual_pages
            set_manual_pages(gid, ["path/a.jpg", "path/b.jpg"])
            pages = list_manual_pages(gid)
            assert len(pages) == 2
            assert pages[0]["ordem"] == 1

            from app.models import delete_game
            delete_game(gid)
            assert list_manual_pages(gid) == []

    def test_upsert_idempotent(self, app):
        with app.app_context():
            from app.models import upsert_game_by_area_nome
            data = {"descricao": "versao 1"}
            id1 = upsert_game_by_area_nome("anatomia", "Jogo X", data)
            id2 = upsert_game_by_area_nome("anatomia", "Jogo X", {"descricao": "versao 2"})
            assert id1 == id2


def _create_jogo(app, nome="Jogo Teste", area="anatomia"):
    from app.models import create_game
    return create_game({
        "nome": nome,
        "area": area,
        "descricao": "Descricao",
        "num_jogadores": "2-4",
        "duracao_min": "30",
    })


def _get_game(app, game_id):
    from app.models import get_game
    return get_game(game_id)


def _list_games(app, area=None, q=None):
    from app.models import list_games
    results, pagination = list_games(area=area, q=q)
    return results
