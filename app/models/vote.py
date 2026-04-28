from app import db
from datetime import datetime

class Vote(db.Model):
    __tablename__ = "votes"

    id = db.Column(db.Integer, primary_key=True)

    form_id = db.Column(db.Integer, db.ForeignKey("forms.id"), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey("voters.id"), nullable=False)

    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey("options.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    form = db.relationship("Form", backref="votes")
    voter = db.relationship("Voter")
    question = db.relationship("Question")
    option = db.relationship("Option")
