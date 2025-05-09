from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
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
    branch_id = current_user.branch_id

    total_users = Usuario.query.filter_by(branch_id=branch_id).count()
    total_clients = Usuario.query.filter_by(branch_id=branch_id, role="client").count()
    total_employees = Usuario.query.filter_by(branch_id=branch_id, role="employee").count()
    total_reservations = Reservation.query.filter_by(branch_id=branch_id).count()

    pending_services = Reservation.query.filter_by(branch_id=branch_id, status="pending").all()
    accepted_count = Reservation.query.filter_by(branch_id=branch_id, status="accepted").count()
    completed_count = Reservation.query.filter_by(branch_id=branch_id, status="completed").count()
    confirmed_pending = Reservation.query.filter_by(branch_id=branch_id, status="completed_by_employee").count()

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
    if reservation.branch_id != current_user.branch_id:
        abort(403)
    if reservation.status == "pending":
        reservation.status = "accepted"
        db.session.commit()
        flash("Service accepted.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_user():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"].strip()
        password = request.form["password"]

        if not email:
            flash("Email cannot be empty.", "danger")
            return redirect(url_for("admin.create_user"))

        existing_user = Usuario.query.filter(db.func.lower(Usuario.email) == email.lower()).first()
        if existing_user:
            flash(t["register_exists"], "danger")
            return redirect(url_for("admin.create_user"))

        new_user = Usuario(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=request.form.get("role", "employee"),
            branch_id=current_user.branch_id
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
    if user.branch_id != current_user.branch_id:
        abort(403)

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

    if user.branch_id != current_user.branch_id:
        abort(403)
    if user.role == "admin":
        flash("You cannot delete an admin user.", "danger")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin.users"))

@admin_bp.route("/all-chats")
@login_required
@role_required("admin")
def all_chats():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    services = Reservation.query.filter_by(branch_id=current_user.branch_id)\
                                 .order_by(Reservation.created_at.desc()).all()
    return render_template("admin/all_chats.html", services=services, t=t)

@admin_bp.route("/users")
@login_required
@role_required("admin")
def users():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    role_filter = request.args.get("role")
    branch_id = current_user.branch_id

    if role_filter:
        users = Usuario.query.filter_by(branch_id=branch_id, role=role_filter).all()
    else:
        users = Usuario.query.filter_by(branch_id=branch_id).all()

    return render_template("admin/users.html", users=users, t=t, role_filter=role_filter)