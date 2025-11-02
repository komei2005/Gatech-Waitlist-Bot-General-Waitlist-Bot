import os
from dotenv import load_dotenv

load_dotenv()

TERM = os.getenv("TERM", "").strip()
CRNS = [c.strip() for c in os.getenv("CRNS", "").split(",") if c.strip()]
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "10"))

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "").strip()
EMAIL_SMTP_PORT = os.getenv("EMAIL_SMTP_PORT", "587").strip()
EMAIL_USERNAME  = os.getenv("EMAIL_USERNAME", "").strip()
EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD", "").strip()
EMAIL_TO        = os.getenv("EMAIL_TO", "").strip()

