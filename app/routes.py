"""Rotas Flask para o gerenciador de jogos."""

import shutil
from pathlib import Path

import markdown
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    send_from_directory, current_app, flash, abort, session,
)
from werkzeug.security import check_password_hash

from . import models
from .auth import login_required, role_required, current_user
from .importer import slugify, resize_image
from .db import init_db, get_db

bp = Blueprint("games", __name__)

ALLOWED_AREAS = ("anatomia", "histologia", "microbiologia")

DDD_RANGE = range(11, 100)


def _validate_telefone(ddd, numero):
    """Valida DDD (2 digitos, 11-99) e numero (8-9 digitos).
    Retorna string concatenada 'DDDnumero' ou levanta ValueError."""
    ddd = (ddd or "").strip()
    numero = (numero or "").strip()
    if not ddd or not numero:
        raise ValueError("Telefone é obrigatório.")
    if len(ddd) != 2 or not ddd.isdigit() or int(ddd) not in DDD_RANGE:
        raise ValueError("DDD inválido.")
    if len(numero) < 8 or len(numero) > 9 or not numero.isdigit():
        raise ValueError("Número de telefone inválido.")
    return ddd + numero


@bp.app_context_processor
def inject_current_user():
    return dict(current_user=current_user())


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        senha = request.form.get("senha") or ""
        user = models.get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], senha):
            flash("Credenciais inválidas.", "error")
            return render_template("login.html"), 401
        if not user["ativo"]:
            flash("Conta inativa. Contate um administrador.", "error")
            return render_template("login.html"), 401
        session["user_id"] = user["id"]
        return redirect(url_for("games.index"))
    return render_template("login.html")


@bp.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        email = (request.form.get("email") or "").strip()
        senha = request.form.get("senha") or ""
        confirmacao = request.form.get("confirmacao") or ""
        escola_id = request.form.get("escola_id") or None
        telefone_ddd = (request.form.get("telefone_ddd") or "").strip()
        telefone_numero = (request.form.get("telefone_numero") or "").strip()
        whatsapp = 1 if request.form.get("whatsapp") == "1" else 0
        consentimento = 1 if request.form.get("consentimento") == "1" else 0

        errors = []
        if not nome:
            errors.append("Nome é obrigatório.")
        if not email:
            errors.append("Email é obrigatório.")
        elif models.get_user_by_email(email):
            errors.append("Email já cadastrado.")
        if not senha:
            errors.append("Senha é obrigatória.")
        elif len(senha) < 4:
            errors.append("Senha deve ter pelo menos 4 caracteres.")
        elif senha != confirmacao:
            errors.append("Senhas não conferem.")
        if not escola_id:
            errors.append("Escola é obrigatória.")
        try:
            telefone = _validate_telefone(telefone_ddd, telefone_numero)
        except ValueError as e:
            errors.append(str(e))
            telefone = ""
        if consentimento != 1:
            errors.append("É necessário consentir com os termos.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("registrar.html", schools=models.list_schools(),
                                   form=request.form), 400

        from werkzeug.security import generate_password_hash
        models.create_user({
            "nome": nome,
            "email": email,
            "password_hash": generate_password_hash(senha),
            "role": "usuario",
            "escola_id": int(escola_id),
            "ativo": 1,
            "telefone": telefone,
            "whatsapp": whatsapp,
            "consentimento": consentimento,
        })
        flash("Conta criada! Faça login.", "success")
        return redirect(url_for("games.login"))
    return render_template("registrar.html", schools=models.list_schools(), form={})


@bp.route("/logout")
def logout():
    session.clear()
    flash("Sessão encerrada.", "success")
    return redirect(url_for("games.index"))


def _save_uploaded(file_storage, area, slug, field_name):
    """Salva um upload de imagem em data/<area>/<slug>/<field_name>.jpg.
    Retorna o path relativo (área/slug/arquivo.jpg) ou None.
    """
    if not file_storage or not file_storage.filename:
        return None
    data_dir = Path(current_app.config["DATA_DIR"])
    dest_dir = data_dir / area / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    dst = dest_dir / f"{field_name}.jpg"
    # Salva temporário e redimensiona
    tmp = dst.with_suffix(".tmp")
    file_storage.save(tmp)
    resize_image(tmp, dst)
    tmp.unlink(missing_ok=True)
    return f"{area}/{slug}/{field_name}.jpg"


