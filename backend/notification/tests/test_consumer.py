"""Retry / dead-letter decisions, with a fake message and no broker."""
import asyncio

from app.messaging.consumer import ACKED, DEAD_LETTERED, RETRIED, handle_message
from app.processor import PoisonMessageError


class FakeMessage:
    def __init__(self, attempt=None, body=b"{}"):
        self.body = body
        self.headers = {"x-attempt": attempt} if attempt else {}
        self.message_id = "m-1"
        self.acked = 0

    async def ack(self):
        self.acked += 1


class Recorder:
    def __init__(self):
        self.retries, self.dead = [], []

    async def retry(self, message, attempt, error):
        self.retries.append((attempt, error))

    async def dead_letter(self, message, attempt, reason):
        self.dead.append((attempt, reason))


def run(message, process, recorder, max_attempts=3):
    return asyncio.run(handle_message(
        message, process=process, send_retry=recorder.retry,
        send_dead_letter=recorder.dead_letter, max_attempts=max_attempts,
    ))


def test_success_is_acked_once():
    recorder, message = Recorder(), FakeMessage()

    async def ok(body):
        return "sent"

    assert run(message, ok, recorder) == ACKED
    assert message.acked == 1 and recorder.retries == [] and recorder.dead == []


def test_temporary_failure_goes_to_the_retry_queue_with_a_higher_attempt():
    recorder, message = Recorder(), FakeMessage()

    async def down(body):
        raise ConnectionError("smtp down")

    assert run(message, down, recorder) == RETRIED
    assert recorder.retries[0][0] == 2 and "smtp down" in recorder.retries[0][1]
    assert message.acked == 1 and recorder.dead == []  # acked AFTER being copied to retry


def test_the_attempt_counter_follows_the_message():
    recorder = Recorder()

    async def down(body):
        raise ConnectionError("x")

    assert run(FakeMessage(attempt=2), down, recorder) == RETRIED
    assert recorder.retries[0][0] == 3


def test_after_max_attempts_it_is_dead_lettered():
    recorder, message = Recorder(), FakeMessage(attempt=3)

    async def down(body):
        raise ConnectionError("still down")

    assert run(message, down, recorder, max_attempts=3) == DEAD_LETTERED
    assert recorder.retries == [] and "gave up after 3 attempts" in recorder.dead[0][1]
    assert message.acked == 1


def test_poison_messages_skip_retries_entirely():
    recorder, message = Recorder(), FakeMessage()

    async def poison(body):
        raise PoisonMessageError("bad shape")

    assert run(message, poison, recorder) == DEAD_LETTERED
    assert recorder.retries == [] and "bad shape" in recorder.dead[0][1]


def test_a_failure_while_parking_leaves_the_message_unacked():
    # If we cannot even copy it to the retry queue, we must NOT ack: the broker
    # will redeliver, so nothing is lost.
    message = FakeMessage()

    async def down(body):
        raise ConnectionError("x")

    async def broken_retry(message, attempt, error):
        raise RuntimeError("broker unreachable")

    try:
        asyncio.run(handle_message(
            message, process=down, send_retry=broken_retry,
            send_dead_letter=Recorder().dead_letter, max_attempts=3,
        ))
    except RuntimeError:
        pass
    assert message.acked == 0
