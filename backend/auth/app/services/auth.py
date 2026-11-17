from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import DUMMY_HASH, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    """Business rules. Knows nothing about HTTP."""

    @staticmethod
    def register(db: Session, email: str, password: str, role: str) -> User:
        if UserRepository.get_by_email(db, email):
            raise EmailAlreadyRegisteredError()

        try:
            return UserRepository.create(
                db, email=email, password_hash=hash_password(password), role=role
            )
        except IntegrityError:
            # Two requests passed the check above at the same time; the
            # unique index rejected the second one.
            db.rollback()
            raise EmailAlreadyRegisteredError()

    @staticmethod
    def login(db: Session, email: str, password: str) -> User:
        user = UserRepository.get_by_email(db, email)

        # Always run one bcrypt check, even for unknown emails, so response
        # time does not reveal which emails are registered.
        hashed = user.password_hash if user else DUMMY_HASH
        password_ok = verify_password(password, hashed)

        if user is None or not password_ok or not user.is_active:
            # Same error for every failure: do not say which part was wrong.
            raise InvalidCredentialsError()

        return user
