import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]
API_KEY: str = os.getenv("API_KEY", "")
ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "")
BASE_WEBCAL_URL: str = os.getenv(
    "BASE_WEBCAL_URL", "webcal://matchcalender.com/api/calendar"
)

RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")
SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@matchcalender.com")
