from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clinic_client import verify_membership
from app.models.doctor import Doctor
from app.repositories.doctor import DoctorRepository
from app.schemas.doctor import DoctorProfile


class ProfileAlreadyExistsError(Exception):
    pass


class ProfileNotFoundError(Exception):
    pass


class DoctorService:
    @staticmethod
    def create_profile(db: Session, user_id: int, token: str, data: DoctorProfile) -> Doctor:
        if DoctorRepository.get_by_user_id(db, user_id):
            raise ProfileAlreadyExistsError()

        # Raises NotClinicMemberError / ClinicServiceUnavailableError.
        if data.clinic_id is not None:
            verify_membership(data.clinic_id, user_id, token)

        try:
            doctor = DoctorRepository.add(db, user_id, data.model_dump())
            db.commit()
        except IntegrityError:
            # Two simultaneous requests: the unique index on user_id caught it.
            db.rollback()
            raise ProfileAlreadyExistsError()
        db.refresh(doctor)
        return doctor

    @staticmethod
    def get_my_profile(db: Session, user_id: int) -> Doctor:
        doctor = DoctorRepository.get_by_user_id(db, user_id)
        if doctor is None:
            raise ProfileNotFoundError()
        return doctor

    @staticmethod
    def update_my_profile(db: Session, user_id: int, token: str, data: DoctorProfile) -> Doctor:
        doctor = DoctorService.get_my_profile(db, user_id)

        # Only call the clinic service when the clinic actually changes.
        if data.clinic_id is not None and data.clinic_id != doctor.clinic_id:
            verify_membership(data.clinic_id, user_id, token)

        for field, value in data.model_dump().items():
            setattr(doctor, field, value)
        db.commit()
        db.refresh(doctor)
        return doctor

    @staticmethod
    def get_public(db: Session, doctor_id: int) -> Doctor:
        doctor = DoctorRepository.get_by_id(db, doctor_id)
        if doctor is None:
            raise ProfileNotFoundError()
        return doctor
