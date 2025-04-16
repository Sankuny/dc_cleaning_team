from flask import Blueprint, render_template, session, request, redirect, url_for
import json, os

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
    return render_template("public/home.html", t=t)
