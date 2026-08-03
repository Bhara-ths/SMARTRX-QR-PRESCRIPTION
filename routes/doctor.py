from flask import Blueprint, render_template
from flask_login import login_required, current_user
from functools import wraps
from flask import abort
from models import Doctor, Patient, Prescription, Appointment
from extensions import db

doctor_bp = Blueprint('doctor', __name__)

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'doctor':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@doctor_bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        abort(404)
        
    # Get recent prescriptions by this doctor
    recent_prescriptions = Prescription.query.filter_by(doctor_id=doctor.doctor_id).order_by(Prescription.created_at.desc()).limit(5).all()
    
    # Get today's appointments and stats
    from datetime import date, timedelta
    today = date.today()
    
    appointments_today = Appointment.query.filter_by(doctor_id=doctor.doctor_id, appointment_date=today).order_by(Appointment.appointment_time).all()
    
    todays_count = len(appointments_today)
    completed_count = sum(1 for a in appointments_today if a.status == 'Completed')
    pending_count = sum(1 for a in appointments_today if a.status == 'Scheduled')
    cancelled_count = sum(1 for a in appointments_today if a.status == 'Cancelled')
    
    # Get missed medicines for this doctor's patients
    from models import MedicineReminder, RefillReminder, PrescriptionMedicine
    
    missed_medicines = MedicineReminder.query.join(MedicineReminder.prescription_medicine).join(PrescriptionMedicine.prescription).filter(
        Prescription.doctor_id == doctor.doctor_id,
        MedicineReminder.status == 'Skipped',
        MedicineReminder.date >= (date.today() - timedelta(days=7))
    ).limit(5).all()
    
    pending_refills = RefillReminder.query.join(RefillReminder.prescription_medicine).join(PrescriptionMedicine.prescription).filter(
        Prescription.doctor_id == doctor.doctor_id,
        RefillReminder.estimated_refill_date >= date.today(),
        RefillReminder.estimated_refill_date <= (date.today() + timedelta(days=7))
    ).limit(5).all()
    
    return render_template('doctor/dashboard.html', 
                           doctor=doctor, 
                           prescriptions=recent_prescriptions, 
                           appointments=appointments_today,
                           todays_count=todays_count,
                           completed_count=completed_count,
                           pending_count=pending_count,
                           cancelled_count=cancelled_count,
                           missed_medicines=missed_medicines,
                           pending_refills=pending_refills)

import uuid
import os
import qrcode
from flask import request, redirect, url_for, flash, current_app
from forms.prescription_forms import PrescriptionForm

