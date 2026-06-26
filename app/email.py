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
        pass  # Silently fail - notifications are best-effort


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
    if not receber:
        return  # Opt-out

    if loan is None:
        return

    if tipo == "loan_approved":
        game = models.get_game(loan["game_id"])
        slot_info = ""
        if loan["pickup_slot_id"]:
            slot = models.get_pickup_slot(loan["pickup_slot_id"])
            if slot:
                slot_info = f" Horario confirmado: {models.format_pickup_slot(slot)}. Compareca ao balcao neste horario."
        send_email(user["email"], f"Emprestimo reservado: {game['nome']}",
                   f"Seu emprestimo de '{game['nome']}' foi reservado.{slot_info}")
    elif tipo == "pickup_requested":
        game = models.get_game(loan["game_id"])
        slot_info = "Aguardando definicao de horario."
        if loan["pickup_slot_id"]:
            slot = models.get_pickup_slot(loan["pickup_slot_id"])
            if slot:
                slot_info = f"Horario solicitado: {models.format_pickup_slot(slot)}."
        send_email(user["email"], f"Solicitacao recebida: {game['nome']}",
                   f"Recebemos sua solicitacao para '{game['nome']}'. {slot_info} Aguarde aprovacao.")
    elif tipo == "loan_loaned":
        game = models.get_game(loan["game_id"])
        send_email(user["email"], f"Jogo emprestado: {game['nome']}",
                   f"O jogo '{game['nome']}' foi emprestado a você. "
                   f"Devolução prevista: {loan.get('devolucao_prevista', 'a combinar')}.")
    elif tipo == "renewal_approved":
        game = models.get_game(loan["game_id"])
        send_email(user["email"], f"Renovação aprovada: {game['nome']}",
                   f"Sua renovação de '{game['nome']}' foi aprovada. "
                   f"Nova devolução prevista: {loan.get('devolucao_prevista', 'a combinar')}.")
    elif tipo == "renewal_rejected":
        game = models.get_game(loan["game_id"])
        send_email(user["email"], f"Renovação rejeitada: {game['nome']}",
                   f"Sua renovação de '{game['nome']}' foi rejeitada. Devolva o jogo na data prevista.")
    elif tipo == "overdue":
        game = models.get_game(loan["game_id"])
        send_email(user["email"], f"Devolução atrasada: {game['nome']}",
                   f"O jogo '{game['nome']}' está com devolução atrasada. "
                   f"Devolução prevista era: {loan.get('devolucao_prevista', 'desconhecida')}.")
    elif tipo == "queue_available":
        if extra:
            send_email(extra["email"], "Jogo disponível!",
                       f"O jogo que você reservou está disponível. "
                       f"Procure o administrador para retirar.")
