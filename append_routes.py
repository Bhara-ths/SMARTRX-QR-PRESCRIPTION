import os

file_path = r"c:\Users\GUNAVARDHAN\Desktop\qr_prescription_system\routes\doctor.py"

routes_code = """
@doctor_bp.route('/prescriptions', methods=['GET'])
@login_required
@role_required('Doctor')
def prescriptions_list():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    # Filter functionality
    query = Prescription.query.filter_by(doctor_id=doctor.doctor_id)
    
    patient_query = request.args.get('patient')
    status = request.args.get('status')
    date = request.args.get('date')
    
    if patient_query:
        query = query.join(Patient).filter((Patient.first_name.ilike(f'%{patient_query}%')) | (Patient.last_name.ilike(f'%{patient_query}%')) | (Patient.patient_uid.ilike(f'%{patient_query}%')))
    if status:
        query = query.filter(Prescription.status == status)
    if date:
        query = query.filter(db.func.date(Prescription.created_at) == date)
        
    prescriptions = query.order_by(Prescription.created_at.desc()).all()
    
    return render_template('doctor/prescriptions_list.html', prescriptions=prescriptions)

@doctor_bp.route('/prescription/edit/<uuid>', methods=['GET', 'POST'])
@login_required
@role_required('Doctor')
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
@role_required('Doctor')
def delete_prescription(uuid):
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    prescription = Prescription.query.filter_by(uuid=uuid, doctor_id=doctor.doctor_id).first_or_404()
    
    db.session.delete(prescription)
    db.session.commit()
    flash('Prescription deleted successfully!', 'success')
    return redirect(url_for('doctor.prescriptions_list'))

"""

with open(file_path, "a", encoding="utf-8") as f:
    f.write(routes_code)

print("Routes appended to doctor.py")
