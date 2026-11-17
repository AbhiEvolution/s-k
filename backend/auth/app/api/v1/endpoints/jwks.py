from fastapi import APIRouter

from app.core.tokens import build_jwks

router = APIRouter(tags=["jwks"])


@router.get("/.well-known/jwks.json")
def jwks():
    """Public keys for verifying tokens. Safe to expose: it is only the public half."""
    return build_jwks()
