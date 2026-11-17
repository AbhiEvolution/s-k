from datetime import timedelta

from conftest import OTHER_PRIVATE_KEY, as_user, make_token

URL = "/api/v1/doctors"
PROFILE = {"full_name": "Dr. Ada Lovelace", "specialty": "Cardiology"}


def test_requires_authentication(client):
    assert client.get(f"{URL}/me").status_code == 401
    assert client.post(URL, json=PROFILE).status_code == 401


def test_rejects_forged_expired_and_wrong_type_tokens(client):
    bad = [
        make_token(1, "doctor", key=OTHER_PRIVATE_KEY),
        make_token(1, "doctor", expires_in=timedelta(seconds=-5)),
        make_token(1, "doctor", token_type="password_reset"),
        make_token(1, "doctor", audience="other"),
    ]
    for token in bad:
        response = client.get(f"{URL}/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_only_doctor_accounts_can_create_a_profile(client):
    response = client.post(URL, json=PROFILE, headers=as_user(7, "patient"))
    assert response.status_code == 403


def test_create_and_read_own_profile(client):
    headers = as_user(7)
    created = client.post(URL, json=PROFILE, headers=headers)
    assert created.status_code == 201
    assert created.json()["user_id"] == 7  # taken from the token

    me = client.get(f"{URL}/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["full_name"] == "Dr. Ada Lovelace"


def test_owner_cannot_be_chosen_in_request_body(client):
    # An extra user_id in the body is ignored; the token decides the owner.
    response = client.post(URL, json={**PROFILE, "user_id": 999}, headers=as_user(7))
    assert response.json()["user_id"] == 7


def test_second_profile_for_same_account_conflicts(client):
    headers = as_user(7)
    assert client.post(URL, json=PROFILE, headers=headers).status_code == 201
    assert client.post(URL, json=PROFILE, headers=headers).status_code == 409


def test_profile_not_found_before_creation(client):
    assert client.get(f"{URL}/me", headers=as_user(7)).status_code == 404


def test_update_changes_only_my_profile(client):
    client.post(URL, json=PROFILE, headers=as_user(7))
    other = client.post(URL, json={"full_name": "Dr. Other"}, headers=as_user(8)).json()

    updated = client.put(
        f"{URL}/me", json={**PROFILE, "specialty": "Neurology"}, headers=as_user(7)
    )
    assert updated.status_code == 200
    assert updated.json()["specialty"] == "Neurology"

    still_other = client.get(f"{URL}/me", headers=as_user(8)).json()
    assert still_other["specialty"] is None and still_other["id"] == other["id"]


def test_public_view_hides_private_fields(client):
    private = {**PROFILE, "mobile_number": "+15551234567", "address": "1 Main St", "age": 40}
    doctor_id = client.post(URL, json=private, headers=as_user(7)).json()["id"]

    # A patient (different account) can see the public card only.
    public = client.get(f"{URL}/{doctor_id}", headers=as_user(50, "patient"))
    assert public.status_code == 200
    assert public.json() == {
        "id": doctor_id,
        "full_name": PROFILE["full_name"],
        "specialty": "Cardiology",
        "clinic_id": None,
    }


def test_unknown_doctor_is_404(client):
    assert client.get(f"{URL}/12345", headers=as_user(7)).status_code == 404


def test_health_endpoints_need_no_token(client):
    assert client.get("/health").status_code == 200
