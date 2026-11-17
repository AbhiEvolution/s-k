from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.appointment import BOOKED, Appointment, Availability, OutboxEvent

# Repositories add/query and flush; the service owns commit/rollback.


class AppointmentRepository:
    @staticmethod
    def add(db: Session, **fields) -> Appointment:
        appointment = Appointment(**fields)
        db.add(appointment)
        db.flush()  # sends the INSERT now, so a unique-index violation surfaces here
        return appointment

    @staticmethod
    def get(db: Session, appointment_id: int) -> Appointment | None:
        return db.get(Appointment, appointment_id)

    @staticmethod
    def get_by_idempotency_key(db: Session, user_id: int, key: str) -> Appointment | None:
        stmt = select(Appointment).where(
            Appointment.created_by_user_id == user_id, Appointment.idempotency_key == key
        )
        return db.scalars(stmt).first()

    @staticmethod
    def booked_for_doctor_at(db: Session, doctor_id: int, starts_at: datetime) -> Appointment | None:
        stmt = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.starts_at == starts_at,
            Appointment.status == BOOKED,
        )
        return db.scalars(stmt).first()

    @staticmethod
    def booked_starts(db: Session, doctor_id: int, start: datetime, end: datetime) -> set[datetime]:
        stmt = select(Appointment.starts_at).where(
            Appointment.doctor_id == doctor_id,
            Appointment.status == BOOKED,
            Appointment.starts_at >= start,
            Appointment.starts_at < end,
        )
        return set(db.scalars(stmt))

    @staticmethod
    def search(
        db: Session, clinic_id: int, doctor_id: int | None, patient_id: int | None,
        start_from: datetime | None, start_to: datetime | None, status: str | None,
        skip: int, limit: int,
    ) -> list[Appointment]:
        stmt = select(Appointment).where(Appointment.clinic_id == clinic_id)
        if doctor_id is not None:
            stmt = stmt.where(Appointment.doctor_id == doctor_id)
        if patient_id is not None:
            stmt = stmt.where(Appointment.patient_id == patient_id)
        if start_from is not None:
            stmt = stmt.where(Appointment.starts_at >= start_from)
        if start_to is not None:
            stmt = stmt.where(Appointment.starts_at < start_to)
        if status is not None:
            stmt = stmt.where(Appointment.status == status)
        stmt = stmt.order_by(Appointment.starts_at, Appointment.id).offset(skip).limit(limit)
        return list(db.scalars(stmt))


class OutboxRepository:
    @staticmethod
    def add(db: Session, event: dict) -> OutboxEvent:
        row = OutboxEvent(event_id=event["event_id"], event_type=event["type"], payload=event)
        db.add(row)
        db.flush()
        return row

    @staticmethod
    def fetch_unpublished(db: Session, limit: int) -> list[OutboxEvent]:
        # SKIP LOCKED: if two relays run, they take different rows instead of
        # waiting for (or double-sending) each other's. SQLite ignores the hint.
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(db.scalars(stmt))


class AvailabilityRepository:
    @staticmethod
    def for_doctor(db: Session, doctor_id: int) -> list[Availability]:
        stmt = select(Availability).where(Availability.doctor_id == doctor_id)
        return list(db.scalars(stmt.order_by(Availability.weekday, Availability.start_time)))

    @staticmethod
    def replace(db: Session, doctor_id: int, clinic_id: int, windows) -> None:
        db.execute(delete(Availability).where(Availability.doctor_id == doctor_id))
        for window in windows:
            db.add(Availability(
                doctor_id=doctor_id, clinic_id=clinic_id, weekday=window.weekday,
                start_time=window.start_time, end_time=window.end_time,
            ))
        db.flush()
