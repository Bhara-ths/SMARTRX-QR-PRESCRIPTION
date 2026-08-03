import os
import sys

# Add the parent directory to sys.path so we can import the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from sqlalchemy import text
from models.user import User
from models.settings import SystemSettings
from models.audit import SystemAuditLog

app = create_app()

def migrate():
    with app.app_context():
        # Add is_active column to users table if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;"))
            print("Successfully added 'is_active' column to 'users' table.")
        except Exception as e:
            print("Notice: 'is_active' column might already exist or another error occurred:", str(e))
        
        db.session.commit()

        # Create the new tables (system_settings, system_audit_logs)
        # db.create_all() will create tables that don't exist yet
        print("Creating new tables...")
        SystemSettings.__table__.create(db.engine, checkfirst=True)
        SystemAuditLog.__table__.create(db.engine, checkfirst=True)
        
        print("Tables created successfully.")

        # Seed System Settings if none exist
        settings = SystemSettings.query.first()
        if not settings:
            new_settings = SystemSettings(
                hospital_name="SmartRx Medical Center",
                hospital_address="123 Health Avenue, Medical District",
                phone_number="+1 234 567 8900",
                email="contact@smartrx.com",
                theme="light"
            )
            db.session.add(new_settings)
            db.session.commit()
            print("Seeded default System Settings.")

if __name__ == '__main__':
    migrate()
