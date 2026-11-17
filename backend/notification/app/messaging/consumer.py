"""Receive messages, decide what to do with each, acknowledge exactly once.

Acknowledgements are MANUAL. A message is acked only after its fate is safe:
processed, or copied to the retry/dead-letter queue (publisher-confirmed). If
the worker dies before that, RabbitMQ redelivers the message: nothing is lost.
"""
import asyncio
import logging
from typing import Awaitable, Callable

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractIncomingMessage

from app.core.config import Settings
from app.messaging.topology import declare
from app.processor import PoisonMessageError

logger = logging.getLogger("consumer")

ACKED, RETRIED, DEAD_LETTERED = "acked", "retried", "dead_lettered"


async def handle_message(
    message: AbstractIncomingMessage,
    *,
    process: Callable[[bytes], Awaitable[str]],
    send_retry: Callable[[AbstractIncomingMessage, int, str], Awaitable[None]],
    send_dead_letter: Callable[[AbstractIncomingMessage, int, str], Awaitable[None]],
    max_attempts: int,
) -> str:
    attempt = int((message.headers or {}).get("x-attempt", 1))

    try:
        outcome = await process(message.body)
    except PoisonMessageError as exc:
        # Retrying a malformed message just wastes time: park it for a human.
        await send_dead_letter(message, attempt, f"poison message: {exc}")
        await message.ack()
        logger.error("dead-lettered poison message %s: %s", message.message_id, exc)
        return DEAD_LETTERED
    except Exception as exc:  # noqa: BLE001 - anything else might be temporary (SMTP down, DB blip)
        if attempt >= max_attempts:
            await send_dead_letter(message, attempt, f"gave up after {attempt} attempts: {exc!r}")
            await message.ack()
            logger.error("dead-lettered %s after %d attempts: %r", message.message_id, attempt, exc)
            return DEAD_LETTERED
        await send_retry(message, attempt + 1, repr(exc))
        await message.ack()
        logger.warning("attempt %d failed for %s (%r); retrying later", attempt, message.message_id, exc)
        return RETRIED

    await message.ack()
    logger.info("handled %s: %s", message.message_id, outcome)
    return ACKED


def _copy(message: AbstractIncomingMessage, headers: dict) -> aio_pika.Message:
    return aio_pika.Message(
        message.body,
        headers=headers,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        content_type=message.content_type,
        message_id=message.message_id,
        type=message.type,
    )


def make_publishers(channel: AbstractChannel, settings: Settings):
    async def send(queue_name: str, message: AbstractIncomingMessage, attempt: int, note_key: str, note: str):
        headers = {**(message.headers or {}), "x-attempt": attempt, note_key: note[:500]}
        # The default exchange routes by queue name. With publisher confirms (the
        # aio-pika default) this returns only once the broker has stored it.
        await channel.default_exchange.publish(_copy(message, headers), routing_key=queue_name)

    async def send_retry(message, attempt, error):
        await send(settings.retry_queue, message, attempt, "x-last-error", error)

    async def send_dead_letter(message, attempt, reason):
        await send(settings.dead_letter_queue, message, attempt, "x-dead-letter-reason", reason)

    return send_retry, send_dead_letter


async def run(settings: Settings, process: Callable[[bytes], Awaitable[str]]) -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)  # reconnects by itself
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=settings.prefetch)
        queue = await declare(channel, settings)
        send_retry, send_dead_letter = make_publishers(channel, settings)

        async def on_message(message: AbstractIncomingMessage) -> None:
            await handle_message(
                message,
                process=process,
                send_retry=send_retry,
                send_dead_letter=send_dead_letter,
                max_attempts=settings.max_attempts,
            )

        await queue.consume(on_message)
        logger.info("consuming %s (prefetch %d, max attempts %d)", settings.queue_name,
                    settings.prefetch, settings.max_attempts)
        await asyncio.Future()  # run until cancelled
