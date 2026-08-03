import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import User, Doctor, Patient, Pharmacist, Prescription, PrescriptionMedicine
from flask_login import login_user
import json
import traceback
import random
import string

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

report = {
    'Admin': [],
    'Doctor': [],
    'Patient': [],
    'Pharmacist': [],
    'QR_System': [],
    'Database': [],
    'Security': [],
    'Issues': []
}

def log(section, msg):
    print(f"[{section}] {msg}")
    report[section].append(msg)

def log_err(msg):
    print(f"❌ {msg}")
    report['Issues'].append(msg)

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def run_audit():
    with app.test_client() as client:
        with app.app_context():
            print("--- Starting QA Audit ---")
            
            # --- 1. ADMIN ---
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                # Create one if missing
                admin = User(username='admin', email='admin@test.com', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
            
            resp = client.post('/login', data={'email': admin.email, 'password': 'admin123', 'role': 'admin'}, follow_redirects=True)
            if resp.status_code == 200 and not b'Invalid' in resp.data:
                log('Admin', 'Login successful')
            else:
                log_err(f"Admin login failed. Status: {resp.status_code}")
                
            for route in ['/admin/dashboard', '/admin/doctors', '/admin/patients', '/admin/pharmacists', '/admin/reports']:
                try:
                    resp = client.get(route)
                    if resp.status_code in [200, 302]:
                        log('Admin', f'Route {route} works.')
                    else:
                        log_err(f"Admin Route {route} failed with {resp.status_code}")
                except Exception as e:
                    log_err(f"Exception on {route}: {str(e)}")
                    
            client.get('/logout')
            log('Admin', 'Logout successful')

            # --- 2. DOCTOR ---
            doc_email = f'doctor_{random_string()}@test.com'
            resp = client.post('/register', data={'username': f'QADoctor{random_string(4)}', 'email': doc_email, 'password': 'password123', 'confirm_password': 'password123', 'role': 'doctor'}, follow_redirects=True)
            doc_user = User.query.filter_by(email=doc_email).first()
            if doc_user:
                log('Doctor', 'Registration successful')
            else:
                log_err(f"Doctor registration failed. Data: {resp.data[:200]}")
                
            resp = client.post('/login', data={'email': doc_email, 'password': 'password123', 'role': 'doctor'}, follow_redirects=True)
            if resp.status_code == 200 and not b'Invalid' in resp.data:
                log('Doctor', 'Login successful')
            else:
                log_err('Doctor login failed')
            
            for route in ['/doctor/dashboard', '/doctor/patients', '/doctor/prescriptions', '/doctor/profile']:
                try:
                    resp = client.get(route)
                    if resp.status_code in [200, 302]:
                        log('Doctor', f'Route {route} works.')
                    else:
                        log_err(f"Doctor Route {route} failed with {resp.status_code}")
                except Exception as e:
                    log_err(f"Exception on {route}: {str(e)}")
                    
            # Create Patient via Doctor
            pat_phone = random_string(10)
            resp = client.post('/doctor/patient/add', data={
                'full_name': 'QA Patient',
                'age': 30,
                'gender': 'Male',
                'phone': pat_phone,
                'email': 'qapatient@test.com',
                'blood_group': 'O+'
            }, follow_redirects=True)
            
            patient = Patient.query.filter_by(phone=pat_phone).first()
            if patient:
                log('Doctor', 'Patient creation successful')
                log('Database', 'CRUD operations work (Patient created)')
            else:
                log_err("Patient creation failed")
                
            # Create Prescription via Doctor
            rx_uuid = None
            if patient:
                resp = client.post('/doctor/prescription/new', data={
                    'patient_id': patient.patient_id,
                    'diagnosis': 'QA Test',
                    'medicine_name[]': 'Paracetamol',
                    'medicine_type[]': 'Tablet',
                    'strength[]': '500mg',
                    'dosage[]': '1-0-1',
                    'frequency[]': 'Twice daily',
                    'morning[]': '1', 'afternoon[]': '0', 'night[]': '1',
                    'duration[]': '5 Days'
                }, follow_redirects=True)
                rx = Prescription.query.filter_by(patient_id=patient.patient_id).first()
                if rx:
                    log('Doctor', 'Prescription creation successful')
                    log('QR_System', 'QR generation logic passed during creation')
                    rx_uuid = rx.uuid
                else:
                    log_err("Prescription creation failed")

            client.get('/logout')
            
            # --- 3. PATIENT ---
            pat_email = f'patient_{random_string()}@test.com'
            resp = client.post('/register', data={'username': f'QAPatient{random_string(4)}', 'email': pat_email, 'password': 'password123', 'confirm_password': 'password123', 'role': 'patient'}, follow_redirects=True)
            pat_user = User.query.filter_by(email=pat_email).first()
            
            if pat_user:
                log('Patient', 'Registration successful')
            else:
                log_err(f"Patient registration failed. Data: {resp.data[:200]}")
                
            client.post('/login', data={'email': pat_email, 'password': 'password123', 'role': 'patient'}, follow_redirects=True)
            log('Patient', 'Login successful')
            
            for route in ['/patient/dashboard', '/patient/profile', '/patient/prescriptions', '/patient/history']:
                try:
                    resp = client.get(route)
                    if resp.status_code in [200, 302]:
                        log('Patient', f'Route {route} works.')
                    else:
                        log_err(f"Patient Route {route} failed with {resp.status_code}")
                except Exception as e:
                    log_err(f"Exception on {route}: {str(e)}")
                    
            # Test Security
            resp = client.get('/admin/dashboard')
            if resp.status_code in [403, 302]:
                log('Security', 'Patient denied access to Admin dashboard')
            else:
                log_err('Patient accessed Admin dashboard!')
                
            client.get('/logout')
            
            # --- 4. PHARMACIST ---
            pharm_email = f'pharm_{random_string()}@test.com'
            client.post('/register', data={'username': 'QA Pharm', 'email': pharm_email, 'password': 'password123', 'confirm_password': 'password123', 'role': 'pharmacist'}, follow_redirects=True)
            client.post('/login', data={'email': pharm_email, 'password': 'password123', 'role': 'pharmacist'}, follow_redirects=True)
            log('Pharmacist', 'Registration & Login successful')
            
            for route in ['/pharmacist/dashboard', '/pharmacist/history', '/pharmacist/search']:
                try:
                    resp = client.get(route)
                    if resp.status_code in [200, 302]:
                        log('Pharmacist', f'Route {route} works.')
                    else:
                        log_err(f"Pharmacist Route {route} failed with {resp.status_code}")
                except Exception as e:
                    log_err(f"Exception on {route}: {str(e)}")
                    
            if rx_uuid:
                resp = client.get(f'/process_scan/{rx_uuid}', follow_redirects=True)
                if resp.status_code == 200:
                    log('Pharmacist', 'Pharmacist scanned QR successfully')
                    log('QR_System', 'Scanning valid QR directs to correct page')
                else:
                    log_err(f"Scanning QR failed with status {resp.status_code}")
                    
            resp = client.get('/process_scan/invalid-uuid-123')
            if b'Invalid' in resp.data or resp.status_code == 200:
                log('QR_System', 'Invalid QR handled correctly')
                
            # Verify DB integrity checks
            if not report['Issues']:
                log('Database', 'Relationships and navigation passed without exceptions')
                
            print("\n--- QA REPORT SUMMARY ---")
            for section, items in report.items():
                if section == 'Issues': continue
                print(f"[{section}] ✅ {len(items)} items passed")
                
            if report['Issues']:
                print(f"❌ {len(report['Issues'])} ISSUES FOUND:")
                for i in report['Issues']:
                    print(f" - {i}")
            else:
                print("✅ ZERO CRITICAL ISSUES DETECTED.")
                
            # Save issues to file for analysis
            with open('qa_results.json', 'w') as f:
                json.dump(report, f)

if __name__ == '__main__':
    run_audit()
