from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import Usuario
from app import db
import json, os
from flask_login import current_user



auth_bp = Blueprint("auth", __name__)


def load_translations(lang="en"):
    path = os.path.join("app", "translations", f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = Usuario.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(t["login_success"], "success")
            return redirect_by_role()  
        else:
            flash(t["login_fail"], "danger")

    return render_template("auth/login.html", t=t)



@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    if request.method == "POST":
        name = request.form["name"]  # ✅ aquí corregido
        email = request.form["email"]
        password = request.form["password"]

        existing_user = Usuario.query.filter_by(email=email).first()
        if existing_user:
            flash(t["register_exists"], "danger")
            return redirect(url_for("auth.register"))

        new_user = Usuario(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="client"  # ✅ aquí también
        )
        db.session.add(new_user)
        db.session.commit()

        flash(t["register_success"], "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", t=t)



def redirect_by_role():
    print("🧭 Detected role:", current_user.role)  # 👈 para debug
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    elif current_user.role == "employee":
        return redirect(url_for("employee.dashboard"))
    elif current_user.role == "client":
        return redirect(url_for("client.dashboard"))
    elif current_user.role == "supervisor":
        return redirect(url_for("supervisor.inspections"))
    elif current_user.role == "master":
        return redirect(url_for("master.list_branches"))
    else:
        return redirect(url_for("public.home"))



@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))