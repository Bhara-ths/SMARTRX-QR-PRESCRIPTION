from extensions import db
from datetime import datetime

class Hospital(db.Model):
    __tablename__ = 'hospitals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    registration_number = db.Column(db.String(100))
    logo_path = db.Column(db.String(255))
    
    # Address
    address = db.Column(db.String(500))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    google_maps_url = db.Column(db.String(500))
    
    # Contact
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    website = db.Column(db.String(255))
    emergency_contact = db.Column(db.String(50))
    
    # Details
    working_hours = db.Column(db.String(255))
    description = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    doctors = db.relationship('Doctor', backref='hospital_rel', lazy=True)
    pharmacists = db.relationship('Pharmacist', backref='hospital_rel', lazy=True)
