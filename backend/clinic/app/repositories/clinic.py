from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.clinic import Clinic, ClinicMember

# Repositories only add/query and flush. They never commit: the service decides
# where the transaction ends, so several steps can succeed or fail together.


class ClinicRepository:
    @staticmethod
    def add(db: Session, name: str, address: str | None, phone: str | None) -> Clinic:
        clinic = Clinic(name=name, address=address, phone=phone)
        db.add(clinic)
        db.flush()  # sends the INSERT so clinic.id is available, without committing
        return clinic

    @staticmethod
    def get(db: Session, clinic_id: int) -> Clinic | None:
        return db.get(Clinic, clinic_id)

    @staticmethod
    def list_for_user(db: Session, user_id: int) -> list[Clinic]:
        # Tenancy in one query: only clinics this user is a member of.
        stmt = (
            select(Clinic)
            .join(ClinicMember, ClinicMember.clinic_id == Clinic.id)
            .where(ClinicMember.user_id == user_id)
            .order_by(Clinic.id)
        )
        return list(db.scalars(stmt))


class MemberRepository:
    @staticmethod
    def get(db: Session, clinic_id: int, user_id: int) -> ClinicMember | None:
        stmt = select(ClinicMember).where(
            ClinicMember.clinic_id == clinic_id, ClinicMember.user_id == user_id
        )
        return db.scalars(stmt).first()

    @staticmethod
    def list_for_clinic(db: Session, clinic_id: int) -> list[ClinicMember]:
        stmt = select(ClinicMember).where(ClinicMember.clinic_id == clinic_id)
        return list(db.scalars(stmt.order_by(ClinicMember.id)))

    @staticmethod
    def add(db: Session, clinic_id: int, user_id: int, role: str) -> ClinicMember:
        member = ClinicMember(clinic_id=clinic_id, user_id=user_id, role=role)
        db.add(member)
        db.flush()
        return member

    @staticmethod
    def count_admins(db: Session, clinic_id: int) -> int:
        stmt = select(func.count()).select_from(ClinicMember).where(
            ClinicMember.clinic_id == clinic_id, ClinicMember.role == "clinic_admin"
        )
        return db.scalar(stmt) or 0

    @staticmethod
    def delete(db: Session, member: ClinicMember) -> None:
        db.delete(member)
        db.flush()
