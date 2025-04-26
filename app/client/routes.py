from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.decorators import role_required
from app.forms import RequestServiceForm, UpdateProfileForm, ChangePasswordForm
from app.models import Reservation
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
    to_rate = Reservation.query.filter_by(user_id=current_user.id, status="completed").first()

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

    # ✨ Traducciones para los campos select
    form.service_type.choices = [
        ('residential', t["residential"]),
        ('deep', t["deep"]),
        ('office', t["office"])
    ]

    if form.validate_on_submit():
        lat = request.form.get("lat")
        lng = request.form.get("lng")

        # ✨ Crear reservación normal
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

    # ✨ Obtener reservas completadas pero no calificadas
    reservas_completadas = Reservation.query.filter_by(user_id=current_user.id, status="completed").all()
    reservas_no_calificadas = [r for r in reservas_completadas if not r.rating]

    return render_template("client/rate_service.html", reservas=reservas_no_calificadas, t=t)


@client_bp.route("/submit-rating/<int:reservation_id>", methods=["POST"])
@login_required
@role_required("client")
def submit_rating(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)

    # ❌ Seguridad: debe ser su propia reservación, no calificada y completada
    if reservation.user_id != current_user.id or reservation.rating or reservation.status != "completed":
        abort(403)

    # ✨ Soportar recepción por AJAX o formulario clásico
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        data = request.get_json()
        rating_value = int(data.get("rating", 0))
        comment = data.get("comment", "")
    else:
        rating_value = int(request.form.get("rating", 0))
        comment = request.form.get("comment", "")

    # ❌ Validar rango de rating (1 a 5)
    if not 1 <= rating_value <= 5:
        abort(400, description="Invalid rating value.")

    # ✨ Guardar calificación
    rating = Rating(
        reservation_id=reservation.id,
        rating=rating_value,
        comment=comment
    )
    db.session.add(rating)
    db.session.commit()

    # ✨ Respuesta adecuada según tipo de solicitud
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




