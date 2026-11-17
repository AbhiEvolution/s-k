"""Event contracts published by this service.

An event is a FACT that already happened ("appointment.booked"), named in the
past tense. Consumers must not need to call back for more data, so each event
carries a snapshot of everything a typical consumer needs.
"""
import uuid
from datetime import datetime, timezone

from app.models.appointment import Appointment
from app.services.slots import as_utc

BOOKED = "appointment.booked"
CANCELLED = "appointment.cancelled"


def appointment_event(event_type: str, appointment: Appointment) -> dict:
    return {
        "event_id": str(uuid.uuid4()),  # lets consumers ignore duplicates
        "type": event_type,
        "version": 1,  # bump when the shape changes incompatibly
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "data": {
            "appointment_id": appointment.id,
            "clinic_id": appointment.clinic_id,
            "doctor_id": appointment.doctor_id,
            "doctor_name": appointment.doctor_name,
            "patient_id": appointment.patient_id,
            "patient_name": appointment.patient_name,
            "patient_email": appointment.patient_email,
            "starts_at": as_utc(appointment.starts_at).isoformat(),
            "ends_at": as_utc(appointment.ends_at).isoformat(),
            "reason": appointment.reason,
        },
    }
