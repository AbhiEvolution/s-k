from app.core.config import get_settings

CREDS = {"email": "dr@example.com", "password": "s3cret-pass"}


def login(client) -> dict:
    client.post("/api/v1/auth/register", json={**CREDS, "role": "doctor"})
    response = client.post("/api/v1/auth/login", json=CREDS)
    assert response.status_code == 200
    return response.json()


def refresh(client, token: str):
    return client.post("/api/v1/auth/refresh", json={"refresh_token": token})


def test_login_returns_both_tokens(client):
    tokens = login(client)
    assert tokens["access_token"] and tokens["refresh_token"]
    assert tokens["access_token"] != tokens["refresh_token"]


def test_refresh_rotates_to_a_new_pair(client):
    first = login(client)
    response = refresh(client, first["refresh_token"])
    assert response.status_code == 200
    second = response.json()
    assert second["refresh_token"] != first["refresh_token"]
    assert second["access_token"]


def test_new_refresh_token_works_again(client):
    token = login(client)["refresh_token"]
    for _ in range(3):  # a chain of rotations
        response = refresh(client, token)
        assert response.status_code == 200
        token = response.json()["refresh_token"]


def test_old_token_is_single_use(client):
    first = login(client)["refresh_token"]
    assert refresh(client, first).status_code == 200
    assert refresh(client, first).status_code == 401


def test_reuse_revokes_the_whole_session(client):
    # Attacker replays a stolen, already-rotated token. The legitimate
    # client's NEWEST token must die too, forcing a fresh login.
    stolen = login(client)["refresh_token"]
    newest = refresh(client, stolen).json()["refresh_token"]

    assert refresh(client, stolen).status_code == 401  # reuse detected
    assert refresh(client, newest).status_code == 401  # family burned


def test_other_sessions_survive_reuse_detection(client):
    first_session = login(client)["refresh_token"]
    second_session = client.post("/api/v1/auth/login", json=CREDS).json()["refresh_token"]

    refresh(client, first_session)
    refresh(client, first_session)  # reuse: burns only the first session

    assert refresh(client, second_session).status_code == 200


def test_unknown_token_is_rejected(client):
    assert refresh(client, "made-up-token").status_code == 401


def test_logout_revokes_the_session(client):
    token = login(client)["refresh_token"]
    assert client.post("/api/v1/auth/logout", json={"refresh_token": token}).status_code == 204
    assert refresh(client, token).status_code == 401


def test_logout_is_idempotent_and_does_not_leak(client):
    token = login(client)["refresh_token"]
    for value in (token, token, "made-up-token"):
        response = client.post("/api/v1/auth/logout", json={"refresh_token": value})
        assert response.status_code == 204


def test_logout_kills_rotated_descendants(client):
    first = login(client)["refresh_token"]
    newest = refresh(client, first).json()["refresh_token"]
    client.post("/api/v1/auth/logout", json={"refresh_token": newest})
    assert refresh(client, newest).status_code == 401


def test_expired_refresh_token_is_rejected(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "refresh_token_expire_days", -1)
    token = login(client)["refresh_token"]  # already expired when issued
    assert refresh(client, token).status_code == 401
