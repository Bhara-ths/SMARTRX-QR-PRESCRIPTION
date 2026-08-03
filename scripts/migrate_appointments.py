import sys
import os

# Add the project root to sys.path so we can import app and extensions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check if columns already exist to make it idempotent
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('appointments')]
        
        if 'appointment_time' not in columns:
            print("Adding appointment_time...")
            db.session.execute(text('ALTER TABLE appointments ADD COLUMN appointment_time TIME NOT NULL DEFAULT "09:00:00";'))
            
        if 'department' not in columns:
            print("Adding department...")
            db.session.execute(text('ALTER TABLE appointments ADD COLUMN department VARCHAR(100);'))
            
        if 'reason_for_visit' not in columns:
            print("Adding reason_for_visit...")
            db.session.execute(text('ALTER TABLE appointments ADD COLUMN reason_for_visit VARCHAR(255);'))
            
        if 'appointment_type' not in columns:
            print("Adding appointment_type...")
            db.session.execute(text('ALTER TABLE appointments ADD COLUMN appointment_type ENUM("New", "Follow-up", "Emergency") DEFAULT "New";'))
            
        # Try to modify appointment_date to DATE if it was DATETIME
        db.session.execute(text('ALTER TABLE appointments MODIFY appointment_date DATE NOT NULL;'))
        
        db.session.commit()
        print('Appointments table migrated successfully.')
    except Exception as e:
        print('Error:', e)
        db.session.rollback()
