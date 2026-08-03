import os
import sys

# Add the parent directory to sys.path so we can import the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.ai import AIChatHistory

app = create_app()

def migrate():
    with app.app_context():
        # Create the new table
        print("Creating new table: ai_chat_history...")
        AIChatHistory.__table__.create(db.engine, checkfirst=True)
        print("Table created successfully.")

if __name__ == '__main__':
    migrate()
