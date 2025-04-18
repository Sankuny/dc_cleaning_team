# app/sockets/chat_socket.py
from flask_socketio import emit, join_room
from flask_login import current_user
from app.models import Reservation, ChatMessage
from app import db 

def register_chat_events(socketio):

    @socketio.on("join")
    def on_join(data):
        room = f"service_{data['service_id']}"
        join_room(room)
        # (opcional) Confirmación de unión
        emit("status", {
            "msg": f"{current_user.name} joined the chat."
        }, room=room)

    @socketio.on("send_message")
    def handle_send_message(data):
        service_id = data.get("service_id")
        message_text = data.get("message", "").strip()

        # Validación: ¿el usuario pertenece a ese servicio?
        service = Reservation.query.get(service_id)
        if not service or not (
            current_user.id == service.user_id or
            current_user in service.employees or
            current_user.role == "admin"
        ):
            return  # No autorizado

        # Guardar el mensaje en la base de datos
        msg = ChatMessage(
            service_id=service_id,
            sender_id=current_user.id,
            message=message_text
        )
        db.session.add(msg)
        db.session.commit()

        # Enviar a todos los conectados a esta sala
        room = f"service_{service_id}"
        emit("receive_message", {
            "id":         msg.id,
            "service_id": service_id,              
            "sender_id":  current_user.id,
            "sender":     current_user.name,
            "role":       current_user.role,
            "message":    message_text,
            "timestamp":  msg.timestamp.strftime('%H:%M %d/%m/%Y')
        }, room=room)
