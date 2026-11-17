"""Business logic for one message. No RabbitMQ in here, so it is easy to test.

Contract with the consumer:
  - returns an outcome string  -> the message is done (acknowledge it)
  - raises PoisonMessageError  -> it can NEVER succeed (dead-letter it, no retries)
  - raises anything else       -> it MIGHT succeed later (retry with a delay)
"""
import logging
from typing import Callable

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.handlers.appointments import AppointmentData, render
from app.models.notification import NotificationLog

logger = logging.getLogger("processor")

SENT = "sent"
DUPLICATE = "duplicate"
SKIPPED = "skipped_no_recipient"
IGNORED = "ignored"


class PoisonMessageError(Exception):
    """The message is malformed. Retrying will never help."""


class Envelope(BaseModel):
    event_id: str
    type: str
    version: int = 1
    data: dict


def process_message(db: Session, body: bytes, send: Callable[[str, str, str], None]) -> str:
    try:
        envelope = Envelope.model_validate_json(body)
    except ValidationError as exc:
        raise PoisonMessageError(f"not a valid event envelope: {exc.error_count()} error(s)") from exc

    if not envelope.type.startswith("appointment."):
        return IGNORED  # a type we do not know about is not an error: stay forward-compatible

    # Idempotency: have we already handled this exact event?
    if db.scalars(select(NotificationLog.id).where(NotificationLog.event_id == envelope.event_id)).first():
        return DUPLICATE

    try:
        data = AppointmentData.model_validate(envelope.data)
    except ValidationError as exc:
        raise PoisonMessageError(f"invalid {envelope.type} payload: {exc.error_count()} error(s)") from exc

    rendered = render(envelope.type, data)
    if rendered is None:
        return IGNORED

    if not data.patient_email:
        # Nobody to tell. Record it so a redelivery does not repeat the work.
        return _record(db, envelope, None, None, SKIPPED)

    subject, text = rendered
    send(str(data.patient_email), subject, text)  # may raise: the consumer will retry
    # If we crash right here, before the commit below, the retry sends again.
    # Email cannot be made exactly-once; this is the smallest possible window.
    return _record(db, envelope, str(data.patient_email), subject, SENT)


def _record(db: Session, envelope: Envelope, recipient: str | None, subject: str | None, status: str) -> str:
    db.add(NotificationLog(
        event_id=envelope.event_id, event_type=envelope.type,
        recipient=recipient, subject=subject, status=status,
    ))
    try:
        db.commit()
    except IntegrityError:
        # Two workers handled the same event at once; the unique index picked one.
        db.rollback()
        return DUPLICATE
    return status
