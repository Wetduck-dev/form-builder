from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # اصلاحش کن اگر route login تو admin هست
login_manager.login_message = "برای دسترسی به این بخش باید وارد شوید."


@login_manager.user_loader
def load_user(user_id):
    # ایمپورت داخل فانکشن برای جلوگیری از circular import
    from app.models.admin import Admin
    return Admin.query.get(int(user_id))
