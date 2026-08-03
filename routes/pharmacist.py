from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, make_response
from flask_login import login_required, current_user
from functools import wraps
from flask import abort
from models import Pharmacist, DispensingHistory, Prescription, PrescriptionMedicine, Patient, Doctor, Medicine
from models.audit import QRScanHistory, MedicineDispensing
from extensions import db
import datetime
import io
import csv
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

pharmacist_bp = Blueprint('pharmacist', __name__)

def pharmacist_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'pharmacist':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@pharmacist_bp.route('/dashboard')
@login_required
@pharmacist_required
def dashboard():
    pharmacist = Pharmacist.query.filter_by(user_id=current_user.id).first()
    if not pharmacist:
        abort(404)
        
    today = datetime.date.today()
    
    # Stats
    today_dispensed = MedicineDispensing.query.filter(
        db.func.date(MedicineDispensing.dispensed_at) == today,
        MedicineDispensing.pharmacist_id == pharmacist.pharmacist_id
    ).count()
    
    pending_rx = PrescriptionMedicine.query.filter_by(dispense_status='Pending').count()
    partial_rx = PrescriptionMedicine.query.filter_by(dispense_status='Partially Dispensed').count()
    completed_rx = PrescriptionMedicine.query.filter_by(dispense_status='Fully Dispensed').count()
    
    from models.notification import RefillReminder
    upcoming_refills = RefillReminder.query.filter(
        RefillReminder.estimated_refill_date >= today,
        RefillReminder.estimated_refill_date <= (today + datetime.timedelta(days=7))
    ).order_by(RefillReminder.estimated_refill_date).all()
    
    recent_scans = QRScanHistory.query.filter_by(pharmacist_id=pharmacist.pharmacist_id).order_by(QRScanHistory.scanned_at.desc()).limit(5).all()
    
    return render_template('pharmacist/dashboard.html', 
                           pharmacist=pharmacist, 
                           today_dispensed=today_dispensed,
                           pending_rx=pending_rx,
                           partial_rx=partial_rx,
                           completed_rx=completed_rx,
                           recent_scans=recent_scans,
                           upcoming_refills=upcoming_refills)

@pharmacist_bp.route('/dispense/<uuid>', methods=['GET', 'POST'])
@login_required
@pharmacist_required
def dispense(uuid):
    pharmacist = Pharmacist.query.filter_by(user_id=current_user.id).first()
    if not pharmacist:
        abort(404)
        
    prescription = Prescription.query.filter_by(uuid=uuid).first()
    if not prescription:
        flash('Invalid Prescription QR', 'danger')
        return redirect(url_for('pharmacist.dashboard'))
        
    if request.method == 'POST':
        if prescription.status == 'Cancelled':
            flash('Cannot dispense medicines for a Cancelled prescription.', 'danger')
            return redirect(url_for('pharmacist.dispense', uuid=uuid))
            
        notes = request.form.get('dispense_notes', '')
        
        # Update medicine statuses and create dispensing log
        for rx_med in prescription.medicines:
            status = request.form.get(f'med_status_{rx_med.id}')
            qty_str = request.form.get(f'med_qty_{rx_med.id}', '0')
            qty = int(qty_str) if qty_str.isdigit() else 0
            med_remarks = request.form.get(f'med_remarks_{rx_med.id}', '')
            
            valid_statuses = ['Pending', 'Partially Dispensed', 'Fully Dispensed', 'Not Available', 'Cancelled']
            if status in valid_statuses:
                # If status changed or qty > 0, log it
                if status != rx_med.dispense_status or qty > 0:
                    rx_med.dispense_status = status
                    med_dispense = MedicineDispensing(
                        prescription_medicine_id=rx_med.id,
                        pharmacist_id=pharmacist.pharmacist_id,
                        quantity=qty,
                        status=status,
                        remarks=med_remarks
                    )
                    db.session.add(med_dispense)
                
        # Record overall prescription dispensing history
        history = DispensingHistory(
            prescription_id=prescription.prescription_id,
            pharmacist_id=pharmacist.pharmacist_id,
            notes=notes
        )
        db.session.add(history)
        db.session.commit()
        
        flash('Dispensing records updated successfully.', 'success')
        return redirect(url_for('pharmacist.dashboard'))
        
    return render_template('pharmacist/dispense.html', prescription=prescription)

@pharmacist_bp.route('/prescription/<uuid>/pdf')
@login_required
@pharmacist_required
def prescription_pdf(uuid):
    rx = Prescription.query.filter_by(uuid=uuid).first()
    if not rx:
        abort(404)
        
    from services.pdf_service import generate_prescription_pdf
    from flask import make_response
    
    pdf_buffer = generate_prescription_pdf(rx)
    
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Disposition'] = f'inline; filename=Prescription_{rx.uuid[:8]}.pdf'
    response.headers['Content-type'] = 'application/pdf'
    return response

