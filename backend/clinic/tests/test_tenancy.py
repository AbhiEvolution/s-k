from conftest import as_user

ADMIN = as_user(1, "admin")


def make_clinic(client, headers=ADMIN, name="Sunrise Clinic"):
    response = client.post("/api/v1/clinics", json={"name": name}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_requires_authentication(client):
    assert client.get("/api/v1/clinics").status_code == 401


def test_only_admin_can_create_clinic(client):
    response = client.post(
        "/api/v1/clinics", json={"name": "Nope Clinic"}, headers=as_user(2, "doctor")
    )
    assert response.status_code == 403


def test_creator_becomes_clinic_admin(client):
    clinic_id = make_clinic(client)
    members = client.get(f"/api/v1/clinics/{clinic_id}/members", headers=ADMIN).json()
    assert members == [{"user_id": 1, "role": "clinic_admin"}]


def test_outsider_cannot_see_other_clinic(client):
    clinic_a = make_clinic(client)
    outsider = as_user(99, "doctor")

    # 404, not 403: the clinic's existence is not revealed.
    assert client.get(f"/api/v1/clinics/{clinic_a}", headers=outsider).status_code == 404
    assert client.get("/api/v1/clinics", headers=outsider).json() == []


def test_clinic_a_admin_cannot_touch_clinic_b(client):
    admin_a, admin_b = as_user(1, "admin"), as_user(2, "admin")
    clinic_a = make_clinic(client, admin_a, "Clinic A")
    clinic_b = make_clinic(client, admin_b, "Clinic B")

    assert client.get(f"/api/v1/clinics/{clinic_b}", headers=admin_a).status_code == 404
    assert (
        client.put(f"/api/v1/clinics/{clinic_b}", json={"name": "Hacked"}, headers=admin_a).status_code
        == 404
    )
    assert client.get(f"/api/v1/clinics/{clinic_a}", headers=admin_a).status_code == 200


def test_member_with_low_role_is_forbidden_to_manage(client):
    clinic_id = make_clinic(client)
    client.post(
        f"/api/v1/clinics/{clinic_id}/members",
        json={"user_id": 5, "role": "staff"},
        headers=ADMIN,
    )
    staff = as_user(5, "patient")  # account role is irrelevant inside a clinic

    assert client.get(f"/api/v1/clinics/{clinic_id}", headers=staff).status_code == 200
    forbidden = client.put(
        f"/api/v1/clinics/{clinic_id}", json={"name": "Renamed"}, headers=staff
    )
    assert forbidden.status_code == 403


def test_duplicate_member_is_conflict(client):
    clinic_id = make_clinic(client)
    body = {"user_id": 5, "role": "doctor"}
    url = f"/api/v1/clinics/{clinic_id}/members"
    assert client.post(url, json=body, headers=ADMIN).status_code == 201
    assert client.post(url, json=body, headers=ADMIN).status_code == 409


def test_cannot_remove_last_admin(client):
    clinic_id = make_clinic(client)
    response = client.delete(f"/api/v1/clinics/{clinic_id}/members/1", headers=ADMIN)
    assert response.status_code == 409
