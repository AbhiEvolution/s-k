"""Entry point:  python -m app.worker"""
import asyncio
import logging

from app.channels.email import send_email
from app.core.config import get_settings
from app.messaging import consumer
from app.processor import process_message

logger = logging.getLogger("worker")


def _process_sync(body: bytes) -> str:
    """Runs in a thread: database and SMTP calls are blocking."""
    from db.database import SessionLocal

    with SessionLocal() as db:
        return process_message(db, body, send_email)


async def process(body: bytes) -> str:
    return await asyncio.to_thread(_process_sync, body)


async def main() -> None:
    settings = get_settings()
    while True:
        try:
            await consumer.run(settings, process)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Typically RabbitMQ is not up yet (containers start in any order).
            logger.exception("worker error; retrying in 5s")
            await asyncio.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(main())
