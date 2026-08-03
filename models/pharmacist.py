from extensions import db

class Pharmacist(db.Model):
    __tablename__ = 'pharmacists'
    pharmacist_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('pharmacist', uselist=False))
    full_name = db.Column(db.String(150), nullable=False)
    pharmacy_name = db.Column(db.String(150)) # Legacy
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'))
    license_number = db.Column(db.String(50))
    phone = db.Column(db.String(20))
