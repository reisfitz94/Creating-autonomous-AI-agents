import os
import json
from typing import Any


SlackWebhook = os.getenv("SLACK_WEBHOOK_URL")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "0"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_slack(message: str):
    """Post a message to Slack using an incoming webhook if configured.

    Falls back to printing if no webhook is set or an error occurs.
    """
    if SlackWebhook:
        try:
            import requests

            resp = requests.post(SlackWebhook, json={"text": message}, timeout=5)
            resp.raise_for_status()
        except Exception:
            print(f"[Slack-fallback] {message}")
    else:
        print(f"[Slack] {message}")


def send_email(recipient: str, subject: str, body: str):
    """Send an email via SMTP if server details are provided.

    Otherwise prints to stdout as a fallback.
    """
    if SMTP_SERVER and SMTP_PORT:
        try:
            import smtplib

            from email.message import EmailMessage

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = SMTP_USER or "no-reply@example.com"
            msg["To"] = recipient
            msg.set_content(body)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as s:
                if SMTP_USER and SMTP_PASSWORD:
                    s.login(SMTP_USER, SMTP_PASSWORD)
                s.send_message(msg)
        except Exception:
            print(f"[Email-fallback to {recipient}] {subject}: {body}")
    else:
        print(f"[Email to {recipient}] {subject}: {body}")
