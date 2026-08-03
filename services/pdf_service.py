import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from flask import current_app

def generate_prescription_pdf(rx):
    """
    Generates a professional Hospital Prescription PDF using ReportLab Platypus.
    Returns a BytesIO buffer containing the PDF data.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=150, bottomMargin=100
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#ffffff'),
        backColor=colors.HexColor('#0d6efd'),
        spaceBefore=10,
        spaceAfter=10,
        leftIndent=5,
        rightIndent=5
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    
    bold_style = ParagraphStyle(
        'BoldStyle',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold'
    )
    
    elements = []
    
    # --- Doctor & Patient Info (Dual Column Layout via Table) ---
    doctor_info = [
        Paragraph(f"<b>Dr. {rx.doctor.full_name}</b>", bold_style),
        Paragraph(f"{rx.doctor.specialization}", normal_style),
        Paragraph(f"Reg No: {rx.doctor.registration_number}", normal_style),
        Paragraph(f"Phone: {rx.doctor.phone}", normal_style)
    ]
    
    patient_info = [
        Paragraph(f"<b>Patient Name:</b> {rx.patient.full_name}", normal_style),
        Paragraph(f"<b>Patient ID:</b> {rx.patient.patient_uid}", normal_style),
        Paragraph(f"<b>Age/Gender:</b> {rx.patient.age} / {rx.patient.gender}", normal_style),
        Paragraph(f"<b>Blood Group:</b> {rx.patient.blood_group or 'N/A'}", normal_style),
        Paragraph(f"<b>Phone:</b> {rx.patient.phone}", normal_style)
    ]
    
    info_table_data = [[doctor_info, patient_info]]
    info_table = Table(info_table_data, colWidths=[3*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0)
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 15))
    
    # --- Clinical Section ---
    elements.append(Paragraph("Clinical Details", section_header_style))
    
    clinical_data = [
        [Paragraph("<b>Diagnosis:</b>", bold_style), Paragraph(rx.diagnosis or 'Not Specified', normal_style)],
        [Paragraph("<b>Symptoms:</b>", bold_style), Paragraph(rx.symptoms or 'Not Specified', normal_style)],
        [Paragraph("<b>Clinical Notes:</b>", bold_style), Paragraph(rx.clinical_notes or 'None', normal_style)],
    ]
    
    if rx.blood_pressure or rx.temperature:
        vitals = f"BP: {rx.blood_pressure or '-'} | Temp: {rx.temperature or '-'} | Pulse: {rx.pulse or '-'} | SpO2: {rx.oxygen_saturation or '-'}%"
        clinical_data.append([Paragraph("<b>Vitals:</b>", bold_style), Paragraph(vitals, normal_style)])
        
    clinical_table = Table(clinical_data, colWidths=[1.5*inch, 4.5*inch])
    clinical_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8)
    ]))
    
    elements.append(clinical_table)
    elements.append(Spacer(1, 15))
    
    # --- Medicines Table ---
    elements.append(Paragraph("Prescribed Medicines", section_header_style))
    
    med_table_data = [["Medicine", "Strength", "Dosage", "Frequency", "Duration", "Instructions"]]
    
    for rx_med in rx.medicines:
        med_table_data.append([
            Paragraph(rx_med.medicine.medicine_name, normal_style),
            Paragraph(rx_med.strength or '-', normal_style),
            Paragraph(rx_med.dosage or '-', normal_style),
            Paragraph(rx_med.frequency or '-', normal_style),
            Paragraph(rx_med.duration or '-', normal_style),
            Paragraph(rx_med.instructions or '-', normal_style)
        ])
        
    if len(med_table_data) == 1:
        med_table_data.append(["No medicines prescribed", "", "", "", "", ""])
        
    med_table = Table(med_table_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch, 1.3*inch])
    med_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    elements.append(med_table)
    elements.append(Spacer(1, 15))
    
    # --- Follow Up ---
    if rx.follow_up_date:
        elements.append(Paragraph(f"<b>Follow-up Date:</b> {rx.follow_up_date.strftime('%B %d, %Y')}", normal_style))
        elements.append(Spacer(1, 20))
        
    # --- Footer Signatures ---
    # We will use onFirstPage and onLaterPages to draw fixed headers and footers
    
    def header_footer(canvas, doc):
        canvas.saveState()
        
        # Get hospital info
        hospital = rx.doctor.hospital_rel
        h_name = hospital.name if hospital else "SmartRx Multispeciality Hospital"
        h_addr = f"{hospital.address}, {hospital.city}" if hospital else "123 Health Avenue, Medical District"
        h_contact = f"Phone: {hospital.phone} | Email: {hospital.email}" if hospital else "Phone: +1 234 567 890 | Email: care@smartrx.com"
        
        # Draw Header
        header_y = A4[1] - 40
        try:
            if hospital and hospital.logo_path:
                logo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'logos', hospital.logo_path)
            else:
                logo_path = os.path.join(current_app.root_path, 'static', 'images', 'hospital_logo.png')
                
            if os.path.exists(logo_path):
                canvas.drawImage(logo_path, 40, header_y - 40, width=150, height=60, preserveAspectRatio=True)
        except Exception:
            pass
            
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(220, header_y, h_name)
        canvas.setFont("Helvetica", 10)
        canvas.drawString(220, header_y - 15, h_addr)
        canvas.drawString(220, header_y - 30, h_contact)
        
        canvas.line(40, header_y - 50, A4[0] - 40, header_y - 50)
        
        # Draw Footer
        footer_y = 90
        canvas.line(40, footer_y, A4[0] - 40, footer_y)
        
        # QR Code - note that we don't have qr_code_path in Prescription model, it generates dynamically
        # I will check if the file exists by uuid
        qr_path = os.path.join(current_app.root_path, 'static', 'qrcodes', f"{rx.uuid}.png")
        if os.path.exists(qr_path):
            canvas.drawImage(qr_path, 40, footer_y - 80, width=70, height=70)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.setFillColor(colors.HexColor('#198754'))
            canvas.drawString(40, footer_y - 10, "Authentic SmartRx QR")
            canvas.setFillColor(colors.black)
            
        # Signature
        try:
            sig_path = os.path.join(current_app.root_path, 'static', 'images', 'signature.png')
            if os.path.exists(sig_path):
                canvas.drawImage(sig_path, A4[0] - 150, footer_y - 60, width=100, height=40, preserveAspectRatio=True)
        except Exception:
            pass
            
        canvas.setFont("Helvetica", 10)
        canvas.drawString(A4[0] - 160, footer_y - 75, f"Dr. {rx.doctor.full_name}")
        
        # Meta info
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(130, footer_y - 40, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        canvas.drawString(130, footer_y - 55, "This is a digitally generated and QR verifiable prescription.")
        
        canvas.restoreState()

    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    
    buffer.seek(0)
    return buffer