def _save_manual_uploads(files, area, slug):
    """Salva múltiplas páginas de manual: manual_1.jpg, manual_2.jpg, ...
    `files` é uma lista de FileStorage. Retorna lista de paths relativos.
    """
    paths = []
    data_dir = Path(current_app.config["DATA_DIR"])
    dest_dir = data_dir / area / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    idx = 1
    for fs in files:
        if not fs or not fs.filename:
            continue
        dst = dest_dir / f"manual_{idx}.jpg"
        tmp = dst.with_suffix(".tmp")
        fs.save(tmp)
        resize_image(tmp, dst)
        tmp.unlink(missing_ok=True)
        paths.append(f"{area}/{slug}/manual_{idx}.jpg")
        idx += 1
    return paths


def _remove_game_files(area, slug):
    """Remove a pasta data/<area>/<slug>/ do disco."""
    data_dir = Path(current_app.config["DATA_DIR"])
    target = data_dir / area / slug
    if target.exists():
        shutil.rmtree(target)


@bp.route("/")
def index():
    area = request.args.get("area") or None
    q = request.args.get("q") or None
    page = request.args.get("page", 1, type=int)
    if area == "todas":
        area = None
    games_with_avail, pagination = models.get_games_with_availability(area=area, q=q, page=page)
    return render_template("index.html", games=games_with_avail, area=area, q=q,
                           areas=ALLOWED_AREAS, pagination=pagination)


@bp.route("/novo", methods=["GET", "POST"])
@role_required("admin_sistema", "admin_jogos")
def novo():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        area = (request.form.get("area") or "").strip()
        errors = []
        if not nome:
            errors.append("Nome é obrigatório.")
        if area not in ALLOWED_AREAS:
            errors.append("Área inválida.")
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("form.html", game=None, areas=ALLOWED_AREAS,
                                   form=request.form), 400

        slug = slugify(nome)
        data = {
            "nome": nome,
            "area": area,
            "descricao": request.form.get("descricao") or None,
            "regras_resumo": request.form.get("regras_resumo") or None,
            "num_jogadores": request.form.get("num_jogadores") or None,
            "duracao_min": request.form.get("duracao_min") or None,
        }

        comp_path = _save_uploaded(request.files.get("imagem_componentes"), area, slug, "componentes")
        if comp_path:
            data["imagem_componentes"] = comp_path
        perfil_path = _save_uploaded(request.files.get("imagem_perfil"), area, slug, "perfil")
        if perfil_path:
            data["imagem_perfil"] = perfil_path

        manual_files = request.files.getlist("manual_pages")
        manual_paths = _save_manual_uploads(manual_files, area, slug)

        game_id = models.create_game(data)
        if manual_paths:
            models.set_manual_pages(game_id, manual_paths)
        flash(f"Jogo '{nome}' criado.", "success")
        return redirect(url_for("games.detalhe", game_id=game_id))

    return render_template("form.html", game=None, areas=ALLOWED_AREAS, form={})


@bp.route("/<int:game_id>")
def detalhe(game_id):
    game = models.get_game(game_id)
    if not game:
        abort(404)
    pages = models.list_manual_pages(game_id)
    descricao_html = ""
    if game["descricao"]:
        descricao_html = markdown.markdown(game["descricao"], extensions=["extra"])
    status, loan_id = models.get_game_availability(game_id)
    loan_history = []
    user = current_user()
    user_has_active_loan = False
    if user:
        user_has_active_loan = models.user_has_active_loan(user["id"], game_id)
        if user["role"] in ("admin_sistema", "admin_jogos"):
            loan_history = models.get_loan_history(game_id)
    return render_template("detail.html", game=game, pages=pages,
                           descricao_html=descricao_html,
                           availability_status=status, active_loan_id=loan_id,
                           loan_history=loan_history,
                           user_has_active_loan=user_has_active_loan)


