from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    # Path to the RSA private key (PEM). Only the auth service ever has this.
    jwt_private_key_path: str = "keys/private.pem"
    # Stamped into every token. Verifiers check both, so a token minted for
    # another system (or by another issuer) is rejected.
    jwt_issuer: str = "auth-service"
    jwt_audience: str = "clinic-platform"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
