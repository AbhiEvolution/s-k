from datetime import date, datetime, time, timedelta, timezone

import pytest
from conftest import as_user

from app.core.clients import NotClinicMemberError, ServiceUnavailableError

# ---- a tiny fake world standing in for the clinic, doctor and patient services
CLINIC = 1
OTHER_CLINIC = 2
DOCTOR_USER, DOCTOR_ID = 10, 100           # a doctor with profile id 100 at clinic 1
DOCTOR2_USER, DOCTOR2_ID = 11, 101
STAFF_USER = 12                            # clinic staff
OUTSIDER = 99                              # belongs to no clinic
MEMBERS = {CLINIC: {DOCTOR_USER, DOCTOR2_USER, STAFF_USER}, OTHER_CLINIC: {50}}
DOCTORS = {
    DOCTOR_ID: {"id": DOCTOR_ID, "full_name": "Dr. One", "specialty": None, "clinic_id": CLINIC},
    DOCTOR2_ID: {"id": DOCTOR2_ID, "full_name": "Dr. Two", "specialty": None, "clinic_id": CLINIC},
    200: {"id": 200, "full_name": "Dr. Far", "specialty": None, "clinic_id": OTHER_CLINIC},
}
PROFILES = {DOCTOR_USER: DOCTORS[DOCTOR_ID], DOCTOR2_USER: DOCTORS[DOCTOR2_ID]}
PATIENTS = {1: {"id": 1, "clinic_id": CLINIC}, 2: {"id": 2, "clinic_id": CLINIC}, 3: {"id": 3, "clinic_id": OTHER_CLINIC}}


@pytest.fixture(autouse=True)
def fake_services(monkeypatch):
    def verify(clinic_id, user_id, token):
        if user_id not in MEMBERS.get(clinic_id, set()):
            raise NotClinicMemberError()

    # Patch the names where the service module uses them.
    monkeypatch.setattr("app.services.appointment.verify_membership", verify)
    monkeypatch.setattr("app.services.appointment.fetch_doctor", lambda doctor_id, token: DOCTORS.get(doctor_id))
    monkeypatch.setattr("app.services.appointment.fetch_patient", lambda patient_id, token: PATIENTS.get(patient_id))

    def my_doctor(token):
        import jwt  # the fake reads the caller from the token, like the real service would

        user_id = int(jwt.decode(token, options={"verify_signature": False})["sub"])
        return PROFILES.get(user_id)

    monkeypatch.setattr("app.services.appointment.fetch_my_doctor", my_doctor)


def next_monday() -> date:
    today = date.today() + timedelta(days=7)
    return today + timedelta(days=(7 - today.weekday()) % 7)


def at(hour, minute=0, day=None) -> str:
    day = day or next_monday()
    return datetime.combine(day, time(hour, minute), tzinfo=timezone.utc).isoformat()


WINDOWS = {"windows": [{"weekday": 0, "start_time": "09:00:00", "end_time": "12:00:00"}]}
URL = "/api/v1/appointments"


def set_hours(client, user=DOCTOR_USER, body=WINDOWS):
    return client.put(f"{URL}/availability", json=body, headers=as_user(user, "doctor"))


def book(client, hour=9, minute=0, patient=1, doctor=DOCTOR_ID, clinic=CLINIC, user=STAFF_USER, key=None):
    headers = as_user(user, "doctor")
    if key:
        headers["Idempotency-Key"] = key
    return client.post(
        URL,
        json={"clinic_id": clinic, "doctor_id": doctor, "patient_id": patient, "starts_at": at(hour, minute)},
        headers=headers,
    )


@pytest.fixture
def ready(client):
    """Doctor 100 works Mondays 09:00-12:00 UTC."""
    assert set_hours(client).status_code == 200
    return client


# ------------------------------------------------------------------ availability
def test_requires_authentication(client):
    assert client.get(f"{URL}?clinic_id=1").status_code == 401


def test_doctor_sets_and_reads_own_availability(client):
    response = set_hours(client)
    assert response.status_code == 200 and response.json()["doctor_id"] == DOCTOR_ID
    read = client.get(f"{URL}/availability?doctor_id={DOCTOR_ID}", headers=as_user(STAFF_USER))
    assert read.status_code == 200 and len(read.json()["windows"]) == 1


def test_setting_availability_replaces_the_old_hours(client):
    set_hours(client)
    set_hours(client, body={"windows": [{"weekday": 1, "start_time": "10:00:00", "end_time": "11:00:00"}]})
    windows = client.get(f"{URL}/availability?doctor_id={DOCTOR_ID}", headers=as_user(STAFF_USER)).json()["windows"]
    assert [w["weekday"] for w in windows] == [1]


