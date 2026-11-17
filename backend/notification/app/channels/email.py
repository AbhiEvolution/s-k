import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


logger = logging.getLogger(__name__)


class PasswordResetEmailError(Exception):
  pass


def _get_reset_url(token: str) -> str:
  reset_url = os.getenv("PASSWORD_RESET_URL")
  if not reset_url:
    raise PasswordResetEmailError("PASSWORD_RESET_URL is not configured")

  parsed_url = urlsplit(reset_url)
  is_local_http = parsed_url.scheme == "http" and parsed_url.hostname in {
    "localhost",
    "127.0.0.1",
  }
  if (
    (parsed_url.scheme != "https" and not is_local_http)
    or not parsed_url.hostname
    or parsed_url.username
    or parsed_url.password
    or parsed_url.fragment
  ):
    raise PasswordResetEmailError(
      "PASSWORD_RESET_URL must be an HTTPS URL (HTTP is allowed for localhost)"
    )

  query = [
    (key, value)
    for key, value in parse_qsl(parsed_url.query, keep_blank_values=True)
    if key != "token"
  ]
  query.append(("token", token))
  return urlunsplit(
    parsed_url._replace(query=urlencode(query))
  )


def send_password_reset_email(to_email: str, token: str) -> None:
  try:
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM")
    if not host or not sender:
      raise PasswordResetEmailError(
        "SMTP_HOST and SMTP_FROM must be configured"
      )

    use_ssl_setting = os.getenv("SMTP_USE_SSL", "true").lower()
    if use_ssl_setting not in {"true", "false"}:
      raise PasswordResetEmailError("SMTP_USE_SSL must be true or false")
    use_ssl = use_ssl_setting == "true"

    try:
      default_port = "465" if use_ssl else "587"
      port = int(os.getenv("SMTP_PORT", default_port))
    except ValueError as exc:
      raise PasswordResetEmailError("SMTP_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
      raise PasswordResetEmailError("SMTP_PORT must be between 1 and 65535")

    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    if bool(username) != bool(password):
      raise PasswordResetEmailError(
        "SMTP_USERNAME and SMTP_PASSWORD must be configured together"
      )

    reset_url = _get_reset_url(token)
    message = EmailMessage()
    message["Subject"] = "Reset your doctor account password"
    message["From"] = sender
    message["To"] = to_email
    message.set_content(
      "We received a request to reset your password. Use the link below "
      "within 15 minutes to choose a new password:\n\n"
      f"{reset_url}\n\n"
      "If you did not request a password reset, you can ignore this email."
    )

    context = ssl.create_default_context()
    if use_ssl:
      with smtplib.SMTP_SSL(host, port, context=context, timeout=10) as server:
        if username and password:
          server.login(username, password)
        server.send_message(message)
    else:
      with smtplib.SMTP(host, port, timeout=10) as server:
        server.starttls(context=context)
        if username and password:
          server.login(username, password)
        server.send_message(message)
  except (OSError, ValueError, smtplib.SMTPException, PasswordResetEmailError):
    logger.exception("Password reset email delivery failed")
