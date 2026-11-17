URL = "/api/v1/auth/users"


def account(client, email, role):
    user = client.post("/api/v1/auth/register", json={"email": email, "password": "s3cret-pass", "role": role}).json()
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "s3cret-pass"}).json()["access_token"]
    return user["id"], {"Authorization": f"Bearer {token}"}


def test_admin_can_look_up_by_email_case_insensitively(client):
    _, admin = account(client, "root@example.com", "admin")
    doctor_id, _ = account(client, "dr@example.com", "doctor")
    found = client.get(f"{URL}?email=DR@Example.com", headers=admin).json()
    assert found == [{"id": doctor_id, "email": "dr@example.com", "role": "doctor"}]


def test_lookup_by_ids_and_unknowns(client):
    _, admin = account(client, "root@example.com", "admin")
    a, _ = account(client, "a@example.com", "doctor")
    b, _ = account(client, "b@example.com", "patient")
    found = client.get(f"{URL}?ids={a},{b},9999", headers=admin).json()
    assert [u["id"] for u in found] == [a, b]
    assert client.get(f"{URL}?email=nobody@example.com", headers=admin).json() == []


def test_response_never_contains_password_material(client):
    _, admin = account(client, "root@example.com", "admin")
    account(client, "dr@example.com", "doctor")
    assert "password" not in client.get(f"{URL}?email=dr@example.com", headers=admin).text


def test_non_admins_are_refused(client):
    _, doctor = account(client, "dr@example.com", "doctor")
    assert client.get(f"{URL}?email=dr@example.com", headers=doctor).status_code == 403


def test_authentication_is_required_and_forgeries_fail(client):
    assert client.get(f"{URL}?email=x@example.com").status_code == 401
    assert client.get(f"{URL}?email=x@example.com", headers={"Authorization": "Bearer not.a.jwt"}).status_code == 401


def test_it_is_a_lookup_not_a_listing(client):
    _, admin = account(client, "root@example.com", "admin")
    assert client.get(URL, headers=admin).status_code == 422                          # nothing given
    assert client.get(f"{URL}?email=a@example.com&ids=1", headers=admin).status_code == 422  # both given
    assert client.get(f"{URL}?ids=abc", headers=admin).status_code == 422
    assert client.get(f"{URL}?ids={','.join(map(str, range(101)))}", headers=admin).status_code == 422
