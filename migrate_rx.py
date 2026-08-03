from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    queries = [
        "ALTER TABLE doctors ADD COLUMN registration_number VARCHAR(100);",
        "ALTER TABLE doctors ADD COLUMN department VARCHAR(150);",
        
        "ALTER TABLE prescriptions ADD COLUMN blood_pressure VARCHAR(20);",
        "ALTER TABLE prescriptions ADD COLUMN pulse INT;",
        "ALTER TABLE prescriptions ADD COLUMN temperature FLOAT;",
        "ALTER TABLE prescriptions ADD COLUMN oxygen_saturation INT;",
        "ALTER TABLE prescriptions ADD COLUMN follow_up_date DATE;",
        
        "ALTER TABLE prescription_medicines ADD COLUMN medicine_type VARCHAR(50);",
        "ALTER TABLE prescription_medicines ADD COLUMN morning VARCHAR(20);",
        "ALTER TABLE prescription_medicines ADD COLUMN afternoon VARCHAR(20);",
        "ALTER TABLE prescription_medicines ADD COLUMN night VARCHAR(20);"
    ]
    
    for q in queries:
        try:
            db.session.execute(text(q))
            db.session.commit()
            print(f"Executed: {q}")
        except Exception as e:
            db.session.rollback()
            print(f"Skipping (likely already exists or error): {e}")

    print("Migration completed.")
