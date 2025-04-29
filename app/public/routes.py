from flask import Blueprint, render_template, session, request, redirect, url_for
import json, os
from flask_login import current_user


public_bp = Blueprint("public", __name__)


def load_translations(lang="en"):
    path = os.path.join("app", "translations", f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@public_bp.before_app_request
def set_language():
    lang = request.args.get("lang")
    if lang:
        session["lang"] = lang
    elif "lang" not in session:
        session["lang"] = "en"  # idioma por defecto

@public_bp.route("/")
def home():
    from flask import g

    # 📥 Detectar idioma
    lang = session.get("lang", "en")
    t = load_translations(lang)
    g.t = t  # Opcional si quieres mantenerlo accesible en g

    # 🔒 Si el usuario está autenticado, redirigir según su rol
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif current_user.role == "employee":
            return redirect(url_for("employee.dashboard"))
        elif current_user.role == "supervisor":
            return redirect(url_for("supervisor.inspections"))  # inspections es su dashboard
        elif current_user.role == "master":
            return redirect(url_for("master.list_branches"))  # redirigir al panel de master
        else:
            return redirect(url_for("client.dashboard"))  # 👈 el cliente redirige aquí

    # 🌐 Renderizar home público si no ha iniciado sesión
    return render_template("public/home.html", t=t)

