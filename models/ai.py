from extensions import db
from datetime import datetime

class AIChatHistory(db.Model):
    __tablename__ = 'ai_chat_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('chat_history', lazy=True, cascade="all, delete-orphan"))
