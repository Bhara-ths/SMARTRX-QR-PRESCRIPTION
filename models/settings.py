from extensions import db

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    hospital_name = db.Column(db.String(200), default="SmartRx Medical Center")
    hospital_address = db.Column(db.String(500), default="123 Health Avenue, Medical District")
    phone_number = db.Column(db.String(50), default="+1 234 567 8900")
    email = db.Column(db.String(120), default="contact@smartrx.com")
    theme = db.Column(db.String(50), default="light")
    logo_path = db.Column(db.String(255), default="default_logo.png")
