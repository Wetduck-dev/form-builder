from app.extensions import db
from datetime import datetime
import json

class FormHistory(db.Model):
    __tablename__ = "form_history"

    id = db.Column(db.Integer, primary_key=True)

    form_id = db.Column(db.Integer, db.ForeignKey("forms.id"), nullable=False)

    action = db.Column(db.String(20), nullable=False)  
    # add / delete / update

    entity_type = db.Column(db.String(20), nullable=False)
    # page / question / option

    entity_id = db.Column(db.Integer, nullable=True)

    snapshot = db.Column(db.Text, nullable=False)  
    # JSON ذخیره می‌کنیم

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
