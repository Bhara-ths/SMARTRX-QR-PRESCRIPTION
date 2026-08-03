import os
from app import create_app
from extensions import db
from models.audit import PatientDeletionAudit

app = create_app()

with app.app_context():
    db.create_all()
    print("patient_deletion_audit table created if it didn't exist.")
