"""Conexão com SQLite e gerenciamento do schema."""

import os
import sqlite3
from pathlib import Path

from flask import g, current_app

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db():
    """Retorna a conexão SQLite associada ao contexto da aplicação Flask."""
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exception=None):
    """Fecha a conexão SQLite ao final do request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db_path):
    """Cria (ou recria) o schema em db_path."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _apply_column_migrations(conn)
        _ensure_game_delete_cascade(conn)
    finally:
        conn.close()


def _apply_column_migrations(conn):
    """Aplica migrations idempotentes de ADD COLUMN na tabela users.

    Cada ALTER falha silenciosamente se a coluna já existir (DB já migrado
    ou criado a partir do schema.sql atual).
    """
    migrations = (
        "ALTER TABLE users ADD COLUMN receber_emails INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN telefone TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN whatsapp INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN consentimento INTEGER DEFAULT 0",
    )
    for statement in migrations:
        try:
            conn.execute(statement)
            conn.commit()
        except sqlite3.OperationalError:
            conn.rollback()


def _ensure_game_delete_cascade(conn):
    """Garante que ``loans.game_id`` e ``reservation_queue.game_id`` tenham
    ``ON DELETE CASCADE``.

    Bancos criados antes desse ajuste tinham essas FKs sem ``CASCADE``, o
    que fazia ``DELETE FROM games`` falhar com ``FOREIGN KEY constraint
    failed`` quando havia empréstimos ou entradas de fila associadas.
    SQLite não suporta ``ALTER TABLE ... DROP CONSTRAINT``, então a
    estratégia é recriar a tabela preservando os dados.
    """
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute("BEGIN")
        for table in ("loans", "reservation_queue"):
            fk = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if not fk or "ON DELETE CASCADE" in fk[0]:
                continue
            _recreate_table_with_cascade(conn, table)
        conn.execute("COMMIT")
    except sqlite3.OperationalError:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def _recreate_table_with_cascade(conn, table):
    """Recria ``table`` adicionando ``ON DELETE CASCADE`` na FK ``game_id``.

    Preserva todas as linhas e índices existentes.
    """
    cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if "game_id" not in cols:
        return

    quoted_cols = ", ".join(f"[{c}]" for c in cols)
    select_cols = ", ".join(f"[{c}]" for c in cols)

    conn.execute(f"ALTER TABLE {table} RENAME TO {table}_old")

    create_sql = _build_cascade_create_sql(conn, table)
    conn.execute(create_sql)

    conn.execute(
        f"INSERT INTO {table} ({quoted_cols}) SELECT {select_cols} FROM {table}_old"
    )
    conn.execute(f"DROP TABLE {table}_old")
    _recreate_indexes(conn, table)


def _build_cascade_create_sql(conn, table):
    """Reconstrói o ``CREATE TABLE`` injetando ``ON DELETE CASCADE`` na FK
    ``game_id`` quando ela ainda não estiver presente.
    """
    original = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (f"{table}_old",),
    ).fetchone()[0]

    base_sql = original.replace(f'"{table}_old"', f'"{table}"', 1)

    if "REFERENCES games(id)" in base_sql and "ON DELETE CASCADE" not in base_sql:
        base_sql = base_sql.replace(
            "REFERENCES games(id)", "REFERENCES games(id) ON DELETE CASCADE"
        )
    return base_sql


def _recreate_indexes(conn, table):
    """Recria índices que referenciam ``table``."""
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL",
        (table,),
    ).fetchall()
    for (sql,) in rows:
        conn.execute(sql)


def init_app(app):
    """Registra hooks de DB na aplicação Flask."""
    app.teardown_appcontext(close_db)
