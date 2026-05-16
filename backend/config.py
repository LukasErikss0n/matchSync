from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]
API_KEY: str = os.getenv("API_KEY", "")
BASE_WEBCAL_URL: str = os.getenv("BASE_WEBCAL_URL", "webcal://matchsync.vinlaro.com/api/calendar")

RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")
