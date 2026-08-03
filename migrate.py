from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    queries = [
        "ALTER TABLE patients ADD COLUMN patient_uid VARCHAR(20) UNIQUE;",
        "ALTER TABLE patients ADD COLUMN dob DATE;",
        "ALTER TABLE patients ADD COLUMN email VARCHAR(150);",
        "ALTER TABLE patients ADD COLUMN city VARCHAR(100);",
        "ALTER TABLE patients ADD COLUMN state VARCHAR(100);",
        "ALTER TABLE patients ADD COLUMN pin_code VARCHAR(20);",
        "ALTER TABLE patients ADD COLUMN height FLOAT;",
        "ALTER TABLE patients ADD COLUMN emergency_contact_name VARCHAR(150);",
        "ALTER TABLE patients ADD COLUMN emergency_contact_number VARCHAR(20);",
        "ALTER TABLE patients ADD COLUMN allergies TEXT;",
        "ALTER TABLE patients ADD COLUMN chronic_diseases TEXT;",
        "ALTER TABLE patients ADD COLUMN past_medical_history TEXT;",
        "ALTER TABLE patients ADD COLUMN registration_date DATETIME DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE patients ADD COLUMN status ENUM('Active', 'Inactive') DEFAULT 'Active';"
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
