"""Funções de acesso a dados (CRUD de games + manual pages)."""

from datetime import datetime

from werkzeug.security import generate_password_hash

from .db import get_db

SQL_WHERE = " WHERE "
SQL_AND = " AND "
SQL_ORDER_BY_NOME = " ORDER BY nome"
SQL_UPDATED_AT = "updated_at = ?"


def _parse_int(value):
    """Converte value para int, retornando None se value for None ou string vazia."""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return int(value)


def list_games(area=None, q=None, page=1, per_page=20):
    sql = "SELECT * FROM games"
    count_sql = "SELECT COUNT(*) as total FROM games"
    clauses, params = [], []
    if area:
        clauses.append("area = ?")
        params.append(area)
    if q:
        clauses.append("LOWER(nome) LIKE ?")
        params.append(f"%{q.lower()}%")
    if clauses:
        where = SQL_WHERE + SQL_AND.join(clauses)
        sql += where
        count_sql += where
    sql += SQL_ORDER_BY_NOME

    db = get_db()
    total = db.execute(count_sql, params).fetchone()["total"]
    offset = (page - 1) * per_page
    sql += f" LIMIT ? OFFSET ?"
    results = db.execute(sql, params + [per_page, offset]).fetchall()

    pages = max(1, (total + per_page - 1) // per_page)
    pagination = {
        "page": page, "per_page": per_page, "total": total, "pages": pages,
        "has_prev": page > 1, "has_next": page < pages,
        "prev_num": page - 1 if page > 1 else None,
        "next_num": page + 1 if page < pages else None,
    }
    return results, pagination


def get_game(game_id):
    """Retorna um jogo pelo ID, ou None."""
    return get_db().execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()


def list_manual_pages(game_id):
    """Lista as páginas de manual de um jogo, ordenadas por `ordem`."""
    return get_db().execute(
        "SELECT * FROM game_manual_pages WHERE game_id = ? ORDER BY ordem",
        (game_id,),
    ).fetchall()


def set_manual_pages(game_id, paths):
    """Substitui todas as páginas de manual de um jogo por `paths`."""
    db = get_db()
    db.execute("DELETE FROM game_manual_pages WHERE game_id = ?", (game_id,))
    for ordem, path in enumerate(paths or [], start=1):
        db.execute(
            "INSERT INTO game_manual_pages (game_id, ordem, path) VALUES (?, ?, ?)",
            (game_id, ordem, path),
        )


def create_game(data):
    """Insere um novo jogo e retorna seu ID. `data` é dict com campos do form."""
    db = get_db()
    cur = db.execute(
        """INSERT INTO games
           (nome, area, descricao, regras_resumo, num_jogadores, duracao_min,
            imagem_componentes, imagem_perfil)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["nome"],
            data["area"],
            data.get("descricao"),
            data.get("regras_resumo"),
            data.get("num_jogadores"),
            _parse_int(data.get("duracao_min")),
            data.get("imagem_componentes"),
            data.get("imagem_perfil"),
        ),
    )
    game_id = cur.lastrowid
    db.commit()
    return game_id


def update_game(game_id, data):
    """Atualiza um jogo existente. `data` é dict com campos a atualizar."""
    db = get_db()
    fields, params = [], []
    for key in ("nome", "area", "descricao", "regras_resumo",
                "num_jogadores", "imagem_componentes", "imagem_perfil"):
        if key in data and data[key] is not None:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if "duracao_min" in data:
        fields.append("duracao_min = ?")
        params.append(_parse_int(data.get("duracao_min")))
    fields.append(SQL_UPDATED_AT)
    params.append(datetime.now().isoformat(timespec="seconds"))
    params.append(game_id)
    db.execute(f"UPDATE games SET {', '.join(fields)} WHERE id = ?", params)
    db.commit()


def delete_game(game_id):
    """Remove um jogo (e suas páginas em cascade)."""
    db = get_db()
    db.execute("DELETE FROM games WHERE id = ?", (game_id,))
    db.commit()


def list_schools(rede=None, q=None, ativo_only=True):
    """Lista escolas, opcionalmente filtradas por rede, texto no nome e ativo."""
    sql = "SELECT * FROM schools"
    clauses, params = [], []
    if rede:
        clauses.append("rede = ?")
        params.append(rede)
    if q:
        clauses.append("LOWER(nome) LIKE ?")
        params.append(f"%{q.lower()}%")
    if ativo_only:
        clauses.append("ativo = 1")
    if clauses:
        sql += SQL_WHERE + SQL_AND.join(clauses)
    sql += SQL_ORDER_BY_NOME
    return get_db().execute(sql, params).fetchall()


def get_school(school_id):
    """Retorna uma escola pelo ID, ou None."""
    return get_db().execute("SELECT * FROM schools WHERE id = ?", (school_id,)).fetchone()


def get_school_by_inep(codigo_inep):
    """Retorna uma escola pelo código INEP, ou None."""
    return get_db().execute("SELECT * FROM schools WHERE codigo_inep = ?", (codigo_inep,)).fetchone()


def create_school(data):
    """Insere uma nova escola e retorna seu ID."""
    db = get_db()
    cur = db.execute(
        """INSERT INTO schools (codigo_inep, nome, rede, endereco, bairro, cep)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            data.get("codigo_inep"),
            data["nome"],
            data.get("rede"),
            data.get("endereco"),
            data.get("bairro"),
            data.get("cep"),
        ),
    )
    school_id = cur.lastrowid
    db.commit()
    return school_id


