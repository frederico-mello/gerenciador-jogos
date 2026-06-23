"""Decorators e helpers de autenticação."""

from functools import wraps

from flask import session, redirect, url_for, flash, abort

from . import models


def current_user():
    """Retorna o usuário logado (Row) ou None."""
    uid = session.get("user_id")
    if uid is None:
        return None
    return models.get_user(uid)


def login_required(f):
    """Redireciona para /login se não logado."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Login necessário.", "error")
            return redirect(url_for("games.login"))
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Retorna 403 se o usuário não tiver um dos papéis especificados."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Login necessário.", "error")
                return redirect(url_for("games.login"))
            if user["role"] not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def active_required(f):
    """Rejeita login de usuário inativo (ativo=0)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            flash("Login necessário.", "error")
            return redirect(url_for("games.login"))
        if not user["ativo"]:
            flash("Conta inativa. Contate um administrador.", "error")
            session.clear()
            return redirect(url_for("games.login"))
        return f(*args, **kwargs)
    return wrapper
