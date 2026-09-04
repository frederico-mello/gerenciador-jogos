"""Cobre o bug original (FOREIGN KEY constraint failed) e a protecao contra
excluir jogo com emprestimos ativos.
"""
import sqlite3
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

from app.db import init_db
from app.models import (
    ACTIVE_LOAN_STATUSES,
    GameHasActiveLoansError,
    create_game,
    create_loan,
    create_user,
    delete_game,
    get_game,
)


def _make_user(app, email):
    with app.app_context():
        return create_user({
            "nome": "User",
            "email": email,
            "password_hash": generate_password_hash("123"),
            "role": "usuario",
            "ativo": 1,
            "telefone": "",
            "whatsapp": 0,
            "consentimento": 0,
        })


def _make_loan(app, game_id, user_id, status, devolucao="2099-01-01"):
    with app.app_context():
        # create_loan assume status 'solicitado'; atualizamos para o desejado
        # por causa da trigger/CHECK (se houver).
        loan_id = create_loan(game_id, user_id, devolucao)
        from app.db import get_db
        get_db().execute("UPDATE loans SET status = ? WHERE id = ?", (status, loan_id))
        get_db().commit()
        return loan_id


def test_delete_game_with_historical_loan_succeeds(admin_client, app):
    """Jogo com emprestimo ja devolvido pode ser excluido (cascade)."""
    with app.app_context():
        gid = create_game({"nome": "Jogo Historico", "area": "anatomia"})
        uid = _make_user(app, "h@t.com")
        _make_loan(app, gid, uid, "devolvido")

    resp = admin_client.post(f"/{gid}/excluir", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert get_game(gid) is None


def test_delete_game_with_active_loan_blocks(admin_client, app):
    """Jogo com emprestimo ativo (emprestado) NAO pode ser excluido."""
    with app.app_context():
        gid = create_game({"nome": "Jogo Ativo", "area": "anatomia"})
        uid = _make_user(app, "a@t.com")
        _make_loan(app, gid, uid, "emprestado")

    resp = admin_client.post(f"/{gid}/excluir", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert get_game(gid) is not None, "Jogo deveria continuar existindo"


def test_delete_game_raises_when_active_loan(app):
    """delete_game levanta GameHasActiveLoansError quando ha emprestimos ativos."""
    with app.app_context():
        gid = create_game({"nome": "Jogo X", "area": "anatomia"})
        uid = _make_user(app, "x@t.com")
        _make_loan(app, gid, uid, "reservado")

    with app.app_context():
        with pytest.raises(GameHasActiveLoansError):
            delete_game(gid)
        assert get_game(gid) is not None


def test_migration_adds_cascade_to_existing_db(tmp_path):
    """Simula um banco pre-existente sem CASCADE e garante que init_db
    atualiza loans e reservation_queue preservando os dados."""
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                area TEXT NOT NULL
            );
            CREATE TABLE loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (game_id) REFERENCES games(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE reservation_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL REFERENCES games(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                posicao INTEGER NOT NULL
            );
            """
        )
        conn.execute("INSERT INTO games (id, nome, area) VALUES (1, 'Antigo', 'anatomia')")
        conn.execute(
            "INSERT INTO loans (game_id, user_id, status) VALUES (1, 1, 'devolvido')"
        )
        conn.execute(
            "INSERT INTO reservation_queue (game_id, user_id, posicao) VALUES (1, 1, 1)"
        )
        conn.commit()
    finally:
        conn.close()

    init_db(db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        sql_loans = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='loans'"
        ).fetchone()[0]
        sql_queue = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='reservation_queue'"
        ).fetchone()[0]
        assert "ON DELETE CASCADE" in sql_loans
        assert "ON DELETE CASCADE" in sql_queue

        # Dados preservados
        assert conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM reservation_queue").fetchone()[0] == 1

        # Cascade funciona: deletar o jogo apaga loans e queue
        conn.execute("DELETE FROM games WHERE id = 1")
        conn.commit()
        assert conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM reservation_queue").fetchone()[0] == 0
    finally:
        conn.close()