def test_only_doctors_can_set_availability(client):
    response = client.put(f"{URL}/availability", json=WINDOWS, headers=as_user(STAFF_USER, "patient"))
    assert response.status_code == 403


def test_doctor_without_profile_cannot_set_availability(client):
    assert client.put(f"{URL}/availability", json=WINDOWS, headers=as_user(77, "doctor")).status_code == 409


@pytest.mark.parametrize("window", [
    {"weekday": 0, "start_time": "09:00:00", "end_time": "09:00:00"},   # empty
    {"weekday": 0, "start_time": "10:00:00", "end_time": "09:00:00"},   # backwards
    {"weekday": 0, "start_time": "09:10:00", "end_time": "10:00:00"},   # off grid
    {"weekday": 7, "start_time": "09:00:00", "end_time": "10:00:00"},   # no such weekday
])
def test_invalid_windows_are_rejected(client, window):
    assert set_hours(client, body={"windows": [window]}).status_code == 422


def test_overlapping_windows_are_rejected(client):
    body = {"windows": [
        {"weekday": 0, "start_time": "09:00:00", "end_time": "11:00:00"},
        {"weekday": 0, "start_time": "10:30:00", "end_time": "12:00:00"},
    ]}
    assert set_hours(client, body=body).status_code == 422


def test_outsider_cannot_see_a_doctors_availability(client):
    set_hours(client)
    assert client.get(f"{URL}/availability?doctor_id={DOCTOR_ID}", headers=as_user(OUTSIDER)).status_code == 403


# ------------------------------------------------------------------------- slots
def test_slots_for_a_working_day(ready):
    slots = ready.get(f"{URL}/slots?doctor_id={DOCTOR_ID}&day={next_monday()}", headers=as_user(STAFF_USER)).json()
    assert [s["starts_at"][11:16] for s in slots] == ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30"]
    assert all(s["available"] for s in slots)


def test_slots_empty_on_a_day_off(ready):
    tuesday = next_monday() + timedelta(days=1)
    assert ready.get(f"{URL}/slots?doctor_id={DOCTOR_ID}&day={tuesday}", headers=as_user(STAFF_USER)).json() == []


def test_booked_slot_is_marked_unavailable_and_cancelling_frees_it(ready):
    appointment = book(ready, 10, 0).json()
    slot_url = f"{URL}/slots?doctor_id={DOCTOR_ID}&day={next_monday()}"

    def state():
        return {s["starts_at"][11:16]: s["available"] for s in ready.get(slot_url, headers=as_user(STAFF_USER)).json()}

    assert state()["10:00"] is False and state()["09:30"] is True
    ready.post(f"{URL}/{appointment['id']}/cancel", headers=as_user(STAFF_USER))
    assert state()["10:00"] is True


# ----------------------------------------------------------------------- booking
def test_book_happy_path(ready):
    response = book(ready, 9, 30)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "booked" and body["created_by_user_id"] == STAFF_USER
    assert body["starts_at"].endswith("Z") or body["starts_at"].endswith("+00:00")
    assert body["ends_at"][11:16] == "10:00"  # 30-minute slot


def test_double_booking_the_same_doctor_slot_is_refused(ready):
    assert book(ready, 9, patient=1).status_code == 201
    second = book(ready, 9, patient=2)  # a different patient, same doctor, same time
    assert second.status_code == 409


def test_a_patient_cannot_be_in_two_places_at_once(ready):
    set_hours(ready, user=DOCTOR2_USER)
    assert book(ready, 9, patient=1, doctor=DOCTOR_ID).status_code == 201
    assert book(ready, 9, patient=1, doctor=DOCTOR2_ID).status_code == 409


def test_same_doctor_different_time_is_fine(ready):
    assert book(ready, 9, patient=1).status_code == 201
    assert book(ready, 9, 30, patient=2).status_code == 201


def test_cancelled_slot_can_be_booked_again(ready):
    first = book(ready, 9).json()
    ready.post(f"{URL}/{first['id']}/cancel", headers=as_user(STAFF_USER))
    assert book(ready, 9, patient=2).status_code == 201


def test_booking_outside_working_hours_is_refused(ready):
    assert book(ready, 8).status_code == 422
    assert book(ready, 12).status_code == 422   # window ends at 12:00
    assert book(ready, 11, 30).status_code == 201  # last slot fits


def test_off_grid_time_is_refused(ready):
    assert book(ready, 9, 15).status_code == 422


