from app.extensions import db

class Option(db.Model):
    __tablename__ = "options"

    id = db.Column(db.Integer, primary_key=True)

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("questions.id"),
        nullable=False
    )

    text = db.Column(db.String(255), nullable=False)

    question = db.relationship("Question", backref="options")
    order = db.Column(db.Integer, default=0)
