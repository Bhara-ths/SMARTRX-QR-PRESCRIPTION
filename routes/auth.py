from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from models.pharmacist import Pharmacist
from extensions import db
from forms.auth_forms import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user.role)
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, role=form.role.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact administration.', 'danger')
                from models.audit import SystemAuditLog
                log = SystemAuditLog(user_id=user.id, action="Failed Login", details="Attempted login on deactivated account", ip_address=request.remote_addr)
                db.session.add(log)
                db.session.commit()
                return redirect(url_for('auth.login'))
                
            login_user(user)
            flash('Logged in successfully.', 'success')
            
            from models.audit import SystemAuditLog
            log = SystemAuditLog(user_id=user.id, action="Login", details="User logged in successfully", ip_address=request.remote_addr)
            db.session.add(log)
            db.session.commit()
            
            return redirect_based_on_role(user.role)
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user.role)

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Create corresponding role profile
        if form.role.data == 'patient':
            patient = Patient(user_id=user.id, full_name=form.username.data)
            db.session.add(patient)
        elif form.role.data == 'doctor':
            doctor = Doctor(user_id=user.id, full_name=form.username.data)
            db.session.add(doctor)
        elif form.role.data == 'pharmacist':
            pharmacist = Pharmacist(user_id=user.id, full_name=form.username.data)
            db.session.add(pharmacist)
            
        db.session.commit()
        
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    from models.audit import SystemAuditLog
    log = SystemAuditLog(user_id=current_user.id, action="Logout", details="User logged out", ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

def redirect_based_on_role(role):
    # These routes will be implemented in their respective blueprints
    if role == 'admin':
        return redirect(url_for('admin.dashboard')) 
    elif role == 'doctor':
        return redirect(url_for('doctor.dashboard'))
    elif role == 'patient':
        return redirect(url_for('patient.dashboard'))
    elif role == 'pharmacist':
        return redirect(url_for('pharmacist.dashboard'))
    return redirect(url_for('auth.login'))
