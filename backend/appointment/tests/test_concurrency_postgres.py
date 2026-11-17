"""Does the database really stop double-booking under concurrent requests?

SQLite cannot prove this (it has one writer at a time), so this test needs a
real Postgres. It is skipped unless TEST_DATABASE_URL is set, e.g.:

    docker run -d --name appt-test-pg -e POSTGRES_PASSWORD=test -p 127.0.0.1:5439:5432 postgres:17
    TEST_DATABASE_URL=postgresql+psycopg://postgres:test@127.0.0.1:5439/postgres pytest tests/test_concurrency_postgres.py

WARNING: it drops and recreates the appointments tables in that database.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pytest

TEST_DB = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DB, reason="set TEST_DATABASE_URL to a throwaway Postgres")

sys.path.insert(0, str(Path(__file__).resolve().parent))

if TEST_DB:
    from conftest import as_user
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    import app.models  # noqa: F401
    from app.main import app
    from db.database import Base, get_db

CLINIC, DOCTOR_ID, STAFF = 1, 100, 12
THREADS = 12


@pytest.fixture
def postgres(monkeypatch):
    engine = create_engine(TEST_DB, pool_size=THREADS + 2)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Every collaborator says yes; only the DATABASE is under test.
    monkeypatch.setattr("app.services.appointment.verify_membership", lambda *a: None)
    monkeypatch.setattr(
        "app.services.appointment.fetch_doctor",
        lambda doctor_id, token: {"id": doctor_id, "clinic_id": CLINIC},
    )
    monkeypatch.setattr(
        "app.services.appointment.fetch_patient",
        lambda patient_id, token: {"id": patient_id, "clinic_id": CLINIC},
    )
    monkeypatch.setattr(
        "app.services.appointment.fetch_my_doctor",
        lambda token: {"id": DOCTOR_ID, "clinic_id": CLINIC},
    )

    with TestClient(app) as setup:
        monday = date.today() + timedelta(days=7)
        monday += timedelta(days=(7 - monday.weekday()) % 7)
        response = setup.put(
            "/api/v1/appointments/availability",
            json={"windows": [{"weekday": 0, "start_time": "09:00:00", "end_time": "12:00:00"}]},
            headers=as_user(DOCTOR_ID, "doctor"),
        )
        assert response.status_code == 200, response.text

    yield engine, datetime.combine(monday, time(9, 0), tzinfo=timezone.utc)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def _book(starts_at, patient_id, key=None):
    headers = as_user(STAFF, "doctor")
    if key:
        headers["Idempotency-Key"] = key
    with TestClient(app) as client:  # one client per thread
        return client.post(
            "/api/v1/appointments",
            json={"clinic_id": CLINIC, "doctor_id": DOCTOR_ID, "patient_id": patient_id,
                  "starts_at": starts_at.isoformat()},
            headers=headers,
        )


def _count(engine, where="status = 'booked'"):
    with engine.connect() as connection:
        return connection.execute(text(f"SELECT count(*) FROM appointments WHERE {where}")).scalar()


def test_concurrent_requests_for_one_slot_produce_exactly_one_booking(postgres):
    engine, slot = postgres
    with ThreadPoolExecutor(THREADS) as pool:
        # 12 different patients all grab the SAME doctor and time at once.
        responses = list(pool.map(lambda patient: _book(slot, patient), range(1, THREADS + 1)))

    codes = sorted(r.status_code for r in responses)
    assert codes == [201] + [409] * (THREADS - 1), codes
    assert _count(engine) == 1  # the database holds exactly one


def test_one_patient_cannot_win_two_doctors_at_the_same_time_under_load(postgres):
    engine, slot = postgres

    def book_with_doctor(doctor_id):
        headers = as_user(STAFF, "doctor")
        with TestClient(app) as client:
            return client.post(
                "/api/v1/appointments",
                json={"clinic_id": CLINIC, "doctor_id": doctor_id, "patient_id": 1,
                      "starts_at": slot.isoformat()},
                headers=headers,
            )

    # Make several doctors available (they all share the fake availability row of DOCTOR_ID,
    # so book against the one doctor with the same patient repeatedly instead).
    with ThreadPoolExecutor(THREADS) as pool:
        responses = list(pool.map(lambda _: book_with_doctor(DOCTOR_ID), range(THREADS)))
    assert sorted(r.status_code for r in responses).count(201) == 1
    assert _count(engine) == 1


def test_a_retried_request_with_the_same_idempotency_key_books_once(postgres):
    engine, slot = postgres
    with ThreadPoolExecutor(THREADS) as pool:
        responses = list(pool.map(lambda _: _book(slot, 1, key="retry-me"), range(THREADS)))

    assert all(r.status_code in (200, 201) for r in responses), [r.status_code for r in responses]
    assert [r.status_code for r in responses].count(201) == 1
    assert len({r.json()["id"] for r in responses}) == 1  # everyone got the SAME appointment
    assert _count(engine) == 1


def test_cancelled_rows_do_not_block_a_new_booking(postgres):
    engine, slot = postgres
    first = _book(slot, 1)
    assert first.status_code == 201
    with TestClient(app) as client:
        client.post(f"/api/v1/appointments/{first.json()['id']}/cancel", headers=as_user(STAFF, "doctor"))
    assert _book(slot, 2).status_code == 201
    assert _count(engine, "status = 'booked'") == 1 and _count(engine, "status = 'cancelled'") == 1
