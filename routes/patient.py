from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, make_response
from flask_login import login_required, current_user
from functools import wraps
from models import Patient, Prescription, Appointment, User, PrescriptionMedicine, Medicine
from extensions import db
import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

patient_bp = Blueprint('patient', __name__)

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'patient':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@patient_bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        abort(404)
        
    prescriptions = Prescription.query.filter_by(patient_id=patient.patient_id).order_by(Prescription.created_at.desc()).all()
    appointments = Appointment.query.filter_by(patient_id=patient.patient_id).order_by(Appointment.appointment_date).all()
    
    # Stats
    total_rx = len(prescriptions)
    active_rx = sum(1 for rx in prescriptions if rx.status == 'Active')
    completed_rx = sum(1 for rx in prescriptions if rx.status == 'Completed')
    upcoming_appointments = sum(1 for apt in appointments if apt.appointment_date >= datetime.date.today())
    
    recent_rx = prescriptions[:5]
    
    # Find the next appointment (first scheduled appointment from today onwards)
    next_appointment = Appointment.query.filter(
        Appointment.patient_id == patient.patient_id,
        Appointment.status == 'Scheduled',
        Appointment.appointment_date >= datetime.date.today()
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).first()
    
    # Today's Reminders
    from models.notification import MedicineReminder, RefillReminder
    today_reminders = MedicineReminder.query.filter_by(patient_id=patient.patient_id, date=datetime.date.today()).all()
    
    reminders_grouped = {
        'Morning': [r for r in today_reminders if r.time_of_day == 'Morning'],
        'Afternoon': [r for r in today_reminders if r.time_of_day == 'Afternoon'],
        'Evening': [r for r in today_reminders if r.time_of_day == 'Evening'],
        'Night': [r for r in today_reminders if r.time_of_day == 'Night']
    }
    
    # Upcoming Refills (next 7 days)
    upcoming_refills = RefillReminder.query.filter(
        RefillReminder.patient_id == patient.patient_id,
        RefillReminder.estimated_refill_date >= datetime.date.today(),
        RefillReminder.estimated_refill_date <= (datetime.date.today() + datetime.timedelta(days=7))
    ).order_by(RefillReminder.estimated_refill_date).all()
    
    return render_template('patient/dashboard.html', 
                           patient=patient, 
                           recent_rx=recent_rx,
                           appointments=appointments,
                           next_appointment=next_appointment,
                           total_rx=total_rx,
                           active_rx=active_rx,
                           completed_rx=completed_rx,
                           upcoming_appointments=upcoming_appointments,
                           today_date=datetime.date.today(),
                           reminders_grouped=reminders_grouped,
                           upcoming_refills=upcoming_refills)

@patient_bp.route('/prescriptions')
@login_required
@patient_required
def prescriptions():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    rx_list = Prescription.query.filter_by(patient_id=patient.patient_id).order_by(Prescription.created_at.desc()).all()
    return render_template('patient/prescriptions.html', prescriptions=rx_list)

@patient_bp.route('/prescription/<uuid>')
@login_required
@patient_required
def prescription_view(uuid):
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    rx = Prescription.query.filter_by(uuid=uuid, patient_id=patient.patient_id).first()
    
    if not rx:
        flash('Prescription not found or unauthorized access.', 'danger')
        return redirect(url_for('patient.prescriptions'))
        
    return render_template('patient/prescription_view.html', prescription=rx)

@patient_bp.route('/prescription/<uuid>/pdf')
@login_required
@patient_required
def prescription_pdf(uuid):
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    rx = Prescription.query.filter_by(uuid=uuid, patient_id=patient.patient_id).first()
    
    if not rx:
        abort(404)
        
    from services.pdf_service import generate_prescription_pdf
    pdf_buffer = generate_prescription_pdf(rx)
    
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Disposition'] = f'inline; filename=Prescription_{rx.uuid[:8]}.pdf'
    response.headers['Content-type'] = 'application/pdf'
    return response

