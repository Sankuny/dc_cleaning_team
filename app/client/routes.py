from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.decorators import role_required
from app.forms import RequestServiceForm, UpdateProfileForm, ChangePasswordForm
from app.models import Reservation, RecurringService
from app import db
import os, json
from flask import abort
from app.models import Rating


client_bp = Blueprint("client", __name__)  # ✅ ESTA LÍNEA ES VITAL

def load_translations(lang="en"):
    path = os.path.join("app", "translations", f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
@client_bp.route("/dashboard")
@login_required
@role_required("client")
def dashboard():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    # Notificación si tiene servicios por calificar
    to_rate = Reservation.query.filter_by(user_id=current_user.id, status="completed_by_employee").first()

    # Última solicitud (puedes personalizarlo si prefieres mostrar solo 'pending', etc.)
    latest_service = Reservation.query.filter_by(user_id=current_user.id)\
                                      .order_by(Reservation.created_at.desc()).first()

    return render_template("client/dashboard.html", t=t, name=current_user.name,
                           to_rate=to_rate, latest_service=latest_service)




@client_bp.route("/request-service", methods=["GET", "POST"])
@login_required
@role_required("client")
def request_service():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    form = RequestServiceForm()

    # Traducciones para los campos select
    form.service_type.choices = [
        ('residential', t["residential"]),
        ('deep', t["deep"]),
        ('office', t["office"])
    ]
    form.frequency.choices = [
        ('weekly', t["weekly"]),
        ('biweekly', t["biweekly"]),
        ('monthly', t["monthly"])
    ]

    if form.validate_on_submit():
        lat = request.form.get("lat")
        lng = request.form.get("lng")

        if form.recurrent.data:
            # Primero crea el servicio recurrente como plantilla
            recurring = RecurringService(
                user_id=current_user.id,
                service_type=form.service_type.data,
                address=form.address.data,
                notes=form.notes.data,
                lat=float(lat) if lat else None,
                lng=float(lng) if lng else None,
                start_date=form.date.data,
                frequency=form.frequency.data,
                status="active"
            )
            db.session.add(recurring)
            db.session.flush()  # Obtener el id sin hacer commit

            # Luego crea la reserva inicial enlazada
            reservation = Reservation(
                user_id=current_user.id,
                service_type=form.service_type.data,
                date=form.date.data,
                time=form.time.data,
                address=form.address.data,
                notes=form.notes.data,
                lat=float(lat) if lat else None,
                lng=float(lng) if lng else None,
                recurring_id=recurring.id
            )
            db.session.add(reservation)

        else:
            # Solo crea la reserva
            reservation = Reservation(
                user_id=current_user.id,
                service_type=form.service_type.data,
                date=form.date.data,
                time=form.time.data,
                address=form.address.data,
                notes=form.notes.data,
                lat=float(lat) if lat else None,
                lng=float(lng) if lng else None
            )
            db.session.add(reservation)

        db.session.commit()
        flash(t["request_success"], "success")
        return redirect(url_for("client.dashboard"))

    return render_template("client/request_service.html", form=form, t=t)





@client_bp.route("/rate-service", methods=["GET", "POST"])
@login_required
@role_required("client")
def rate_service():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    # ✅ Solo servicios que fueron completados por el empleado y no han sido calificados aún
    reservas = Reservation.query.filter_by(user_id=current_user.id, status="completed_by_employee").all()
    no_calificados = [r for r in reservas if not r.rating]

    return render_template("client/rate_service.html", reservas=no_calificados, t=t)



@client_bp.route("/submit-rating/<int:reservation_id>", methods=["POST"])
@login_required
@role_required("client")
def submit_rating(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)

    if reservation.user_id != current_user.id or reservation.rating or reservation.status != "completed_by_employee":
        abort(403)

    # ✅ Soportar JSON recibido por AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        data = request.get_json()
        rating_value = int(data.get("rating"))
        comment = data.get("comment", "")
    else:
        # Fallback por si algún día usas POST clásico
        rating_value = int(request.form["rating"])
        comment = request.form.get("comment", "")

    # Guardar calificación
    rating = Rating(
        reservation_id=reservation.id,
        rating=rating_value,
        comment=comment
    )
    db.session.add(rating)

    # Cambiar estado a "completed"
    reservation.status = "completed"
    db.session.commit()

    # ✅ Devolver respuesta adecuada si fue por AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return "", 204

    flash("Thank you for confirming and rating the service!", "success")
    return redirect(url_for("client.rate_service"))





@client_bp.route("/service-history")
@login_required
@role_required("client")
def service_history():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    # Obtener solo las reservas con estado "Completed"
    reservations = Reservation.query.filter_by(user_id=current_user.id, status="completed")\
                                    .order_by(Reservation.date.desc())\
                                    .all()

    return render_template("client/service_history.html", reservations=reservations, t=t)



@client_bp.route("/profile")
@login_required
@role_required("client")
def profile():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    update_form = UpdateProfileForm(obj=current_user)
    password_form = ChangePasswordForm()

    return render_template("client/profile.html", t=t, update_form=update_form, password_form=password_form)

@client_bp.route("/profile/update", methods=["POST"])
@login_required
@role_required("client")
def update_profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your information has been updated.", "success")
    else:
        flash("Please check the form for errors.", "danger")
    return redirect(url_for("client.profile"))

from werkzeug.security import check_password_hash, generate_password_hash

@client_bp.route("/profile/change-password", methods=["POST"])
@login_required
@role_required("client")
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("client.profile"))

        current_user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash("Password updated successfully.", "success")
    else:
        flash("Please check the form for errors.", "danger")
    return redirect(url_for("client.profile"))

from app.models import RecurringService  # Asegúrate de importar el modelo correcto

# 🔁 Ver servicios recurrentes del cliente
@client_bp.route("/recurring-services")
@login_required
@role_required("client")
def recurring_services():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    services = RecurringService.query.filter_by(
        user_id=current_user.id
    ).filter(RecurringService.status.in_(["active", "paused"])).all()

    return render_template("client/recurring_services.html", services=services, t=t)

# 🟡 Pausar servicio
@client_bp.route("/pause-recurring/<int:id>", methods=["POST"])
@login_required
@role_required("client")
def pause_recurring(id):
    recurring = RecurringService.query.get_or_404(id)
    if recurring.user_id != current_user.id:
        abort(403)
    recurring.status = "paused"
    db.session.commit()
    flash("Service paused.", "info")
    return redirect(url_for("client.recurring_services"))

# 🟢 Reanudar servicio
@client_bp.route("/resume-recurring/<int:id>", methods=["POST"])
@login_required
@role_required("client")
def resume_recurring(id):
    recurring = RecurringService.query.get_or_404(id)
    if recurring.user_id != current_user.id:
        abort(403)
    recurring.status = "active"
    db.session.commit()
    flash("Service resumed.", "success")
    return redirect(url_for("client.recurring_services"))

# 🔴 Cancelar servicio
@client_bp.route("/cancel-recurring/<int:id>", methods=["POST"])
@login_required
@role_required("client")
def cancel_recurring(id):
    recurring = RecurringService.query.get_or_404(id)
    if recurring.user_id != current_user.id:
        abort(403)
    recurring.status = "canceled"
    db.session.commit()
    flash("Service canceled.", "warning")
    return redirect(url_for("client.recurring_services"))