@bp.route("/<int:game_id>/editar", methods=["GET", "POST"])
@role_required("admin_sistema", "admin_jogos")
def editar(game_id):
    game = models.get_game(game_id)
    if not game:
        abort(404)

    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        area = (request.form.get("area") or "").strip()
        errors = []
        if not nome:
            errors.append("Nome é obrigatório.")
        if area not in ALLOWED_AREAS:
            errors.append("Área inválida.")
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("form.html", game=game, areas=ALLOWED_AREAS,
                                   form=request.form,
                                   pages=models.list_manual_pages(game_id)), 400

        slug = slugify(nome)
        data = {
            "nome": nome,
            "area": area,
            "descricao": request.form.get("descricao") or None,
            "regras_resumo": request.form.get("regras_resumo") or None,
            "num_jogadores": request.form.get("num_jogadores") or None,
            "duracao_min": request.form.get("duracao_min") or None,
        }

        comp_path = _save_uploaded(request.files.get("imagem_componentes"), area, slug, "componentes")
        if comp_path:
            data["imagem_componentes"] = comp_path
        perfil_path = _save_uploaded(request.files.get("imagem_perfil"), area, slug, "perfil")
        if perfil_path:
            data["imagem_perfil"] = perfil_path

        manual_files = request.files.getlist("manual_pages")
        manual_paths = _save_manual_uploads(manual_files, area, slug) if any(f and f.filename for f in manual_files) else None

        models.update_game(game_id, data)
        if manual_paths is not None:
            models.set_manual_pages(game_id, manual_paths)
        flash(f"Jogo '{nome}' atualizado.", "success")
        return redirect(url_for("games.detalhe", game_id=game_id))

    pages = models.list_manual_pages(game_id)
    return render_template("form.html", game=game, areas=ALLOWED_AREAS,
                           form={}, pages=pages)


@bp.route("/<int:game_id>/excluir", methods=["POST"])
@role_required("admin_sistema", "admin_jogos")
def excluir(game_id):
    game = models.get_game(game_id)
    if not game:
        abort(404)
    nome = game["nome"]
    area = game["area"]
    slug = slugify(nome)
    models.delete_game(game_id)
    _remove_game_files(area, slug)
    flash(f"Jogo '{nome}' excluído.", "success")
    return redirect(url_for("games.index"))


@bp.route("/admin/schools")
@role_required("admin_sistema")
def admin_schools():
    rede = request.args.get("rede") or None
    q = request.args.get("q") or None
    schools = models.list_schools(rede=rede, q=q)
    return render_template("admin_schools.html", schools=schools, rede=rede, q=q)


@bp.route("/admin/schools/criar", methods=["GET", "POST"])
@role_required("admin_sistema")
def admin_schools_criar():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        errors = []
        if not nome:
            errors.append("Nome é obrigatório.")
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("admin_school_form.html", school=None, form=request.form), 400

        data = {
            "nome": nome,
            "codigo_inep": request.form.get("codigo_inep") or None,
            "rede": request.form.get("rede") or None,
            "endereco": request.form.get("endereco") or None,
            "bairro": request.form.get("bairro") or None,
            "cep": request.form.get("cep") or None,
        }
        models.create_school(data)
        flash(f"Escola '{nome}' criada.", "success")
        return redirect(url_for("games.admin_schools"))

    return render_template("admin_school_form.html", school=None, form={})


@bp.route("/admin/schools/<int:school_id>/editar", methods=["GET", "POST"])
@role_required("admin_sistema")
def admin_schools_editar(school_id):
    school = models.get_school(school_id)
    if not school:
        abort(404)

    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        errors = []
        if not nome:
            errors.append("Nome é obrigatório.")
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("admin_school_form.html", school=school, form=request.form), 400

        data = {
            "nome": nome,
            "codigo_inep": request.form.get("codigo_inep") or None,
            "rede": request.form.get("rede") or None,
            "endereco": request.form.get("endereco") or None,
            "bairro": request.form.get("bairro") or None,
            "cep": request.form.get("cep") or None,
        }
        models.update_school(school_id, data)
        flash(f"Escola '{nome}' atualizada.", "success")
        return redirect(url_for("games.admin_schools"))

    return render_template("admin_school_form.html", school=school, form={})


@bp.route("/admin/schools/<int:school_id>/inativar", methods=["POST"])
@role_required("admin_sistema")
def admin_schools_inativar(school_id):
    school = models.get_school(school_id)
    if not school:
        abort(404)
    models.set_school_ativo(school_id, 0)
    flash(f"Escola '{school['nome']}' inativada.", "success")
    return redirect(url_for("games.admin_schools"))


@bp.route("/admin/schools/<int:school_id>/reativar", methods=["POST"])
@role_required("admin_sistema")
def admin_schools_reativar(school_id):
    school = models.get_school(school_id)
    if not school:
        abort(404)
    models.set_school_ativo(school_id, 1)
    flash(f"Escola '{school['nome']}' reativada.", "success")
    return redirect(url_for("games.admin_schools"))


