import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# Carga .env
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # ✔️ Configuración desde .env
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-unsafe-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dc_cleaning.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    Migrate(app, db)

    # Importar modelos para que Flask‑Migrate los vea
    with app.app_context():
        from app import models

    # User loader
    from app.models import Usuario
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar blueprints
    from app.public.routes   import public_bp
    from app.auth.routes     import auth_bp
    from app.admin.routes    import admin_bp
    from app.employee.routes import employee_bp
    from app.client.routes   import client_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp,     url_prefix="/auth")
    app.register_blueprint(admin_bp)
    app.register_blueprint(employee_bp, url_prefix="/employee")
    app.register_blueprint(client_bp,   url_prefix="/client")

    # Errores 403 / 404 traducidos
    @app.errorhandler(403)
    def forbidden(error):
        from flask import render_template, session
        import json
        lang = session.get("lang", "en")
        path = os.path.join("app", "translations", f"{lang}.json")
        with open(path, "r", encoding="utf-8") as f:
            t = json.load(f)
        return render_template("errors/403.html", t=t), 403

    @app.errorhandler(404)
    def page_not_found(error):
        from flask import render_template, session
        import json
        lang = session.get("lang", "en")
        path = os.path.join("app", "translations", f"{lang}.json")
        with open(path, "r", encoding="utf-8") as f:
            t = json.load(f)
        return render_template("errors/404.html", t=t), 404

    return app
