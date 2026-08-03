from flask import Flask, redirect
from config import Config
from extensions import db, login_manager, mail, csrf
from flask_login import current_user
from models import *
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Initialize APScheduler for background reminders
    from services.notification_service import init_scheduler
    init_scheduler()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated:
            from models.notification import Notification
            count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            return dict(unread_notifications_count=count)
        return dict(unread_notifications_count=0)

    @app.context_processor
    def inject_hospital():
        from models.hospital import Hospital
        hospital = None
        if current_user.is_authenticated:
            if current_user.role == 'doctor':
                from models.doctor import Doctor
                doc = Doctor.query.filter_by(user_id=current_user.id).first()
                if doc and doc.hospital_id:
                    hospital = Hospital.query.get(doc.hospital_id)
            elif current_user.role == 'pharmacist':
                from models.pharmacist import Pharmacist
                pharm = Pharmacist.query.filter_by(user_id=current_user.id).first()
                if pharm and pharm.hospital_id:
                    hospital = Hospital.query.get(pharm.hospital_id)
        
        # Fallback to the first hospital created in the system (for patients, admins, public views)
        if not hospital:
            hospital = Hospital.query.first()
            
        return dict(current_hospital=hospital)

    # Create upload directories if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # Register Blueprints
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from routes.admin import admin_bp
    from routes.doctor import doctor_bp
    from routes.patient import patient_bp
    from routes.pharmacist import pharmacist_bp
    from routes.public import public_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(pharmacist_bp, url_prefix='/pharmacist')
    app.register_blueprint(public_bp)

    @app.route('/')
    def index():
        return redirect("/login")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
# for render / gunicorn
app = create_app()