def update_school(school_id, data):
    """Atualiza uma escola existente."""
    db = get_db()
    fields, params = [], []
    for key in ("codigo_inep", "nome", "rede", "endereco", "bairro", "cep"):
        if key in data and data[key] is not None:
            fields.append(f"{key} = ?")
            params.append(data[key])
    fields.append(SQL_UPDATED_AT)
    params.append(datetime.now().isoformat(timespec="seconds"))
    params.append(school_id)
    db.execute(f"UPDATE schools SET {', '.join(fields)} WHERE id = ?", params)
    db.commit()


def set_school_ativo(school_id, ativo):
    """Ativa ou inativa uma escola (soft delete)."""
    db = get_db()
    db.execute("UPDATE schools SET ativo = ?, updated_at = ? WHERE id = ?",
               (ativo, datetime.now().isoformat(timespec="seconds"), school_id))
    db.commit()


def upsert_school_by_inep(codigo_inep, data):
    """Idempotente: insere ou atualiza pelo código INEP. Retorna o ID."""
    existing = get_school_by_inep(codigo_inep)
    if existing:
        update_school(existing["id"], data)
        return existing["id"]
    data["codigo_inep"] = codigo_inep
    return create_school(data)


def get_user(user_id):
    """Retorna um usuário pelo ID, ou None."""
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_email(email):
    """Retorna um usuário pelo email, ou None."""
    return get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def create_user(data):
    """Insere um novo usuário e retorna seu ID.
    `data` deve conter: nome, email, password_hash, role, escola_id (opcional), ativo (default 1).
    """
    db = get_db()
    cur = db.execute(
        """INSERT INTO users (nome, email, password_hash, role, escola_id, ativo,
           telefone, whatsapp, consentimento)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["nome"],
            data["email"],
            data.get("password_hash") or generate_password_hash(data.get("senha", "")),
            data.get("role", "usuario"),
            data.get("escola_id"),
            data.get("ativo", 1),
            data.get("telefone", ""),
            data.get("whatsapp", 0),
            data.get("consentimento", 0),
        ),
    )
    user_id = cur.lastrowid
    db.commit()
    return user_id


def update_user(user_id, data):
    """Atualiza um usuário existente.
    Se data contiver 'senha', gera novo hash. Caso contrário, não altera a senha.
    """
    db = get_db()
    fields, params = [], []
    for key in ("nome", "email", "role", "escola_id", "ativo", "receber_emails",
                "telefone", "whatsapp", "consentimento"):
        if key in data and data[key] is not None:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if "senha" in data and data["senha"]:
        fields.append("password_hash = ?")
        params.append(generate_password_hash(data["senha"]))
    fields.append(SQL_UPDATED_AT)
    params.append(datetime.now().isoformat(timespec="seconds"))
    params.append(user_id)
    db.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", params)
    db.commit()


def set_user_role(user_id, role):
    """Promove ou rebaixa um usuário."""
    db = get_db()
    db.execute("UPDATE users SET role = ?, updated_at = ? WHERE id = ?",
               (role, datetime.now().isoformat(timespec="seconds"), user_id))
    db.commit()


def set_user_ativo(user_id, ativo):
    """Ativa ou inativa um usuário (soft delete)."""
    db = get_db()
    db.execute("UPDATE users SET ativo = ?, updated_at = ? WHERE id = ?",
               (ativo, datetime.now().isoformat(timespec="seconds"), user_id))
    db.commit()


def list_users(role=None, escola_id=None, ativo_only=True):
    """Lista usuários, opcionalmente filtrados por role, escola e ativo."""
    sql = "SELECT id, nome, email, role, escola_id, ativo, telefone, whatsapp, created_at, updated_at FROM users"
    clauses, params = [], []
    if role:
        clauses.append("role = ?")
        params.append(role)
    if escola_id:
        clauses.append("escola_id = ?")
        params.append(escola_id)
    if ativo_only:
        clauses.append("ativo = 1")
    if clauses:
        sql += SQL_WHERE + SQL_AND.join(clauses)
    sql += SQL_ORDER_BY_NOME
    return get_db().execute(sql, params).fetchall()


def count_admins_sistema():
    """Retorna o número de usuários com role='admin_sistema'."""
    return get_db().execute(
        "SELECT COUNT(*) AS cnt FROM users WHERE role = 'admin_sistema'"
    ).fetchone()["cnt"]


def user_has_active_loan(user_id, game_id):
    loan = get_db().execute(
        """SELECT id FROM loans
           WHERE game_id = ? AND user_id = ? AND status IN ('solicitado','reservado','emprestado')
           LIMIT 1""",
        (game_id, user_id),
    ).fetchone()
    return loan is not None


def create_loan(game_id, user_id, devolucao_prevista):
    db = get_db()
    cur = db.execute(
        """INSERT INTO loans (game_id, user_id, status, devolucao_prevista, solicitado_at)
           VALUES (?, ?, 'solicitado', ?, ?)""",
        (game_id, user_id, devolucao_prevista, datetime.now().isoformat(timespec="seconds")),
    )
    loan_id = cur.lastrowid
    add_status_history(loan_id, None, "solicitado", user_id)
    db.commit()
    return loan_id


def get_loan(loan_id):
    return get_db().execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()


def list_loans_by_user(user_id, page=1, per_page=30):
    return _list_loans_paginated("l.user_id = ?", [user_id], page, per_page)


def _list_loans_paginated(where_clause, params, page=1, per_page=30):
    base_sql = """SELECT l.*, g.nome AS game_nome, g.area AS game_area, u.nome AS user_nome
                  FROM loans l JOIN games g ON l.game_id = g.id JOIN users u ON l.user_id = u.id"""
    count_sql = "SELECT COUNT(*) AS total FROM loans l JOIN games g ON l.game_id = g.id JOIN users u ON l.user_id = u.id"

    where = SQL_WHERE + where_clause if where_clause else ""
    sql = base_sql + where + " ORDER BY l.created_at DESC"
    count_sql += where

    db = get_db()
    total = db.execute(count_sql, params).fetchone()["total"]
    offset = (page - 1) * per_page
    sql += " LIMIT ? OFFSET ?"
    results = db.execute(sql, params + [per_page, offset]).fetchall()

    pages = max(1, (total + per_page - 1) // per_page)
    pagination = {
        "page": page, "per_page": per_page, "total": total, "pages": pages,
        "has_prev": page > 1, "has_next": page < pages,
        "prev_num": page - 1 if page > 1 else None,
        "next_num": page + 1 if page < pages else None,
    }
    return results, pagination


def list_loans_all(status=None, user_id=None, area=None, data_inicio=None, data_fim=None, page=1, per_page=30):
    clauses, params = [], []
    if status:
        clauses.append("l.status = ?")
        params.append(status)
    if user_id:
        clauses.append("l.user_id = ?")
        params.append(user_id)
    if area:
        clauses.append("g.area = ?")
        params.append(area)
    if data_inicio:
        clauses.append("l.created_at >= ?")
        params.append(data_inicio)
    if data_fim:
        clauses.append("l.created_at <= ?")
        params.append(data_fim)

    where = SQL_AND.join(clauses) if clauses else "1=1"
    return _list_loans_paginated(where, params, page, per_page)


def list_loans_by_game(game_id):
    return get_db().execute(
        """SELECT l.*, u.nome AS user_nome
           FROM loans l JOIN users u ON l.user_id = u.id
           WHERE l.game_id = ? ORDER BY l.created_at DESC""",
        (game_id,),
    ).fetchall()


def update_loan_status(loan_id, novo_status, changed_by, observacao=None):
    db = get_db()
    loan = get_loan(loan_id)
    if not loan:
        return None
    status_anterior = loan["status"]

    now = datetime.now().isoformat(timespec="seconds")
    ts_field = {
        "reservado": "reservado_at",
        "emprestado": "emprestado_at",
        "devolvido": "devolvido_at",
    }.get(novo_status)

    fields = ["status = ?", SQL_UPDATED_AT]
    params = [novo_status, now]
    if ts_field:
        fields.append(f"{ts_field} = ?")
        params.append(now)

    db.execute(f"UPDATE loans SET {', '.join(fields)} WHERE id = ?", params + [loan_id])
    add_status_history(loan_id, status_anterior, novo_status, changed_by, observacao)
    db.commit()
    return loan_id


def set_renovacao_pendente(loan_id, nova_devolucao_prevista):
    db = get_db()
    db.execute(
        """UPDATE loans SET renovacao_pendente = 1, nova_devolucao_prevista = ?, updated_at = ?
           WHERE id = ?""",
        (nova_devolucao_prevista, datetime.now().isoformat(timespec="seconds"), loan_id),
    )
    db.commit()


def aprovar_renovacao(loan_id, changed_by):
    db = get_db()
    loan = get_loan(loan_id)
    if not loan or not loan["nova_devolucao_prevista"]:
        return None
    db.execute(
        """UPDATE loans SET devolucao_prevista = nova_devolucao_prevista,
           renovacao_pendente = 0, nova_devolucao_prevista = NULL, updated_at = ? WHERE id = ?""",
        (datetime.now().isoformat(timespec="seconds"), loan_id),
    )
    add_status_history(loan_id, loan["status"], loan["status"], changed_by, "Renovação aprovada")
    db.commit()
    return loan_id


def rejeitar_renovacao(loan_id, changed_by):
    db = get_db()
    loan = get_loan(loan_id)
    if not loan:
        return None
    db.execute(
        """UPDATE loans SET renovacao_pendente = 0, nova_devolucao_prevista = NULL, updated_at = ?
           WHERE id = ?""",
        (datetime.now().isoformat(timespec="seconds"), loan_id),
    )
    add_status_history(loan_id, loan["status"], loan["status"], changed_by, "Renovação rejeitada")
    db.commit()
    return loan_id


def get_game_availability(game_id):
    loan = get_db().execute(
        """SELECT id, status FROM loans
           WHERE game_id = ? AND status IN ('solicitado','reservado','emprestado')
           ORDER BY id DESC LIMIT 1""",
        (game_id,),
    ).fetchone()
    if not loan:
        return ("disponivel", None)
    return (loan["status"], loan["id"])


def add_to_queue(game_id, user_id):
    db = get_db()
    max_pos = db.execute(
        "SELECT COALESCE(MAX(posicao), 0) + 1 AS p FROM reservation_queue WHERE game_id=? AND status='na_fila'",
        (game_id,)
    ).fetchone()["p"]
    db.execute(
        "INSERT INTO reservation_queue (game_id, user_id, posicao, status) VALUES (?, ?, ?, 'na_fila')",
        (game_id, user_id, max_pos),
    )
    db.commit()


def get_queue(game_id):
    return get_db().execute(
        "SELECT q.*, u.nome AS user_nome, u.email FROM reservation_queue q JOIN users u ON q.user_id=u.id "
        "WHERE q.game_id=? ORDER BY q.posicao", (game_id,)
    ).fetchall()


def get_next_in_queue(game_id):
    return get_db().execute(
        "SELECT q.*, u.nome AS user_nome, u.email FROM reservation_queue q JOIN users u ON q.user_id=u.id "
        "WHERE q.game_id=? AND q.status='na_fila' ORDER BY q.posicao LIMIT 1", (game_id,)
    ).fetchone()


def notify_next_in_queue(game_id):
    entry = get_next_in_queue(game_id)
    if not entry:
        return None
    entry_id = entry["id"]
    db = get_db()
    db.execute("UPDATE reservation_queue SET status='notificado', updated_at=datetime('now') WHERE id=?",
               (entry_id,))
    db.commit()
    return get_db().execute(
        "SELECT q.*, u.nome AS user_nome, u.email FROM reservation_queue q JOIN users u ON q.user_id=u.id WHERE q.id=?",
        (entry_id,)
    ).fetchone()


def cancel_queue_entry(entry_id):
    db = get_db()
    db.execute("UPDATE reservation_queue SET status='cancelado', updated_at=datetime('now') WHERE id=?",
               (entry_id,))
    db.commit()


def count_queue(game_id):
    return get_db().execute(
        "SELECT COUNT(*) AS c FROM reservation_queue WHERE game_id=? AND status='na_fila'",
        (game_id,)
    ).fetchone()["c"]


def count_loans_by_status():
    rows = get_db().execute(
        "SELECT status, COUNT(*) AS cnt FROM loans GROUP BY status"
    ).fetchall()
    return {r["status"]: r["cnt"] for r in rows}


def get_games_with_availability(area=None, q=None, page=1, per_page=20):
    games, pagination = list_games(area=area, q=q, page=page, per_page=per_page)
    result = []
    for g in games:
        status, loan_id = get_game_availability(g["id"])
        queue_count = count_queue(g["id"])
        result.append({**g, "availability_status": status, "active_loan_id": loan_id, "queue_count": queue_count})
    return result, pagination


def add_status_history(loan_id, status_anterior, status_novo, changed_by, observacao=None):
    db = get_db()
    db.execute(
        """INSERT INTO loan_status_history (loan_id, status_anterior, status_novo, changed_by, observacao)
           VALUES (?, ?, ?, ?, ?)""",
        (loan_id, status_anterior, status_novo, changed_by, observacao),
    )
    db.commit()


def list_status_history(loan_id):
    return get_db().execute(
        """SELECT h.*, u.nome AS changed_by_nome
           FROM loan_status_history h
           JOIN users u ON h.changed_by = u.id
           WHERE h.loan_id = ? ORDER BY h.changed_at""",
        (loan_id,),
    ).fetchall()


def get_loan_history(game_id):
    return get_db().execute(
        """SELECT l.*, u.nome AS user_nome
           FROM loans l JOIN users u ON l.user_id = u.id
           WHERE l.game_id = ? ORDER BY l.created_at DESC""",
        (game_id,),
    ).fetchall()


def upsert_game_by_area_nome(area, nome, data, manual_paths=None):
    """Idempotente: insere ou atualiza pela chave (area, nome). Retorna o ID."""
    db = get_db()
    row = db.execute(
        "SELECT id FROM games WHERE area = ? AND nome = ?", (area, nome)
    ).fetchone()
    if row:
        game_id = row["id"]
        update_game(game_id, data)
        if manual_paths is not None:
            set_manual_pages(game_id, manual_paths)
        return game_id
    data["nome"] = nome
    data["area"] = area
    game_id = create_game(data)
    if manual_paths is not None:
        set_manual_pages(game_id, manual_paths)
    return game_id
