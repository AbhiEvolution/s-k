from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.doctor import Doctor


class DoctorRepository:
    @staticmethod
    def get_by_id(db: Session, doctor_id: int) -> Doctor | None:
        return db.get(Doctor, doctor_id)

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Doctor | None:
        return db.scalars(select(Doctor).where(Doctor.user_id == user_id)).first()

    @staticmethod
    def add(db: Session, user_id: int, fields: dict) -> Doctor:
        doctor = Doctor(user_id=user_id, **fields)
        db.add(doctor)
        db.flush()
        return doctor
