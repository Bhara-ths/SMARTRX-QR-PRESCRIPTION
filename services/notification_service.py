from extensions import mail
from flask_mail import Message
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import logging

scheduler = BackgroundScheduler()

class NotificationService:
    @staticmethod
    def send_email(to_email, subject, body):
        try:
            msg = Message(subject=subject, recipients=[to_email])
            msg.body = body
            # msg.html = ... (can add HTML version here)
            mail.send(msg)
            return True
        except Exception as e:
            logging.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    @staticmethod
    def check_appointments():
        """
        Job to check for upcoming appointments (e.g., 24 hrs and 2 hrs before)
        and send email reminders.
        """
        from app import create_app
        app = create_app()
        with app.app_context():
            from models import Appointment, User
            now = datetime.datetime.utcnow()
            
            # Example logic: find appointments in exactly 24 hours
            # In a real app, you'd want a more robust range query and a flag to mark 'reminder_sent'
            target_time = now + datetime.timedelta(hours=24)
            # appointments = Appointment.query.filter(...)
            
            # For demonstration, we just log it
            logging.info(f"Checked appointments at {now}")

    @staticmethod
    def check_medication_reminders():
        """
        Job to check for medication timings and notify patients.
        """
        logging.info("Checking medication reminders...")

# Initialize jobs
def init_scheduler():
    if not scheduler.running:
        scheduler.add_job(func=NotificationService.check_appointments, trigger="interval", minutes=60)
        scheduler.add_job(func=NotificationService.check_medication_reminders, trigger="interval", minutes=15)
        scheduler.start()
