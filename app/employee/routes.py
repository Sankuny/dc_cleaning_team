from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from app.decorators import role_required
import json, os
from datetime import datetime
from pytz import timezone

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

    # 🕒 Fecha actual para mostrarla si se desea
    vancouver = timezone("America/Vancouver")
    today = datetime.now(vancouver).date()

    return render_template("employee/dashboard.html", t=t, today=today)

