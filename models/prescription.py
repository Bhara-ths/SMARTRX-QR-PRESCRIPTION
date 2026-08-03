from extensions import db
from datetime import datetime

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    prescription_id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False) # For QR Code
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    diagnosis = db.Column(db.String(255))
    symptoms = db.Column(db.Text)
    clinical_notes = db.Column(db.Text)
    
    # Vitals
    blood_pressure = db.Column(db.String(20))
    pulse = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    oxygen_saturation = db.Column(db.Integer)
    
    follow_up_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('Active', 'Completed', 'Cancelled'), default='Active')

    @property
    def qr_code_path(self):
        return f"{self.uuid}.png"

    medicines = db.relationship('PrescriptionMedicine', backref='prescription', lazy=True, cascade="all, delete-orphan")
    doctor = db.relationship('Doctor')
    patient = db.relationship('Patient')

class PrescriptionMedicine(db.Model):
    __tablename__ = 'prescription_medicines'
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.prescription_id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.medicine_id'), nullable=False)
    medicine_type = db.Column(db.String(50)) # e.g., Tablet, Capsule, Syrup
    dosage = db.Column(db.String(100))
    strength = db.Column(db.String(100))
    frequency = db.Column(db.String(100))
    
    # Timing
    morning = db.Column(db.String(20))
    afternoon = db.Column(db.String(20))
    night = db.Column(db.String(20))
    
    route = db.Column(db.String(100))
    duration = db.Column(db.String(100))
    instructions = db.Column(db.Text)
    food_relation = db.Column(db.Enum('Before Food', 'After Food', 'Anytime'), default='Anytime')
    dispense_status = db.Column(db.String(50), default='Pending') # 'Pending', 'Partially Dispensed', 'Fully Dispensed'
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    refill_count = db.Column(db.Integer, default=0)

    medicine = db.relationship('Medicine')
