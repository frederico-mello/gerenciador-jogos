"""Testes para funcionalidades extras: fila, paginação, CSV export, email."""

import csv, io
from app.db import get_db


def _create_game(app, nome="Jogo Teste Extras"):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO games (nome, area) VALUES (?, 'anatomia')", (nome,))
        db.commit()
        return db.execute("SELECT id FROM games WHERE nome = ?", (nome,)).fetchone()["id"]


def _create_user(app, email="user_extras@teste.com", role="usuario"):
    with app.app_context():
        from werkzeug.security import generate_password_hash
        db = get_db()
        db.execute(
            "INSERT INTO users (nome, email, password_hash, role, ativo, telefone, whatsapp, consentimento) VALUES (?, ?, ?, ?, 1, ?, ?, ?)",
            ("User Extras", email, generate_password_hash("senha123"), role, "11999998888", 0, 0),
        )
        db.commit()
        return db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"]


class TestReservationQueue:
    def test_add_to_queue_and_count(self, app):
        game_id = _create_game(app)
        user_id = _create_user(app)
        user_id2 = _create_user(app, email="user_extras2@teste.com")
        with app.app_context():
            from app.models import add_to_queue, count_queue, get_queue
            add_to_queue(game_id, user_id)
            assert count_queue(game_id) == 1
            add_to_queue(game_id, user_id2)
            assert count_queue(game_id) == 2
            queue = get_queue(game_id)
            assert len(queue) == 2
            assert queue[0]["posicao"] == 1
            assert queue[1]["posicao"] == 2

    def test_get_next_and_notify(self, app):
        game_id = _create_game(app)
        user_id = _create_user(app)
        with app.app_context():
            from app.models import add_to_queue, get_next_in_queue, notify_next_in_queue, get_queue
            add_to_queue(game_id, user_id)
            next_entry = get_next_in_queue(game_id)
            assert next_entry is not None
            assert next_entry["status"] == "na_fila"

            entry = notify_next_in_queue(game_id)
            assert entry is not None
            assert entry["status"] == "notificado"
            assert get_next_in_queue(game_id) is None  # queue empty after notify

    def test_cancel_queue_entry(self, app):
        game_id = _create_game(app)
        user_id = _create_user(app)
        with app.app_context():
            from app.models import add_to_queue, cancel_queue_entry, get_queue
            add_to_queue(game_id, user_id)
            entry = get_queue(game_id)[0]
            cancel_queue_entry(entry["id"])
            entry2 = get_queue(game_id)[0]
            assert entry2["status"] == "cancelado"


class TestPagination:
    def test_list_games_pagination(self, app):
        with app.app_context():
            from app.models import list_games
            for i in range(25):
                db = get_db()
                db.execute("INSERT INTO games (nome, area) VALUES (?, 'anatomia')", (f"Game {i}",))
                db.commit()

            results, pag = list_games(page=1, per_page=10)
            assert len(results) == 10
            assert pag["page"] == 1
            assert pag["pages"] == 3
            assert pag["has_next"] is True
            assert pag["total"] >= 25

            results2, pag2 = list_games(page=2, per_page=10)
            assert len(results2) == 10
            assert pag2["page"] == 2

            results3, pag3 = list_games(page=999, per_page=10)
            assert len(results3) == 0  # beyond limit returns empty
            assert pag3["page"] == 999

    def test_list_games_filter_preserved(self, app):
        with app.app_context():
            from app.models import list_games
            results, pag = list_games(area="histologia", page=1, per_page=10)
            assert pag["page"] == 1


class TestCSVExport:
    def test_csv_export_content(self, app, admin_client):
        resp = admin_client.get("/emprestimos/admin/export.csv")
        assert resp.status_code == 200
        assert resp.mimetype == "text/csv"
        content = resp.data.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) >= 1
        assert rows[0][0] == "ID"
        assert "Jogo" in rows[0]

    def test_csv_export_filtered(self, app, admin_client):
        resp = admin_client.get("/emprestimos/admin/export.csv?status=emprestado")
        assert resp.status_code == 200


class TestEmailModule:
    def test_send_email_no_smtp(self, app):
        from app.email import send_email
        send_email("test@test.com", "Subject", "Body")

    def test_send_notification_no_user(self, app):
        from app.email import send_notification
        send_notification("loan_approved", None)

    def test_send_notification_opt_out(self, app):
        game_id = _create_game(app)
        user_id = _create_user(app)
        with app.app_context():
            db = get_db()
            db.execute("UPDATE users SET receber_emails=0 WHERE id=?", (user_id,))
            db.commit()
            from app.models import get_user, create_loan
            db.execute(
                "INSERT INTO loans (game_id, user_id, status, devolucao_prevista, solicitado_at) "
                "VALUES (?, ?, 'solicitado', '2026-07-15', datetime('now'))",
                (game_id, user_id),
            )
            db.commit()
            loan = db.execute("SELECT * FROM loans").fetchone()
            from app.email import send_notification
            send_notification("loan_approved", loan)

    def test_send_notification_opt_in(self, app):
        game_id = _create_game(app)
        user_id = _create_user(app)
        with app.app_context():
            db = get_db()
            db.execute("UPDATE users SET receber_emails=1 WHERE id=?", (user_id,))
            db.commit()
            from app.models import get_user
            db.execute(
                "INSERT INTO loans (game_id, user_id, status, devolucao_prevista, solicitado_at) "
                "VALUES (?, ?, 'solicitado', '2026-07-15', datetime('now'))",
                (game_id, user_id),
            )
            db.commit()
            loan = db.execute("SELECT * FROM loans").fetchone()
            from app.email import send_notification
            send_notification("loan_approved", loan)


class TestProfile:
    def test_get_profile_page(self, app, client):
        _create_user(app)
        client.post("/login", data={"email": "user_extras@teste.com", "senha": "senha123"})
        resp = client.get("/perfil")
        assert resp.status_code == 200

    def test_update_profile(self, app, client):
        _create_user(app)
        client.post("/login", data={"email": "user_extras@teste.com", "senha": "senha123"})
        resp = client.post("/perfil", data={
            "nome": "Updated Name",
            "email": "user_extras@teste.com",
            "receber_emails": "1",
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            from app.models import get_user_by_email
            user = get_user_by_email("user_extras@teste.com")
            assert user["receber_emails"] == 1
