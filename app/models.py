from datetime import datetime
from flask_login import UserMixin
from app import db

# 👤 Modelo de Usuario
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="client")

    def __repr__(self):
        return f"<Usuario {self.email} - {self.role}>"

# 📅 Modelo de Reservación
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    service_type = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    address = db.Column(db.String(200))
    notes = db.Column(db.Text)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    status = db.Column(db.String(20), default="pending")  # pending, accepted, completed, canceled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Usuario', backref='reservations')
    rating = db.relationship('Rating', backref='reservation', uselist=False)
    inspection = db.relationship('Inspection', back_populates='reservation', uselist=False)

# ⭐ Modelo de Calificación
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ✅ Modelo de Inspección por parte del supervisor
class Inspection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    area_checklist = db.Column(db.JSON, nullable=False)  # Estructura por áreas con evidencia
    comment = db.Column(db.Text)
    rating = db.Column(db.Integer)
    approved = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    reservation = db.relationship('Reservation', back_populates='inspection', lazy=True)
    supervisor = db.relationship('Usuario', backref='inspections', lazy=True)

# 💬 Modelo de Mensajes de Chat
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('Usuario', backref='sent_messages')
