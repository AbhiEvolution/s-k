import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite://"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.auth as core_auth
import app.models  # noqa: F401
from app.main import app
from db.database import Base, get_db

# Stand-in for the auth service's key pair. The clinic service only ever
# receives the public half, exactly like production.
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def make_token(
    user_id: int,
    role: str = "doctor",
    *,
    key=PRIVATE_KEY,
    audience: str = "clinic-platform",
    issuer: str = "auth-service",
    token_type: str = "access",
    expires_in: timedelta = timedelta(minutes=15),
) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "role": role,
            "type": token_type,
            "iss": issuer,
            "aud": audience,
            "iat": now,
            "exp": now + expires_in,
        },
        key,
        algorithm="RS256",
    )


def as_user(user_id: int, role: str = "doctor") -> dict:
    return {"Authorization": f"Bearer {make_token(user_id, role)}"}


@pytest.fixture(autouse=True)
def fake_jwks(monkeypatch):
    # Skip the HTTP download of the JWKS; hand back the matching public key.
    monkeypatch.setattr(
        core_auth, "get_signing_key", lambda token: PRIVATE_KEY.public_key()
    )


@pytest.fixture
def session_factory():
    """A fresh in-memory database per test; tests may open sessions to inspect it."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