@bp.route("/admin/users")
@role_required("admin_sistema")
def admin_users():
    role = request.args.get("role") or None
    escola_id = request.args.get("escola_id") or None
    users = models.list_users(role=role, escola_id=escola_id, ativo_only=False)
    return render_template("admin_users.html", users=users, role=role, escolas=models.list_schools(ativo_only=False))


@bp.route("/admin/users/<int:user_id>/editar", methods=["GET", "POST"])
@role_required("admin_sistema", "admin_jogos")
def admin_users_editar(user_id):
    user = models.get_user(user_id)
    if not user:
        abort(404)

    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        errors = []
        if not nome:
            errors.append("Nome é obrigatório.")
        telefone_ddd = (request.form.get("telefone_ddd") or "").strip()
        telefone_numero = (request.form.get("telefone_numero") or "").strip()
        telefone = None
        if telefone_ddd or telefone_numero:
            try:
                telefone = _validate_telefone(telefone_ddd, telefone_numero)
            except ValueError as e:
                errors.append(str(e))
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("admin_user_form.html", user=user, escolas=models.list_schools(ativo_only=False),
                                   form=request.form), 400

        data = {"nome": nome}
        if telefone is not None:
            data["telefone"] = telefone
        email = request.form.get("email") or None
        if email:
            data["email"] = email
        escola_id = request.form.get("escola_id") or None
        if escola_id:
            data["escola_id"] = int(escola_id)
        else:
            data["escola_id"] = None
        senha = request.form.get("senha") or ""
        if senha:
            data["senha"] = senha
        ativo = request.form.get("ativo")
        if ativo is not None:
            data["ativo"] = 1 if ativo == "1" else 0
        whatsapp = 1 if request.form.get("whatsapp") == "1" else 0
        data["whatsapp"] = whatsapp
        consentimento = 1 if request.form.get("consentimento") == "1" else 0
        data["consentimento"] = consentimento

        models.update_user(user_id, data)
        flash(f"Usuário '{nome}' atualizado.", "success")
        return redirect(url_for("games.admin_users"))

    form = dict(user)
    t = form.get("telefone") or ""
    form["telefone_ddd"] = t[:2] if len(t) >= 2 else ""
    form["telefone_numero"] = t[2:] if len(t) > 2 else ""
    return render_template("admin_user_form.html", user=user, escolas=models.list_schools(ativo_only=False), form=form)


@bp.route("/admin/users/<int:user_id>/role", methods=["POST"])
@role_required("admin_sistema")
def admin_users_role(user_id):
    user = models.get_user(user_id)
    if not user:
        abort(404)
    nova_role = request.form.get("role")
    if nova_role not in ("admin_sistema", "admin_jogos", "usuario"):
        flash("Papel inválido.", "error")
        return redirect(url_for("games.admin_users"))

    logged_user = current_user()
    if logged_user and user["id"] == logged_user["id"] and nova_role != "admin_sistema":
        flash("Você não pode remover seu próprio papel de administrador.", "error")
        return redirect(url_for("games.admin_users"))

    if (user["role"] == "admin_sistema" and nova_role != "admin_sistema"
            and models.count_admins_sistema() <= 1):
        flash("Não é possível remover o último administrador do sistema.", "error")
        return redirect(url_for("games.admin_users"))

    models.set_user_role(user_id, nova_role)
    flash(f"Papel de '{user['nome']}' alterado para {nova_role}.", "success")
    return redirect(url_for("games.admin_users"))


