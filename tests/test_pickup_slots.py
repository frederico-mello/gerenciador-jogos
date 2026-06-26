"""Testes do subsistema de horarios de retirada (pickup_slots)."""

import csv
import io

import pytest
from app.db import get_db


def _create_pickup_slot(app, dia_semana=0, hora="09:00"):
    from app.models import create_pickup_slot
    with app.app_context():
        slot_id = create_pickup_slot(dia_semana, hora)
        assert slot_id is not None
        return slot_id


def _create_game(app, nome="Jogo Slot", area="anatomia"):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO games (nome, area) VALUES (?, ?)", (nome, area))
        db.commit()
        return db.execute("SELECT id FROM games WHERE nome = ?", (nome,)).fetchone()["id"]


def _create_user(app, nome="User Slot", email="user_slot@teste.com", role="usuario"):
    from werkzeug.security import generate_password_hash
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (nome, email, password_hash, role, ativo) VALUES (?, ?, ?, ?, 1)",
            (nome, email, generate_password_hash("senha123"), role),
        )
        db.commit()
        return db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"]


class TestPickupSlotsCRUD:
    def test_create_pickup_slot(self, app):
        from app.models import create_pickup_slot, get_pickup_slot
        with app.app_context():
            slot_id = create_pickup_slot(0, "09:00")
            assert slot_id is not None
            slot = get_pickup_slot(slot_id)
            assert slot is not None
            assert slot["dia_semana"] == 0
            assert slot["hora"] == "09:00"
            assert slot["ativo"] == 1

    def test_create_duplicate(self, app):
        from app.models import create_pickup_slot
        with app.app_context():
            slot_id = create_pickup_slot(1, "10:00")
            assert slot_id is not None
            slot_id2 = create_pickup_slot(1, "10:00")
            assert slot_id2 is None

    def test_list_pickup_slots(self, app):
        from app.models import create_pickup_slot, list_pickup_slots
        with app.app_context():
            create_pickup_slot(0, "08:00")
            create_pickup_slot(1, "10:00")
            slots = list_pickup_slots(ativo_only=False)
            assert len(slots) >= 2

    def test_list_pickup_slots_ativo_only(self, app):
        from app.models import create_pickup_slot, list_pickup_slots, set_pickup_slot_ativo
        with app.app_context():
            slot_id = create_pickup_slot(2, "11:00")
            set_pickup_slot_ativo(slot_id, 0)
            slots = list_pickup_slots(ativo_only=True)
            for s in slots:
                assert s["id"] != slot_id

    def test_update_pickup_slot(self, app):
        from app.models import create_pickup_slot, update_pickup_slot, get_pickup_slot
        with app.app_context():
            slot_id = create_pickup_slot(3, "12:00")
            ok = update_pickup_slot(slot_id, {"dia_semana": 4, "hora": "13:00"})
            assert ok
            slot = get_pickup_slot(slot_id)
            assert slot["dia_semana"] == 4
            assert slot["hora"] == "13:00"

    def test_update_duplicate(self, app):
        from app.models import create_pickup_slot, update_pickup_slot
        with app.app_context():
            create_pickup_slot(5, "14:00")
            slot_id2 = create_pickup_slot(6, "15:00")
            ok = update_pickup_slot(slot_id2, {"dia_semana": 5, "hora": "14:00"})
            assert not ok

    def test_set_ativo(self, app):
        from app.models import create_pickup_slot, set_pickup_slot_ativo, get_pickup_slot
        with app.app_context():
            slot_id = create_pickup_slot(3, "16:00")
            set_pickup_slot_ativo(slot_id, 0)
            slot = get_pickup_slot(slot_id)
            assert slot["ativo"] == 0
            set_pickup_slot_ativo(slot_id, 1)
            slot = get_pickup_slot(slot_id)
            assert slot["ativo"] == 1

    def test_format_pickup_slot(self, app):
        from app.models import format_pickup_slot
        assert "Segunda-feira, 08:00" in format_pickup_slot({"dia_semana": 0, "hora": "08:00"})
        assert format_pickup_slot(None) == ""
        assert format_pickup_slot({}) == ""


