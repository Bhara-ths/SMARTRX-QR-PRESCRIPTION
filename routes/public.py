from flask import Blueprint, render_template, abort, request, redirect, url_for
from flask_login import current_user
from models import Prescription, Patient, Doctor, Pharmacist
from models.audit import QRScanHistory
from extensions import db
import datetime

public_bp = Blueprint('public', __name__)

@public_bp.route('/prescription/view/<uuid>')
def view_prescription(uuid):
    # Find prescription by UUID
    prescription = Prescription.query.filter_by(uuid=uuid).first()
    if not prescription:
        abort(404)
        
    patient = Patient.query.get(prescription.patient_id)
    doctor = Doctor.query.get(prescription.doctor_id)
    
    # If the user is logged in and scans the QR code directly or visits the URL
    # they should ideally go through /process_scan, but if they land here directly
    # and they are a doctor or pharmacist, we can still show them the public view
    # with a banner or just rely on them using the /scan portal.
    
    return render_template('public/prescription_view.html', prescription=prescription, patient=patient, doctor=doctor)

@public_bp.route('/scan')
def scan_qr():
    return render_template('scanner.html')

@public_bp.route('/process_scan/<uuid>')
def process_scan(uuid):
    prescription = Prescription.query.filter_by(uuid=uuid).first()
    if not prescription:
        # Invalid QR
        return render_template('invalid_qr.html')
        
    # Log the scan
    pharmacist_id = None
    if current_user.is_authenticated and current_user.role == 'pharmacist':
        pharm = Pharmacist.query.filter_by(user_id=current_user.id).first()
        if pharm:
            pharmacist_id = pharm.pharmacist_id
            
    scan_log = QRScanHistory(
        prescription_id=prescription.prescription_id,
        pharmacist_id=pharmacist_id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:250],
        status='Success'
    )
    db.session.add(scan_log)
    db.session.commit()
    
    # Route based on role
    if current_user.is_authenticated:
        if current_user.role == 'doctor':
            # Redirect to doctor's detailed view
            return redirect(url_for('doctor.view_prescription', uuid=uuid))
        elif current_user.role == 'pharmacist':
            # Redirect to pharmacist dispense view
            return redirect(url_for('pharmacist.dispense', uuid=uuid))
        elif current_user.role == 'patient':
            # Redirect to public view (or patient specific view if it exists)
            return redirect(url_for('public.view_prescription', uuid=uuid))
            
    # Default to public view for guests
    return redirect(url_for('public.view_prescription', uuid=uuid))
