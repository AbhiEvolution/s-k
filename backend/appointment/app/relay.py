"""Outbox relay: moves events from the database to RabbitMQ.

Run as its own process:  python -m app.relay

Delivery is AT-LEAST-ONCE. If the relay crashes after publishing but before
marking a row, that row is published again later. Consumers therefore ignore
events whose event_id they have already handled.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

import aio_pika

from app.core.config import get_settings
from app.repositories.appointment import OutboxRepository

logger = logging.getLogger("relay")


async def relay_batch(session_factory, publish, batch_size: int) -> int:
    """Publish one batch of unpublished events. Returns how many were sent.

    `publish(routing_key, body, message_id)` is injected so this is testable
    without a broker.
    """
    db = session_factory()
    sent = 0
    try:
        for row in OutboxRepository.fetch_unpublished(db, batch_size):
            await publish(row.event_type, json.dumps(row.payload).encode(), row.event_id)
            row.published_at = datetime.now(timezone.utc)
            sent += 1
    finally:
        # Commit progress even if a later publish raised: those rows stay
        # unpublished and are retried, the sent ones are not sent twice.
        db.commit()
        db.close()
    return sent


async def run() -> None:
    from db.database import SessionLocal

    settings = get_settings()
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            async with connection:
                # Publisher confirms: publish() returns only once the broker has the message.
                channel = await connection.channel(publisher_confirms=True)
                exchange = await channel.declare_exchange(
                    settings.events_exchange, aio_pika.ExchangeType.TOPIC, durable=True
                )

                async def publish(routing_key: str, body: bytes, message_id: str) -> None:
                    message = aio_pika.Message(
                        body,
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # survives a broker restart
                        content_type="application/json",
                        message_id=message_id,
                        type=routing_key,
                    )
                    # mandatory=True: if NO queue is bound yet the broker would silently
                    # drop the message. Instead publishing fails, the row stays in the
                    # outbox, and we retry once a consumer has declared its queue.
                    await exchange.publish(message, routing_key=routing_key, mandatory=True)

                logger.info("relay connected; polling the outbox")
                while True:
                    sent = await relay_batch(SessionLocal, publish, settings.relay_batch_size)
                    if sent:
                        logger.info("published %d event(s)", sent)
                    else:
                        await asyncio.sleep(settings.relay_poll_seconds)
        except Exception:
            logger.exception("relay error; retrying in 5s")
            await asyncio.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run())