@pharmacist_bp.route('/history')
@login_required
@pharmacist_required
def history():
    pharmacist = Pharmacist.query.filter_by(user_id=current_user.id).first()
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = MedicineDispensing.query.filter_by(pharmacist_id=pharmacist.pharmacist_id)
    if search:
        # Join appropriately to search patient, rx, etc.
        query = query.join(PrescriptionMedicine).join(Prescription).join(Patient).filter(
            db.or_(
                Patient.full_name.ilike(f'%{search}%'),
                Prescription.uuid.ilike(f'%{search}%')
            )
        )
        
    pagination = query.order_by(MedicineDispensing.dispensed_at.desc()).paginate(page=page, per_page=20)
    return render_template('pharmacist/history.html', pagination=pagination, search=search)

@pharmacist_bp.route('/search')
@login_required
@pharmacist_required
def search():
    query = request.args.get('q', '')
    results = []
    if query:
        # Search prescriptions
        prescriptions = Prescription.query.join(Patient).join(Doctor).outerjoin(PrescriptionMedicine).outerjoin(Medicine).filter(
            db.or_(
                Prescription.uuid.ilike(f'%{query}%'),
                Prescription.prescription_id.cast(db.String).ilike(f'%{query}%'),
                Patient.full_name.ilike(f'%{query}%'),
                Patient.patient_uid.ilike(f'%{query}%'),
                Patient.phone.ilike(f'%{query}%'),
                Doctor.full_name.ilike(f'%{query}%'),
                Medicine.medicine_name.ilike(f'%{query}%')
            )
        ).limit(20).all()
        # Deduplicate results since outerjoin can multiply rows
        results = list({p.prescription_id: p for p in prescriptions}.values())
        
    return render_template('pharmacist/search.html', results=results, query=query)

@pharmacist_bp.route('/refills')
@login_required
@pharmacist_required
def refills():
    pharmacist = Pharmacist.query.filter_by(user_id=current_user.id).first()
    
    # Get medicines that have refills remaining
    refillable_meds = PrescriptionMedicine.query.filter(PrescriptionMedicine.refill_count > 0).all()
    
    return render_template('pharmacist/refills.html', meds=refillable_meds)

@pharmacist_bp.route('/refill/<int:med_id>', methods=['POST'])
@login_required
@pharmacist_required
def process_refill(med_id):
    pharmacist = Pharmacist.query.filter_by(user_id=current_user.id).first()
    rx_med = PrescriptionMedicine.query.get_or_404(med_id)
    
    if rx_med.refill_count > 0:
        rx_med.refill_count -= 1
        qty = request.form.get('quantity', type=int, default=0)
        remarks = request.form.get('remarks', 'Refill processed')
        
        med_dispense = MedicineDispensing(
            prescription_medicine_id=rx_med.id,
            pharmacist_id=pharmacist.pharmacist_id,
            quantity=qty,
            status='Fully Dispensed',
            remarks=remarks
        )
        db.session.add(med_dispense)
        db.session.commit()
        flash('Refill processed successfully.', 'success')
    else:
        flash('No refills remaining for this medicine.', 'danger')
        
    return redirect(url_for('pharmacist.refills'))

