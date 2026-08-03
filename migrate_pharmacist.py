from app import create_app
from extensions import db
from models.audit import MedicineDispensing

app = create_app()

with app.app_context():
    # Attempt to create the missing tables safely.
    # db.create_all() will only create tables that do not exist.
    db.create_all()
    print("Checked and created missing tables (MedicineDispensing).")
