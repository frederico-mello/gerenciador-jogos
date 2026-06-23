"""Factory da aplicação Flask."""

import os
import warnings
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from . import db

csrf = CSRFProtect()


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    base_dir = Path(__file__).resolve().parent.parent
    instance_dir = base_dir / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)

    secret_key = os.environ.get("FLASK_SECRET_KEY")
    if not secret_key:
        warnings.warn("FLASK_SECRET_KEY não definida — usando chave dev insegura", RuntimeWarning)
        secret_key = "dev-insecure-key"

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE_PATH=str(instance_dir / "jogos.db"),
        DATA_DIR=str(base_dir / "data"),
        MAX_CONTENT_LENGTH=32 * 1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.config["DATA_DIR"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    from . import routes
    app.register_blueprint(routes.bp)

    return app
