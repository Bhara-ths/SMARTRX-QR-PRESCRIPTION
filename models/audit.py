from extensions import db
from datetime import datetime

class QRScanHistory(db.Model):
    __tablename__ = 'qr_scan_history'
    scan_id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.prescription_id'), nullable=False)
    pharmacist_id = db.Column(db.Integer, db.ForeignKey('pharmacists.pharmacist_id'), nullable=True) # Nullable if scanned by patient/system
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    status = db.Column(db.Enum('Success', 'Failed', 'Tampered'), default='Success')

    prescription = db.relationship('Prescription')
    pharmacist = db.relationship('Pharmacist')

class DispensingHistory(db.Model):
    __tablename__ = 'dispensing_history'
    dispense_id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.prescription_id'), nullable=False)
    pharmacist_id = db.Column(db.Integer, db.ForeignKey('pharmacists.pharmacist_id'), nullable=False)
    dispensed_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    prescription = db.relationship('Prescription')
    pharmacist = db.relationship('Pharmacist')

class MedicineDispensing(db.Model):
    __tablename__ = 'medicine_dispensing'
    id = db.Column(db.Integer, primary_key=True)
    prescription_medicine_id = db.Column(db.Integer, db.ForeignKey('prescription_medicines.id'), nullable=False)
    pharmacist_id = db.Column(db.Integer, db.ForeignKey('pharmacists.pharmacist_id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50)) # 'Dispensed', 'Partially Dispensed', 'Not Available', 'Cancelled'
    remarks = db.Column(db.Text)
    dispensed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    prescription_medicine = db.relationship('PrescriptionMedicine', backref='dispensing_logs')
    pharmacist = db.relationship('Pharmacist')

class PatientDeletionAudit(db.Model):
    __tablename__ = 'patient_deletion_audit'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, nullable=False)
    doctor_name = db.Column(db.String(150), nullable=False)
    patient_id = db.Column(db.Integer, nullable=False)
    patient_name = db.Column(db.String(150), nullable=False)
    deleted_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

class SystemAuditLog(db.Model):
    __tablename__ = 'system_audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Nullable for pre-login errors or system events
    action = db.Column(db.String(100), nullable=False) # e.g. "Login", "Logout", "Create Doctor"
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
