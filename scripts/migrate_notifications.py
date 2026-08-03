import os
import sys

# Add the parent directory to sys.path so we can import the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.notification import Notification, MedicineReminder, AppointmentReminder, RefillReminder

app = create_app()

def migrate():
    with app.app_context():
        # Create the new tables
        print("Creating new tables: notifications, medicine_reminders, appointment_reminders, refill_reminders...")
        Notification.__table__.create(db.engine, checkfirst=True)
        MedicineReminder.__table__.create(db.engine, checkfirst=True)
        AppointmentReminder.__table__.create(db.engine, checkfirst=True)
        RefillReminder.__table__.create(db.engine, checkfirst=True)
        print("Tables created successfully.")

if __name__ == '__main__':
    migrate()
