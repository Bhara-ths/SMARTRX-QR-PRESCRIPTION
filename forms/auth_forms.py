from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models.user import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('admin', 'Hospital Administrator'), ('doctor', 'Doctor'), ('pharmacist', 'Pharmacist'), ('patient', 'Patient')], validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('patient', 'Patient'), ('doctor', 'Doctor'), ('pharmacist', 'Pharmacist'), ('admin', 'Hospital Administrator')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data, role=self.role.data).first()
        if user:
            raise ValidationError('An account with this email already exists for this role.')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data, role=self.role.data).first()
        if user:
            raise ValidationError('That username is already taken for this role. Please choose a different one.')