@bp.route("/admin/users/criar", methods=["GET", "POST"])
@role_required("admin_sistema")
def admin_users_criar():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        email = (request.form.get("email") or "").strip()
        senha = request.form.get("senha") or ""
        confirmacao = request.form.get("confirmacao") or ""
        role = request.form.get("role") or "usuario"
        escola_id = request.form.get("escola_id") or None
        ativo = 1 if request.form.get("ativo") == "1" else 0
        whatsapp = 1 if request.form.get("whatsapp") == "1" else 0
        consentimento = 1 if request.form.get("consentimento") == "1" else 0

        errors = []
        if not nome:
            errors.append("Nome é obrigatório.")
        if not email:
            errors.append("Email é obrigatório.")
        elif models.get_user_by_email(email):
            errors.append("Email já cadastrado.")
        if not senha:
            errors.append("Senha é obrigatória.")
        elif len(senha) < 4:
            errors.append("Senha deve ter pelo menos 4 caracteres.")
        elif senha != confirmacao:
            errors.append("Senhas não conferem.")
        if role not in ("admin_sistema", "admin_jogos", "usuario"):
            errors.append("Papel inválido.")
        try:
            telefone = _validate_telefone(
                request.form.get("telefone_ddd"),
                request.form.get("telefone_numero"),
            )
        except ValueError as e:
            errors.append(str(e))
            telefone = ""

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("admin_user_create.html",
                                   escolas=models.list_schools(ativo_only=False),
                                   form=request.form), 400

        from werkzeug.security import generate_password_hash
        models.create_user({
            "nome": nome,
            "email": email,
            "password_hash": generate_password_hash(senha),
            "role": role,
            "escola_id": int(escola_id) if escola_id else None,
            "ativo": ativo,
            "telefone": telefone,
            "whatsapp": whatsapp,
            "consentimento": consentimento,
        })
        flash(f"Usuário '{nome}' criado com papel {role}.", "success")
        return redirect(url_for("games.admin_users"))

    return render_template("admin_user_create.html",
                           escolas=models.list_schools(ativo_only=False), form={})


@bp.route("/admin/users/<int:user_id>/inativar", methods=["POST"])
@role_required("admin_sistema")
def admin_users_inativar(user_id):
    user = models.get_user(user_id)
    if not user:
        abort(404)
    models.set_user_ativo(user_id, 0)
    flash(f"Usuário '{user['nome']}' inativado.", "success")
    return redirect(url_for("games.admin_users"))


@bp.route("/admin/users/<int:user_id>/reativar", methods=["POST"])
@role_required("admin_sistema")
def admin_users_reativar(user_id):
    user = models.get_user(user_id)
    if not user:
        abort(404)
    models.set_user_ativo(user_id, 1)
    flash(f"Usuário '{user['nome']}' reativado.", "success")
    return redirect(url_for("games.admin_users"))


# ─── Fila de reserva ──────────────────────────────────────────────────

@bp.route("/emprestimos/fila/confirmar/<int:game_id>")
@login_required
def confirmar_fila(game_id):
    game = models.get_game(game_id)
    if not game:
        abort(404)
    queue_count = models.count_queue(game_id)
    return render_template("confirmar_fila.html", game=game, queue_count=queue_count)


@bp.route("/emprestimos/fila/entrar/<int:game_id>", methods=["POST"])
@login_required
def entrar_fila(game_id):
    game = models.get_game(game_id)
    if not game:
        abort(404)
    user = current_user()
    models.add_to_queue(game_id, user["id"])
    flash("Você entrou na fila de reserva.", "success")
    return redirect(url_for("games.index"))


@bp.route("/emprestimos/fila/notificar/<int:game_id>", methods=["POST"])
@role_required("admin_sistema", "admin_jogos")
def notificar_fila(game_id):
    entry = models.notify_next_in_queue(game_id)
    if not entry:
        flash("Fila vazia.", "error")
    else:
        flash(f"Usuário {entry['user_nome']} notificado.", "success")
        # Try to send email if SMTP configured
        from .email import send_notification
        send_notification("queue_available", None, None, entry)
    return redirect(url_for("games.emprestimos_admin"))


@bp.route("/emprestimos/fila/cancelar/<int:entry_id>", methods=["POST"])
@login_required
def cancelar_fila(entry_id):
    models.cancel_queue_entry(entry_id)
    flash("Reserva cancelada.", "success")
    return redirect(url_for("games.emprestimos"))


# ─── Empréstimos (usuário) ──────────────────────────────────────────────

