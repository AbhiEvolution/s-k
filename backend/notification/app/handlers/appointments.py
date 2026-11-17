"""Turns an appointment event into an email (or decides there is nothing to send)."""
from datetime import datetime

from pydantic import BaseModel, EmailStr


class AppointmentData(BaseModel):
    """The part of the event we rely on. Extra fields are ignored, so the
    publisher can add fields without breaking us (a compatible change)."""

    appointment_id: int
    clinic_id: int
    doctor_name: str | None = None
    patient_name: str | None = None
    patient_email: EmailStr | None = None
    starts_at: datetime
    reason: str | None = None


def _when(value: datetime) -> str:
    return value.strftime("%A %d %B %Y at %H:%M UTC")


def render(event_type: str, data: AppointmentData) -> tuple[str, str] | None:
    """Return (subject, body), or None if this event type sends nothing."""
    name = data.patient_name or "there"
    doctor = f"Dr. {data.doctor_name.removeprefix('Dr. ')}" if data.doctor_name else "your doctor"
    reason = f"\nReason: {data.reason}" if data.reason else ""

    if event_type == "appointment.booked":
        return (
            "Your appointment is confirmed",
            f"Hello {name},\n\nYour appointment with {doctor} is confirmed for "
            f"{_when(data.starts_at)}.{reason}\n\nIf you cannot attend, please contact the clinic.",
        )
    if event_type == "appointment.cancelled":
        return (
            "Your appointment was cancelled",
            f"Hello {name},\n\nYour appointment with {doctor} on {_when(data.starts_at)} "
            f"has been cancelled.{reason}\n\nPlease contact the clinic to book another time.",
        )
    return None
