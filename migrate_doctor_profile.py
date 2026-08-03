from app import create_app
from extensions import db
from models.doctor import DoctorProfile

app = create_app()

with app.app_context():
    db.create_all()
    print("Checked and created missing tables (DoctorProfile).")
