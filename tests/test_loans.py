"""Testes do subsistema de empréstimos (loans)."""

import pytest
from app.db import get_db


def _create_game(app, nome="Jogo Teste", area="anatomia"):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO games (nome, area) VALUES (?, ?)", (nome, area))
        db.commit()
        return db.execute("SELECT id FROM games WHERE nome = ?", (nome,)).fetchone()["id"]


def _create_user(app, nome="User Teste", email="user@teste.com", role="usuario"):
    with app.app_context():
        from werkzeug.security import generate_password_hash
        db = get_db()
        db.execute(
            "INSERT INTO users (nome, email, password_hash, role, ativo) VALUES (?, ?, ?, ?, 1)",
            (nome, email, generate_password_hash("senha123"), role),
        )
        db.commit()
        return db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"]


def _login(client, email="user@teste.com"):
    client.post("/login", data={"email": email, "senha": "senha123"})


class TestLoanCreation:
    def test_solicitar_emprestimo_valido(self, app, client):
        game_id = _create_game(app)
        user_id = _create_user(app)
        _login(client)

        resp = client.post(f"/emprestimos/solicitar/{game_id}", data={
            "devolucao_prevista": "2026-07-15",
        }, follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            db = get_db()
            loan = db.execute("SELECT * FROM loans WHERE game_id = ?", (game_id,)).fetchone()
            assert loan is not None
            assert loan["status"] == "solicitado"
            assert loan["user_id"] == user_id
            assert loan["solicitado_at"] is not None
            assert loan["devolucao_prevista"] == "2026-07-15"

    def test_jogo_indisponivel(self, app, client):
        game_id = _create_game(app)
        _create_user(app)
        _login(client)
        client.post(f"/emprestimos/solicitar/{game_id}", data={"devolucao_prevista": "2026-07-15"})
        resp = client.post(f"/emprestimos/solicitar/{game_id}", data={
            "devolucao_prevista": "2026-07-20",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_solicitacao_duplicada_rejeitada(self, app, client):
        game_id = _create_game(app)
        _create_user(app)
        _login(client)
        client.post(f"/emprestimos/solicitar/{game_id}", data={"devolucao_prevista": "2026-07-15"})
        resp = client.post(f"/emprestimos/solicitar/{game_id}", data={
            "devolucao_prevista": "2026-07-20",
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            db = get_db()
            loans = db.execute("SELECT * FROM loans WHERE game_id = ?", (game_id,)).fetchall()
            assert len(loans) == 1

    def test_solicitar_sem_login_redirect(self, app, client):
        game_id = _create_game(app)
        resp = client.post(f"/emprestimos/solicitar/{game_id}", data={
            "devolucao_prevista": "2026-07-15",
        }, follow_redirects=False)
        assert resp.status_code == 302


class TestUserLoanList:
    def test_detalhe_mostra_user_has_active_loan(self, app, client):
        game_id = _create_game(app)
        _create_user(app)
        _login(client)
        resp = client.get(f"/{game_id}")
        assert resp.status_code == 200

    def test_detalhe_user_com_loan_ativo(self, app, client):
        game_id = _create_game(app)
        _create_user(app)
        _login(client)
        client.post(f"/emprestimos/solicitar/{game_id}", data={"devolucao_prevista": "2026-07-15"})
        resp = client.get(f"/{game_id}")
        assert resp.status_code == 200

    def test_lista_proprios_emprestimos(self, app, client):
        game_id = _create_game(app)
        _create_user(app)
        _login(client)
        client.post(f"/emprestimos/solicitar/{game_id}", data={"devolucao_prevista": "2026-07-15"})
        resp = client.get("/emprestimos")
        assert resp.status_code == 200
        assert b"Jogo Teste" in resp.data

    def test_lista_vazia(self, app, client):
        _create_user(app)
        _login(client)
        resp = client.get("/emprestimos")
        assert resp.status_code == 200


class TestUserCancel:
    def test_cancelar_solicitacao_propria(self, app, client):
        game_id = _create_game(app)
        _create_user(app)
        _login(client)
        client.post(f"/emprestimos/solicitar/{game_id}", data={"devolucao_prevista": "2026-07-15"})
        with app.app_context():
            loan_id = get_db().execute("SELECT id FROM loans").fetchone()["id"]

        resp = client.post(f"/emprestimos/{loan_id}/cancelar", follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            loan = get_db().execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
            assert loan["status"] == "cancelado"

    def test_cancelar_emprestimo_alheio_403(self, app, client):
        game_id = _create_game(app)
        _create_user(app)
        _login(client)
        client.post(f"/emprestimos/solicitar/{game_id}", data={"devolucao_prevista": "2026-07-15"})
        with app.app_context():
            db = get_db()
            loan_id = db.execute("SELECT id FROM loans").fetchone()["id"]
            db.execute("UPDATE loans SET status='emprestado' WHERE id=?", (loan_id,))
            db.commit()

        resp = client.post(f"/emprestimos/{loan_id}/cancelar", follow_redirects=True)
        assert resp.status_code == 200


class TestUserRenew:
    def test_solicitar_renovacao(self, app, client):
        game_id = _create_game(app)
        _create_user(app)
        _login(client)
        client.post(f"/emprestimos/solicitar/{game_id}", data={"devolucao_prevista": "2026-07-15"})

        with app.app_context():
            db = get_db()
            loan_id = db.execute("SELECT id FROM loans").fetchone()["id"]
            db.execute(
                "UPDATE loans SET status='emprestado', emprestado_at=datetime('now') WHERE id=?",
                (loan_id,),
            )
            db.commit()

        resp = client.post(f"/emprestimos/{loan_id}/renovar", data={
            "nova_devolucao_prevista": "2026-08-01",
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            loan = get_db().execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
            assert loan["renovacao_pendente"] == 1
            assert loan["nova_devolucao_prevista"] == "2026-08-01"


class TestAdminTransitions:
    def _setup_loan(self, app):
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
            return db.execute("SELECT id FROM loans").fetchone()["id"]

    def test_aprovar(self, app, admin_client):
        loan_id = self._setup_loan(app)
        resp = admin_client.post(f"/emprestimos/{loan_id}/aprovar", follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            loan = get_db().execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
            assert loan["status"] == "reservado"
            assert loan["reservado_at"] is not None

    def test_emprestar(self, app, admin_client):
        loan_id = self._setup_loan(app)
        admin_client.post(f"/emprestimos/{loan_id}/aprovar")
        resp = admin_client.post(f"/emprestimos/{loan_id}/emprestar", data={
            "devolucao_prevista": "2026-08-01",
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            loan = get_db().execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
            assert loan["status"] == "emprestado"
            assert loan["emprestado_at"] is not None
            assert loan["devolucao_prevista"] == "2026-08-01"

    def test_devolver(self, app, admin_client):
        loan_id = self._setup_loan(app)
        admin_client.post(f"/emprestimos/{loan_id}/aprovar")
        admin_client.post(f"/emprestimos/{loan_id}/emprestar")
        resp = admin_client.post(f"/emprestimos/{loan_id}/devolver", follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            loan = get_db().execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
            assert loan["status"] == "devolvido"
            assert loan["devolvido_at"] is not None

    def test_transicao_invalida(self, app, admin_client):
        loan_id = self._setup_loan(app)
        resp = admin_client.post(f"/emprestimos/{loan_id}/devolver", follow_redirects=True)
        assert resp.status_code == 400


class TestAdminRenewal:
    def _setup_emprestado_com_renovacao(self, app):
        game_id = _create_game(app)
        user_id = _create_user(app)
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO loans (game_id, user_id, status, devolucao_prevista, "
                "solicitado_at, emprestado_at, renovacao_pendente, nova_devolucao_prevista) "
                "VALUES (?, ?, 'emprestado', '2026-07-15', datetime('now'), datetime('now'), 1, '2026-08-01')",
                (game_id, user_id),
            )
            db.commit()
            return db.execute("SELECT id FROM loans").fetchone()["id"]

    def test_aprovar_renovacao(self, app, admin_client):
        loan_id = self._setup_emprestado_com_renovacao(app)
        resp = admin_client.post(f"/emprestimos/{loan_id}/renovar/aprovar", follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            loan = get_db().execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
            assert loan["devolucao_prevista"] == "2026-08-01"
            assert loan["renovacao_pendente"] == 0
            assert loan["nova_devolucao_prevista"] is None

    def test_rejeitar_renovacao(self, app, admin_client):
        loan_id = self._setup_emprestado_com_renovacao(app)
        resp = admin_client.post(f"/emprestimos/{loan_id}/renovar/rejeitar", follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            loan = get_db().execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
            assert loan["devolucao_prevista"] == "2026-07-15"
            assert loan["renovacao_pendente"] == 0
            assert loan["nova_devolucao_prevista"] is None


class TestAvailability:
    def test_disponivel_sem_loan(self, app):
        game_id = _create_game(app)
        from app.models import get_game_availability
        with app.app_context():
            status, loan_id = get_game_availability(game_id)
            assert status == "disponivel"
            assert loan_id is None

    def test_indisponivel_com_loan_ativo(self, app):
        game_id = _create_game(app)
        _create_user(app)
        from app.models import get_game_availability
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO loans (game_id, user_id, status, devolucao_prevista, solicitado_at) "
                "VALUES (?, 1, 'emprestado', '2026-07-15', datetime('now'))",
                (game_id,),
            )
            db.commit()
            status, loan_id = get_game_availability(game_id)
            assert status == "emprestado"


class TestStatusHistory:
    def test_historico_registrado(self, app, admin_client):
        game_id = _create_game(app)
        _create_user(app)
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO loans (game_id, user_id, status, devolucao_prevista, solicitado_at) "
                "VALUES (?, 1, 'solicitado', '2026-07-15', datetime('now'))",
                (game_id,),
            )
            db.commit()
            loan_id = db.execute("SELECT id FROM loans").fetchone()["id"]
            # Record initial status manually (bypasses create_loan that does this automatically)
            from app.models import add_status_history
            add_status_history(loan_id, None, "solicitado", 1)

        resp = admin_client.post(f"/emprestimos/{loan_id}/aprovar", follow_redirects=False)
        assert resp.status_code == 302, f"Unexpected status: {resp.status_code}"
        assert "login" not in resp.headers.get("Location", ""), "Redirect to login - not authenticated!"

        with app.app_context():
            db = get_db()
            history = db.execute(
                "SELECT * FROM loan_status_history WHERE loan_id = ? ORDER BY id",
                (loan_id,),
            ).fetchall()
            assert len(history) >= 2, f"Expected >=2 history entries, got {len(history)}"
            assert history[0]["status_novo"] == "solicitado"
            assert history[1]["status_novo"] == "reservado"


class TestAuthorization:
    def test_usuario_nao_acessa_admin(self, app, client):
        _create_user(app)
        _login(client)
        resp = client.get("/emprestimos/admin")
        assert resp.status_code == 403

    def test_admin_acessa_admin(self, app, admin_client):
        resp = admin_client.get("/emprestimos/admin")
        assert resp.status_code == 200

    def test_usuario_nao_acessa_dashboard(self, app, client):
        _create_user(app)
        _login(client)
        resp = client.get("/admin/dashboard")
        assert resp.status_code == 403

    def test_admin_acessa_dashboard(self, app, admin_client):
        resp = admin_client.get("/admin/dashboard")
        assert resp.status_code == 200
