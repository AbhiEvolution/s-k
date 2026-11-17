import jwt

CREDS = {"email": "Dr.Who@Example.com", "password": "s3cret-pass", "role": "doctor"}


def register(client, **overrides):
    return client.post("/api/v1/auth/register", json={**CREDS, **overrides})


def test_register_normalizes_email_and_hides_password(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "dr.who@example.com"
    assert "password" not in body and "password_hash" not in body


def test_duplicate_email_conflicts_regardless_of_case(client):
    assert register(client).status_code == 201
    assert register(client, email="DR.WHO@example.com").status_code == 409


def test_login_wrong_password_and_unknown_email_look_identical(client):
    register(client)
    wrong = client.post("/api/v1/auth/login", json={"email": CREDS["email"], "password": "nope-nope"})
    unknown = client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "nope-nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_login_returns_token_verifiable_with_published_public_key(client):
    register(client)
    login = client.post("/api/v1/auth/login", json={"email": CREDS["email"], "password": CREDS["password"]})
    assert login.status_code == 200
    token = login.json()["access_token"]

    # Do what another service does: fetch the JWKS and verify, no private key.
    jwks = client.get("/.well-known/jwks.json").json()
    header = jwt.get_unverified_header(token)
    jwk = next(k for k in jwks["keys"] if k["kid"] == header["kid"])
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)

    claims = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience="clinic-platform",
        issuer="auth-service",
    )
    assert claims["role"] == "doctor"
    assert claims["type"] == "access"
    assert claims["sub"].isdigit()
    assert "jti" in claims


def test_jwks_exposes_no_private_material(client):
    key = client.get("/.well-known/jwks.json").json()["keys"][0]
    assert not {"d", "p", "q", "dp", "dq", "qi"} & key.keys()
