"""The queues this service owns.

    clinic.events (topic exchange, declared by the publisher too)
          │  binding "appointment.*"
          ▼
    notification.appointments ───────────────► consumer
          ▲                                       │ transient failure
          │ after the delay                       ▼
          └──── notification.appointments.retry (waits retry_delay_ms, then
                dead-letters straight back into the main queue)

    notification.appointments.dlq   <- messages that can never succeed, or that
                                       failed max_attempts times. Inspect them,
                                       fix the cause, then move them back by hand.
"""
import aio_pika
from aio_pika.abc import AbstractChannel, AbstractQueue

from app.core.config import Settings


async def declare(channel: AbstractChannel, settings: Settings) -> AbstractQueue:
    exchange = await channel.declare_exchange(
        settings.events_exchange, aio_pika.ExchangeType.TOPIC, durable=True
    )

    await channel.declare_queue(settings.dead_letter_queue, durable=True)

    # The delay queue: messages sit here for retry_delay_ms, then RabbitMQ
    # "dead-letters" them via the default exchange into the main queue.
    # NOTE: queue arguments are fixed at creation. Changing retry_delay_ms later
    # needs this queue deleted first, or RabbitMQ answers PRECONDITION_FAILED.
    await channel.declare_queue(
        settings.retry_queue,
        durable=True,
        arguments={
            "x-message-ttl": settings.retry_delay_ms,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": settings.queue_name,
        },
    )

    main = await channel.declare_queue(settings.queue_name, durable=True)
    await main.bind(exchange, routing_key=settings.binding_key)
    return main
