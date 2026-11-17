from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # Must match the exchange the appointment service publishes to.
    events_exchange: str = "clinic.events"
    queue_name: str = "notification.appointments"
    binding_key: str = "appointment.*"

    prefetch: int = 10          # messages handed to this worker at once
    max_attempts: int = 3       # total tries before a message goes to the dead-letter queue
    retry_delay_ms: int = 10_000

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_security: Literal["none", "starttls", "ssl"] = "none"
    smtp_from: str = "clinic@example.com"
    smtp_username: str | None = None
    smtp_password: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def retry_queue(self) -> str:
        return f"{self.queue_name}.retry"

    @property
    def dead_letter_queue(self) -> str:
        return f"{self.queue_name}.dlq"


@lru_cache
def get_settings() -> Settings:
    return Settings()