@doctor_bp.route('/prescription/new', methods=['GET', 'POST'])
@login_required
@doctor_required
def new_prescription():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        abort(404)
        
    form = PrescriptionForm()
    
    if form.validate_on_submit():
        # Ensure a patient is selected
        patient_id = form.patient_id.data
        if not patient_id:
            flash("Please search and select a patient first.", "danger")
            return redirect(url_for('doctor.new_prescription'))
            
        patient = Patient.query.get(patient_id)
        if not patient:
            flash("Selected patient not found.", "danger")
            return redirect(url_for('doctor.new_prescription'))
            
        prescription_uuid = str(uuid.uuid4())
        new_rx = Prescription(
            uuid=prescription_uuid,
            doctor_id=doctor.doctor_id,
            patient_id=patient.patient_id,
            diagnosis=form.diagnosis.data,
            symptoms=form.symptoms.data,
            clinical_notes=form.clinical_notes.data,
            blood_pressure=form.blood_pressure.data,
            pulse=form.pulse.data if form.pulse.data else None,
            temperature=form.temperature.data if form.temperature.data else None,
            oxygen_saturation=form.oxygen_saturation.data if form.oxygen_saturation.data else None,
            follow_up_date=form.follow_up_date.data
        )
        db.session.add(new_rx)
        db.session.flush() # get new_rx.prescription_id
        
        # Handle Medicines
        med_names = request.form.getlist('medicine_name[]')
        medicine_types = request.form.getlist('medicine_type[]')
        strengths = request.form.getlist('strength[]')
        dosages = request.form.getlist('dosage[]')
        frequencies = request.form.getlist('frequency[]')
        durations = request.form.getlist('duration[]')
        food_relations = request.form.getlist('food_relation[]')
        instructions = request.form.getlist('instructions[]')
        mornings = request.form.getlist('morning[]')
        afternoons = request.form.getlist('afternoon[]')
        nights = request.form.getlist('night[]')
        
        for i in range(len(med_names)):
            name = med_names[i].strip()
            if not name:
                continue
                
            # Find or create medicine
            from models import Medicine, PrescriptionMedicine
            medicine = Medicine.query.filter_by(medicine_name=name).first()
            if not medicine:
                medicine = Medicine(medicine_name=name)
                db.session.add(medicine)
                db.session.flush()
                
            # Create PrescriptionMedicine link
            rx_med = PrescriptionMedicine(
                prescription_id=new_rx.prescription_id,
                medicine_id=medicine.medicine_id,
                medicine_type=medicine_types[i] if i < len(medicine_types) else '',
                strength=strengths[i] if i < len(strengths) else '',
                dosage=dosages[i] if i < len(dosages) else '',
                frequency=frequencies[i] if i < len(frequencies) else '',
                morning=mornings[i] if i < len(mornings) else '',
                afternoon=afternoons[i] if i < len(afternoons) else '',
                night=nights[i] if i < len(nights) else '',
                duration=durations[i] if i < len(durations) else '',
                food_relation=food_relations[i] if i < len(food_relations) else 'Anytime',
                instructions=instructions[i] if i < len(instructions) else ''
            )
            db.session.add(rx_med)

        db.session.commit()
        
        # Trigger Reminder Generation
        from services.reminder_service import ReminderService
        ReminderService.generate_medicine_reminders(new_rx)
        
        # Generate QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        # The URL for the public prescription view / scanner handler
        base_url = current_app.config.get('BASE_URL')
        if base_url:
            public_url = f"{base_url.rstrip('/')}{url_for('public.process_scan', uuid=prescription_uuid)}"
        else:
            public_url = url_for('public.process_scan', uuid=prescription_uuid, _external=True)
            
        qr.add_data(public_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        qr_filename = f"{prescription_uuid}.png"
        qr_path = os.path.join(current_app.config['QR_FOLDER'], qr_filename)
        img.save(qr_path)
        
        flash('Prescription created successfully! QR Code generated.', 'success')
        return redirect(url_for('doctor.dashboard'))
        
    return render_template('doctor/new_prescription.html', form=form)

@doctor_bp.route('/prescription/view/<uuid>')
@login_required
@doctor_required
def view_prescription(uuid):
    prescription = Prescription.query.filter_by(uuid=uuid).first()
    if not prescription:
        abort(404)
        
    # Ensure this doctor owns the prescription
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if prescription.doctor_id != doctor.doctor_id:
        abort(403)
        
    patient = Patient.query.get(prescription.patient_id)
    return render_template('doctor/view_prescription.html', prescription=prescription, patient=patient, doctor=doctor)

@doctor_bp.route('/prescription/<uuid>/pdf')
@login_required
@doctor_required
def prescription_pdf(uuid):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    rx = Prescription.query.filter_by(uuid=uuid, doctor_id=doctor.doctor_id).first()
    
    if not rx:
        abort(404)
        
    from services.pdf_service import generate_prescription_pdf
    from flask import make_response
    
    pdf_buffer = generate_prescription_pdf(rx)
    
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Disposition'] = f'inline; filename=Prescription_{rx.uuid[:8]}.pdf'
    response.headers['Content-type'] = 'application/pdf'
    return response

@doctor_bp.route('/patients')
@login_required
@doctor_required
def patients_list():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    
    query = Patient.query
    if search_query:
        query = query.filter(
            db.or_(
                Patient.patient_uid.ilike(f'%{search_query}%'),
                Patient.full_name.ilike(f'%{search_query}%'),
                Patient.phone.ilike(f'%{search_query}%')
            )
        )
    
    pagination = query.order_by(Patient.registration_date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('doctor/patients_list.html', pagination=pagination, search_query=search_query)

@doctor_bp.route('/patient/add', methods=['GET', 'POST'])
@login_required
@doctor_required
def add_patient():
    from forms.patient_forms import PatientForm
    form = PatientForm()
    
    if form.validate_on_submit():
        phone = form.phone.data
        if Patient.query.filter_by(phone=phone).first():
            flash('Phone number is already registered to another patient.', 'danger')
            return render_template('doctor/add_patient.html', form=form)
            
        new_patient = Patient(
            full_name=form.full_name.data,
            dob=form.dob.data,
            age=form.age.data,
            gender=form.gender.data,
            blood_group=form.blood_group.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            pin_code=form.pin_code.data,
            height=form.height.data,
            weight=form.weight.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_number=form.emergency_contact_number.data,
            allergies=form.allergies.data,
            chronic_diseases=form.chronic_diseases.data,
            past_medical_history=form.past_medical_history.data,
            status=form.status.data
        )
        
        db.session.add(new_patient)
        db.session.flush() # get patient_id
        
        # Generate patient_uid
        new_patient.patient_uid = f"PT{new_patient.patient_id:06d}"
        
        db.session.commit()
        
        flash(f'Patient {new_patient.full_name} added successfully with ID {new_patient.patient_uid}.', 'success')
        return redirect(url_for('doctor.patients_list'))
        
    return render_template('doctor/add_patient.html', form=form)

@doctor_bp.route('/patient/view/<int:patient_id>')
@login_required
@doctor_required
def view_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.created_at.desc()).all()
    appointments = Appointment.query.filter_by(patient_id=patient_id).all()
    return render_template('doctor/view_patient.html', patient=patient, prescriptions=prescriptions, appointments=appointments)

@doctor_bp.route('/patient/edit/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@doctor_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    from forms.patient_forms import PatientForm
    form = PatientForm(obj=patient)
    
    if form.validate_on_submit():
        if Patient.query.filter(Patient.phone == form.phone.data, Patient.patient_id != patient.patient_id).first():
            flash('Phone number is already registered to another patient.', 'danger')
            return render_template('doctor/edit_patient.html', form=form, patient=patient)
            
        form.populate_obj(patient)
        db.session.commit()
        flash('Patient details updated successfully.', 'success')
        return redirect(url_for('doctor.view_patient', patient_id=patient.patient_id))
        
    return render_template('doctor/edit_patient.html', form=form, patient=patient)

@doctor_bp.route('/api/patients/search')
@login_required
@doctor_required
def api_search_patient():
    from flask import jsonify
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
        
    patients = Patient.query.filter(
        db.or_(
            Patient.patient_uid.ilike(f'%{query}%'),
            Patient.full_name.ilike(f'%{query}%'),
            Patient.phone.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = [{
        'id': p.patient_id,
        'uid': p.patient_uid,
        'name': p.full_name,
        'phone': p.phone,
        'gender': p.gender,
        'age': p.age,
        'blood_group': p.blood_group,
        'weight': p.weight
    } for p in patients]
    
    return jsonify(results)

@doctor_bp.route('/prescriptions', methods=['GET'])
@login_required
@doctor_required
def prescriptions_list():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    # Filter functionality
    query = Prescription.query.filter_by(doctor_id=doctor.doctor_id)
    
    patient_query = request.args.get('patient')
    status = request.args.get('status')
    date = request.args.get('date')
    
    if patient_query:
        query = query.join(Patient).filter(db.or_(Patient.full_name.ilike(f'%{patient_query}%'), Patient.patient_uid.ilike(f'%{patient_query}%')))
    if status:
        query = query.filter(Prescription.status == status)
    if date:
        query = query.filter(db.func.date(Prescription.created_at) == date)
        
    prescriptions = query.order_by(Prescription.created_at.desc()).all()
    
    return render_template('doctor/prescriptions_list.html', prescriptions=prescriptions)

@doctor_bp.route('/prescription/edit/<uuid>', methods=['GET', 'POST'])
@login_required
@doctor_required
def edit_prescription(uuid):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    prescription = Prescription.query.filter_by(uuid=uuid, doctor_id=doctor.doctor_id).first_or_404()
    
    from forms.prescription_forms import PrescriptionForm
    form = PrescriptionForm(obj=prescription)
    
    if request.method == 'GET':
        form.patient_id.data = prescription.patient_id
    
    if form.validate_on_submit():
        prescription.diagnosis = form.diagnosis.data
        prescription.symptoms = form.symptoms.data
        prescription.clinical_notes = form.clinical_notes.data
        prescription.blood_pressure = form.blood_pressure.data
        prescription.pulse = form.pulse.data if form.pulse.data else None
        prescription.temperature = form.temperature.data if form.temperature.data else None
        prescription.oxygen_saturation = form.oxygen_saturation.data if form.oxygen_saturation.data else None
        prescription.follow_up_date = form.follow_up_date.data
        prescription.status = form.status.data
        
        # We can optionally handle updating medicines here, or just keep it simple and delete/re-add.
        # For full hospital grade edit: delete all existing meds and add from form
        from models import PrescriptionMedicine, Medicine
        PrescriptionMedicine.query.filter_by(prescription_id=prescription.prescription_id).delete()
        
        # Handle Medicines
        med_names = request.form.getlist('medicine_name[]')
        medicine_types = request.form.getlist('medicine_type[]')
        strengths = request.form.getlist('strength[]')
        dosages = request.form.getlist('dosage[]')
        frequencies = request.form.getlist('frequency[]')
        durations = request.form.getlist('duration[]')
        food_relations = request.form.getlist('food_relation[]')
        instructions = request.form.getlist('instructions[]')
        mornings = request.form.getlist('morning[]')
        afternoons = request.form.getlist('afternoon[]')
        nights = request.form.getlist('night[]')
        
        for i in range(len(med_names)):
            name = med_names[i].strip()
            if not name:
                continue
                
            medicine = Medicine.query.filter_by(medicine_name=name).first()
            if not medicine:
                medicine = Medicine(medicine_name=name)
                db.session.add(medicine)
                db.session.flush()
                
            rx_med = PrescriptionMedicine(
                prescription_id=prescription.prescription_id,
                medicine_id=medicine.medicine_id,
                medicine_type=medicine_types[i] if i < len(medicine_types) else '',
                strength=strengths[i] if i < len(strengths) else '',
                dosage=dosages[i] if i < len(dosages) else '',
                frequency=frequencies[i] if i < len(frequencies) else '',
                morning=mornings[i] if i < len(mornings) else '',
                afternoon=afternoons[i] if i < len(afternoons) else '',
                night=nights[i] if i < len(nights) else '',
                duration=durations[i] if i < len(durations) else '',
                food_relation=food_relations[i] if i < len(food_relations) else 'Anytime',
                instructions=instructions[i] if i < len(instructions) else ''
            )
            db.session.add(rx_med)

        db.session.commit()
        flash('Prescription updated successfully!', 'success')
        return redirect(url_for('doctor.view_prescription', uuid=prescription.uuid))
        
    return render_template('doctor/edit_prescription.html', form=form, prescription=prescription)

@doctor_bp.route('/prescription/delete/<uuid>', methods=['POST'])
@login_required
@doctor_required
def delete_prescription(uuid):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    prescription = Prescription.query.filter_by(uuid=uuid, doctor_id=doctor.doctor_id).first_or_404()
    
    db.session.delete(prescription)
    db.session.commit()
    flash('Prescription deleted successfully!', 'success')
    return redirect(url_for('doctor.prescriptions_list'))

import werkzeug.utils
import os
from forms.doctor_forms import DoctorProfileForm
from models.doctor import DoctorProfile

@doctor_bp.route('/profile')
@login_required
@doctor_required
def profile():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        abort(404)
    return render_template('doctor/profile.html', doctor=doctor)

@doctor_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@doctor_required
def edit_profile():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        abort(404)
        
    form = DoctorProfileForm()
    
    if form.validate_on_submit():
        # Update Doctor fields
        doctor.full_name = form.full_name.data
        doctor.registration_number = form.registration_number.data
        doctor.specialization = form.specialization.data
        doctor.department = form.department.data
        doctor.hospital = form.hospital.data
        doctor.phone = form.phone.data
        
        # Ensure DoctorProfile exists
        if not doctor.profile:
            doctor.profile = DoctorProfile(doctor_id=doctor.doctor_id)
            
        profile = doctor.profile
        profile.qualification = form.qualification.data
        profile.years_of_experience = form.years_of_experience.data
        profile.address = form.address.data
        profile.consultation_timings = form.consultation_timings.data
        profile.biography = form.biography.data
        
        # Update User email if changed
        user = current_user
        if form.email.data and form.email.data != user.email:
            # check if email exists
            from models.user import User
            if User.query.filter(User.email == form.email.data, User.id != user.id).first():
                flash('Email is already in use by another account.', 'danger')
                return render_template('doctor/edit_profile.html', form=form, doctor=doctor)
            user.email = form.email.data
            
        # Handle file uploads securely
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'doctors')
        os.makedirs(upload_folder, exist_ok=True)
        
        if form.profile_photo.data:
            photo = form.profile_photo.data
            filename = werkzeug.utils.secure_filename(f"profile_{doctor.doctor_id}_{photo.filename}")
            photo_path = os.path.join(upload_folder, filename)
            photo.save(photo_path)
            profile.profile_photo = filename
            
        if form.digital_signature.data:
            sig = form.digital_signature.data
            filename = werkzeug.utils.secure_filename(f"sig_{doctor.doctor_id}_{sig.filename}")
            sig_path = os.path.join(upload_folder, filename)
            sig.save(sig_path)
            profile.digital_signature = filename
            
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('doctor.profile'))
        
    elif request.method == 'GET':
        # Populate form
        form.full_name.data = doctor.full_name
        form.registration_number.data = doctor.registration_number
        form.specialization.data = doctor.specialization
        form.department.data = doctor.department
        form.hospital.data = doctor.hospital
        form.phone.data = doctor.phone
        form.email.data = current_user.email
        
        if doctor.profile:
            form.qualification.data = doctor.profile.qualification
            form.years_of_experience.data = doctor.profile.years_of_experience
            form.address.data = doctor.profile.address
            form.consultation_timings.data = doctor.profile.consultation_timings
            form.biography.data = doctor.profile.biography
            
    return render_template('doctor/edit_profile.html', form=form, doctor=doctor)

@doctor_bp.route('/patient/delete/<int:patient_id>', methods=['POST'])
@login_required
@doctor_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    password = request.form.get('password')
    from werkzeug.security import check_password_hash
    
    if not check_password_hash(current_user.password_hash, password):
        flash('Incorrect password.', 'danger')
        return redirect(url_for('doctor.patients_list'))
        
    from models.audit import PatientDeletionAudit, QRScanHistory, DispensingHistory, MedicineDispensing
    from models.prescription import Prescription, PrescriptionMedicine
    from models.appointment import Appointment
    
    # Audit log
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    audit = PatientDeletionAudit(
        doctor_id=doctor.doctor_id,
        doctor_name=doctor.full_name,
        patient_id=patient.patient_id,
        patient_name=patient.full_name,
        ip_address=ip_address
    )
    db.session.add(audit)
    
    # Cascade delete related records manually to be safe
    Appointment.query.filter_by(patient_id=patient_id).delete()
    
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).all()
    for rx in prescriptions:
        rx_meds = PrescriptionMedicine.query.filter_by(prescription_id=rx.prescription_id).all()
        for rx_med in rx_meds:
            MedicineDispensing.query.filter_by(prescription_medicine_id=rx_med.id).delete()
            db.session.delete(rx_med)
            
        QRScanHistory.query.filter_by(prescription_id=rx.prescription_id).delete()
        DispensingHistory.query.filter_by(prescription_id=rx.prescription_id).delete()
        db.session.delete(rx)
        
    # Delete patient
    db.session.delete(patient)
    db.session.commit()
    
    flash('Patient deleted successfully.', 'success')
    return redirect(url_for('doctor.patients_list'))

from forms.appointment_forms import AppointmentForm
from datetime import datetime

@doctor_bp.route('/appointments')
@login_required
@doctor_required
def appointments_list():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    # Filter parameters
    search_query = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    date_filter = request.args.get('date', '')
    
    query = Appointment.query.filter_by(doctor_id=doctor.doctor_id)
    
    if search_query:
        query = query.join(Patient).filter(
            db.or_(
                Patient.full_name.ilike(f'%{search_query}%'),
                Appointment.appointment_id.cast(db.String).ilike(f'%{search_query}%')
            )
        )
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    if date_filter:
        query = query.filter(Appointment.appointment_date == date_filter)
        
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).paginate(page=page, per_page=15, error_out=False)
    
    return render_template('doctor/appointments_list.html', pagination=pagination, search_query=search_query)

