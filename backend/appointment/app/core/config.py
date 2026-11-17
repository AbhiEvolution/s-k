from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    auth_jwks_url: str = "http://localhost:8003/.well-known/jwks.json"
    jwt_issuer: str = "auth-service"
    jwt_audience: str = "clinic-platform"

    clinic_service_url: str = "http://localhost:8002"
    doctor_service_url: str = "http://localhost:8000"
    patient_service_url: str = "http://localhost:8001"
    service_timeout_seconds: float = 3.0

    # Message broker. The relay publishes outbox events here.
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    events_exchange: str = "clinic.events"
    relay_poll_seconds: float = 1.0
    relay_batch_size: int = 50

    # Appointments sit on a fixed grid (e.g. 09:00, 09:30, 10:00...).
    slot_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
