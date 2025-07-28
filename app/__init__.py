# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

def create_app() -> Flask:
    """
    Application-factory function.
    """
    app = Flask(__name__)

    # ── Core config ────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///parking.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # ── Blueprints ────────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.user import user_bp
    from app.routes.home import home_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(home_bp)

    # ── One-time DB/table creation + admin seeding ────────────────
    with app.app_context():
        db.create_all()

        # Import models *after* db.init_app(app) so the metadata is bound
        from app.models.admin import Admin  # Import Admin model instead

        # Credentials come from env vars with safe defaults
        admin_email = os.environ.get("APP_ADMIN_EMAIL", "admin@gmail.com")
        admin_pass = os.environ.get("APP_ADMIN_PASSWORD", "admin123")

        # Only create if an admin with that e-mail doesn't exist
        if not Admin.query.filter_by(email=admin_email).first():
            admin = Admin(
                username="admin",  # Add this line
                email=admin_email,
                password_hash=generate_password_hash(admin_pass),
            )
            db.session.add(admin)
            db.session.commit()
            app.logger.info(f"✅ Default admin <{admin_email}> created.")
        else:
            app.logger.info("ℹ️  Admin already exists; skipping seeding.")

    return app