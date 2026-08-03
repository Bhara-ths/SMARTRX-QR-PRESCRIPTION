from extensions import db
from datetime import datetime

class Appointment(db.Model):
    __tablename__ = 'appointments'
    appointment_id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    department = db.Column(db.String(100))
    reason_for_visit = db.Column(db.String(255))
    appointment_type = db.Column(db.Enum('New', 'Follow-up', 'Emergency'), default='New')
    status = db.Column(db.Enum('Scheduled', 'Completed', 'Cancelled', 'No Show'), default='Scheduled')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    doctor = db.relationship('Doctor')
    patient = db.relationship('Patient')
