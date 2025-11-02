import json
import smtplib
import requests
from email.mime.text import MIMEText

def discord(webhook_url: str, message: str):
    if not webhook_url:
        return
    try:
        requests.post(webhook_url, json={"content": message}, timeout=10)
    except Exception as e:
        print(f"[notify] Discord error: {e}")

def email(host, port, username, password, to_addr, subject, body):
    if not (host and port and username and password and to_addr):
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = username
        msg["To"] = to_addr

        with smtplib.SMTP(host, int(port)) as s:
            s.starttls()
            s.login(username, password)
            s.sendmail(username, [to_addr], msg.as_string())
    except Exception as e:
        print(f"[notify] Email error: {e}")

