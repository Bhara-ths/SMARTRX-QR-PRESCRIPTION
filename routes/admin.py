from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from flask import abort
from datetime import datetime, date, timedelta
from extensions import db
from models import User, Doctor, Patient, Pharmacist, Appointment, Prescription
from models.audit import SystemAuditLog, QRScanHistory, DispensingHistory, MedicineDispensing
from models.settings import SystemSettings
from models.hospital import Hospital
from forms.admin_forms import StaffForm, EditStaffForm, SettingsForm, HospitalForm
import os
from werkzeug.utils import secure_filename
from flask import current_app

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def log_admin_action(action, details):
    log = SystemAuditLog(user_id=current_user.id, action=action, details=details, ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    today = date.today()
    
    # Gather statistics
    stats = {
        'total_doctors': Doctor.query.count(),
        'total_patients': Patient.query.count(),
        'total_pharmacists': Pharmacist.query.count(),
        'total_prescriptions': Prescription.query.count(),
        'today_appointments': Appointment.query.filter(Appointment.appointment_date == today).count(),
        'today_qr_scans': QRScanHistory.query.filter(db.func.date(QRScanHistory.scanned_at) == today).count(),
        'today_dispensed': DispensingHistory.query.filter(db.func.date(DispensingHistory.dispensed_at) == today).count(),
        'active_users': User.query.filter_by(is_active=True).count()
    }
    
    recent_logs = SystemAuditLog.query.order_by(SystemAuditLog.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', stats=stats, recent_logs=recent_logs)

# --- DOCTOR MANAGEMENT ---

@admin_bp.route('/doctors')
@login_required
@admin_required
def doctors():
    search = request.args.get('q', '')
    query = User.query.filter_by(role='doctor').join(Doctor)
    if search:
        query = query.filter(db.or_(User.username.ilike(f'%{search}%'), User.email.ilike(f'%{search}%')))
    
    doctors = query.all()
    return render_template('admin/doctors.html', doctors=doctors, search=search)

@admin_bp.route('/doctor/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_doctor():
    form = StaffForm()
    form.hospital_id.choices = [(h.id, h.name) for h in Hospital.query.all()]
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role='doctor')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        doctor = Doctor(
            user_id=user.id, 
            full_name=form.username.data,
            hospital_id=form.hospital_id.data,
            department=form.department.data,
            specialization=form.specialization.data
        )
        db.session.add(doctor)
        db.session.commit()
        
        # Add consultation timings if profile exists/created later, or just save them somewhere
        # The prompt says "Assign Consultation Timing". It belongs to DoctorProfile.
        from models.doctor import DoctorProfile
        profile = DoctorProfile(
            doctor_id=doctor.doctor_id,
            consultation_timings=form.consultation_timings.data
        )
        db.session.add(profile)
        db.session.commit()
        
        log_admin_action('Create Doctor', f"Added doctor: {user.email}")
        flash('Doctor added successfully.', 'success')
        return redirect(url_for('admin.doctors'))
        
    return render_template('admin/staff_form.html', form=form, title='Add Doctor')

@admin_bp.route('/doctor/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_doctor(id):
    user = User.query.get_or_404(id)
    if user.role != 'doctor':
        abort(404)
        
    doctor = Doctor.query.filter_by(user_id=user.id).first()
    form = EditStaffForm(obj=user)
    form.hospital_id.choices = [(h.id, h.name) for h in Hospital.query.all()]
    
    if request.method == 'GET' and doctor:
        form.hospital_id.data = doctor.hospital_id
        form.department.data = doctor.department
        form.specialization.data = doctor.specialization
        if doctor.profile:
            form.consultation_timings.data = doctor.profile.consultation_timings
            
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:
            user.set_password(form.password.data)
            
        if doctor:
            doctor.full_name = form.username.data
            doctor.hospital_id = form.hospital_id.data
            doctor.department = form.department.data
            doctor.specialization = form.specialization.data
            
            if doctor.profile:
                doctor.profile.consultation_timings = form.consultation_timings.data
            else:
                from models.doctor import DoctorProfile
                profile = DoctorProfile(
                    doctor_id=doctor.doctor_id,
                    consultation_timings=form.consultation_timings.data
                )
                db.session.add(profile)
            
        db.session.commit()
        log_admin_action('Edit Doctor', f"Updated doctor: {user.email}")
        flash('Doctor updated successfully.', 'success')
        return redirect(url_for('admin.doctors'))
        
    return render_template('admin/staff_form.html', form=form, title='Edit Doctor')

@admin_bp.route('/doctor/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_doctor(id):
    user = User.query.get_or_404(id)
    if user.role != 'doctor':
        abort(404)
    
    user.is_active = not user.is_active
    db.session.commit()
    
    action = "Activated" if user.is_active else "Deactivated"
    log_admin_action(f'{action} Doctor', f"Changed status of doctor: {user.email}")
    flash(f'Doctor {action.lower()} successfully.', 'success')
    return redirect(url_for('admin.doctors'))

# --- PATIENT MANAGEMENT ---

@admin_bp.route('/patients')
@login_required
@admin_required
def patients():
    search = request.args.get('q', '')
    query = User.query.filter_by(role='patient').join(Patient)
    if search:
        query = query.filter(db.or_(User.username.ilike(f'%{search}%'), User.email.ilike(f'%{search}%'), Patient.patient_uid.ilike(f'%{search}%')))
    
    patients = query.all()
    return render_template('admin/patients.html', patients=patients, search=search)

@admin_bp.route('/patient/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_patient(id):
    user = User.query.get_or_404(id)
    if user.role != 'patient':
        abort(404)
    
    user.is_active = not user.is_active
    db.session.commit()
    
    action = "Unarchived" if user.is_active else "Archived"
    log_admin_action(f'{action} Patient', f"Changed status of patient: {user.email}")
    flash(f'Patient {action.lower()} successfully.', 'success')
    return redirect(url_for('admin.patients'))

# --- PHARMACIST MANAGEMENT ---

@admin_bp.route('/pharmacists')
@login_required
@admin_required
def pharmacists():
    search = request.args.get('q', '')
    query = User.query.filter_by(role='pharmacist').join(Pharmacist)
    if search:
        query = query.filter(db.or_(User.username.ilike(f'%{search}%'), User.email.ilike(f'%{search}%')))
    
    pharmacists = query.all()
    return render_template('admin/pharmacists.html', pharmacists=pharmacists, search=search)

@admin_bp.route('/pharmacist/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_pharmacist():
    form = StaffForm()
    # Lock role to pharmacist
    form.role.data = 'pharmacist'
    form.hospital_id.choices = [(h.id, h.name) for h in Hospital.query.all()]
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role='pharmacist')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        pharmacist = Pharmacist(
            user_id=user.id, 
            full_name=form.username.data,
            hospital_id=form.hospital_id.data
        )
        db.session.add(pharmacist)
        db.session.commit()
        
        log_admin_action('Create Pharmacist', f"Added pharmacist: {user.email}")
        flash('Pharmacist added successfully.', 'success')
        return redirect(url_for('admin.pharmacists'))
        
    return render_template('admin/staff_form.html', form=form, title='Add Pharmacist')

@admin_bp.route('/pharmacist/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_pharmacist(id):
    user = User.query.get_or_404(id)
    if user.role != 'pharmacist':
        abort(404)
        
    pharmacist = Pharmacist.query.filter_by(user_id=user.id).first()
    form = EditStaffForm(obj=user)
    form.hospital_id.choices = [(h.id, h.name) for h in Hospital.query.all()]
    
    if request.method == 'GET' and pharmacist:
        form.hospital_id.data = pharmacist.hospital_id
        
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:
            user.set_password(form.password.data)
            
        if pharmacist:
            pharmacist.full_name = form.username.data
            pharmacist.hospital_id = form.hospital_id.data
            
        db.session.commit()
        log_admin_action('Edit Pharmacist', f"Updated pharmacist: {user.email}")
        flash('Pharmacist updated successfully.', 'success')
        return redirect(url_for('admin.pharmacists'))
        
    return render_template('admin/staff_form.html', form=form, title='Edit Pharmacist')

@admin_bp.route('/pharmacist/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_pharmacist(id):
    user = User.query.get_or_404(id)
    if user.role != 'pharmacist':
        abort(404)
    
    user.is_active = not user.is_active
    db.session.commit()
    
    action = "Activated" if user.is_active else "Deactivated"
    log_admin_action(f'{action} Pharmacist', f"Changed status of pharmacist: {user.email}")
    flash(f'Pharmacist {action.lower()} successfully.', 'success')
    return redirect(url_for('admin.pharmacists'))

# --- REPORTS & ANALYTICS ---

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    from models import PrescriptionMedicine, Medicine
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    doctor_id = request.args.get('doctor_id', type=int)
    patient_id = request.args.get('patient_id', type=int)
    pharmacist_id = request.args.get('pharmacist_id', type=int)
    
    today = date.today()
    if not start_date_str:
        start_date = today.replace(day=1)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
    if not end_date_str:
        end_date = today
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
    # Build base queries
    rx_query = Prescription.query.filter(db.func.date(Prescription.created_at) >= start_date, db.func.date(Prescription.created_at) <= end_date)
    appt_query = Appointment.query.filter(Appointment.appointment_date >= start_date, Appointment.appointment_date <= end_date)
    dispense_query = MedicineDispensing.query.filter(db.func.date(MedicineDispensing.dispensed_at) >= start_date, db.func.date(MedicineDispensing.dispensed_at) <= end_date)
    qr_query = QRScanHistory.query.filter(db.func.date(QRScanHistory.scanned_at) >= start_date, db.func.date(QRScanHistory.scanned_at) <= end_date)
    
    # Apply filters
    if doctor_id:
        rx_query = rx_query.filter_by(doctor_id=doctor_id)
        appt_query = appt_query.filter_by(doctor_id=doctor_id)
    if patient_id:
        rx_query = rx_query.filter_by(patient_id=patient_id)
        appt_query = appt_query.filter_by(patient_id=patient_id)
    if pharmacist_id:
        dispense_query = dispense_query.filter_by(pharmacist_id=pharmacist_id)
        qr_query = qr_query.filter_by(pharmacist_id=pharmacist_id)
        
    # --- DOCTOR REPORTS ---
    # We will compute distinct patients from the filtered prescriptions and appointments
    doc_stats = {}
    doc_stats['total_rx'] = rx_query.count()
    doc_stats['today_rx'] = rx_query.filter(db.func.date(Prescription.created_at) == today).count()
    doc_stats['weekly_rx'] = rx_query.filter(db.func.date(Prescription.created_at) >= today - timedelta(days=7)).count()
    doc_stats['monthly_rx'] = rx_query.filter(db.func.date(Prescription.created_at) >= today - timedelta(days=30)).count()
    
    # Total Patients (Distinct patients seen by doctors based on Rx)
    doc_stats['total_patients'] = db.session.query(db.func.count(db.func.distinct(Prescription.patient_id))).filter(
        db.func.date(Prescription.created_at) >= start_date,
        db.func.date(Prescription.created_at) <= end_date
    ).scalar() or 0
    
    # Follow-ups (Appointments with type Follow-up, if applicable, otherwise count completed appointments)
    doc_stats['follow_ups'] = appt_query.filter_by(appointment_type='Follow-up').count()
    
    # --- PATIENT REPORTS ---
    pat_stats = {}
    pat_stats['total_registered'] = Patient.query.count()
    pat_stats['new_this_month'] = Patient.query.filter(db.func.date(Patient.registration_date) >= today.replace(day=1)).count()
    
    # Gender distribution
    males = Patient.query.filter_by(gender='Male').count()
    females = Patient.query.filter_by(gender='Female').count()
    others = Patient.query.filter_by(gender='Other').count()
    pat_stats['gender'] = {'Male': males, 'Female': females, 'Other': others}
    
    # Age groups (0-18, 19-35, 36-60, 60+)
    age_0_18 = Patient.query.filter(Patient.age <= 18).count()
    age_19_35 = Patient.query.filter(Patient.age > 18, Patient.age <= 35).count()
    age_36_60 = Patient.query.filter(Patient.age > 35, Patient.age <= 60).count()
    age_60_plus = Patient.query.filter(Patient.age > 60).count()
    pat_stats['age_groups'] = {'0-18': age_0_18, '19-35': age_19_35, '36-60': age_36_60, '60+': age_60_plus}
    
    # --- PHARMACY REPORTS ---
    pharm_stats = {}
    pharm_stats['dispensed_today'] = dispense_query.filter(db.func.date(MedicineDispensing.dispensed_at) == today).count()
    
    # Get status counts from PrescriptionMedicine within date range
    # Join with Prescription to apply date filters
    rx_med_query = db.session.query(PrescriptionMedicine).join(Prescription).filter(
        db.func.date(Prescription.created_at) >= start_date,
        db.func.date(Prescription.created_at) <= end_date
    )
    
    pharm_stats['pending'] = rx_med_query.filter(PrescriptionMedicine.dispense_status == 'Pending').count()
    pharm_stats['completed'] = rx_med_query.filter(PrescriptionMedicine.dispense_status == 'Fully Dispensed').count()
    pharm_stats['partial'] = rx_med_query.filter(PrescriptionMedicine.dispense_status == 'Partially Dispensed').count()
    
    # Most Dispensed Medicines
    most_dispensed = db.session.query(
        Medicine.medicine_name, db.func.sum(MedicineDispensing.quantity).label('total')
    ).join(PrescriptionMedicine, MedicineDispensing.prescription_medicine_id == PrescriptionMedicine.id)\
     .join(Medicine, PrescriptionMedicine.medicine_id == Medicine.medicine_id)\
     .filter(db.func.date(MedicineDispensing.dispensed_at) >= start_date, db.func.date(MedicineDispensing.dispensed_at) <= end_date)\
     .group_by(Medicine.medicine_name).order_by(db.desc('total')).limit(5).all()
     
    pharm_stats['most_dispensed'] = most_dispensed

    # --- QR REPORTS ---
    qr_stats = {}
    qr_stats['generated'] = rx_query.count() # Every prescription has a QR
    qr_stats['scanned'] = qr_query.filter_by(status='Success').count()
    qr_stats['invalid'] = qr_query.filter(QRScanHistory.status != 'Success').count()
    
    # Lists for filters
    doctors = Doctor.query.all()
    patients = Patient.query.all()
    pharmacists = Pharmacist.query.all()
    
    return render_template('admin/reports.html', 
                           start_date=start_date, end_date=end_date,
                           doctor_id=doctor_id, patient_id=patient_id, pharmacist_id=pharmacist_id,
                           doc_stats=doc_stats, pat_stats=pat_stats, 
                           pharm_stats=pharm_stats, qr_stats=qr_stats,
                           doctors=doctors, patients=patients, pharmacists=pharmacists)

@admin_bp.route('/analytics/data')
@login_required
@admin_required
def analytics_data():
    # Simple JSON data for 7 days trend
    labels = []
    prescriptions = []
    appointments = []
    
    today = date.today()
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime('%a, %b %d'))
        
        rx_count = Prescription.query.filter(db.func.date(Prescription.created_at) == d).count()
        app_count = Appointment.query.filter(Appointment.appointment_date == d).count()
        
        prescriptions.append(rx_count)
        appointments.append(app_count)
        
    return jsonify({
        'labels': labels,
        'prescriptions': prescriptions,
        'appointments': appointments
    })

@admin_bp.route('/search')
@login_required
@admin_required
def global_search():
    from models import Medicine
    query = request.args.get('q', '')
    if not query:
        return render_template('admin/search_results.html', query=query, results={})
        
    results = {
        'patients': Patient.query.filter(db.or_(Patient.full_name.ilike(f'%{query}%'), Patient.patient_uid.ilike(f'%{query}%'))).limit(10).all(),
        'doctors': Doctor.query.filter(Doctor.full_name.ilike(f'%{query}%')).limit(10).all(),
        'prescriptions': Prescription.query.filter(db.or_(Prescription.uuid.ilike(f'%{query}%'), Prescription.diagnosis.ilike(f'%{query}%'))).limit(10).all(),
        'medicines': Medicine.query.filter(Medicine.medicine_name.ilike(f'%{query}%')).limit(10).all()
    }
    
    return render_template('admin/search_results.html', query=query, results=results)

@admin_bp.route('/reports/export')
@login_required
@admin_required
def reports_export():
    import io
    import openpyxl
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from flask import make_response
    
    format_type = request.args.get('format', 'pdf')
    today = date.today()
    
    if format_type == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Hospital Report"
        ws.append(["Metric", "Value"])
        ws.append(["Total Doctors", Doctor.query.count()])
        ws.append(["Total Patients", Patient.query.count()])
        ws.append(["Total Prescriptions", Prescription.query.count()])
        ws.append(["Total Pharmacists", Pharmacist.query.count()])
        
        output = io.BytesIO()
        wb.save(output)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=hospital_report_{today}.xlsx'
        response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return response
        
    elif format_type == 'pdf':
        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=letter)
        p.drawString(100, 750, f"Hospital Analytics Report - {today}")
        
        p.drawString(100, 700, f"Total Doctors: {Doctor.query.count()}")
        p.drawString(100, 680, f"Total Patients: {Patient.query.count()}")
        p.drawString(100, 660, f"Total Prescriptions: {Prescription.query.count()}")
        p.drawString(100, 640, f"Total Pharmacists: {Pharmacist.query.count()}")
        
        p.showPage()
        p.save()
        
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=hospital_report_{today}.pdf'
        response.headers['Content-type'] = 'application/pdf'
        return response
        
    return redirect(url_for('admin.reports'))

# --- AUDIT LOGS ---

@admin_bp.route('/audit_logs')
@login_required
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    pagination = SystemAuditLog.query.order_by(SystemAuditLog.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/audit_logs.html', pagination=pagination)

# --- SETTINGS ---

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    settings_obj = SystemSettings.query.first()
    if not settings_obj:
        settings_obj = SystemSettings()
        db.session.add(settings_obj)
        db.session.commit()
        
    form = SettingsForm(obj=settings_obj)
    if form.validate_on_submit():
        settings_obj.hospital_name = form.hospital_name.data
        settings_obj.hospital_address = form.hospital_address.data
        settings_obj.phone_number = form.phone_number.data
        settings_obj.email = form.email.data
        settings_obj.theme = form.theme.data
        db.session.commit()
        
        log_admin_action('Update Settings', "System settings were modified")
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))
        
    return render_template('admin/settings.html', form=form)

# --- HOSPITAL MANAGEMENT ---

@admin_bp.route('/hospitals')
@login_required
@admin_required
def hospitals():
    hospitals = Hospital.query.all()
    return render_template('admin/hospitals.html', hospitals=hospitals)

@admin_bp.route('/hospital/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_hospital():
    form = HospitalForm()
    if form.validate_on_submit():
        hospital = Hospital(
            name=form.name.data,
            registration_number=form.registration_number.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            country=form.country.data,
            postal_code=form.postal_code.data,
            google_maps_url=form.google_maps_url.data,
            phone=form.phone.data,
            email=form.email.data,
            website=form.website.data,
            emergency_contact=form.emergency_contact.data,
            working_hours=form.working_hours.data,
            description=form.description.data
        )
        
        if form.logo.data:
            logo_file = form.logo.data
            filename = secure_filename(f"hosp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo_file.filename}")
            filepath = os.path.join(current_app.root_path, 'static', 'uploads', 'logos', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            logo_file.save(filepath)
            hospital.logo_path = filename
            
        db.session.add(hospital)
        db.session.commit()
        
        log_admin_action('Create Hospital', f"Added hospital: {hospital.name}")
        flash('Hospital added successfully.', 'success')
        return redirect(url_for('admin.hospitals'))
        
    return render_template('admin/hospital_form.html', form=form, is_edit=False)

@admin_bp.route('/hospital/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_hospital(id):
    hospital = Hospital.query.get_or_404(id)
    form = HospitalForm(obj=hospital)
    
    if form.validate_on_submit():
        hospital.name = form.name.data
        hospital.registration_number = form.registration_number.data
        hospital.address = form.address.data
        hospital.city = form.city.data
        hospital.state = form.state.data
        hospital.country = form.country.data
        hospital.postal_code = form.postal_code.data
        hospital.google_maps_url = form.google_maps_url.data
        hospital.phone = form.phone.data
        hospital.email = form.email.data
        hospital.website = form.website.data
        hospital.emergency_contact = form.emergency_contact.data
        hospital.working_hours = form.working_hours.data
        hospital.description = form.description.data
        
        if form.logo.data:
            logo_file = form.logo.data
            filename = secure_filename(f"hosp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo_file.filename}")
            filepath = os.path.join(current_app.root_path, 'static', 'uploads', 'logos', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            logo_file.save(filepath)
            hospital.logo_path = filename
            
        db.session.commit()
        
        log_admin_action('Edit Hospital', f"Updated hospital: {hospital.name}")
        flash('Hospital updated successfully.', 'success')
        return redirect(url_for('admin.hospitals'))
        
    return render_template('admin/hospital_form.html', form=form, is_edit=True, hospital=hospital)

