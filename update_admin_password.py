import os
from app import create_app
from extensions import db
from models.user import User

app = create_app()

def update_admin_password():
    with app.app_context():
        email = "gunavardhan815@gmail.com"
        new_password = "gunav123@"
        
        user = User.query.filter_by(email=email).first()
        if user and user.role == 'admin':
            print(f"Found admin user with email {email}. Updating password...")
            user.set_password(new_password)
            db.session.commit()
            print("Password updated successfully.")
        else:
            print("Admin user not found.")

if __name__ == "__main__":
    update_admin_password()
