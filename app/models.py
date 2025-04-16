from datetime import datetime
from flask_login import UserMixin
from app import db



# 🔗 Tabla intermedia: Empleados por reservación
reservation_employees = db.Table(
    'reservation_employees',
    db.Column('reservation_id', db.Integer, db.ForeignKey('reservation.id'), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
)

# 👤 Modelo de Usuario
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="client")

    def __repr__(self):
        return f"<Usuario {self.email} - {self.role}>"

# 🔁 Modelo de Servicio Recurrente
class RecurringService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)

    service_type = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    notes = db.Column(db.Text)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    time = db.Column(db.Time, nullable=False)  # Hora base
    start_date = db.Column(db.Date, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # weekly, biweekly, monthly
    status = db.Column(db.String(20), default="active")  # active, paused, canceled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("Usuario", backref="recurring_services")

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
    status = db.Column(db.String(20), default="pending")  # pending, accepted, completed, canceled, completed_by_employee
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recurring_id = db.Column(db.Integer, db.ForeignKey("recurring_service.id"))

    user = db.relationship('Usuario', backref='reservations', foreign_keys=[user_id])
    recurring = db.relationship("RecurringService", backref="generated_reservations")
    employees = db.relationship("Usuario", secondary=reservation_employees, backref="assigned_reservations")
    rating = db.relationship("Rating", backref="reservation", uselist=False)

# ⭐ Modelo de Calificación
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey("reservation.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
