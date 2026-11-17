from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.clinic import Clinic, ClinicMember
from app.repositories.clinic import ClinicRepository, MemberRepository
from app.schemas.clinic import ClinicCreate, MemberCreate


class AlreadyMemberError(Exception):
    pass


class MemberNotFoundError(Exception):
    pass


class LastAdminError(Exception):
    pass


class ClinicService:
    @staticmethod
    def create_clinic(db: Session, creator_id: int, data: ClinicCreate) -> Clinic:
        # Two inserts, one transaction: either the clinic AND its first admin
        # exist, or neither does. A clinic nobody can manage must never exist.
        try:
            clinic = ClinicRepository.add(db, data.name, data.address, data.phone)
            MemberRepository.add(db, clinic.id, creator_id, "clinic_admin")
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(clinic)
        return clinic

    @staticmethod
    def update_clinic(db: Session, clinic: Clinic, data: ClinicCreate) -> Clinic:
        clinic.name = data.name
        clinic.address = data.address
        clinic.phone = data.phone
        db.commit()
        db.refresh(clinic)
        return clinic

    @staticmethod
    def add_member(db: Session, clinic_id: int, data: MemberCreate) -> ClinicMember:
        # Note: we cannot check that user_id exists; users live in the auth
        # service's database. Later this is solved with events (UserRegistered).
        try:
            member = MemberRepository.add(db, clinic_id, data.user_id, data.role)
            db.commit()
        except IntegrityError:
            db.rollback()  # unique (clinic_id, user_id) was violated
            raise AlreadyMemberError()
        return member

    @staticmethod
    def remove_member(db: Session, clinic_id: int, user_id: int) -> None:
        member = MemberRepository.get(db, clinic_id, user_id)
        if member is None:
            raise MemberNotFoundError()

        if member.role == "clinic_admin" and MemberRepository.count_admins(db, clinic_id) <= 1:
            raise LastAdminError()  # would leave the clinic with no admin

        MemberRepository.delete(db, member)
        db.commit()