def test_booking_in_the_past_is_refused(ready):
    past = datetime.now(timezone.utc) - timedelta(days=7)
    past = past.replace(hour=9, minute=0, second=0, microsecond=0)
    set_hours(ready, body={"windows": [{"weekday": past.weekday(), "start_time": "00:00:00", "end_time": "23:00:00"}]})
    response = ready.post(
        URL,
        json={"clinic_id": CLINIC, "doctor_id": DOCTOR_ID, "patient_id": 1, "starts_at": past.isoformat()},
        headers=as_user(STAFF_USER),
    )
    assert response.status_code == 422


def test_naive_datetime_is_refused(ready):
    response = ready.post(
        URL,
        json={"clinic_id": CLINIC, "doctor_id": DOCTOR_ID, "patient_id": 1, "starts_at": "2030-01-07T09:00:00"},
        headers=as_user(STAFF_USER),
    )
    assert response.status_code == 422  # no timezone: we refuse to guess


def test_non_member_cannot_book(ready):
    assert book(ready, user=OUTSIDER).status_code == 403


def test_doctor_from_another_clinic_is_refused(ready):
    assert book(ready, doctor=200).status_code == 422


def test_patient_from_another_clinic_is_refused(ready):
    assert book(ready, patient=3).status_code == 422


def test_unknown_doctor_and_patient_are_404(ready):
    assert book(ready, doctor=9999).status_code == 404
    assert book(ready, patient=9999).status_code == 404


def test_other_service_down_gives_503_and_saves_nothing(ready, monkeypatch):
    def down(*args):
        raise ServiceUnavailableError()

    monkeypatch.setattr("app.services.appointment.fetch_patient", down)
    assert book(ready).status_code == 503
    # nothing was saved: the slot is still free
    monkeypatch.setattr("app.services.appointment.fetch_patient", lambda patient_id, token: PATIENTS.get(patient_id))
    assert book(ready).status_code == 201


# ------------------------------------------------------------------ idempotency
def test_same_idempotency_key_returns_the_same_appointment(ready):
    first = book(ready, 9, key="abc-123")
    again = book(ready, 9, key="abc-123")
    assert first.status_code == 201 and again.status_code == 200
    assert first.json()["id"] == again.json()["id"]
    listed = ready.get(f"{URL}?clinic_id={CLINIC}", headers=as_user(STAFF_USER)).json()
    assert len(listed) == 1


def test_different_keys_are_different_requests(ready):
    assert book(ready, 9, patient=1, key="k1").status_code == 201
    assert book(ready, 9, patient=2, key="k2").status_code == 409  # the slot is taken


# ----------------------------------------------------------- read, list, cancel
def test_get_and_list_and_filters(ready):
    a = book(ready, 9, patient=1).json()
    b = book(ready, 9, 30, patient=2).json()

    assert ready.get(f"{URL}/{a['id']}", headers=as_user(STAFF_USER)).json()["id"] == a["id"]
    listed = ready.get(f"{URL}?clinic_id={CLINIC}", headers=as_user(STAFF_USER)).json()
    assert [x["id"] for x in listed] == [a["id"], b["id"]]  # ordered by time

    by_patient = ready.get(f"{URL}?clinic_id={CLINIC}&patient_id=2", headers=as_user(STAFF_USER)).json()
    assert [x["id"] for x in by_patient] == [b["id"]]

    ready.post(f"{URL}/{a['id']}/cancel", headers=as_user(STAFF_USER))
    booked_only = ready.get(f"{URL}?clinic_id={CLINIC}&status=booked", headers=as_user(STAFF_USER)).json()
    assert [x["id"] for x in booked_only] == [b["id"]]


def test_outsider_cannot_read_list_or_cancel(ready):
    appointment = book(ready).json()
    outsider = as_user(OUTSIDER)
    assert ready.get(f"{URL}/{appointment['id']}", headers=outsider).status_code == 404  # hidden, not 403
    assert ready.post(f"{URL}/{appointment['id']}/cancel", headers=outsider).status_code == 404
    assert ready.get(f"{URL}?clinic_id={CLINIC}", headers=outsider).status_code == 403
    assert ready.get(f"{URL}/{appointment['id']}", headers=as_user(STAFF_USER)).json()["status"] == "booked"


def test_cancel_is_idempotent(ready):
    appointment = book(ready).json()
    first = ready.post(f"{URL}/{appointment['id']}/cancel", headers=as_user(STAFF_USER))
    second = ready.post(f"{URL}/{appointment['id']}/cancel", headers=as_user(STAFF_USER))
    assert first.status_code == second.status_code == 200
    assert second.json()["status"] == "cancelled" and second.json()["cancelled_at"]


def test_unknown_appointment_is_404(ready):
    assert ready.get(f"{URL}/12345", headers=as_user(STAFF_USER)).status_code == 404
