from app.extensions import db


class Voter(db.Model):
    __tablename__ = "voters"

    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey("forms.id"), nullable=False)

    national_id = db.Column(db.String(10), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    has_voted = db.Column(db.Boolean, default=False)

    form = db.relationship("Form", backref="voters")
