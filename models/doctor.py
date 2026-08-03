from extensions import db

class Doctor(db.Model):
    __tablename__ = 'doctors'
    doctor_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('doctor', uselist=False))
    full_name = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(100))
    hospital = db.Column(db.String(150)) # Legacy text field
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'))
    department = db.Column(db.String(150))
    registration_number = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    profile = db.relationship('DoctorProfile', backref='doctor', uselist=False, cascade="all, delete-orphan")

class DoctorProfile(db.Model):
    __tablename__ = 'doctor_profiles'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id', ondelete='CASCADE'), nullable=False, unique=True)
    
    qualification = db.Column(db.String(200))
    years_of_experience = db.Column(db.Integer)
    address = db.Column(db.Text)
    consultation_timings = db.Column(db.String(200))
    biography = db.Column(db.Text)
    
    profile_photo = db.Column(db.String(255))
    digital_signature = db.Column(db.String(255))
