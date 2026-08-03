from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, TextAreaField, SelectField, SubmitField, DateField
from wtforms.validators import DataRequired, Optional

class PrescriptionForm(FlaskForm):
    # Patient Details handled by JS search
    patient_id = HiddenField('Patient ID', validators=[DataRequired(message="Please select a patient.")])
    search_patient = StringField('Search Patient (Name, Phone, ID)', validators=[Optional()])

    # Prescription Details
    diagnosis = StringField('Diagnosis', validators=[DataRequired()])
    symptoms = TextAreaField('Symptoms')
    clinical_notes = TextAreaField('Clinical Notes')
    
    # Vitals
    blood_pressure = StringField('Blood Pressure (mmHg)', validators=[Optional()])
    pulse = StringField('Pulse (bpm)', validators=[Optional()])
    temperature = StringField('Temperature (°F)', validators=[Optional()])
    oxygen_saturation = StringField('SpO2 (%)', validators=[Optional()])
    
    # Follow Up
    follow_up_date = DateField('Follow Up Date', format='%Y-%m-%d', validators=[Optional()])
    
    # Status
    status = SelectField('Status', choices=[('Active', 'Active'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Active')
    
    # We will add medicines via dynamic JS form
    
    submit = SubmitField('Save Prescription')
