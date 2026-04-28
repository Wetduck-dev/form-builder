from app.extensions import db
from datetime import datetime
import secrets

class Form(db.Model):
    __tablename__ = "forms"
    __table_args__ = {'sqlite_autoincrement': True}


    id = db.Column(db.Integer, primary_key=True , autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    token = db.Column(db.String(64), nullable=False, unique=True, default=lambda: secrets.token_hex(16))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_active = db.Column(db.Boolean, default=True)

    # این فیلد را اضافه کن
    is_finalized = db.Column(db.Boolean, default=False)

    status = db.Column(db.String(20), default="draft")