@bp.route("/emprestimos/admin/export.csv")
@role_required("admin_sistema", "admin_jogos")
def export_emprestimos_csv():
    import csv, io
    status = request.args.get("status") or None
    user_id = request.args.get("user_id") or None
    area = request.args.get("area") or None
    data_inicio = request.args.get("data_inicio") or None
    data_fim = request.args.get("data_fim") or None

    loans, _ = models.list_loans_all(
        status=status, user_id=user_id, area=area,
        data_inicio=data_inicio, data_fim=data_fim, page=1, per_page=999999,
    )
    from datetime import date
    hoje = date.today().isoformat()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Jogo", "Área", "Usuário", "Email", "Escola", "Status",
                     "Solicitado em", "Reservado em", "Emprestado em", "Devolvido em",
                     "Devolução Prevista", "Atrasado", "Observações"])
    for loan in loans:
        from app import models as m
        user_detail = m.get_user(loan["user_id"])
        escola_nome = ""
        if user_detail and user_detail["escola_id"]:
            school = m.get_school(user_detail["escola_id"])
            if school:
                escola_nome = school["nome"]
        atrasado = "Sim" if (loan["status"] == "emprestado" and loan["devolucao_prevista"]
                             and loan["devolucao_prevista"] < hoje) else "Não"
        writer.writerow([
            loan["id"], loan["game_nome"], loan["game_area"], loan["user_nome"],
            user_detail["email"] if user_detail else "", escola_nome,
            loan["status"], loan["solicitado_at"], loan["reservado_at"],
            loan["emprestado_at"], loan["devolvido_at"],
            loan["devolucao_prevista"] or "", atrasado, loan["observacoes"] or "",
        ])

    output = si.getvalue()
    si.close()
    return current_app.response_class(
        output, mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=emprestimos.csv"},
    )


LOAN_TRANSITIONS = {
    "aprovar": ("solicitado", "reservado"),
    "emprestar": ("reservado", "emprestado"),
    "devolver": ("emprestado", "devolvido"),
}


def _validate_loan_transition(loan, target_status):
    if loan["status"] == target_status:
        flash(f"Empréstimo já está como {target_status}.", "error")
        return False
    return True


@bp.route("/emprestimos/solicitar/<int:game_id>", methods=["POST"])
@login_required
def solicitar_emprestimo(game_id):
    game = models.get_game(game_id)
    if not game:
        abort(404)

    user = current_user()

    if models.user_has_active_loan(user["id"], game_id):
        flash("Você já possui uma solicitação ou empréstimo ativo para este jogo.", "error")
        return redirect(url_for("games.emprestimos"))

    status, _ = models.get_game_availability(game_id)
    if status != "disponivel":
        # Offer queue entry instead of just rejecting
        flash("Jogo indisponível no momento.", "error")
        return redirect(url_for("games.confirmar_fila", game_id=game_id))
    devolucao_prevista = request.form.get("devolucao_prevista") or ""
    if not devolucao_prevista:
        from datetime import date, timedelta
        devolucao_prevista = (date.today() + timedelta(days=7)).isoformat()

    models.create_loan(game_id, user["id"], devolucao_prevista)
    flash("Solicitação enviada.", "success")
    return redirect(url_for("games.emprestimos"))


@bp.route("/emprestimos")
@login_required
def emprestimos():
    user = current_user()
    page = request.args.get("page", 1, type=int)
    loans, pagination = models.list_loans_by_user(user["id"], page=page)
    from datetime import date
    hoje = date.today().isoformat()
    return render_template("emprestimos.html", loans=loans, hoje=hoje, pagination=pagination)


@bp.route("/emprestimos/<int:loan_id>/cancelar", methods=["POST"])
@login_required
def cancelar_emprestimo(loan_id):
    loan = models.get_loan(loan_id)
    if not loan:
        abort(404)
    user = current_user()
    if loan["user_id"] != user["id"]:
        abort(403)
    if loan["status"] != "solicitado":
        flash("Cancelamento deve ser feito por um administrador.", "error")
        return redirect(url_for("games.emprestimos"))

    models.update_loan_status(loan_id, "cancelado", user["id"], "Cancelado pelo usuário")
    flash("Solicitação cancelada.", "success")
    return redirect(url_for("games.emprestimos"))


@bp.route("/emprestimos/<int:loan_id>/renovar", methods=["POST"])
@login_required
def renovar_emprestimo(loan_id):
    loan = models.get_loan(loan_id)
    if not loan:
        abort(404)
    user = current_user()
    if loan["user_id"] != user["id"]:
        abort(403)
    if loan["status"] != "emprestado":
        flash("Só é possível renovar empréstimos com status emprestado.", "error")
        return redirect(url_for("games.emprestimos"))

    nova_data = request.form.get("nova_devolucao_prevista") or ""
    if not nova_data:
        flash("Informe a nova data de devolução.", "error")
        return redirect(url_for("games.emprestimos"))

    models.set_renovacao_pendente(loan_id, nova_data)
    flash("Pedido de renovação enviado.", "success")
    return redirect(url_for("games.emprestimos"))


