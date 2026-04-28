from app import db
from datetime import datetime, timedelta

class OTP(db.Model):
    __tablename__ = "otp_codes"

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        if not self.created_at:
            return False
        now = datetime.utcnow()
        return (now - self.created_at) < timedelta(minutes=3)