@doctor_bp.route('/appointments/new', methods=['GET', 'POST'])
@login_required
@doctor_required
def new_appointment():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    form = AppointmentForm()
    
    if form.validate_on_submit():
        patient = Patient.query.get(form.patient_id.data)
        if not patient:
            flash("Selected patient not found.", "danger")
            return render_template('doctor/appointment_form.html', form=form, action="Book")
            
        new_app = Appointment(
            doctor_id=doctor.doctor_id,
            patient_id=patient.patient_id,
            appointment_date=form.appointment_date.data,
            appointment_time=form.appointment_time.data,
            department=form.department.data,
            reason_for_visit=form.reason_for_visit.data,
            appointment_type=form.appointment_type.data,
            status=form.status.data,
            notes=form.notes.data
        )
        
        db.session.add(new_app)
        db.session.commit()
        
        from services.reminder_service import ReminderService
        ReminderService.create_appointment_reminder(new_app)
        
        flash("Appointment booked successfully.", "success")
        return redirect(url_for('doctor.appointments_list'))
        
    return render_template('doctor/appointment_form.html', form=form, action="Book")

@doctor_bp.route('/appointments/edit/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@doctor_required
def edit_appointment(appointment_id):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.filter_by(appointment_id=appointment_id, doctor_id=doctor.doctor_id).first_or_404()
    
    form = AppointmentForm(obj=appointment)
    
    if form.validate_on_submit():
        patient = Patient.query.get(form.patient_id.data)
        if not patient:
            flash("Selected patient not found.", "danger")
            return render_template('doctor/appointment_form.html', form=form, action="Edit")
            
        form.populate_obj(appointment)
        db.session.commit()
        
        flash("Appointment updated successfully.", "success")
        return redirect(url_for('doctor.appointments_list'))
        
    if request.method == 'GET':
        # Ensure patient_id is pre-filled correctly
        form.patient_id.data = appointment.patient_id
        
    # We pass the patient name to pre-fill the search box if using JS
    patient = Patient.query.get(appointment.patient_id)
    return render_template('doctor/appointment_form.html', form=form, action="Edit", patient_name=patient.full_name)

@doctor_bp.route('/appointments/update_status/<int:appointment_id>', methods=['POST'])
@login_required
@doctor_required
def update_appointment_status(appointment_id):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.filter_by(appointment_id=appointment_id, doctor_id=doctor.doctor_id).first_or_404()
    
    new_status = request.form.get('status')
    if new_status in ['Scheduled', 'Completed', 'Cancelled', 'No Show']:
        appointment.status = new_status
        db.session.commit()
        flash(f"Appointment status updated to {new_status}.", "success")
    else:
        flash("Invalid status.", "danger")
        
    return redirect(request.referrer or url_for('doctor.appointments_list'))

@doctor_bp.route('/appointments/delete/<int:appointment_id>', methods=['POST'])
@login_required
@doctor_required
def delete_appointment(appointment_id):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.filter_by(appointment_id=appointment_id, doctor_id=doctor.doctor_id).first_or_404()
    
    db.session.delete(appointment)
    db.session.commit()
    
    flash("Appointment deleted successfully.", "success")
    return redirect(url_for('doctor.appointments_list'))

from flask import jsonify
from services.ai_service import AIService

@doctor_bp.route('/prescription/<uuid>/ai_explanation')
@login_required
@doctor_required
def prescription_ai_explanation(uuid):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    rx = Prescription.query.filter_by(uuid=uuid, doctor_id=doctor.doctor_id).first_or_404()
    
    # Build context
    context = f"Prescription ID: {rx.uuid[:8]}\nPatient: {rx.patient.full_name}\nDiagnosis: {rx.diagnosis}\nMedicines:\n"
    for med in rx.medicines:
        context += f"- {med.medicine.medicine_name}: {med.dosage}, {med.frequency} for {med.duration_days} days. Instructions: {med.instructions}\n"
        
    explanation = AIService.get_prescription_explanation(context)
    
    return jsonify({'explanation': explanation})
