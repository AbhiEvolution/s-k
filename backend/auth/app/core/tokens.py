import base64
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from app.core.config import get_settings

ALGORITHM = "RS256"


@lru_cache
def load_private_key() -> RSAPrivateKey:
    """Read the signing key once. Called at startup so a missing key fails fast."""
    pem = Path(get_settings().jwt_private_key_path).read_bytes()
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, RSAPrivateKey):
        raise RuntimeError("JWT private key must be an RSA key")
    return key


@lru_cache
def key_id() -> str:
    """Short fingerprint of the public key, sent as the token's `kid` header.

    Verifiers use it to pick the right key from the JWKS. When you rotate keys
    later, old and new tokens carry different kids and both stay verifiable.
    """
    der = load_private_key().public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    digest = hashlib.sha256(der).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()[:16]


def create_access_token(user_id: int, role: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),  # who the token is about
        "role": role,  # account role: admin | doctor | patient
        "type": "access",  # so other token kinds can never pass as access tokens
        "iss": settings.jwt_issuer,  # who issued it
        "aud": settings.jwt_audience,  # who it is meant for
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": str(uuid.uuid4()),  # unique id, needed later for revocation
    }
    return jwt.encode(
        payload, load_private_key(), algorithm=ALGORITHM, headers={"kid": key_id()}
    )


def build_jwks() -> dict:
    """The PUBLIC key in JWK format. Other services download this to verify tokens."""
    public_key = load_private_key().public_key()
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(public_key, as_dict=True)
    jwk.update({"kid": key_id(), "use": "sig", "alg": ALGORITHM})
    return {"keys": [jwk]}
