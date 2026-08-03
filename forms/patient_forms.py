from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, DateField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional

class PatientForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=150)])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    age = IntegerField('Age', validators=[Optional()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    blood_group = SelectField('Blood Group', choices=[('', 'Unknown'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')], validators=[Optional()])
    
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=150)])
    
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    state = StringField('State', validators=[Optional(), Length(max=100)])
    pin_code = StringField('PIN Code', validators=[Optional(), Length(max=20)])
    
    height = FloatField('Height (cm)', validators=[Optional()])
    weight = FloatField('Weight (kg)', validators=[Optional()])
    
    emergency_contact_name = StringField('Emergency Contact Name', validators=[Optional(), Length(max=150)])
    emergency_contact_number = StringField('Emergency Contact Number', validators=[Optional(), Length(max=20)])
    
    allergies = TextAreaField('Allergies', validators=[Optional()])
    chronic_diseases = TextAreaField('Chronic Diseases', validators=[Optional()])
    past_medical_history = TextAreaField('Past Medical History', validators=[Optional()])
    
    status = SelectField('Status', choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')
    
    submit = SubmitField('Save Patient')
