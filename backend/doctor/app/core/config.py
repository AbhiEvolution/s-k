from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    # Public keys of the auth service. No shared secret any more.
    auth_jwks_url: str = "http://localhost:8003/.well-known/jwks.json"
    jwt_issuer: str = "auth-service"
    jwt_audience: str = "clinic-platform"

    # Used to verify a doctor really belongs to the clinic they claim.
    clinic_service_url: str = "http://localhost:8002"
    clinic_service_timeout_seconds: float = 3.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
