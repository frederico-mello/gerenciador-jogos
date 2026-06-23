import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request
from flask_wtf.csrf import CSRFProtect

from . import db

csrf = CSRFProtect()


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    base_dir = Path(__file__).resolve().parent.parent
    instance_dir = base_dir / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)

    flask_env = os.environ.get("FLASK_ENV", "development")
    secret_key = os.environ.get("FLASK_SECRET_KEY")

    if flask_env == "production":
        if not secret_key:
            print("ERRO: FLASK_SECRET_KEY é obrigatória em produção.", file=sys.stderr)
            sys.exit(1)
        if len(secret_key) < 32:
            print("ERRO: FLASK_SECRET_KEY deve ter pelo menos 32 caracteres em produção.", file=sys.stderr)
            sys.exit(1)
        app.config["DEBUG"] = False
    else:
        if not secret_key:
            import warnings
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

    @app.after_request
    def add_security_headers(response):
        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("X-Frame-Options", "DENY")
        response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    return app
