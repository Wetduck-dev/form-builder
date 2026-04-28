from flask import Flask
from config import Config

from app.extensions import db, migrate, login_manager
from app.models.admin import Admin

def create_app():
    app = Flask(__name__ , template_folder = "templates",static_folder = "static",instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # import models so migrations can see them
    from app.models import form, voter, option, vote, otp, admin  # admin را بعداً می‌سازیم

    # register blueprints
    from app.routes.admin import admin_bp
    from app.routes.vote import vote_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(vote_bp, url_prefix="/vote")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app
