import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cashtrace-sih26184-secret-key-development')
    DATABASE_PATH = os.path.join(BASE_DIR, 'backend', 'database', 'cyberx.db')
    SCHEMA_PATH = os.path.join(BASE_DIR, 'backend', 'database', 'schema.sql')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'backend', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    JSON_SORT_KEYS = False

    # Google Gemini API Key (Set in environment or paste your key here)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

    SIH_ID = "SIH26184"
    TITLE = "Development of a Predictive Analytics Framework for Cybercrime Complaints to Forecast Likely Cash Withdrawal Locations in Advance"
    ORGANIZATION = "Ministry of Home Affairs (MHA)"
    DEPARTMENT = "Indian Cyber Crime Coordination Centre (I4C), CIS Division"
    PLATFORM_NAME = "CashTrace AI"
    TAGLINE = "Report Smart. Detect Patterns. Prevent Cyber Crime."