# ─── Empréstimos (admin) ───────────────────────────────────────────────

@bp.route("/emprestimos/admin")
@role_required("admin_sistema", "admin_jogos")
def emprestimos_admin():
    status = request.args.get("status") or None
    user_id = request.args.get("user_id") or None
    area = request.args.get("area") or None
    data_inicio = request.args.get("data_inicio") or None
    data_fim = request.args.get("data_fim") or None
    page = request.args.get("page", 1, type=int)

    loans, pagination = models.list_loans_all(
        status=status, user_id=user_id, area=area,
        data_inicio=data_inicio, data_fim=data_fim, page=page,
    )
    from datetime import date
    hoje = date.today().isoformat()
    users_list = models.list_users(ativo_only=False)
    return render_template(
        "emprestimos_admin.html", loans=loans, hoje=hoje,
        users_list=users_list, areas=ALLOWED_AREAS,
        filtros={"status": status, "user_id": user_id, "area": area,
                  "data_inicio": data_inicio, "data_fim": data_fim},
        pagination=pagination,
    )


@bp.route("/emprestimos/<int:loan_id>/aprovar", methods=["POST"])
@role_required("admin_sistema", "admin_jogos")
def aprovar_emprestimo(loan_id):
    loan = models.get_loan(loan_id)
    if not loan:
        abort(404)
    if not _validate_loan_transition(loan, "reservado"):
        return redirect(url_for("games.emprestimos_admin"))
    if loan["status"] != "solicitado":
        abort(400)
    user = current_user()
    models.update_loan_status(loan_id, "reservado", user["id"])
    from .email import send_notification
    send_notification("loan_approved", models.get_loan(loan_id))
    flash("Empréstimo reservado.", "success")
    return redirect(url_for("games.emprestimos_admin"))


@bp.route("/emprestimos/<int:loan_id>/emprestar", methods=["POST"])
@role_required("admin_sistema", "admin_jogos")
def emprestar_jogo(loan_id):
    loan = models.get_loan(loan_id)
    if not loan:
        abort(404)
    if loan["status"] != "reservado":
        abort(400)
    user = current_user()
    devolucao_prevista = request.form.get("devolucao_prevista") or loan["devolucao_prevista"]
    models.update_loan_status(loan_id, "emprestado", user["id"])
    if devolucao_prevista:
        db = get_db()
        db.execute(
            "UPDATE loans SET devolucao_prevista = ? WHERE id = ?",
            (devolucao_prevista, loan_id),
        )
        db.commit()
    from .email import send_notification
    send_notification("loan_loaned", models.get_loan(loan_id))
    flash("Jogo emprestado.", "success")
    return redirect(url_for("games.emprestimos_admin"))


@bp.route("/emprestimos/<int:loan_id>/devolver", methods=["POST"])
@role_required("admin_sistema", "admin_jogos")
def devolver_jogo(loan_id):
    loan = models.get_loan(loan_id)
    if not loan:
        abort(404)
    if loan["status"] != "emprestado":
        abort(400)
    user = current_user()
    models.update_loan_status(loan_id, "devolvido", user["id"])
    flash("Jogo devolvido.", "success")
    return redirect(url_for("games.emprestimos_admin"))


@bp.route("/emprestimos/<int:loan_id>/cancelar/admin", methods=["POST"])
@role_required("admin_sistema", "admin_jogos")
def cancelar_emprestimo_admin(loan_id):
    loan = models.get_loan(loan_id)
    if not loan:
        abort(404)
    if loan["status"] in ("devolvido", "cancelado"):
        abort(400)
    user = current_user()
    observacao = request.form.get("observacao") or "Cancelado por administrador"
    models.update_loan_status(loan_id, "cancelado", user["id"], observacao)
    flash("Empréstimo cancelado.", "success")
    return redirect(url_for("games.emprestimos_admin"))


@bp.route("/emprestimos/<int:loan_id>/renovar/aprovar", methods=["POST"])
@role_required("admin_sistema", "admin_jogos")
def aprovar_renovacao(loan_id):
    loan = models.get_loan(loan_id)
    if not loan:
        abort(404)
    user = current_user()
    models.aprovar_renovacao(loan_id, user["id"])
    from .email import send_notification
    send_notification("renewal_approved", models.get_loan(loan_id))
    flash("Renovação aprovada.", "success")
    return redirect(url_for("games.emprestimos_admin"))


