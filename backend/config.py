import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
print(GROQ_API_KEY)  # Debug print to verify the API key is loaded
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
SECRET_KEY = os.getenv("SECRET_KEY", "sightflow-secret")
ABSENCE_THRESHOLD_SECONDS = int(os.getenv("ABSENCE_THRESHOLD_SECONDS", 5))
RISK_HIGH_THRESHOLD = int(os.getenv("RISK_HIGH_THRESHOLD", 60))
RISK_WARNING_THRESHOLD = int(os.getenv("RISK_WARNING_THRESHOLD", 30))