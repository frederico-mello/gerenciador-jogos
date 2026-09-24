import hashlib
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request, url_for
from flask_wtf.csrf import CSRFProtect

from . import db

csrf = CSRFProtect()

# Cache no processo de fingerprints de estáticos: caminho absoluto -> fingerprint
# hex (10 chars). O os.stat roda 1x por arquivo por processo; deploys reiniciam
# o Gunicorn, então arquivos substituídos são re-estatados no boot seguinte.
_static_fingerprint_cache: dict[str, str] = {}


def _static_fingerprint(path: str) -> str | None:
    """Fingerprint curto (10 hex de sha256 de "{mtime_ns}:{size}") do arquivo.

    Retorna None quando o arquivo não pode ser lido via os.stat (arquivo
    ausente) — o helper de template então cai para a URL sem `?v=`, sem
    quebrar o render.
    """
    cached = _static_fingerprint_cache.get(path)
    if cached is not None:
        return cached
    try:
        st = os.stat(path)
    except OSError:
        return None
    payload = f"{st.st_mtime_ns}:{st.st_size}"
    fingerprint = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]
    _static_fingerprint_cache[path] = fingerprint
    return fingerprint


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

    # Migra o schema automaticamente no boot (idempotente): cria o banco se
    # não existir e aplica migrações condicionais (ADD COLUMN, FKs com
    # ON DELETE CASCADE) sem passo manual no deploy.
    db.init_db(app.config["DATABASE_PATH"])

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

    @app.context_processor
    def inject_static_v():
        """Disponibiliza `static_v(filename)` em todas as templates.

        Retorna a URL de `url_for('static', ...)` acrescida de `?v=<fingerprint>`
        (mtime_ns+size do arquivo), invalidando o cache `expires 30d` immutable
        do Nginx quando o asset muda. Sem fingerprint (stat falhou), retorna a
        URL sem `?v=` — nunca quebra o render.
        """
        def static_v(filename: str) -> str:
            static_folder = app.static_folder or ""
            fingerprint = _static_fingerprint(os.path.join(static_folder, filename))
            if fingerprint is None:
                return url_for("static", filename=filename)
            return url_for("static", filename=filename, v=fingerprint)

        return {"static_v": static_v}

    return app
