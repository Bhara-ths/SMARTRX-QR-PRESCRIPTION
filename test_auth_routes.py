import sys
import traceback
from app import create_app
from extensions import db
from models import User, Doctor, Patient, Pharmacist

app = create_app()

def login_and_test(role, email, password, prefix):
    with app.test_client() as client:
        with app.app_context():
            print(f"\n--- Testing {role.upper()} routes ---")
            resp = client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)
            if b'Invalid email or password' in resp.data:
                print(f"Could not login as {role}")
                return
            
            rules = [rule for rule in app.url_map.iter_rules() if 'GET' in rule.methods and str(rule).startswith(prefix)]
            errors = []
            for rule in rules:
                if '<' not in str(rule):
                    path = str(rule)
                    try:
                        resp = client.get(path)
                        if resp.status_code == 500:
                            errors.append(f"500 Internal Error on {path}")
                        else:
                            print(f"OK: {path} -> {resp.status_code}")
                    except Exception as e:
                        errors.append(f"Exception on {path}: {str(e)}")
            
            if errors:
                for e in errors:
                    print(e)
            else:
                print(f"No 500 errors found for {role}!")

if __name__ == '__main__':
    with app.app_context():
        # Find one of each user
        admin = User.query.filter_by(role='admin').first()
        doc = User.query.filter_by(role='doctor').first()
        pat = User.query.filter_by(role='patient').first()
        pharm = User.query.filter_by(role='pharmacist').first()
        
    if admin: login_and_test('admin', admin.email, 'password', '/admin')
    if doc: login_and_test('doctor', doc.email, 'password', '/doctor')
    if pat: login_and_test('patient', pat.email, 'password', '/patient')
    if pharm: login_and_test('pharmacist', pharm.email, 'password', '/pharmacist')