@bp.route("/emprestimos/<int:loan_id>/renovar/rejeitar", methods=["POST"])
@role_required("admin_sistema", "admin_jogos")
def rejeitar_renovacao(loan_id):
    loan = models.get_loan(loan_id)
    if not loan:
        abort(404)
    user = current_user()
    models.rejeitar_renovacao(loan_id, user["id"])
    from .email import send_notification
    send_notification("renewal_rejected", models.get_loan(loan_id))
    flash("Renovação rejeitada.", "success")
    return redirect(url_for("games.emprestimos_admin"))


# ─── Dashboard admin ───────────────────────────────────────────────────

@bp.route("/admin/dashboard")
@role_required("admin_sistema", "admin_jogos")
def admin_dashboard():
    db = get_db()
    total_jogos = db.execute("SELECT COUNT(*) AS c FROM games").fetchone()["c"]
    jogos_por_area = db.execute(
        "SELECT area, COUNT(*) AS c FROM games GROUP BY area ORDER BY area"
    ).fetchall()

    loans_ativos = db.execute(
        "SELECT COUNT(*) AS c FROM loans WHERE status IN ('solicitado','reservado','emprestado')"
    ).fetchone()["c"]
    loans_atrasados = db.execute(
        "SELECT COUNT(*) AS c FROM loans WHERE status='emprestado' AND devolucao_prevista < date('now')"
    ).fetchone()["c"]
    loans_mes = db.execute(
        "SELECT COUNT(*) AS c FROM loans WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
    ).fetchone()["c"]

    top_games = db.execute(
        """SELECT g.nome, g.area, COUNT(l.id) AS total
           FROM loans l JOIN games g ON l.game_id = g.id
           GROUP BY l.game_id ORDER BY total DESC LIMIT 5"""
    ).fetchall()

    top_users = db.execute(
        """SELECT u.nome, COUNT(l.id) AS total
           FROM loans l JOIN users u ON l.user_id = u.id
           GROUP BY l.user_id ORDER BY total DESC LIMIT 5"""
    ).fetchall()

    return render_template("dashboard.html",
        total_jogos=total_jogos, jogos_por_area=jogos_por_area,
        loans_ativos=loans_ativos, loans_atrasados=loans_atrasados,
        loans_mes=loans_mes, top_games=top_games, top_users=top_users,
    )


# ─── Badge de disponibilidade ──────────────────────────────────────────

# ─── Perfil do usuário ─────────────────────────────────────────────────

@bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    user = current_user()
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        email = (request.form.get("email") or "").strip()
        receber_emails = 1 if request.form.get("receber_emails") == "1" else 0
        whatsapp = 1 if request.form.get("whatsapp") == "1" else 0
        consentimento = 1 if request.form.get("consentimento") == "1" else 0
        errors = []
        if not nome:
            errors.append("Nome é obrigatório.")
        if not email:
            errors.append("Email é obrigatório.")
        elif email != user["email"] and models.get_user_by_email(email):
            errors.append("Email já cadastrado.")
        telefone_ddd = (request.form.get("telefone_ddd") or "").strip()
        telefone_numero = (request.form.get("telefone_numero") or "").strip()
        telefone = None
        if telefone_ddd or telefone_numero:
            try:
                telefone = _validate_telefone(telefone_ddd, telefone_numero)
            except ValueError as e:
                errors.append(str(e))
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("perfil.html", form=request.form), 400

        data = {"nome": nome, "email": email, "receber_emails": receber_emails,
                "whatsapp": whatsapp, "consentimento": consentimento}
        if telefone is not None:
            data["telefone"] = telefone
        senha = request.form.get("senha") or ""
        if senha:
            if len(senha) < 4:
                flash("Senha deve ter pelo menos 4 caracteres.", "error")
                return render_template("perfil.html", form=request.form), 400
            data["senha"] = senha

        models.update_user(user["id"], data)
        flash("Perfil atualizado.", "success")
        return redirect(url_for("games.perfil"))
    form = dict(user)
    t = form.get("telefone") or ""
    form["telefone_ddd"] = t[:2] if len(t) >= 2 else ""
    form["telefone_numero"] = t[2:] if len(t) > 2 else ""
    return render_template("perfil.html", form=form)


@bp.route("/media/<path:filename>")
def media(filename):
    data_dir = current_app.config["DATA_DIR"]
    return send_from_directory(data_dir, filename)
