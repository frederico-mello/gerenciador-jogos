"""Cobre a migração automática no boot (auto-migrate-on-boot).

Verifica que create_app() executa init_db sobre DATABASE_PATH:
- cria o banco quando ele não existe;
- é idempotente (repetir o boot não altera dados nem falha);
- migra banco legado (FKs sem ON DELETE CASCADE) preservando linhas.
"""
import sqlite3

from app import create_app


def _legacy_db(db_path):
    """Cria um banco pré-migração com FKs sem ON DELETE CASCADE e dados."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                area TEXT NOT NULL
            );
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                escola_id INTEGER,
                ativo INTEGER DEFAULT 1
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
        conn.execute("INSERT INTO users (id, nome, email, password_hash, role) VALUES (1, 'U', 'u@t.com', 'x', 'usuario')")
        conn.execute("INSERT INTO loans (game_id, user_id, status) VALUES (1, 1, 'devolvido')")
        conn.execute("INSERT INTO reservation_queue (game_id, user_id, posicao) VALUES (1, 1, 1)")
        conn.commit()
    finally:
        conn.close()


def _fk_sql(db_path, table):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()[0]
    finally:
        conn.close()


def _count(db_path, table):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def _columns(db_path, table):
    """Retorna o conjunto de colunas de uma tabela (PRAGMA table_info)."""
    conn = sqlite3.connect(db_path)
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    finally:
        conn.close()


def test_boot_creates_db_when_missing(tmp_path):
    """create_app() cria o banco com o schema completo quando ele não existe."""
    db_path = tmp_path / "jogos.db"
    app = create_app({
        "DATABASE_PATH": str(db_path),
        "DATA_DIR": str(tmp_path / "data"),
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
    })
    assert db_path.exists()
    tables = {row[0] for row in sqlite3.connect(db_path).execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    assert {"games", "loans", "reservation_queue", "users"} <= tables
    assert "ON DELETE CASCADE" in _fk_sql(db_path, "loans")
    assert "ON DELETE CASCADE" in _fk_sql(db_path, "reservation_queue")


def test_boot_is_idempotent(tmp_path):
    """Chamar create_app() duas vezes sobre o mesmo banco não altera dados."""
    db_path = tmp_path / "jogos.db"
    cfg = {
        "DATABASE_PATH": str(db_path),
        "DATA_DIR": str(tmp_path / "data"),
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
    }
    create_app(cfg)

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO games (nome, area) VALUES ('Jogo X', 'anatomia')")
    conn.commit()
    conn.close()

    # segundo boot sobre o mesmo banco
    create_app(cfg)

    assert _count(db_path, "games") == 1
    assert "ON DELETE CASCADE" in _fk_sql(db_path, "loans")


def test_boot_migrates_legacy_db_preserving_rows(tmp_path):
    """Boot sobre banco legado (sem CASCADE) termina com FKs em cascade e
    linhas preservadas."""
    db_path = tmp_path / "legacy.db"
    _legacy_db(db_path)

    create_app({
        "DATABASE_PATH": str(db_path),
        "DATA_DIR": str(tmp_path / "data"),
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
    })

    assert "ON DELETE CASCADE" in _fk_sql(db_path, "loans")
    assert "ON DELETE CASCADE" in _fk_sql(db_path, "reservation_queue")
    assert _count(db_path, "loans") == 1
    assert _count(db_path, "reservation_queue") == 1

    # Cascade de fato funciona após a migração
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM games WHERE id = 1")
        conn.commit()
        assert _count(db_path, "loans") == 0
        assert _count(db_path, "reservation_queue") == 0
    finally:
        conn.close()


def test_boot_migrates_legacy_users_columns(tmp_path):
    """Boot sobre banco legado adiciona as colunas novas de users via
    _apply_column_migrations (caminho do boot: create_app -> init_db).

    O banco legado criado por _legacy_db() tem a tabela users SEM as
    colunas receber_emails/telefone/whatsapp/consentimento; o boot deve
    adicioná-las (idempotente) preservando as linhas existentes.
    """
    db_path = tmp_path / "legacy.db"
    _legacy_db(db_path)
    assert not {"receber_emails", "telefone", "whatsapp", "consentimento"} <= _columns(db_path, "users")

    create_app({
        "DATABASE_PATH": str(db_path),
        "DATA_DIR": str(tmp_path / "data"),
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
    })

    cols = _columns(db_path, "users")
    assert {"receber_emails", "telefone", "whatsapp", "consentimento"} <= cols
    # Linhas preservadas após o ADD COLUMN
    assert _count(db_path, "users") == 1

    # Idempotente: um segundo boot não quebra nem duplica colunas
    create_app({
        "DATABASE_PATH": str(db_path),
        "DATA_DIR": str(tmp_path / "data"),
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
    })
    assert _columns(db_path, "users") == cols