class TestPickupSlotsRoutes:
    def test_admin_list_slots(self, app, admin_client):
        _create_pickup_slot(app, 0, "08:00")
        resp = admin_client.get("/admin/pickup-slots")
        assert resp.status_code == 200

    def test_admin_create_slot(self, app, admin_client):
        resp = admin_client.post("/admin/pickup-slots/criar", data={
            "dia_semana": "2",
            "hora": "14:00",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_edit_slot(self, app, admin_client):
        slot_id = _create_pickup_slot(app, 1, "10:00")
        resp = admin_client.post(f"/admin/pickup-slots/{slot_id}/editar", data={
            "dia_semana": "3",
            "hora": "11:00",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_inativar_slot(self, app, admin_client):
        slot_id = _create_pickup_slot(app, 4, "15:00")
        resp = admin_client.post(f"/admin/pickup-slots/{slot_id}/inativar", follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_reativar_slot(self, app, admin_client):
        slot_id = _create_pickup_slot(app, 5, "16:00")
        admin_client.post(f"/admin/pickup-slots/{slot_id}/inativar")
        resp = admin_client.post(f"/admin/pickup-slots/{slot_id}/reativar", follow_redirects=True)
        assert resp.status_code == 200


class TestPickupSlotSelection:
    def test_solicitar_with_slot(self, app, client):
        slot_id = _create_pickup_slot(app, 0, "09:00")
        game_id = _create_game(app)
        _create_user(app)
        client.post("/login", data={"email": "user_slot@teste.com", "senha": "senha123"})
        resp = client.post(f"/emprestimos/solicitar/{game_id}", data={
            "pickup_slot_id": str(slot_id),
            "devolucao_prevista": "2026-07-15",
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            db = get_db()
            loan = db.execute("SELECT * FROM loans WHERE game_id = ?", (game_id,)).fetchone()
            assert loan is not None
            assert loan["pickup_slot_id"] == slot_id

    def test_solicitar_invalid_slot(self, app, client):
        game_id = _create_game(app)
        _create_user(app)
        client.post("/login", data={"email": "user_slot@teste.com", "senha": "senha123"})
        resp = client.post(f"/emprestimos/solicitar/{game_id}", data={
            "pickup_slot_id": "99999",
            "devolucao_prevista": "2026-07-15",
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestApprovalSlotValidation:
    def test_slot_inactive_on_approval(self, app, admin_client):
        slot_id = _create_pickup_slot(app, 0, "09:00")
        game_id = _create_game(app)
        user_id = _create_user(app)
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO loans (game_id, user_id, status, devolucao_prevista, solicitado_at, pickup_slot_id) "
                "VALUES (?, ?, 'solicitado', '2026-07-15', datetime('now'), ?)",
                (game_id, user_id, slot_id),
            )
            db.commit()
            loan_id = db.execute("SELECT id FROM loans").fetchone()["id"]

        from app.models import set_pickup_slot_ativo
        with app.app_context():
            set_pickup_slot_ativo(slot_id, 0)

        resp = admin_client.post(f"/emprestimos/{loan_id}/aprovar", follow_redirects=True)
        assert resp.status_code == 200

    def test_slot_inactive_on_solicitar(self, app, client):
        slot_id = _create_pickup_slot(app, 0, "09:00")
        from app.models import set_pickup_slot_ativo
        with app.app_context():
            set_pickup_slot_ativo(slot_id, 0)

        game_id = _create_game(app)
        _create_user(app)
        client.post("/login", data={"email": "user_slot@teste.com", "senha": "senha123"})
        resp = client.post(f"/emprestimos/solicitar/{game_id}", data={
            "pickup_slot_id": str(slot_id),
            "devolucao_prevista": "2026-07-15",
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestLoanLegado:
    def test_loan_sem_slot_aparece(self, app, admin_client):
        game_id = _create_game(app)
        user_id = _create_user(app)
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO loans (game_id, user_id, status, devolucao_prevista, solicitado_at) "
                "VALUES (?, ?, 'solicitado', '2026-07-15', datetime('now'))",
                (game_id, user_id),
            )
            db.commit()

        resp = admin_client.get("/emprestimos/admin")
        assert resp.status_code == 200


class TestCSVExport:
    def test_csv_export_column(self, app, admin_client):
        game_id = _create_game(app)
        user_id = _create_user(app, email="csv_user@teste.com")
        with app.app_context():
            db = get_db()
            db.execute("INSERT INTO schools (nome, ativo) VALUES ('Escola CSV', 1)")
            db.commit()
            escola_id = db.execute("SELECT id FROM schools").fetchone()["id"]

            db.execute("UPDATE users SET escola_id = ? WHERE id = ?", (escola_id, user_id))
            db.commit()

            db.execute(
                "INSERT INTO loans (game_id, user_id, status, devolucao_prevista, solicitado_at) "
                "VALUES (?, ?, 'solicitado', '2026-07-15', datetime('now'))",
                (game_id, user_id),
            )
            db.commit()

        resp = admin_client.get("/emprestimos/admin/export.csv")
        assert resp.status_code == 200
        assert resp.mimetype == "text/csv"
        content = resp.data.decode("utf-8-sig") if resp.data.startswith(b'\xef\xbb\xbf') else resp.data.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) >= 2
        assert "Horario de Retirada" in rows[0]
