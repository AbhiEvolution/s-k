from datetime import timedelta

import pytest
from conftest import OTHER_PRIVATE_KEY, as_user, make_token

from app.core.clinic_client import ClinicServiceUnavailableError, NotClinicMemberError

URL = "/api/v1/patients"
PATIENT = {
  "clinic_id": 1,
  "name": "Grace Hopper",
  "age": 45,
  "address": "1 Navy Way",
  "mobile_number": "+15551234567",
  "gender": "female",
}

# Pretend clinic memberships: {clinic_id: {user_ids}}. Stands in for the clinic service.
MEMBERS = {1: {10, 11}, 2: {20}}


@pytest.fixture(autouse=True)
def fake_clinic_service(monkeypatch):
  def fake(clinic_id, user_id, token):
    if user_id not in MEMBERS.get(clinic_id, set()):
      raise NotClinicMemberError()

  monkeypatch.setattr("app.services.patient.verify_membership", fake)


def create(client, headers, **overrides):
  response = client.post(URL, json={**PATIENT, **overrides}, headers=headers)
  assert response.status_code == 201, response.text
  return response.json()["id"]


def test_requires_authentication(client):
  assert client.get(f"{URL}?clinic_id=1").status_code == 401


def test_rejects_forged_expired_and_wrong_type_tokens(client):
  bad = [
    make_token(10, "doctor", key=OTHER_PRIVATE_KEY),
    make_token(10, "doctor", expires_in=timedelta(seconds=-5)),
    make_token(10, "doctor", token_type="password_reset"),
    make_token(10, "doctor", audience="other"),
  ]
  for token in bad:
    response = client.get(f"{URL}?clinic_id=1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_member_can_create_and_read(client):
  patient_id = create(client, as_user(10))
  response = client.get(f"{URL}/{patient_id}", headers=as_user(10))
  assert response.status_code == 200
  assert response.json()["clinic_id"] == 1
  assert response.json()["created_by_user_id"] == 10


def test_colleague_in_same_clinic_can_access(client):
  # The point of clinic ownership: not just the creating doctor.
  patient_id = create(client, as_user(10))
  assert client.get(f"{URL}/{patient_id}", headers=as_user(11, "doctor")).status_code == 200
  assert client.put(f"{URL}/{patient_id}", json={k: v for k, v in PATIENT.items() if k != "clinic_id"},
                    headers=as_user(11)).status_code == 200


def test_outsider_cannot_read_edit_or_delete(client):
  patient_id = create(client, as_user(10))
  outsider = as_user(20)  # member of clinic 2 only
  body = {k: v for k, v in PATIENT.items() if k != "clinic_id"}

  assert client.get(f"{URL}/{patient_id}", headers=outsider).status_code == 404
  assert client.put(f"{URL}/{patient_id}", json=body, headers=outsider).status_code == 404
  assert client.delete(f"{URL}/{patient_id}", headers=outsider).status_code == 404
  assert client.get(f"{URL}/{patient_id}", headers=as_user(10)).status_code == 200


def test_cannot_create_in_a_clinic_you_do_not_belong_to(client):
  assert client.post(URL, json={**PATIENT, "clinic_id": 2}, headers=as_user(10)).status_code == 403


def test_list_is_scoped_to_one_clinic_and_checks_membership(client):
  create(client, as_user(10), name="Clinic One A")
  create(client, as_user(20), name="Clinic Two A", clinic_id=2)

  names = {p["name"] for p in client.get(f"{URL}?clinic_id=1", headers=as_user(10)).json()}
  assert names == {"Clinic One A"}
  assert client.get(f"{URL}?clinic_id=2", headers=as_user(10)).status_code == 403


def test_put_cannot_move_patient_to_another_clinic(client):
  patient_id = create(client, as_user(10))
  body = {k: v for k, v in PATIENT.items() if k != "clinic_id"}
  client.put(f"{URL}/{patient_id}", json={**body, "clinic_id": 2}, headers=as_user(10))
  assert client.get(f"{URL}/{patient_id}", headers=as_user(10)).json()["clinic_id"] == 1


def test_clinic_service_down_gives_503(client, monkeypatch):
  def down(*args):
    raise ClinicServiceUnavailableError()

  monkeypatch.setattr("app.services.patient.verify_membership", down)
  assert client.get(f"{URL}?clinic_id=1", headers=as_user(10)).status_code == 503


def test_pagination_limit_is_enforced(client):
  assert client.get(f"{URL}?clinic_id=1&limit=1000", headers=as_user(10)).status_code == 422


def test_health_needs_no_token(client):
  assert client.get("/health").status_code == 200
