from flask import Blueprint, render_template, abort, request, redirect, url_for, session
from flask_login import login_required, current_user
from app.models import Reservation, ChatMessage
from app import db
import os, json

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

# 🌍 Traducciones
def load_translations(lang="en"):
    path = os.path.join("app", "translations", f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@chat_bp.route("/<int:service_id>", methods=["GET", "POST"])
@login_required
def chat(service_id):
    service = Reservation.query.get_or_404(service_id)

    if not (
        current_user.id == service.user_id or
        current_user in service.employees or
        current_user.role == "admin"
    ):
        abort(403)

    # Traducciones
    lang = session.get("lang", "en")
    t = load_translations(lang)

    # Enviar mensaje
    if request.method == "POST":
        message_text = request.form.get("message")
        if message_text:
            new_msg = ChatMessage(
                service_id=service.id,
                sender_id=current_user.id,
                message=message_text
            )
            db.session.add(new_msg)
            db.session.commit()
            return redirect(url_for("chat.chat", service_id=service.id))

    # Mensajes anteriores
    messages = ChatMessage.query.filter_by(service_id=service.id).order_by(ChatMessage.timestamp).all()

    return render_template("chat/chat.html", service=service, messages=messages, t=t)

@chat_bp.route("/messages/<int:service_id>")
@login_required
def get_messages(service_id):
    service = Reservation.query.get_or_404(service_id)

    if not (
        current_user.id == service.user_id or
        current_user in service.employees or
        current_user.role == "admin"
    ):
        abort(403)

    messages = ChatMessage.query.filter_by(service_id=service_id).order_by(ChatMessage.timestamp).all()

    return {
        "messages": [
            {
                "id": msg.id,
                "sender": msg.sender.name,
                "role": msg.sender.role,
                "message": msg.message,
                "timestamp": msg.timestamp.strftime('%H:%M')
            }
            for msg in messages
        ]
    }


@chat_bp.route("/embed/<int:service_id>")
@login_required
def chat_embed(service_id):
    service = Reservation.query.get_or_404(service_id)
    # ... mismo control de acceso que en la vista normal ...
    messages = ChatMessage.query.filter_by(service_id=service.id).order_by(ChatMessage.timestamp).all()
    lang     = session.get("lang","en")
    t        = load_translations(lang)
    return render_template("chat/embed.html",
                           service=service,
                           messages=messages,
                           t=t)
