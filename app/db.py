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
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))  # NOSONAR: pythonsecurity:S3649 — SCHEMA_PATH is a static, developer-controlled file, not user input
        try:
            conn.execute("ALTER TABLE users ADD COLUMN receber_emails INTEGER DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            conn.rollback()
    finally:
        conn.close()


def init_app(app):
    """Registra hooks de DB na aplicação Flask."""
    app.teardown_appcontext(close_db)
