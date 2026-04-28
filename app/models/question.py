from app.extensions import db

class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey("pages.id"), nullable=False)

    text = db.Column(db.String(500), nullable=False)

    min_select = db.Column(db.Integer, default=1)
    max_select = db.Column(db.Integer, default=1)

    page = db.relationship("Page", backref="questions")