@pharmacist_bp.route('/patient/<int:patient_id>')
@login_required
@pharmacist_required
def patient_view(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    prescriptions = Prescription.query.filter_by(patient_id=patient.patient_id).order_by(Prescription.created_at.desc()).all()
    return render_template('pharmacist/patient_view.html', patient=patient, prescriptions=prescriptions)

@pharmacist_bp.route('/reports')
@login_required
@pharmacist_required
def reports():
    pharmacist = Pharmacist.query.filter_by(user_id=current_user.id).first()
    return render_template('pharmacist/reports.html')

@pharmacist_bp.route('/reports/export')
@login_required
@pharmacist_required
def export_report():
    pharmacist = Pharmacist.query.filter_by(user_id=current_user.id).first()
    report_type = request.args.get('type', 'today')
    
    query = MedicineDispensing.query.filter_by(pharmacist_id=pharmacist.pharmacist_id)
    today = datetime.date.today()
    
    if report_type == 'today':
        query = query.filter(db.func.date(MedicineDispensing.dispensed_at) == today)
    elif report_type == 'weekly':
        week_ago = today - datetime.timedelta(days=7)
        query = query.filter(db.func.date(MedicineDispensing.dispensed_at) >= week_ago)
    elif report_type == 'monthly':
        month_ago = today - datetime.timedelta(days=30)
        query = query.filter(db.func.date(MedicineDispensing.dispensed_at) >= month_ago)
        
    dispensings = query.order_by(MedicineDispensing.dispensed_at.desc()).all()
    
    export_format = request.args.get('format', 'csv')
    
    if export_format == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{report_type.capitalize()} Report"
        ws.append(['Date', 'Medicine', 'Patient', 'Quantity', 'Status', 'Remarks'])
        
        for d in dispensings:
            med_name = d.prescription_medicine.medicine.medicine_name if d.prescription_medicine else 'Unknown'
            patient_name = d.prescription_medicine.prescription.patient.full_name if d.prescription_medicine and d.prescription_medicine.prescription.patient else 'Unknown'
            ws.append([
                d.dispensed_at.strftime('%Y-%m-%d %H:%M'),
                med_name,
                patient_name,
                d.quantity,
                d.status,
                d.remarks
            ])
            
        output = io.BytesIO()
        wb.save(output)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=dispensing_report_{report_type}.xlsx'
        response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return response
        
    elif export_format == 'pdf':
        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=letter)
        p.drawString(100, 750, f"Pharmacist Dispensing Report: {report_type.capitalize()}")
        p.drawString(100, 735, f"Date: {today.strftime('%Y-%m-%d')}")
        
        y = 700
        p.drawString(50, y, "Date")
        p.drawString(150, y, "Medicine")
        p.drawString(280, y, "Patient")
        p.drawString(400, y, "Qty")
        p.drawString(450, y, "Status")
        
        y -= 20
        for d in dispensings:
            med_name = d.prescription_medicine.medicine.medicine_name if d.prescription_medicine else 'Unknown'
            patient_name = d.prescription_medicine.prescription.patient.full_name if d.prescription_medicine and d.prescription_medicine.prescription.patient else 'Unknown'
            
            p.drawString(50, y, d.dispensed_at.strftime('%Y-%m-%d %H:%M'))
            p.drawString(150, y, (med_name[:18] + '..') if len(med_name) > 20 else med_name)
            p.drawString(280, y, (patient_name[:15] + '..') if len(patient_name) > 17 else patient_name)
            p.drawString(400, y, str(d.quantity))
            p.drawString(450, y, d.status)
            y -= 20
            
            if y < 50:
                p.showPage()
                y = 750
                
        p.save()
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=dispensing_report_{report_type}.pdf'
        response.headers['Content-type'] = 'application/pdf'
        return response
        
    else:
        # Fallback to CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Medicine', 'Patient', 'Quantity', 'Status', 'Remarks'])
        
        for d in dispensings:
            med_name = d.prescription_medicine.medicine.medicine_name if d.prescription_medicine else 'Unknown'
            patient_name = d.prescription_medicine.prescription.patient.full_name if d.prescription_medicine and d.prescription_medicine.prescription.patient else 'Unknown'
            
            writer.writerow([
                d.dispensed_at.strftime('%Y-%m-%d %H:%M'),
                med_name,
                patient_name,
                d.quantity,
                d.status,
                d.remarks
            ])
            
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=dispensing_report_{report_type}.csv'
        response.headers['Content-type'] = 'text/csv'
        return response

@pharmacist_bp.route('/appointments')
@login_required
@pharmacist_required
def appointments():
    pharmacist = Pharmacist.query.filter_by(user_id=current_user.id).first()
    
    # Pharmacists can view all appointments (maybe for today to prepare meds or just view status)
    search_query = request.args.get('q', '')
    date_filter = request.args.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    
    from models import Appointment, Patient
    query = Appointment.query
    
    if search_query:
        query = query.join(Patient).filter(
            db.or_(
                Patient.full_name.ilike(f'%{search_query}%'),
                Appointment.appointment_id.cast(db.String).ilike(f'%{search_query}%')
            )
        )
    if date_filter:
        query = query.filter(Appointment.appointment_date == date_filter)
        
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).paginate(page=page, per_page=15, error_out=False)
    
    return render_template('pharmacist/appointments.html', pagination=pagination, search_query=search_query, date_filter=date_filter)

from flask import jsonify
from services.ai_service import AIService

@pharmacist_bp.route('/prescription/<uuid>/ai_explanation')
@login_required
@pharmacist_required
def prescription_ai_explanation(uuid):
    rx = Prescription.query.filter_by(uuid=uuid).first_or_404()
    
    # Build context
    context = f"Prescription ID: {rx.uuid[:8]}\nPatient: {rx.patient.full_name}\nDiagnosis: {rx.diagnosis}\nMedicines:\n"
    for med in rx.medicines:
        context += f"- {med.medicine.medicine_name}: {med.dosage}, {med.frequency} for {med.duration_days} days. Instructions: {med.instructions}\n"
        
    explanation = AIService.get_prescription_explanation(context)
    
    return jsonify({'explanation': explanation})
