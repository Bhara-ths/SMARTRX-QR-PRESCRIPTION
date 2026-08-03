from app import create_app
from extensions import db
from models.audit import QRScanHistory, DispensingHistory

app = create_app()

with app.app_context():
    # Attempt to create the missing tables safely.
    # db.create_all() will only create tables that do not exist.
    db.create_all()
    print("Checked and created missing tables (QRScanHistory, DispensingHistory).")
    
    # Add dispense_status to prescription_medicines using raw SQL
    try:
        db.session.execute(db.text("ALTER TABLE prescription_medicines ADD COLUMN dispense_status VARCHAR(50) DEFAULT 'Pending'"))
        db.session.commit()
        print("Added dispense_status to prescription_medicines.")
    except Exception as e:
        print(f"Column dispense_status might already exist or error occurred: {e}")
        db.session.rollback()
