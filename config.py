import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # App Configuration
    BASE_URL = os.environ.get('BASE_URL', None) # e.g. http://192.168.1.100:5000 for local network testing
    
    # Security Configuration
    SESSION_COOKIE_SECURE = False # Should be True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800 # 30 minutes

    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+mysqlconnector://root:password@localhost/qr_prescription_system'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Paths for uploads (QRs and PDFs)
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    QR_FOLDER = os.path.join(basedir, 'static', 'qr')
    PDF_FOLDER = os.path.join(basedir, 'static', 'pdf')

    # Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # AI Config
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
