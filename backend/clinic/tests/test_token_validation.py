from datetime import timedelta

import jwt
from conftest import OTHER_PRIVATE_KEY, make_token

URL = "/api/v1/clinics"


def call(client, token: str):
    return client.get(URL, headers={"Authorization": f"Bearer {token}"})


def test_valid_token_is_accepted(client):
    assert call(client, make_token(1)).status_code == 200


def test_missing_token_is_rejected(client):
    assert client.get(URL).status_code == 401


def test_expired_token_is_rejected(client):
    assert call(client, make_token(1, expires_in=timedelta(seconds=-10))).status_code == 401


def test_token_signed_with_another_key_is_rejected(client):
    # This is the forgery the RS256 design prevents.
    forged = make_token(1, "admin", key=OTHER_PRIVATE_KEY)
    assert call(client, forged).status_code == 401


def test_wrong_audience_is_rejected(client):
    assert call(client, make_token(1, audience="some-other-system")).status_code == 401


def test_wrong_issuer_is_rejected(client):
    assert call(client, make_token(1, issuer="evil-issuer")).status_code == 401


def test_non_access_token_type_is_rejected(client):
    assert call(client, make_token(1, token_type="password_reset")).status_code == 401


def test_unsigned_alg_none_token_is_rejected(client):
    unsigned = jwt.encode({"sub": "1", "role": "admin"}, key=None, algorithm="none")
    assert call(client, unsigned).status_code == 401


def test_garbage_token_is_rejected(client):
    assert call(client, "not-a-jwt").status_code == 401
