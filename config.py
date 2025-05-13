import os

# Application configuration
class Config:
    # Flask
    SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-secret-key")
    DEBUG = os.environ.get("DEBUG", "True") == "True"
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Scheduler settings
    SCHEDULER_API_ENABLED = True
    
    # Default alarm check interval (in seconds)
    ALARM_CHECK_INTERVAL = int(os.environ.get("ALARM_CHECK_INTERVAL", "60"))
    
    # Twilio defaults
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")
    
    # EDS API defaults
    EDS_API_URL = os.environ.get("EDS_API_URL", "")
    EDS_API_USERNAME = os.environ.get("EDS_API_USERNAME", "")
    EDS_API_PASSWORD = os.environ.get("EDS_API_PASSWORD", "")
