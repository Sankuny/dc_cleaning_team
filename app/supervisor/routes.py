import os
import json
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Reservation, Inspection
from app.decorators import role_required

supervisor_bp = Blueprint("supervisor", __name__, url_prefix="/supervisor")

# 𝔳 Traducciones multilenguaje
def load_translations(lang="en"):
    try:
        path = os.path.join("app", "translations", f"{lang}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[⚠️] Translation file for '{lang}' not found. Falling back to English.")
        with open(os.path.join("app", "translations", "en.json"), "r", encoding="utf-8") as f:
            return json.load(f)

# 📋 Cargar checklist fijo
base_path = os.path.dirname(os.path.abspath(__file__))
checklist_path = os.path.join(base_path, "..", "data", "inspection_checklist.json")
with open(checklist_path, "r", encoding="utf-8") as f:
    CLEANING_CHECKLIST = json.load(f)

# 👋 Ver servicios del día para inspeccionar
@supervisor_bp.route("/inspections")
@login_required
@role_required("supervisor")
def inspections():
    lang = session.get("lang", "en")
    t = load_translations(lang)

    today = date.today()
    services_today = Reservation.query.filter(
        db.func.date(Reservation.date) == today
    ).all()

    # Ahora se ven servicios "accepted"
    pending = [r for r in services_today if r.status == "accepted"]

    return render_template("supervisor/inspections.html", pending=pending, t=t)

# ✅ Inspeccionar un servicio aceptado
@supervisor_bp.route("/inspect/<int:reservation_id>", methods=["GET", "POST"])
@login_required
@role_required("supervisor")
def inspect(reservation_id):
    lang = session.get("lang", "en")
    t = load_translations(lang)

    reservation = Reservation.query.get_or_404(reservation_id)

    # Solo inspeccionar servicios "accepted"
    if reservation.status != "accepted":
        flash(t.get("not_ready_for_inspection", "This service is not ready for inspection."), "warning")
        return redirect(url_for("supervisor.inspections"))

    if request.method == "POST":
        checklist_result = {}
        fallas_detectadas = False

        for area, tasks in CLEANING_CHECKLIST.items():
            checklist_result[area] = {}
            for index, task in enumerate(tasks):
                field_name = f"{area}_{index}"
                is_checked = request.form.get(field_name) == "on"
                checklist_result[area][str(index)] = {
                    "completed": is_checked,
                    "photo": None
                }

                if not is_checked:
                    file_field = f"{area}_{index}_photo"
                    if file_field in request.files:
                        photo = request.files[file_field]
                        if photo and photo.filename:
                            filename = f"{reservation.id}_{area}_{index}_{secure_filename(photo.filename)}"
                            photo_path = os.path.join("static", "uploads", "inspections")
                            os.makedirs(photo_path, exist_ok=True)
                            photo.save(os.path.join(photo_path, filename))
                            checklist_result[area][str(index)]["photo"] = f"uploads/inspections/{filename}"
                            fallas_detectadas = True

        rating = int(request.form.get("rating", 0))
        comment = request.form.get("comment", "")

        # Guardar inspección
        inspection = Inspection(
            reservation_id=reservation.id,
            supervisor_id=current_user.id,
            area_checklist=checklist_result,
            comment=comment,
            rating=rating,
            approved=not fallas_detectadas,
            timestamp=datetime.utcnow()
        )
        db.session.add(inspection)

        # ✅ Cambiar estado de la reservación a "completed"
        reservation.status = "completed"

        db.session.commit()

        flash(t.get("inspection_saved", "Inspection saved successfully."), "success")
        return redirect(url_for("supervisor.inspections"))

    return render_template("supervisor/inspect.html", reservation=reservation, checklist=CLEANING_CHECKLIST, t=t)
