import os
from app import create_app
from extensions import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.pharmacist import Pharmacist
from sqlalchemy import text

app = create_app()

def migrate():
    with app.app_context():
        # 1. Drop existing unique constraints
        try:
            # For MySQL, it's typically ALTER TABLE users DROP INDEX username, DROP INDEX email
            # We will use raw SQL
            db.session.execute(text("ALTER TABLE users DROP INDEX email"))
            db.session.execute(text("ALTER TABLE users DROP INDEX username"))
            print("Dropped old unique constraints.")
        except Exception as e:
            print("Failed to drop old constraints (might not exist):", e)
            
        # 2. Add composite unique constraints
        try:
            db.session.execute(text("ALTER TABLE users ADD CONSTRAINT uq_email_role UNIQUE (email, role)"))
            db.session.execute(text("ALTER TABLE users ADD CONSTRAINT uq_username_role UNIQUE (username, role)"))
            print("Added new composite constraints.")
        except Exception as e:
            print("Failed to add new constraints (might already exist):", e)
            
        db.session.commit()
        
        # 3. Fix shared accounts
        print("\nChecking for shared accounts...")
        
        # Check Doctors
        doctors = Doctor.query.all()
        for doc in doctors:
            user = User.query.get(doc.user_id)
            if user and user.role != 'doctor':
                print(f"Doctor {doc.full_name} is pointing to a User (ID {user.id}) with role '{user.role}'. Cloning...")
                new_user = User(
                    username=f"doc_{user.username}",
                    email=user.email,
                    password_hash=user.password_hash,
                    role='doctor',
                    is_active=user.is_active
                )
                db.session.add(new_user)
                db.session.flush()
                doc.user_id = new_user.id
                print(f"Created new Doctor User (ID {new_user.id}) for {doc.full_name}.")
                
        # Check Pharmacists
        pharmacists = Pharmacist.query.all()
        for pharm in pharmacists:
            user = User.query.get(pharm.user_id)
            if user and user.role != 'pharmacist':
                print(f"Pharmacist {pharm.full_name} is pointing to a User (ID {user.id}) with role '{user.role}'. Cloning...")
                new_user = User(
                    username=f"pharm_{user.username}",
                    email=user.email,
                    password_hash=user.password_hash,
                    role='pharmacist',
                    is_active=user.is_active
                )
                db.session.add(new_user)
                db.session.flush()
                pharm.user_id = new_user.id
                print(f"Created new Pharmacist User (ID {new_user.id}) for {pharm.full_name}.")
                
        # Check Patients
        patients = Patient.query.all()
        for pat in patients:
            if pat.user_id:
                user = User.query.get(pat.user_id)
                if user and user.role != 'patient':
                    print(f"Patient {pat.full_name} is pointing to a User (ID {user.id}) with role '{user.role}'. Cloning...")
                    new_user = User(
                        username=f"pat_{user.username}",
                        email=user.email,
                        password_hash=user.password_hash,
                        role='patient',
                        is_active=user.is_active
                    )
                    db.session.add(new_user)
                    db.session.flush()
                    pat.user_id = new_user.id
                    print(f"Created new Patient User (ID {new_user.id}) for {pat.full_name}.")

        db.session.commit()
        print("\nMigration completed.")

if __name__ == "__main__":
    migrate()
