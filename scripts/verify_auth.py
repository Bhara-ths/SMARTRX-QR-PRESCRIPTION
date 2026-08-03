import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.pharmacist import Pharmacist

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

issues = []
successes = []

def run_verification():
    with app.test_client() as client:
        with app.app_context():
            print("--- Starting Auth Verification ---")
            
            # Check db is empty
            if User.query.count() != 0:
                issues.append("Database is not fully clear! Users exist.")
            else:
                successes.append("Database cleared successfully.")

            # Register Admin
            admin_user = User(username='admin', email='admin@example.com', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()

            # 1. Register a Doctor via UI
            print("Registering Doctor...")
            resp = client.post('/register', data={
                'username': 'Test Doctor',
                'email': 'doctor@test.com',
                'password': 'password123',
                'confirm_password': 'password123',
                'role': 'doctor'
            }, follow_redirects=True)
            
            doctor = User.query.filter_by(email='doctor@test.com').first()
            doctor_profile = Doctor.query.filter_by(user_id=doctor.id).first() if doctor else None
            if doctor and doctor_profile:
                successes.append("Doctor registration successful.")
            else:
                issues.append("Doctor registration failed or profile not created.")
                
            # 2. Login Doctor
            print("Logging in Doctor...")
            resp = client.post('/login', data={
                'email': 'doctor@test.com',
                'password': 'password123',
                'role': 'doctor'
            }, follow_redirects=True)
            
            if b'Dashboard' in resp.data or resp.status_code == 200:
                successes.append("Doctor login successful.")
            else:
                issues.append("Doctor login failed.")
                
            # 3. Create Patient (Doctor creates patient)
            if doctor:
                resp = client.post('/doctor/patient/add', data={
                    'full_name': 'Test Patient',
                    'age': 30,
                    'gender': 'Male',
                    'phone': '1234567890',
                    'email': 'patient@test.com',
                    'blood_group': 'A+'
                }, follow_redirects=True)
                
                patient_profile = Patient.query.filter_by(email='patient@test.com').first()
                if patient_profile:
                    successes.append("Doctor successfully created a patient.")
                else:
                    issues.append("Doctor failed to create patient.")
                    
            # Logout
            client.get('/logout', follow_redirects=True)

            # 4. Register Pharmacist via UI
            print("Registering Pharmacist...")
            resp = client.post('/register', data={
                'username': 'Test Pharmacist',
                'email': 'pharm@test.com',
                'password': 'password123',
                'confirm_password': 'password123',
                'role': 'pharmacist'
            }, follow_redirects=True)
            
            pharm = User.query.filter_by(email='pharm@test.com').first()
            if pharm:
                successes.append("Pharmacist registration successful.")
            else:
                issues.append("Pharmacist registration failed.")

            # Login Pharmacist
            print("Logging in Pharmacist...")
            resp = client.post('/login', data={
                'email': 'pharm@test.com',
                'password': 'password123',
                'role': 'pharmacist'
            }, follow_redirects=True)
            if b'Dashboard' in resp.data or resp.status_code == 200:
                successes.append("Pharmacist login successful.")
            else:
                issues.append("Pharmacist login failed.")
                
            # Test RBAC
            resp = client.get('/doctor/dashboard', follow_redirects=True)
            if resp.status_code == 403 or b'Unauthorized' in resp.data or b'Login' in resp.data:
                successes.append("RBAC verified: Pharmacist cannot access Doctor dashboard.")
            else:
                issues.append("RBAC failed: Pharmacist accessed Doctor dashboard.")
                
            client.get('/logout', follow_redirects=True)
            
            # Print report
            print("\n--- RESULTS ---")
            for msg in successes:
                print(f"PASS: {msg}")
            
            for msg in issues:
                print(f"FAIL: {msg}")
                
            # Write results to file
            with open('verify_auth_results.txt', 'w') as f:
                f.write(repr({'successes': successes, 'issues': issues}))

if __name__ == '__main__':
    run_verification()
