from extensions import db
from models import Notification, MedicineReminder, AppointmentReminder, RefillReminder
from datetime import datetime, timedelta

class ReminderService:
    @staticmethod
    def generate_medicine_reminders(prescription):
        """Generate daily reminders for a new prescription"""
        try:
            for med in prescription.medicines:
                # Estimate duration if string, defaulting to 7 days if not parseable
                duration_days = 7 
                if med.duration:
                    try:
                        duration_days = int(''.join(filter(str.isdigit, med.duration)))
                    except:
                        duration_days = 7

                start_date = datetime.now().date()
                
                # Create reminders for each day
                for i in range(duration_days):
                    current_date = start_date + timedelta(days=i)
                    freq = (med.frequency or '').lower()
                    
                    times_of_day = []
                    
                    if 'morning' in freq or 'od' in freq or 'bid' in freq or 'tid' in freq or 'qid' in freq or '1-0-0' in freq or '1-0-1' in freq or '1-1-1' in freq:
                        times_of_day.append('Morning')
                    if 'afternoon' in freq or 'tid' in freq or 'qid' in freq or '0-1-0' in freq or '1-1-1' in freq:
                        times_of_day.append('Afternoon')
                    if 'evening' in freq or 'qid' in freq:
                        times_of_day.append('Evening')
                    if 'night' in freq or 'bid' in freq or 'tid' in freq or 'qid' in freq or '0-0-1' in freq or '1-0-1' in freq or '1-1-1' in freq:
                        times_of_day.append('Night')
                        
                    for tod in times_of_day:
                        reminder = MedicineReminder(
                            patient_id=prescription.patient_id,
                            prescription_medicine_id=med.id,
                            date=current_date,
                            time_of_day=tod,
                            status='Pending'
                        )
                        db.session.add(reminder)
                
                # Generate Refill Reminder if duration is > 3 days (remind 2 days before)
                if duration_days > 3:
                    refill_date = start_date + timedelta(days=duration_days - 2)
                    refill = RefillReminder(
                        patient_id=prescription.patient_id,
                        prescription_medicine_id=med.id,
                        estimated_refill_date=refill_date,
                        is_sent=False
                    )
                    db.session.add(refill)

            # Send a notification to the patient if they have an account
            if prescription.patient.user_id:
                notif = Notification(
                    user_id=prescription.patient.user_id,
                    category='Prescription',
                    message=f'New prescription issued by {prescription.doctor.full_name}. Reminders have been set up.'
                )
                db.session.add(notif)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error generating reminders: {e}")
            return False

    @staticmethod
    def create_appointment_reminder(appointment):
        """Create appointment reminders"""
        try:
            reminder_time = datetime.combine(appointment.appointment_date, appointment.appointment_time) - timedelta(hours=24)
            reminder = AppointmentReminder(
                patient_id=appointment.patient_id,
                appointment_id=appointment.appointment_id,
                reminder_time=reminder_time,
                is_sent=False
            )
            db.session.add(reminder)
            
            if appointment.patient.user_id:
                notif = Notification(
                    user_id=appointment.patient.user_id,
                    category='Appointment',
                    message=f'Appointment scheduled with {appointment.doctor.full_name} on {appointment.appointment_date}.'
                )
                db.session.add(notif)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error creating appointment reminder: {e}")
