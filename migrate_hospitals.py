import os
from app import create_app
from extensions import db
from models import Hospital, Doctor, Pharmacist, User, SystemSettings

app = create_app()

def migrate():
    with app.app_context():
        # Create hospitals table if it doesn't exist
        print("Creating hospitals table...")
        db.create_all()
        
        # Read existing system settings to migrate to Hospital
        print("Migrating system settings to hospital...")
        settings = SystemSettings.query.first()
        if settings:
            h_name = settings.hospital_name
            h_addr = settings.hospital_address
            h_phone = settings.phone_number
            h_email = settings.email
        else:
            h_name = "SmartRx Default Hospital"
            h_addr = "123 Main St, Cityville"
            h_phone = "+1 234 567 8900"
            h_email = "contact@smartrx.com"
            
        hospital = Hospital.query.first()
        if not hospital:
            hospital = Hospital(
                name=h_name,
                address=h_addr,
                phone=h_phone,
                email=h_email,
                registration_number="HOSP-0001",
                working_hours="24/7"
            )
            db.session.add(hospital)
            db.session.commit()
            print("Default hospital created.")
            
        # Add foreign key columns to doctors and pharmacists via SQLAlchemy engine if they don't exist
        # We can just use raw SQL for SQLite
        from sqlalchemy import text
        try:
            db.session.execute(text('ALTER TABLE doctors ADD COLUMN hospital_id INTEGER REFERENCES hospitals(id)'))
            db.session.commit()
            print("Added hospital_id to doctors.")
        except Exception as e:
            print("Column hospital_id already exists in doctors or error:", e)
            db.session.rollback()

        try:
            db.session.execute(text('ALTER TABLE pharmacists ADD COLUMN hospital_id INTEGER REFERENCES hospitals(id)'))
            db.session.commit()
            print("Added hospital_id to pharmacists.")
        except Exception as e:
            print("Column hospital_id already exists in pharmacists or error:", e)
            db.session.rollback()
            
        # Assign existing doctors and pharmacists to default hospital
        print("Assigning staff to default hospital...")
        Doctor.query.filter_by(hospital_id=None).update({'hospital_id': hospital.id})
        Pharmacist.query.filter_by(hospital_id=None).update({'hospital_id': hospital.id})
        db.session.commit()
        print("Migration complete!")

if __name__ == '__main__':
    migrate()
