from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    # Where to download the auth service's PUBLIC keys. No secret is shared.
    auth_jwks_url: str = "http://localhost:8003/.well-known/jwks.json"
    # Must match what the auth service stamps into tokens.
    jwt_issuer: str = "auth-service"
    jwt_audience: str = "clinic-platform"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
