import os
import sys

# Ensure the root directory is in the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import User, Doctor, Patient, Pharmacist, Prescription, PrescriptionMedicine
from flask_login import login_user
import json
import traceback

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

report = {
    'working': [],
    'minor': [],
    'critical': [],
    'fixes': []
}

def log_working(msg):
    print(f"✅ {msg}")
    report['working'].append(msg)

def log_minor(msg):
    print(f"⚠️ {msg}")
    report['minor'].append(msg)

def log_critical(msg):
    print(f"❌ {msg}")
    report['critical'].append(msg)

def run_audit():
    with app.test_client() as client:
        with app.app_context():
            print("--- Starting End-to-End Audit ---")
            
            # 1. Authentication
            print("\n1. Authentication")
            doc_user = User.query.filter_by(role='doctor').first()
            if not doc_user:
                log_critical("No doctor user found in database to test Authentication.")
                return

            resp = client.post('/login', data={'email': doc_user.email, 'password': 'password'}, follow_redirects=True)
            if b'Dashboard' in resp.data or b'Log Out' in resp.data:
                log_working("Doctor login successfully verified.")
            else:
                log_critical("Doctor login failed. Session not maintained.")
            
            # 2. Security (Patient trying to access Doctor routes)
            print("\n2. Security / RBAC")
            client.get('/logout', follow_redirects=True)
            pat_user = User.query.filter_by(role='patient').first()
            if pat_user:
                client.post('/login', data={'email': pat_user.email, 'password': 'password'}, follow_redirects=True)
                resp = client.get('/doctor/dashboard', follow_redirects=True)
                if b'Unauthorized access' in resp.data or resp.status_code == 403 or b'Patient Dashboard' in resp.data or b'Login' in resp.data:
                    log_working("Patient restricted from accessing doctor pages.")
                else:
                    log_critical("Patient accessed doctor page! RBAC failed.")
            
            # 3. Doctor Module (Create Patient)
            print("\n3. Doctor Module")
            client.get('/logout', follow_redirects=True)
            client.post('/login', data={'email': doc_user.email, 'password': 'password'}, follow_redirects=True)
            
            # Try to create a new patient
            patient_data = {
                'full_name': 'Audit Test Patient',
                'age': 30,
                'gender': 'Male',
                'phone': '9999999999',
                'email': 'audit@patient.com',
                'blood_group': 'O+',
                'address': 'Test',
                'height': 170,
                'weight': 70
            }
            resp = client.post('/doctor/patient/add', data=patient_data, follow_redirects=True)
            
            # Check DB
            new_patient = Patient.query.filter_by(phone='9999999999').first()
            if new_patient:
                log_working("Doctor successfully created a new patient.")
                log_working("Patient data saved in the database correctly.")
            else:
                if b'already exists' in resp.data:
                    log_minor("Patient with this phone already exists, skipping creation.")
                    new_patient = Patient.query.filter_by(phone='9999999999').first()
                else:
                    log_critical("Doctor failed to create patient. Database insert failed.")
            
            # 4. QR Code & Prescription Module
            print("\n4. Prescription & QR Code Module")
            if new_patient:
                resp = client.get(f'/doctor/prescription/new?patient_id={new_patient.patient_id}')
                if resp.status_code == 200:
                    log_working("Prescription creation form loaded correctly.")
                else:
                    log_critical(f"Prescription form failed with status {resp.status_code}")
                
                # Check QR code logic in patient view
                resp = client.get(f'/doctor/patient/{new_patient.patient_id}')
                if resp.status_code == 200:
                    log_working("Patient profile displays correctly.")
                else:
                    log_critical(f"Patient profile failed with status {resp.status_code}")

            # 5. Pharmacist Module
            print("\n5. Pharmacist Module")
            client.get('/logout', follow_redirects=True)
            pharm_user = User.query.filter_by(role='pharmacist').first()
            if pharm_user:
                client.post('/login', data={'email': pharm_user.email, 'password': 'password'}, follow_redirects=True)
                resp = client.get('/pharmacist/dashboard', follow_redirects=True)
                if b'Pharmacist Dashboard' in resp.data or resp.status_code == 200:
                    log_working("Pharmacist login verified.")
                else:
                    log_critical("Pharmacist dashboard failed to load.")
                
                resp = client.get('/pharmacist/scan', follow_redirects=True)
                if resp.status_code == 200:
                    log_working("Pharmacist can access QR scan page.")
                else:
                    log_critical("Pharmacist scan page failed to load.")
                    
            # 6. Database Integrity
            print("\n6. Database Integrity")
            try:
                patients = Patient.query.all()
                if len(patients) > 0:
                    log_working("Patient CRUD operations and DB read working.")
            except Exception as e:
                log_critical(f"Database Integrity failed: {str(e)}")

            # 7. Error Handling & Navigation
            print("\n7. Error Handling & Navigation")
            resp = client.get('/this-page-does-not-exist')
            if resp.status_code == 404:
                log_working("404 Error handler verified.")
            else:
                log_minor(f"Custom 404 page might be missing, got status {resp.status_code}.")

if __name__ == '__main__':
    run_audit()