@patient_bp.route('/schedule')
@login_required
@patient_required
def schedule():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    active_rx = Prescription.query.filter_by(patient_id=patient.patient_id, status='Active').all()
    
    schedule_data = {
        'Morning': [],
        'Afternoon': [],
        'Night': [],
        'As Needed': []
    }
    
    for rx in active_rx:
        for med in rx.medicines:
            freq = med.frequency.lower()
            if 'morning' in freq or 'od' in freq or 'bid' in freq or 'tid' in freq or 'qid' in freq or '1-0-0' in freq or '1-0-1' in freq or '1-1-1' in freq:
                schedule_data['Morning'].append(med)
            if 'afternoon' in freq or 'tid' in freq or 'qid' in freq or '0-1-0' in freq or '1-1-1' in freq:
                schedule_data['Afternoon'].append(med)
            if 'night' in freq or 'bid' in freq or 'tid' in freq or 'qid' in freq or '0-0-1' in freq or '1-0-1' in freq or '1-1-1' in freq:
                schedule_data['Night'].append(med)
            if 'sos' in freq or 'as needed' in freq:
                schedule_data['As Needed'].append(med)
                
    return render_template('patient/schedule.html', schedule=schedule_data)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@patient_required
def profile():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        phone = request.form.get('phone')
        address = request.form.get('address')
        emergency_contact = request.form.get('emergency_contact')
        
        # Optionally password
        password = request.form.get('password')
        
        if phone:
            patient.phone = phone
        patient.address = address
        patient.emergency_contact = emergency_contact
        
        if password:
            current_user.set_password(password)
            
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.profile'))
        
    return render_template('patient/profile.html', patient=patient)

@patient_bp.route('/history')
@login_required
@patient_required
def history():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    search = request.args.get('search', '')
    
    query = Prescription.query.filter_by(patient_id=patient.patient_id)
    
    if search:
        query = query.join(Doctor).filter(
            db.or_(
                Prescription.uuid.ilike(f'%{search}%'),
                Doctor.full_name.ilike(f'%{search}%'),
                db.cast(Prescription.created_at, db.String).ilike(f'%{search}%')
            )
        )
        
    prescriptions = query.order_by(Prescription.created_at.desc()).all()
    
    return render_template('patient/history.html', prescriptions=prescriptions, search=search)

from forms.appointment_forms import PatientAppointmentRequestForm

