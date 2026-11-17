"""The outbox: events are recorded atomically with the change, then relayed."""
import asyncio
import json

import pytest
from sqlalchemy import select
from test_appointments_api import (  # reuse the fake world and helpers
    CLINIC,
    DOCTOR_ID,
    STAFF_USER,
    URL,
    book,
    fake_services,  # noqa: F401  (autouse fixture must be importable here)
    ready,  # noqa: F401
    set_hours,  # noqa: F401
)
from conftest import as_user

from app.models.appointment import OutboxEvent
from app.relay import relay_batch


def events(session_factory):
    with session_factory() as db:
        return list(db.scalars(select(OutboxEvent).order_by(OutboxEvent.id)))


def test_booking_records_an_event_with_a_snapshot(ready, session_factory):
    response = book(ready, 9, patient=1)
    assert response.status_code == 201

    (event,) = events(session_factory)
    assert event.event_type == "appointment.booked" and event.published_at is None
    body = event.payload
    assert body["type"] == "appointment.booked" and body["version"] == 1
    assert body["event_id"] == event.event_id
    data = body["data"]
    assert data["appointment_id"] == response.json()["id"]
    assert data["clinic_id"] == CLINIC and data["doctor_id"] == DOCTOR_ID and data["patient_id"] == 1
    assert data["doctor_name"] == "Dr. One"  # snapshot: consumers need no callbacks
    assert data["starts_at"].endswith("+00:00")


def test_cancelling_records_a_cancelled_event(ready, session_factory):
    appointment = book(ready, 9).json()
    ready.post(f"{URL}/{appointment['id']}/cancel", headers=as_user(STAFF_USER))
    assert [e.event_type for e in events(session_factory)] == ["appointment.booked", "appointment.cancelled"]


def test_cancelling_twice_records_only_one_event(ready, session_factory):
    appointment = book(ready, 9).json()
    for _ in range(2):
        ready.post(f"{URL}/{appointment['id']}/cancel", headers=as_user(STAFF_USER))
    assert [e.event_type for e in events(session_factory)].count("appointment.cancelled") == 1


def test_a_refused_booking_records_no_event(ready, session_factory):
    assert book(ready, 9, patient=1).status_code == 201
    assert book(ready, 9, patient=2).status_code == 409  # double-booking: rolled back
    assert book(ready, 8, patient=2).status_code == 422  # outside hours
    assert len(events(session_factory)) == 1  # only the successful booking


def test_an_idempotent_replay_records_no_second_event(ready, session_factory):
    book(ready, 9, key="same")
    book(ready, 9, key="same")
    assert len(events(session_factory)) == 1


# ------------------------------------------------------------------------- relay
def run(coro):
    return asyncio.run(coro)


def test_relay_publishes_in_order_and_marks_rows_published(ready, session_factory):
    book(ready, 9, patient=1)
    book(ready, 9, 30, patient=2)

    published = []

    async def publish(routing_key, body, message_id):
        published.append((routing_key, json.loads(body)["event_id"], message_id))

    assert run(relay_batch(session_factory, publish, 50)) == 2
    assert [p[0] for p in published] == ["appointment.booked", "appointment.booked"]
    assert all(p[1] == p[2] for p in published)  # message id == event id
    assert all(e.published_at is not None for e in events(session_factory))

    published.clear()
    assert run(relay_batch(session_factory, publish, 50)) == 0  # nothing left to send
    assert published == []


def test_relay_leaves_rows_unpublished_when_the_broker_fails_and_retries_later(ready, session_factory):
    book(ready, 9, patient=1)
    book(ready, 9, 30, patient=2)
    book(ready, 10, patient=1)

    calls = []

    async def flaky(routing_key, body, message_id):
        calls.append(message_id)
        if len(calls) == 2:
            raise ConnectionError("broker went away")

    with pytest.raises(ConnectionError):
        run(relay_batch(session_factory, flaky, 50))

    state = [e.published_at is not None for e in events(session_factory)]
    assert state == [True, False, False]  # progress kept; the failed one and later ones wait

    sent_later = []

    async def healthy(routing_key, body, message_id):
        sent_later.append(message_id)

    assert run(relay_batch(session_factory, healthy, 50)) == 2
    assert len(sent_later) == 2 and calls[0] not in sent_later  # the first is not re-sent
    assert all(e.published_at is not None for e in events(session_factory))


def test_relay_respects_the_batch_size(ready, session_factory):
    for hour, patient in ((9, 1), (10, 2), (11, 1)):
        book(ready, hour, patient=patient)

    async def publish(*args):
        pass

    assert run(relay_batch(session_factory, publish, 2)) == 2
    assert run(relay_batch(session_factory, publish, 2)) == 1
