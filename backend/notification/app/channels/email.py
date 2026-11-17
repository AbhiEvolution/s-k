"""The email channel: the only place that knows about SMTP.

Later channels (SMS, push) would sit next to this file with the same shape:
send(recipient, subject, body). Handlers never import smtplib directly.
"""
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import Settings, get_settings


def build_message(sender: str, recipient: str, subject: str, body: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    # Newlines in a header would let input smuggle extra headers; keep it one line.
    message["Subject"] = " ".join(subject.split())
    message.set_content(body)
    return message


def send_email(recipient: str, subject: str, body: str, settings: Settings | None = None) -> None:
    """Send one email. Raises on any failure, so the caller can retry."""
    settings = settings or get_settings()
    message = build_message(settings.smtp_from, recipient, subject, body)

    if settings.smtp_security == "ssl":
        server = smtplib.SMTP_SSL(
            settings.smtp_host, settings.smtp_port, context=ssl.create_default_context(), timeout=10
        )
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)

    with server:
        if settings.smtp_security == "starttls":
            server.starttls(context=ssl.create_default_context())
        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)
