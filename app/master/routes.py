from flask import Blueprint, session, render_template, request, redirect, url_for, flash, g
from flask_login import login_required
from werkzeug.security import generate_password_hash
from app.decorators import role_required
from app import db
from app.models import Branch, Usuario
import json, os

master_bp = Blueprint('master', __name__, url_prefix='/master')

def load_translations(lang="en"):
    path = os.path.join("app", "translations", f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@master_bp.before_app_request
def set_language():
    lang = request.args.get("lang")
    if lang:
        session["lang"] = lang
    elif "lang" not in session:
        session["lang"] = "en"

@master_bp.before_app_request
def set_translations():
    lang = session.get("lang", "en")
    g.t = load_translations(lang)

# 📄 Ver lista de sucursales
@master_bp.route('/branches')
@login_required
@role_required('master')
def list_branches():
    branches = Branch.query.all()
    return render_template('master/branches.html', branches=branches, t=g.t)

# ➕ Agregar nueva sucursal y su administrador
@master_bp.route('/branches/add', methods=['GET', 'POST'])
@login_required
@role_required('master')
def add_branch():
    if request.method == 'POST':
        # Datos de la sucursal
        name = request.form['name']
        city = request.form['city']
        phone = request.form['phone']
        email = request.form['email']

        # Crear sucursal
        new_branch = Branch(name=name, city=city, phone=phone, email=email)
        db.session.add(new_branch)
        db.session.flush()  # Obtenemos ID antes de commit

        # Datos del admin
        admin_name = request.form['admin_name']
        admin_email = request.form['admin_email']
        admin_password = request.form['admin_password']

        # Crear usuario admin vinculado a la sucursal
        new_admin = Usuario(
            name=admin_name,
            email=admin_email,
            password_hash=generate_password_hash(admin_password),
            role="admin",
            branch_id=new_branch.id
        )
        db.session.add(new_admin)
        db.session.commit()

        flash(g.t["branch_added_successfully"], 'success')
        return redirect(url_for('master.list_branches'))

    return render_template('master/add_branch.html', t=g.t)

# ✏️ Editar sucursal y su administrador
@master_bp.route('/branches/edit/<int:branch_id>', methods=['GET', 'POST'])
@login_required
@role_required('master')
def edit_branch(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    admin_user = Usuario.query.filter_by(branch_id=branch.id, role="admin").first()

    if request.method == 'POST':
        # Actualizar sucursal
        branch.name = request.form['name']
        branch.city = request.form['city']
        branch.phone = request.form['phone']
        branch.email = request.form['email']

        # Actualizar datos del admin si existe
        if admin_user:
            admin_user.name = request.form['admin_name']
            admin_user.email = request.form['admin_email']
            if request.form['admin_password']:
                admin_user.password_hash = generate_password_hash(request.form['admin_password'])

        db.session.commit()
        flash(g.t["branch_updated_successfully"], 'success')
        return redirect(url_for('master.list_branches'))

    return render_template('master/edit_branch.html', branch=branch, admin_user=admin_user, t=g.t)

# 🗑️ Eliminar sucursal
@master_bp.route('/branches/delete/<int:branch_id>')
@login_required
@role_required('master')
def delete_branch(branch_id):
    branch = Branch.query.get_or_404(branch_id)

    # 🧹 Eliminar usuarios de la sucursal
    for user in branch.usuarios:
        db.session.delete(user)

    # 🧹 Eliminar reservaciones de la sucursal
    for reservation in branch.reservations:
        # Eliminar calificaciones
        if reservation.rating:
            db.session.delete(reservation.rating)
        # Eliminar inspección si existe
        if reservation.inspection:
            db.session.delete(reservation.inspection)
        # Eliminar mensajes de chat
        for message in reservation.chat_messages:
            db.session.delete(message)
        db.session.delete(reservation)

    # Finalmente eliminar la sucursal
    db.session.delete(branch)
    db.session.commit()

    flash(g.t["branch_deleted_successfully"], 'success')
    return redirect(url_for('master.list_branches'))

# 🧪 Ruta de prueba
@master_bp.route('/test')
def test():
    return "Master blueprint working! 🚀"