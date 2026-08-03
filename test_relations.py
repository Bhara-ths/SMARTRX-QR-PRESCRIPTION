from app import create_app
from extensions import db
from models.prescription import Prescription

app = create_app()

with app.app_context():
    rx = Prescription.query.first()
    if rx:
        print(f"Prescription ID: {rx.prescription_id}")
        print(f"Doctor: {rx.doctor.full_name if rx.doctor else 'No doctor relationship'}")
        print(f"Patient: {rx.patient.full_name if rx.patient else 'No patient relationship'}")
    else:
        print("No prescriptions found to test.")
