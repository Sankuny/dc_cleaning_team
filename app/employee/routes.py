from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models import Reservation, Rating
from app.decorators import role_required
from app import db
import json, os
from pytz import timezone
from sqlalchemy import func

employee_bp = Blueprint("employee", __name__)

def load_translations(lang="en"):
    path = os.path.join("app", "translations", f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@employee_bp.route("/dashboard")
@login_required
@role_required("employee")
def dashboard():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    # 🕒 Obtener fecha de hoy en zona horaria de Vancouver
    vancouver = timezone("America/Vancouver")
    now_vancouver = datetime.now(vancouver)
    today = now_vancouver.date()
    end_of_week = today + timedelta(days=6)

    # 🔄 Servicios de HOY
    today_services = Reservation.query\
        .filter(Reservation.employees.any(id=current_user.id))\
        .filter(func.date(Reservation.date) == today).all()

    # 🔄 Servicios de la SEMANA
    week_services = Reservation.query\
        .filter(Reservation.employees.any(id=current_user.id))\
        .filter(func.date(Reservation.date).between(today, end_of_week)).all()

    # 🌟 Calificaciones recibidas
    ratings = Rating.query\
        .join(Reservation)\
        .filter(Reservation.employees.any(id=current_user.id))\
        .order_by(Rating.created_at.desc())\
        .limit(5).all()

    # ⭐ Promedio de calificaciones
    avg_rating = db.session.query(db.func.avg(Rating.rating))\
        .join(Reservation)\
        .filter(Reservation.employees.any(id=current_user.id))\
        .scalar()

    return render_template("employee/dashboard.html",
                           t=t,
                           today_services=today_services,
                           week_count=len(week_services),
                           today_count=len(today_services),
                           ratings=ratings,
                           average_rating=round(avg_rating or 0, 1))


@employee_bp.route("/mark-completed/<int:id>", methods=["POST"])
@login_required
@role_required("employee")
def mark_completed(id):
    reservation = Reservation.query.get_or_404(id)

    # Solo si está realmente "assigned"
    if reservation.status != "assigned":
        return ("Bad request", 400)

    # Verifica que el empleado forme parte de la reserva
    if current_user not in reservation.employees:
        return ("Unauthorized", 403)

    # Marca como completado por empleado
    reservation.status = "completed_by_employee"
    db.session.commit()

    # Respuesta AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return ("", 204)

    flash("Marked as completed. Awaiting client confirmation.", "success")
    return redirect(url_for("employee.dashboard"))


@employee_bp.route("/assigned")
@login_required
@role_required("employee")
def assigned_services():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    # Todas las reservas donde el empleado está asignado
    services = Reservation.query\
        .filter(Reservation.employees.any(id=current_user.id))\
        .order_by(Reservation.date.desc(), Reservation.time).all()

    return render_template("employee/assigned_services.html", t=t, services=services)
