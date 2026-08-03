import os
from app import create_app
from extensions import db
from models.user import User

app = create_app()

def seed_admin():
    with app.app_context():
        email = "gunavardhan815@gmail.com"
        password = "guna123@"
        
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"User with email {email} already exists.")
            # ensure it's an admin and update password
            user.role = 'admin'
            user.set_password(password)
            db.session.commit()
            print("Updated existing user to admin with new password.")
        else:
            # We also need a username. We can use the part before @ or just 'Gunavardhan'
            username = "Gunavardhan Admin"
            # verify username isn't taken
            if User.query.filter_by(username=username).first():
                username = f"Admin_{email.split('@')[0]}"
                
            admin_user = User(
                username=username,
                email=email,
                role='admin'
            )
            admin_user.set_password(password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created new Admin user: {email}")

if __name__ == "__main__":
    seed_admin()
