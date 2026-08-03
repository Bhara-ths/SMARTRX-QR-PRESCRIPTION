from extensions import db
from datetime import datetime

class Patient(db.Model):
    __tablename__ = 'patients'
    patient_id = db.Column(db.Integer, primary_key=True)
    patient_uid = db.Column(db.String(20), unique=True, nullable=True) # E.g., PT000001
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    full_name = db.Column(db.String(150), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    age = db.Column(db.Integer)
    gender = db.Column(db.Enum('Male', 'Female', 'Other'))
    blood_group = db.Column(db.String(10))
    phone = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(150), nullable=True)
    address = db.Column(db.Text)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pin_code = db.Column(db.String(20), nullable=True)
    height = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float)
    emergency_contact_name = db.Column(db.String(150), nullable=True)
    emergency_contact_number = db.Column(db.String(20), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    chronic_diseases = db.Column(db.Text, nullable=True)
    past_medical_history = db.Column(db.Text, nullable=True)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('Active', 'Inactive'), default='Active')
