from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from flask_wtf.file import FileField, FileAllowed
from models.user import User

class HospitalForm(FlaskForm):
    name = StringField('Hospital Name', validators=[DataRequired(), Length(max=200)])
    registration_number = StringField('Registration Number', validators=[Optional(), Length(max=100)])
    logo = FileField('Hospital Logo', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    
    address = StringField('Address', validators=[Optional(), Length(max=500)])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    state = StringField('State', validators=[Optional(), Length(max=100)])
    country = StringField('Country', validators=[Optional(), Length(max=100)])
    postal_code = StringField('Postal Code', validators=[Optional(), Length(max=20)])
    google_maps_url = StringField('Google Maps URL', validators=[Optional(), Length(max=500)])
    
    phone = StringField('Phone Number', validators=[Optional(), Length(max=50)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    website = StringField('Website', validators=[Optional(), Length(max=255)])
    emergency_contact = StringField('Emergency Contact', validators=[Optional(), Length(max=50)])
    
    working_hours = StringField('Working Hours', validators=[Optional(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional()])
    
    submit = SubmitField('Save Hospital Profile')

class StaffForm(FlaskForm):
    username = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('doctor', 'Doctor'), ('pharmacist', 'Pharmacist')], validators=[DataRequired()])
    
    # New fields for Hospital Management
    hospital_id = SelectField('Assign Hospital', coerce=int, validators=[DataRequired()])
    department = StringField('Department (Doctor Only)', validators=[Optional(), Length(max=150)])
    specialization = StringField('Specialization (Doctor Only)', validators=[Optional(), Length(max=100)])
    consultation_timings = StringField('Consultation Timing (Doctor Only)', validators=[Optional(), Length(max=200)])
    
    submit = SubmitField('Add Staff')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data, role=self.role.data).first()
        if user:
            raise ValidationError('That email is already registered for this role. Please choose a different one.')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data, role=self.role.data).first()
        if user:
            raise ValidationError('That username/fullname is already registered for this role.')

class EditStaffForm(FlaskForm):
    username = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    
    hospital_id = SelectField('Assign Hospital', coerce=int, validators=[DataRequired()])
    department = StringField('Department (Doctor Only)', validators=[Optional(), Length(max=150)])
    specialization = StringField('Specialization (Doctor Only)', validators=[Optional(), Length(max=100)])
    consultation_timings = StringField('Consultation Timing (Doctor Only)', validators=[Optional(), Length(max=200)])
    
    # Password optional for editing
    password = PasswordField('New Password (leave blank to keep current)', validators=[])
    submit = SubmitField('Update Staff')

class SettingsForm(FlaskForm):
    hospital_name = StringField('Hospital Name', validators=[DataRequired(), Length(max=200)])
    hospital_address = StringField('Hospital Address', validators=[DataRequired(), Length(max=500)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=50)])
    email = StringField('Contact Email', validators=[DataRequired(), Email()])
    theme = SelectField('Theme', choices=[('light', 'Light Mode'), ('dark', 'Dark Mode')])
    submit = SubmitField('Save Settings')
