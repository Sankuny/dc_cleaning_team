from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import Usuario, Reservation
from app import db
import json, os
from werkzeug.security import generate_password_hash


admin_bp = Blueprint("admin", __name__)

def load_translations(lang="en"):
    path = os.path.join("app", "translations", f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    # Stats
    total_users = Usuario.query.count()
    total_clients = Usuario.query.filter_by(role="client").count()
    total_employees = Usuario.query.filter_by(role="employee").count()
    total_reservations = Reservation.query.count()

    pending_services = Reservation.query.filter_by(status="pending").all()
    accepted_count = Reservation.query.filter_by(status="accepted").count()
    completed_count = Reservation.query.filter_by(status="completed").count()
    confirmed_pending = Reservation.query.filter_by(status="completed_by_employee").count()

    return render_template("admin/dashboard.html",
                           t=t,
                           total_users=total_users,
                           total_clients=total_clients,
                           total_employees=total_employees,
                           total_reservations=total_reservations,
                           pending_services=pending_services,
                           accepted_count=accepted_count,
                           completed_count=completed_count,
                           confirmed_pending=confirmed_pending)

@admin_bp.route("/accept-service/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def accept_service(id):
    reservation = Reservation.query.get_or_404(id)
    if reservation.status == "pending":
        reservation.status = "accepted"
        db.session.commit()
        flash("Service accepted.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/accept-all-services", methods=["POST"])
@login_required
@role_required("admin")
def accept_all_services():
    reservations = Reservation.query.filter_by(status="pending").all()
    for r in reservations:
        r.status = "accepted"
    db.session.commit()
    flash("All pending services have been accepted.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/assign-employees")
@login_required
@role_required("admin")
def assign_employees():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    # Servicios aceptados sin empleados asignados
    accepted_services = Reservation.query\
        .filter_by(status="accepted")\
        .filter(~Reservation.employees.any())\
        .all()

    # Todos los empleados
    employees = Usuario.query.filter_by(role="employee").all()

    return render_template("admin/assign_employees.html",
                           t=t,
                           services=accepted_services,
                           employees=employees)

@admin_bp.route("/assign-employees/<int:reservation_id>", methods=["POST"])
@login_required
@role_required("admin")
def assign_employees_post(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    selected_ids = request.form.getlist("employees")

    if not selected_ids:
        flash("You must select at least one employee.", "danger")
        return redirect(url_for("admin.assign_employees"))

    # Limpia y asigna
    reservation.employees = Usuario.query.filter(Usuario.id.in_(selected_ids)).all()
    db.session.commit()
    flash("Employees assigned successfully!", "success")
    return redirect(url_for("admin.assign_employees"))

@admin_bp.route("/users")
@login_required
@role_required("admin")
def users():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    # Filtrar por rol si se proporciona en la query string
    role_filter = request.args.get("role")
    if role_filter:
        users = Usuario.query.filter_by(role=role_filter).all()
    else:
        users = Usuario.query.all()

    return render_template("admin/users.html", t=t, users=users, role_filter=role_filter)


@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_user():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Check if email already exists
        if Usuario.query.filter_by(email=email).first():
            flash(t["register_exists"], "danger")
            return redirect(url_for("admin.create_user"))

        new_user = Usuario(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="employee"
        )
        db.session.add(new_user)
        db.session.commit()
        flash(t["user_created"], "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/create_user.html", t=t)

@admin_bp.route("/users/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_user(id):
    lang = session.get("lang", "en")
    t = load_translations(lang)

    user = Usuario.query.get_or_404(id)

    if request.method == "POST":
        user.name = request.form["name"]
        user.email = request.form["email"]

        new_password = request.form.get("password")
        if new_password:
            user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/edit_user.html", user=user, t=t)

@admin_bp.route("/users/delete/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(id):
    user = Usuario.query.get_or_404(id)

    # Prevenir eliminar admins si quieres protegerlos
    if user.role == "admin":
        flash("You cannot delete an admin user.", "danger")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin.users"))


