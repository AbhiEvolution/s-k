import httpx
import pytest
from conftest import as_user

import app.core.clinic_client as clinic_client
from app.core.clinic_client import (
    ClinicServiceUnavailableError,
    NotClinicMemberError,
)

URL = "/api/v1/doctors"
PROFILE = {"full_name": "Dr. Ada Lovelace", "clinic_id": 3}


@pytest.fixture
def clinic_says_member(monkeypatch):
    """Replace the HTTP call to the clinic service. Records what was asked."""
    calls = []

    def fake(clinic_id, user_id, token):
        calls.append((clinic_id, user_id))

    monkeypatch.setattr("app.services.doctor.verify_membership", fake)
    return calls


def test_profile_can_link_to_a_clinic_after_verification(client, clinic_says_member):
    response = client.post(URL, json=PROFILE, headers=as_user(7))
    assert response.status_code == 201
    assert response.json()["clinic_id"] == 3
    assert clinic_says_member == [(3, 7)]  # asked about THIS user, not a body value


def test_clinic_id_is_optional_and_skips_the_check(client, clinic_says_member):
    response = client.post(URL, json={"full_name": "Dr. Solo"}, headers=as_user(7))
    assert response.status_code == 201
    assert response.json()["clinic_id"] is None
    assert clinic_says_member == []


def test_non_member_cannot_claim_a_clinic(client, monkeypatch):
    def deny(*args):
        raise NotClinicMemberError()

    monkeypatch.setattr("app.services.doctor.verify_membership", deny)
    response = client.post(URL, json=PROFILE, headers=as_user(7))
    assert response.status_code == 403
    # Nothing was saved.
    assert client.get(f"{URL}/me", headers=as_user(7)).status_code == 404


def test_clinic_service_down_gives_503_not_a_silent_save(client, monkeypatch):
    def down(*args):
        raise ClinicServiceUnavailableError()

    monkeypatch.setattr("app.services.doctor.verify_membership", down)
    assert client.post(URL, json=PROFILE, headers=as_user(7)).status_code == 503
    assert client.get(f"{URL}/me", headers=as_user(7)).status_code == 404


def test_update_only_verifies_when_clinic_changes(client, clinic_says_member):
    client.post(URL, json=PROFILE, headers=as_user(7))
    clinic_says_member.clear()

    same = client.put(f"{URL}/me", json={**PROFILE, "specialty": "ENT"}, headers=as_user(7))
    assert same.status_code == 200 and clinic_says_member == []

    moved = client.put(f"{URL}/me", json={**PROFILE, "clinic_id": 4}, headers=as_user(7))
    assert moved.status_code == 200 and clinic_says_member == [(4, 7)]


def test_public_card_shows_clinic(client, clinic_says_member):
    doctor_id = client.post(URL, json=PROFILE, headers=as_user(7)).json()["id"]
    card = client.get(f"{URL}/{doctor_id}", headers=as_user(50, "patient")).json()
    assert card["clinic_id"] == 3


# --- the real verify_membership, with the HTTP layer faked -------------------

def _fake_http(monkeypatch, status_code=200, payload=None, error=None):
    def fake_get(url, headers, timeout):
        if error:
            raise error
        return httpx.Response(status_code, json=payload or [], request=httpx.Request("GET", url))

    monkeypatch.setattr(clinic_client.httpx, "get", fake_get)


def test_verify_accepts_a_doctor_member(monkeypatch):
    _fake_http(monkeypatch, 200, [{"user_id": 7, "role": "doctor"}])
    clinic_client.verify_membership(3, 7, "tok")  # no exception


def test_verify_rejects_staff_role_and_other_users(monkeypatch):
    _fake_http(monkeypatch, 200, [{"user_id": 7, "role": "staff"}, {"user_id": 9, "role": "doctor"}])
    with pytest.raises(NotClinicMemberError):
        clinic_client.verify_membership(3, 7, "tok")


def test_verify_maps_404_to_not_member(monkeypatch):
    _fake_http(monkeypatch, 404)
    with pytest.raises(NotClinicMemberError):
        clinic_client.verify_membership(3, 7, "tok")


def test_verify_maps_network_error_and_5xx_to_unavailable(monkeypatch):
    _fake_http(monkeypatch, error=httpx.ConnectError("down"))
    with pytest.raises(ClinicServiceUnavailableError):
        clinic_client.verify_membership(3, 7, "tok")
    _fake_http(monkeypatch, 500)
    with pytest.raises(ClinicServiceUnavailableError):
        clinic_client.verify_membership(3, 7, "tok")
