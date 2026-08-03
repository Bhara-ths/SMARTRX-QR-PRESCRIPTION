from extensions import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False) # 'Medicine', 'Appointment', 'Prescription', 'General'
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade="all, delete-orphan"))

class MedicineReminder(db.Model):
    __tablename__ = 'medicine_reminders'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    prescription_medicine_id = db.Column(db.Integer, db.ForeignKey('prescription_medicines.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_of_day = db.Column(db.String(20), nullable=False) # 'Morning', 'Afternoon', 'Evening', 'Night'
    status = db.Column(db.String(20), default='Pending') # 'Pending', 'Taken', 'Skipped'
    
    patient = db.relationship('Patient')
    prescription_medicine = db.relationship('PrescriptionMedicine')

class AppointmentReminder(db.Model):
    __tablename__ = 'appointment_reminders'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.appointment_id'), nullable=False)
    reminder_time = db.Column(db.DateTime, nullable=False)
    is_sent = db.Column(db.Boolean, default=False)

    patient = db.relationship('Patient')
    appointment = db.relationship('Appointment')

class RefillReminder(db.Model):
    __tablename__ = 'refill_reminders'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    prescription_medicine_id = db.Column(db.Integer, db.ForeignKey('prescription_medicines.id'), nullable=False)
    estimated_refill_date = db.Column(db.Date, nullable=False)
    is_sent = db.Column(db.Boolean, default=False)

    patient = db.relationship('Patient')
    prescription_medicine = db.relationship('PrescriptionMedicine')
