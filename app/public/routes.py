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
    lang = session.get("lang", "en")
    t = load_translations(lang)

    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif current_user.role == "employee":
            return redirect(url_for("employee.dashboard"))
        else:
            return redirect(url_for("client.dashboard"))

    return render_template("public/home.html", t=t)

