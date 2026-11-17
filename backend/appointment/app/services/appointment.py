from datetime import date, datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.clients import (
    NotClinicMemberError,
    fetch_doctor,
    fetch_my_doctor,
    fetch_patient,
    verify_membership,
)
from app.core.exceptions import (
    AppointmentNotFoundError,
    ConflictError,
    InvalidRequestError,
    NotFoundError,
    SlotUnavailableError,
)
from app.models.appointment import BOOKED, CANCELLED, Appointment
from app.repositories.appointment import (
    AppointmentRepository,
    AvailabilityRepository,
    OutboxRepository,
)
from app.schemas.appointment import AppointmentCreate, AvailabilityUpdate
from app.services import events, slots


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AvailabilityService:
    @staticmethod
    def replace_my_availability(db: Session, token: str, data: AvailabilityUpdate) -> dict:
        doctor = fetch_my_doctor(token)
        if doctor is None:
            raise ConflictError("Create your doctor profile before setting availability")
        if not doctor.get("clinic_id"):
            raise ConflictError("Link your doctor profile to a clinic before setting availability")

        # Existing appointments are never touched, even if they fall outside the new hours.
        AvailabilityRepository.replace(db, doctor["id"], doctor["clinic_id"], data.windows)
        db.commit()
        return {"doctor_id": doctor["id"], "windows": data.windows}

    @staticmethod
    def _doctor_in_my_clinic(user: CurrentUser, token: str, doctor_id: int) -> dict:
        doctor = fetch_doctor(doctor_id, token)
        if doctor is None or not doctor.get("clinic_id"):
            raise NotFoundError("Doctor not found")
        verify_membership(doctor["clinic_id"], user.id, token)  # outsiders -> 403
        return doctor

    @staticmethod
    def get_availability(db: Session, user: CurrentUser, token: str, doctor_id: int) -> dict:
        AvailabilityService._doctor_in_my_clinic(user, token, doctor_id)
        return {"doctor_id": doctor_id, "windows": AvailabilityRepository.for_doctor(db, doctor_id)}

    @staticmethod
    def get_slots(db: Session, user: CurrentUser, token: str, doctor_id: int, day: date) -> list[dict]:
        AvailabilityService._doctor_in_my_clinic(user, token, doctor_id)

        windows = AvailabilityRepository.for_doctor(db, doctor_id)
        starts = slots.generate_slots(day, windows)
        if not starts:
            return []

        taken = {
            slots.as_utc(value)
            for value in AppointmentRepository.booked_starts(db, doctor_id, starts[0], starts[-1] + timedelta(seconds=1))
        }
        now = _now()
        length = slots.slot_length()
        return [
            {"starts_at": start, "ends_at": start + length, "available": start > now and start not in taken}
            for start in starts
        ]


class AppointmentService:
    @staticmethod
    def book(
        db: Session, user: CurrentUser, token: str, data: AppointmentCreate, idempotency_key: str | None
    ) -> tuple[Appointment, bool]:
        """Returns (appointment, created). created=False means an idempotent replay."""
        verify_membership(data.clinic_id, user.id, token)

        if idempotency_key:
            replay = AppointmentRepository.get_by_idempotency_key(db, user.id, idempotency_key)
            if replay is not None:
                return replay, False

        doctor = fetch_doctor(data.doctor_id, token)
        if doctor is None:
            raise NotFoundError("Doctor not found")
        if doctor.get("clinic_id") != data.clinic_id:
            raise InvalidRequestError("That doctor does not work at this clinic")

        patient = fetch_patient(data.patient_id, token)
        if patient is None:
            raise NotFoundError("Patient not found")
        if patient.get("clinic_id") != data.clinic_id:
            raise InvalidRequestError("That patient does not belong to this clinic")

        start = slots.normalize_start(data.starts_at)
        if start <= _now():
            raise InvalidRequestError("Appointments cannot be booked in the past")

        windows = AvailabilityRepository.for_doctor(db, data.doctor_id)
        if not slots.fits_in_a_window(start, windows):
            raise InvalidRequestError("The doctor is not available at that time")

        try:
            appointment = AppointmentRepository.add(
                db,
                clinic_id=data.clinic_id, doctor_id=data.doctor_id, patient_id=data.patient_id,
                starts_at=start, ends_at=start + slots.slot_length(),
                status=BOOKED, reason=data.reason,
                patient_name=patient.get("name"), patient_email=patient.get("email"),
                doctor_name=doctor.get("full_name"),
                created_by_user_id=user.id, idempotency_key=idempotency_key,
            )
            # Same transaction as the appointment: both are saved, or neither is.
            OutboxRepository.add(db, events.appointment_event(events.BOOKED, appointment))
            db.commit()
        except IntegrityError:
            # The database refused: a unique index fired. Work out which one.
            db.rollback()
            if idempotency_key:  # the same request raced with itself
                replay = AppointmentRepository.get_by_idempotency_key(db, user.id, idempotency_key)
                if replay is not None:
                    return replay, False
            if AppointmentRepository.booked_for_doctor_at(db, data.doctor_id, start) is not None:
                raise SlotUnavailableError("That time slot has just been booked by someone else")
            raise SlotUnavailableError("The patient already has an appointment at that time")

        db.refresh(appointment)
        return appointment, True

    @staticmethod
    def _load_visible(db: Session, user: CurrentUser, token: str, appointment_id: int) -> Appointment:
        """Fetch an appointment only if the caller belongs to its clinic."""
        appointment = AppointmentRepository.get(db, appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError()
        try:
            verify_membership(appointment.clinic_id, user.id, token)
        except NotClinicMemberError:
            # Outsiders get the same answer as for a missing id.
            raise AppointmentNotFoundError()
        return appointment

    @staticmethod
    def get(db: Session, user: CurrentUser, token: str, appointment_id: int) -> Appointment:
        return AppointmentService._load_visible(db, user, token, appointment_id)

    @staticmethod
    def cancel(db: Session, user: CurrentUser, token: str, appointment_id: int) -> Appointment:
        appointment = AppointmentService._load_visible(db, user, token, appointment_id)
        if appointment.status == CANCELLED:  # idempotent: cancelling twice is fine
            return appointment

        appointment.status = CANCELLED
        appointment.cancelled_at = _now()
        appointment.cancelled_by_user_id = user.id
        OutboxRepository.add(db, events.appointment_event(events.CANCELLED, appointment))
        db.commit()  # the slot is bookable again: the partial unique index ignores cancelled rows
        db.refresh(appointment)
        return appointment

    @staticmethod
    def list(
        db: Session, user: CurrentUser, token: str, clinic_id: int, doctor_id: int | None,
        patient_id: int | None, start_from: datetime | None, start_to: datetime | None,
        status: str | None, skip: int, limit: int,
    ) -> list[Appointment]:
        verify_membership(clinic_id, user.id, token)
        return AppointmentRepository.search(
            db, clinic_id, doctor_id, patient_id,
            slots.as_utc(start_from) if start_from else None,
            slots.as_utc(start_to) if start_to else None,
            status, skip, limit,
        )
