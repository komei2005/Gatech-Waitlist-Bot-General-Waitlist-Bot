import time
from datetime import datetime
from config import (
    TERM, CRNS, POLL_SECONDS,
    DISCORD_WEBHOOK_URL,
    EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO
)
from banner import get_status
from notify import discord, email

def alert(msg: str):
    print(msg)
    discord(DISCORD_WEBHOOK_URL, msg)
    email(
        EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO,
        subject="[GT Watcher] Seat/Waitlist Alert",
        body=msg
    )

def main():
    if not TERM or not CRNS:
        raise SystemExit("TERM and CRNS must be set in .env")

    print(f"[{datetime.now()}] Watching CRNs {CRNS} for term {TERM} (every {POLL_SECONDS}s)")
    while True:
        for crn in CRNS:
            try:
                status = get_status(crn, TERM)
                sr = status.seats_remaining
                wr = status.wait_remaining

                if sr is not None and sr > 0:
                    alert(f"🟢 OPEN SEAT — CRN {crn}: {sr} remaining\n{status.url}")
                elif wr is not None and wr > 0:
                    alert(f"🟡 OPEN WAITLIST — CRN {crn}: {wr} remaining\n{status.url}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] CRN {crn}: no seats yet")
            except Exception as e:
                print(f"CRN {crn}: error {e}")
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()

