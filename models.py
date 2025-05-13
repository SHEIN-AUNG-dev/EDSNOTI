from app import db
from datetime import datetime

class ApiCredential(db.Model):
    """Model to store API credentials for EDS and Twilio"""
    id = db.Column(db.Integer, primary_key=True)
    api_type = db.Column(db.String(50), unique=True, nullable=False)  # 'eds' or 'twilio'
    api_url = db.Column(db.String(255))  # Base URL for the API
    username = db.Column(db.String(100), nullable=False)  # Username or account SID
    api_key = db.Column(db.String(255), nullable=False)  # API key or password
    api_secret = db.Column(db.String(255))  # Additional secret if needed (e.g., Twilio auth token)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ApiCredential {self.api_type}>"

class ContactNumber(db.Model):
    """Model to store contact phone numbers for SMS notifications"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ContactNumber {self.name}: {self.phone_number}>"

class AlarmEvent(db.Model):
    """Model to store alarm events from EDS API"""
    id = db.Column(db.Integer, primary_key=True)
    alarm_id = db.Column(db.String(50), nullable=False)  # Original alarm ID from EDS
    description = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(100), nullable=False)  # Source of the alarm
    event_time = db.Column(db.DateTime, nullable=False, index=True)  # Timestamp of the alarm
    severity = db.Column(db.String(20), nullable=False)  # HIGH, MEDIUM, LOW, etc.
    status = db.Column(db.String(20), nullable=False)  # ACTIVE, CLEARED, ACKNOWLEDGED, etc.
    raw_data = db.Column(db.Text)  # Raw JSON data from API
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AlarmEvent {self.alarm_id}: {self.description}>"
