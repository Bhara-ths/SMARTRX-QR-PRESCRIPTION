import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.user import User

app = create_app()

def reset_database():
    with app.app_context():
        print("Starting data reset...")
        # Get all table names
        table_names = db.metadata.tables.keys()
        
        try:
            # Disable foreign key checks
            db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 0;'))
            
            for table_name in table_names:
                print(f"Truncating table {table_name}...")
                db.session.execute(db.text(f'TRUNCATE TABLE {table_name};'))
            
            # Re-enable foreign key checks
            db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 1;'))
            db.session.commit()
            print("All tables truncated successfully.")
            
            # Clear upload folders
            folders = [app.config.get('UPLOAD_FOLDER'), app.config.get('QR_FOLDER'), app.config.get('PDF_FOLDER')]
            for folder in folders:
                if folder and os.path.exists(folder):
                    for filename in os.listdir(folder):
                        file_path = os.path.join(folder, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                        except Exception as e:
                            print(f"Failed to delete {file_path}. Reason: {e}")
            print("Upload folders cleared.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during data reset: {e}")
            db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 1;'))

if __name__ == '__main__':
    reset_database()