@patient_bp.route('/appointments')
@login_required
@patient_required
def appointments():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    upcoming = Appointment.query.filter(
        Appointment.patient_id == patient.patient_id,
        Appointment.appointment_date >= datetime.date.today(),
        Appointment.status == 'Scheduled'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    
    history = Appointment.query.filter(
        Appointment.patient_id == patient.patient_id,
        db.or_(Appointment.appointment_date < datetime.date.today(), Appointment.status != 'Scheduled')
    ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    return render_template('patient/appointments.html', upcoming=upcoming, history=history)

@patient_bp.route('/appointments/request', methods=['GET', 'POST'])
@login_required
@patient_required
def request_appointment():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    form = PatientAppointmentRequestForm()
    
    # Populate doctors for the select field
    doctors = Doctor.query.all()
    # We will just pass doctors to the template to build a custom select or we can dynamically set choices
    
    if form.validate_on_submit():
        doctor = Doctor.query.get(form.doctor_id.data)
        if not doctor:
            flash('Selected doctor not found.', 'danger')
            return redirect(url_for('patient.request_appointment'))
            
        new_app = Appointment(
            doctor_id=doctor.doctor_id,
            patient_id=patient.patient_id,
            appointment_date=form.appointment_date.data,
            appointment_time=form.appointment_time.data,
            reason_for_visit=form.reason_for_visit.data,
            appointment_type=form.appointment_type.data,
            status='Scheduled' # Request goes directly to scheduled in this simple workflow
        )
        db.session.add(new_app)
        db.session.commit()
        
        flash('Appointment requested successfully!', 'success')
        return redirect(url_for('patient.appointments'))
        
    return render_template('patient/request_appointment.html', form=form, doctors=doctors)

@patient_bp.route('/appointments/cancel/<int:appointment_id>', methods=['POST'])
@login_required
@patient_required
def cancel_appointment(appointment_id):
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    appointment = Appointment.query.filter_by(appointment_id=appointment_id, patient_id=patient.patient_id).first_or_404()
    
    if appointment.status == 'Scheduled' and appointment.appointment_date >= datetime.date.today():
        appointment.status = 'Cancelled'
        db.session.commit()
        flash('Appointment cancelled successfully.', 'success')
    else:
        flash('Cannot cancel this appointment.', 'danger')
        
    return redirect(url_for('patient.appointments'))

from flask import jsonify
from services.ai_service import AIService
from models.ai import AIChatHistory

@patient_bp.route('/ai_assistant')
@login_required
@patient_required
def ai_assistant():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    # Gather context from active prescriptions
    active_rx = Prescription.query.filter_by(patient_id=patient.patient_id, status='Active').all()
    
    # Load chat history
    chat_history = AIChatHistory.query.filter_by(user_id=current_user.id).order_by(AIChatHistory.timestamp.asc()).all()
    
    return render_template('patient/ai_assistant.html', patient=patient, has_active_rx=len(active_rx) > 0, chat_history=chat_history)

@patient_bp.route('/ai_assistant/chat', methods=['POST'])
@login_required
@patient_required
def ai_assistant_chat():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
        
    user_message = data.get('message')
    
    # Build prescription context
    active_rx = Prescription.query.filter_by(patient_id=patient.patient_id, status='Active').all()
    
    if not active_rx:
        context = "No active prescriptions found for this patient."
    else:
        context_parts = []
        for rx in active_rx:
            rx_part = f"Prescription ID: {rx.uuid[:8]}\nDoctor: {rx.doctor.full_name}\nDiagnosis: {rx.diagnosis}\nMedicines:\n"
            for med in rx.medicines:
                rx_part += f"- {med.medicine.medicine_name}: {med.dosage}, {med.frequency} for {med.duration_days} days. Instructions: {med.instructions}\n"
            context_parts.append(rx_part)
        
        context = "\n\n".join(context_parts)
        
    # Get response from AI Service
    ai_response = AIService.get_assistant_response(patient.full_name, context, user_message)
    
    # Save to database
    history_entry = AIChatHistory(
        user_id=current_user.id,
        message=user_message,
        response=ai_response
    )
    db.session.add(history_entry)
    db.session.commit()
    
    return jsonify({
        'reply': ai_response
    })

@patient_bp.route('/ai_assistant/clear', methods=['POST'])
@login_required
@patient_required
def ai_assistant_clear():
    AIChatHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True})

from models.notification import Notification, MedicineReminder, RefillReminder

@patient_bp.route('/notifications')
@login_required
@patient_required
def notifications():
    category = request.args.get('category', 'All')
    search = request.args.get('search', '')
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if category != 'All':
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Notification.message.ilike(f'%{search}%'))
        
    notifications = query.order_by(Notification.created_at.desc()).all()
    
    return render_template('patient/notifications.html', notifications=notifications, current_category=category, search=search)

@patient_bp.route('/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
@patient_required
def mark_notification_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@patient_bp.route('/notifications/delete/<int:notif_id>', methods=['POST'])
@login_required
@patient_required
def delete_notification(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    db.session.delete(notif)
    db.session.commit()
    return jsonify({'success': True})

@patient_bp.route('/reminders/toggle/<int:reminder_id>', methods=['POST'])
@login_required
@patient_required
def toggle_reminder(reminder_id):
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    reminder = MedicineReminder.query.filter_by(id=reminder_id, patient_id=patient.patient_id).first_or_404()
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status in ['Pending', 'Taken', 'Skipped']:
        reminder.status = new_status
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Invalid status'}), 400
