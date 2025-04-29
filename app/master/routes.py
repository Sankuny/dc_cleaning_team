from flask import Blueprint,session, render_template, request, redirect, url_for, flash, g
from flask_login import login_required
from app.decorators import role_required
from app import db
from app.models import Branch
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
        session["lang"] = "en"  # idioma por defecto

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

# ➕ Agregar nueva sucursal
@master_bp.route('/branches/add', methods=['GET', 'POST'])
@login_required
@role_required('master')
def add_branch():
    if request.method == 'POST':
        name = request.form['name']
        city = request.form['city']
        phone = request.form['phone']
        email = request.form['email']

        new_branch = Branch(name=name, city=city, phone=phone, email=email)
        db.session.add(new_branch)
        db.session.commit()

        flash('Branch added successfully!', 'success')
        return redirect(url_for('master.list_branches'))

    return render_template('master/add_branch.html', t=g.t)

# ✏️ Editar sucursal existente
@master_bp.route('/branches/edit/<int:branch_id>', methods=['GET', 'POST'])
@login_required
@role_required('master')
def edit_branch(branch_id):
    branch = Branch.query.get_or_404(branch_id)

    if request.method == 'POST':
        branch.name = request.form['name']
        branch.city = request.form['city']
        branch.phone = request.form['phone']
        branch.email = request.form['email']

        db.session.commit()
        flash('Branch updated successfully!', 'success')
        return redirect(url_for('master.list_branches'))

    return render_template('master/edit_branch.html', branch=branch, t=g.t)

# 🗑️ Eliminar sucursal
@master_bp.route('/branches/delete/<int:branch_id>')
@login_required
@role_required('master')
def delete_branch(branch_id):
    branch = Branch.query.get_or_404(branch_id)

    db.session.delete(branch)
    db.session.commit()

    flash('Branch deleted successfully!', 'success')
    return redirect(url_for('master.list_branches'))

# 🧪 Ruta de prueba
@master_bp.route('/test')
def test():
    return "Master blueprint working! 🚀"
