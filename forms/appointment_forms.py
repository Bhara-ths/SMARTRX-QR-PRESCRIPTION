from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, TimeField, IntegerField
from wtforms.validators import DataRequired, Optional

class AppointmentForm(FlaskForm):
    # Depending on whether Doctor or Patient books, patient_id might be hidden or a select field.
    # For now, we'll keep it as IntegerField (hidden or populated via JS search)
    patient_id = IntegerField('Patient ID', validators=[DataRequired()])
    
    appointment_date = DateField('Appointment Date', validators=[DataRequired()])
    appointment_time = TimeField('Appointment Time', validators=[DataRequired()])
    
    department = StringField('Department', validators=[Optional()])
    reason_for_visit = StringField('Reason For Visit', validators=[DataRequired()])
    
    appointment_type = SelectField('Appointment Type', choices=[
        ('New', 'New Consultation'),
        ('Follow-up', 'Follow-up'),
        ('Emergency', 'Emergency')
    ], validators=[DataRequired()])
    
    status = SelectField('Status', choices=[
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('No Show', 'No Show')
    ], default='Scheduled')
    
    notes = TextAreaField('Clinical Notes', validators=[Optional()])

class PatientAppointmentRequestForm(FlaskForm):
    doctor_id = IntegerField('Doctor', validators=[DataRequired()])
    appointment_date = DateField('Preferred Date', validators=[DataRequired()])
    appointment_time = TimeField('Preferred Time', validators=[DataRequired()])
    reason_for_visit = StringField('Reason For Visit', validators=[DataRequired()])
    appointment_type = SelectField('Appointment Type', choices=[
        ('New', 'New Consultation'),
        ('Follow-up', 'Follow-up')
    ], validators=[DataRequired()])
