from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """The only place that talks SQL about users."""

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.scalars(select(User).where(User.email == email)).first()

    @staticmethod
    def create(db: Session, email: str, password_hash: str, role: str) -> User:
        user = User(email=email, password_hash=password_hash, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
