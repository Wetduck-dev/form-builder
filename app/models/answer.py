from app import db
from datetime import datetime

class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)

    form_id = db.Column(db.Integer, nullable=False)
    voter_id = db.Column(db.Integer, nullable=False)

    question_id = db.Column(db.Integer, nullable=False)

    option_id = db.Column(db.Integer, nullable=True)

    value = db.Column(db.Text)

    file_path = db.Column(db.String(300))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
