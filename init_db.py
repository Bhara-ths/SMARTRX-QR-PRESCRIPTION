import mysql.connector
import os
from dotenv import load_dotenv

# Load env to get credentials if needed, or hardcode defaults for local dev
load_dotenv('.env')

# Connect to MySQL server (without specifying DB) to create it if it doesn't exist
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="@MGuna4946@"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS qr_prescription_system")
    print("Database qr_prescription_system ensured.")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error creating database: {e}")

# Now initialize SQLAlchemy and create tables
from app import create_app
from extensions import db
from models.user import User

app = create_app()

with app.app_context():
    # Drop all existing tables to apply new schema
    db.drop_all()
    print("Existing tables dropped.")
    
    # Create all tables
    db.create_all()
    print("Tables created successfully.")
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("Creating admin user...")
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created (username: admin, password: admin123).")
    else:
        print("Admin user already exists.")
