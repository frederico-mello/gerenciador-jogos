"""Notificações por email via SMTP (thread separada, opt-in)."""

import os
import smtplib
import threading
from email.message import EmailMessage


def _get_smtp_config():
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT", "587")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    from_addr = os.environ.get("SMTP_FROM", user or "noreply@gerenciador-jogos.local")
    if not host:
        return None
    return {"host": host, "port": int(port), "user": user, "password": password, "from": from_addr}


def send_email(to, subject, body):
    config = _get_smtp_config()
    if not config:
        return
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = config["from"]
    msg["To"] = to
    t = threading.Thread(target=_send, args=(config, msg), daemon=True)
    t.start()


def _send(config, msg):
    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
            server.starttls()
            if config["user"] and config["password"]:
                server.login(config["user"], config["password"])
            server.send_message(msg)
    except Exception:
        pass


def _game_email(user, game, subject, body):
    send_email(user["email"], subject, body)


def _pickup_slot_info(loan):
    from . import models
    if not loan.get("pickup_slot_id"):
        return ""
    slot = models.get_pickup_slot(loan["pickup_slot_id"])
    if not slot:
        return ""
    return models.format_pickup_slot(slot)


def _notify_loan_approved(user, loan):
    from . import models
    game = models.get_game(loan["game_id"])
    slot_info = ""
    if loan["pickup_slot_id"]:
        slot = models.get_pickup_slot(loan["pickup_slot_id"])
        if slot:
            slot_info = f" Horario confirmado: {models.format_pickup_slot(slot)}. Compareca ao balcao neste horario."
    _game_email(user, game, f"Emprestimo reservado: {game['nome']}",
                f"Seu emprestimo de '{game['nome']}' foi reservado.{slot_info}")


def _notify_pickup_requested(user, loan):
    from . import models
    game = models.get_game(loan["game_id"])
    slot_info = "Aguardando definicao de horario."
    if loan["pickup_slot_id"]:
        slot = models.get_pickup_slot(loan["pickup_slot_id"])
        if slot:
            slot_info = f"Horario solicitado: {models.format_pickup_slot(slot)}."
    _game_email(user, game, f"Solicitacao recebida: {game['nome']}",
                f"Recebemos sua solicitacao para '{game['nome']}'. {slot_info} Aguarde aprovacao.")


def _notify_loan_loaned(user, loan):
    from . import models
    game = models.get_game(loan["game_id"])
    _game_email(user, game, f"Jogo emprestado: {game['nome']}",
                f"O jogo '{game['nome']}' foi emprestado a voce. "
                f"Devolucao prevista: {loan.get('devolucao_prevista', 'a combinar')}.")


def _notify_renewal_approved(user, loan):
    from . import models
    game = models.get_game(loan["game_id"])
    _game_email(user, game, f"Renovacao aprovada: {game['nome']}",
                f"Sua renovacao de '{game['nome']}' foi aprovada. "
                f"Nova devolucao prevista: {loan.get('devolucao_prevista', 'a combinar')}.")


def _notify_renewal_rejected(user, loan):
    from . import models
    game = models.get_game(loan["game_id"])
    _game_email(user, game, f"Renovacao rejeitada: {game['nome']}",
                f"Sua renovacao de '{game['nome']}' foi rejeitada. Devolva o jogo na data prevista.")


def _notify_overdue(user, loan):
    from . import models
    game = models.get_game(loan["game_id"])
    _game_email(user, game, f"Devolucao atrasada: {game['nome']}",
                f"O jogo '{game['nome']}' esta com devolucao atrasada. "
                f"Devolucao prevista era: {loan.get('devolucao_prevista', 'desconhecida')}.")


_NOTIFICATION_HANDLERS = {
    "loan_approved": _notify_loan_approved,
    "pickup_requested": _notify_pickup_requested,
    "loan_loaned": _notify_loan_loaned,
    "renewal_approved": _notify_renewal_approved,
    "renewal_rejected": _notify_renewal_rejected,
    "overdue": _notify_overdue,
}


def send_notification(tipo, loan, user=None, extra=None):
    from . import models

    if user is None and loan is not None:
        user = models.get_user(loan["user_id"])
    if user is None:
        return
    try:
        receber = user["receber_emails"]
    except (KeyError, IndexError, TypeError):
        receber = 0
    if not receber or loan is None:
        return

    handler = _NOTIFICATION_HANDLERS.get(tipo)
    if handler:
        handler(user, loan)
    elif tipo == "queue_available" and extra:
        send_email(extra["email"], "Jogo disponivel!",
                   "O jogo que voce reservou esta disponivel. "
                   "Procure o administrador para retirar.")
