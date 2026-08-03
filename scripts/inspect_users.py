import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import User, Doctor, Patient, Pharmacist
from collections import defaultdict
import json

app = create_app()

def inspect_users():
    with app.app_context():
        users = User.query.all()
        
        accounts = []
        emails = defaultdict(list)
        usernames = defaultdict(list)
        issues = []
        
        for u in users:
            emails[u.email].append(u.id)
            usernames[u.username].append(u.id)
            
            can_log_in = True
            missing_profile = False
            
            if u.role == 'doctor':
                if not Doctor.query.filter_by(user_id=u.id).first():
                    missing_profile = True
                    can_log_in = False
                    issues.append(f"Doctor User {u.id} ({u.email}) is missing a Doctor profile.")
            elif u.role == 'patient':
                if not Patient.query.filter_by(user_id=u.id).first():
                    missing_profile = True
                    can_log_in = False
                    issues.append(f"Patient User {u.id} ({u.email}) is missing a Patient profile.")
            elif u.role == 'pharmacist':
                if not Pharmacist.query.filter_by(user_id=u.id).first():
                    missing_profile = True
                    can_log_in = False
                    issues.append(f"Pharmacist User {u.id} ({u.email}) is missing a Pharmacist profile.")
            elif u.role == 'admin':
                # Admins don't need a domain profile
                pass
            else:
                issues.append(f"User {u.id} has invalid role: {u.role}")
                can_log_in = False
                
            if not u.is_active:
                can_log_in = False
                
            accounts.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'role': u.role,
                'is_active': u.is_active,
                'can_log_in': can_log_in,
                'missing_profile': missing_profile
            })
            
        for email, ids in emails.items():
            if len(ids) > 1:
                issues.append(f"Duplicate email found: {email} used by user IDs {ids}")
                
        for username, ids in usernames.items():
            if len(ids) > 1:
                issues.append(f"Duplicate username found: {username} used by user IDs {ids}")
                
        result = {
            'accounts': accounts,
            'issues': issues
        }
        
        with open('user_inspection.json', 'w') as f:
            json.dump(result, f, indent=4)

if __name__ == '__main__':
    inspect_users()
