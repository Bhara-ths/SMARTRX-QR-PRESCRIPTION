from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length

class DoctorProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=150)])
    registration_number = StringField('Registration Number', validators=[DataRequired(), Length(max=100)])
    qualification = StringField('Qualification', validators=[Optional(), Length(max=200)])
    specialization = StringField('Specialization', validators=[Optional(), Length(max=100)])
    department = StringField('Department', validators=[Optional(), Length(max=150)])
    years_of_experience = IntegerField('Years of Experience', validators=[Optional()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Clinic / Hospital Address', validators=[Optional()])
    hospital = StringField('Hospital Name', validators=[Optional(), Length(max=150)])
    consultation_timings = StringField('Consultation Timings', validators=[Optional(), Length(max=200)])
    biography = TextAreaField('Biography / Professional Summary', validators=[Optional()])
    
    profile_photo = FileField('Profile Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    
    digital_signature = FileField('Digital Signature', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    
    submit = SubmitField('Save Profile')
