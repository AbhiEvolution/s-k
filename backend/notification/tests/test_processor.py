import json

import pytest
from sqlalchemy import select

from app.models.notification import NotificationLog
from app.processor import DUPLICATE, IGNORED, SENT, SKIPPED, PoisonMessageError, process_message


class Outbox:
    """A fake email channel that records what would have been sent."""

    def __init__(self):
        self.sent = []

    def __call__(self, recipient, subject, body):
        self.sent.append((recipient, subject, body))


def event(event_id="e-1", type_="appointment.booked", **data):
    payload = {
        "appointment_id": 7, "clinic_id": 1, "doctor_id": 100, "doctor_name": "Dr. Ada",
        "patient_id": 1, "patient_name": "Grace Hopper", "patient_email": "grace@example.com",
        "starts_at": "2030-01-07T09:00:00+00:00", "ends_at": "2030-01-07T09:30:00+00:00",
        "reason": "Check-up",
    }
    payload.update(data)
    return json.dumps({"event_id": event_id, "type": type_, "version": 1, "data": payload}).encode()


def logs(db):
    return list(db.scalars(select(NotificationLog)))


def test_booked_event_sends_a_confirmation(db):
    mail = Outbox()
    assert process_message(db, event(), mail) == SENT

    ((recipient, subject, body),) = mail.sent
    assert recipient == "grace@example.com"
    assert subject == "Your appointment is confirmed"
    assert "Grace Hopper" in body and "Dr. Ada" in body
    assert "Monday 07 January 2030 at 09:00 UTC" in body
    assert "Check-up" in body
    assert [(l.event_id, l.status) for l in logs(db)] == [("e-1", "sent")]


def test_cancelled_event_sends_a_cancellation(db):
    mail = Outbox()
    process_message(db, event(type_="appointment.cancelled"), mail)
    assert mail.sent[0][1] == "Your appointment was cancelled"
    assert "has been cancelled" in mail.sent[0][2]


def test_the_same_event_twice_sends_one_email(db):
    mail = Outbox()
    assert process_message(db, event("dup"), mail) == SENT
    assert process_message(db, event("dup"), mail) == DUPLICATE  # redelivery
    assert process_message(db, event("dup"), mail) == DUPLICATE
    assert len(mail.sent) == 1 and len(logs(db)) == 1


def test_different_events_each_send(db):
    mail = Outbox()
    process_message(db, event("a"), mail)
    process_message(db, event("b"), mail)
    assert len(mail.sent) == 2


def test_no_email_address_means_no_send_but_it_is_recorded(db):
    mail = Outbox()
    assert process_message(db, event("x", patient_email=None), mail) == SKIPPED
    assert mail.sent == []
    assert logs(db)[0].status == "skipped_no_recipient"
    assert process_message(db, event("x", patient_email=None), mail) == DUPLICATE


def test_a_failing_email_channel_raises_and_records_nothing(db):
    def broken(*args):
        raise ConnectionRefusedError("smtp is down")

    with pytest.raises(ConnectionRefusedError):
        process_message(db, event("retry-me"), broken)
    assert logs(db) == []  # nothing recorded, so the retry will try again

    mail = Outbox()
    assert process_message(db, event("retry-me"), mail) == SENT  # the retry succeeds
    assert len(mail.sent) == 1


@pytest.mark.parametrize("body", [
    b"not json at all",
    b'{"hello": "world"}',                                    # no envelope fields
    json.dumps({"event_id": "p", "type": "appointment.booked", "data": {}}).encode(),   # payload missing fields
    event("p2", patient_email="not-an-email"),                # invalid address
    event("p3", starts_at="yesterday-ish"),                   # invalid time
])
def test_malformed_messages_are_poison(db, body):
    with pytest.raises(PoisonMessageError):
        process_message(db, body, Outbox())
    assert logs(db) == []


def test_unknown_event_types_are_ignored_not_errors(db):
    mail = Outbox()
    assert process_message(db, event("u", type_="billing.invoiced"), mail) == IGNORED
    assert process_message(db, event("u2", type_="appointment.rescheduled"), mail) == IGNORED
    assert mail.sent == []


def test_extra_fields_from_a_newer_publisher_are_tolerated(db):
    mail = Outbox()
    assert process_message(db, event("n", brand_new_field={"a": 1}), mail) == SENT
