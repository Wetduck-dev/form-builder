from app.extensions import db

class Page(db.Model):
    __tablename__ = "pages"

    id = db.Column(db.Integer, primary_key=True)

    form_id = db.Column(
        db.Integer,
        db.ForeignKey("forms.id"),
        nullable=False
    )

    title = db.Column(db.String(255))

    order = db.Column(db.Integer, default=0)

    form = db.relationship("Form", backref="pages")
