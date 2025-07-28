from flask import Blueprint

# Importing all blueprints
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.user import user_bp
from app.routes.home import home_bp


