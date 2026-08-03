import os
from app import create_app
from extensions import db
from models.user import User

app = create_app()

def update_emails():
    with app.app_context():
        # Find Admin
        admin = User.query.filter_by(email='gunavardhan815@gmail.com', role='admin').first()
        if admin:
            print(f"Updating Admin email from {admin.email} to admin@smartrx.com")
            admin.email = 'admin@smartrx.com'
            db.session.commit()
        else:
            print("Admin not found with that email.")
            
        # Find Doctor
        doctor = User.query.filter_by(email='gunavardhan815@gmail.com', role='doctor').first()
        if doctor:
            print(f"Updating Doctor email from {doctor.email} to doctor.gunavardhan@smartrx.com")
            doctor.email = 'doctor.gunavardhan@smartrx.com'
            db.session.commit()
        else:
            print("Doctor not found with that email.")
            
        # Verify
        admin_check = User.query.filter_by(email='admin@smartrx.com', role='admin').first()
        if admin_check:
            print(f"Admin verification passed! ID: {admin_check.id}, Email: {admin_check.email}")
            print(f"Password Check for Admin: {admin_check.check_password('gunav123@')}")
            
        doctor_check = User.query.filter_by(email='doctor.gunavardhan@smartrx.com', role='doctor').first()
        if doctor_check:
            print(f"Doctor verification passed! ID: {doctor_check.id}, Email: {doctor_check.email}")
            print(f"Password Check for Doctor: {doctor_check.check_password('guna123@')}")

if __name__ == "__main__":
    update_emails()
