"""Seed a local stack with a usable admin, clinic and doctor. Safe to re-run.

    python scripts/dev_bootstrap.py
    python scripts/dev_bootstrap.py --doctor-email me@example.com --doctor-password my-pass-123

Needs only the Python standard library, and the stack running (docker compose up).
FOR LOCAL DEVELOPMENT ONLY: it creates an admin account with a known password.
"""
import argparse
import base64
import json
import sys
import urllib.error
import urllib.request


def call(method, url, body=None, token=None):
    """Returns (status_code, parsed_json_or_None). Never raises on HTTP errors."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read()
            return response.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            return error.code, json.loads(raw)
        except ValueError:
            return error.code, {"detail": raw.decode(errors="replace")}
    except urllib.error.URLError as error:
        sys.exit(f"Cannot reach {url}: {error.reason}\nIs the stack running? (docker compose up -d)")


def user_id_from_token(token):
    """Read `sub` from the JWT payload. No verification needed: we just got it from auth."""
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return int(json.loads(base64.urlsafe_b64decode(payload))["sub"])


def ensure_account(api, email, password, role):
    status, body = call("POST", f"{api}/auth/register", {"email": email, "password": password, "role": role})
    if status == 201:
        print(f"  created {role} account {email}")
    elif status == 409:
        print(f"  {role} account {email} already exists")
    else:
        sys.exit(f"Registering {email} failed ({status}): {body}")

    status, body = call("POST", f"{api}/auth/login", {"email": email, "password": password})
    if status != 200:
        sys.exit(f"Logging in as {email} failed ({status}): {body}\n"
                 "The account exists with a different password; pass the right one or reset the stack "
                 "(docker compose down -v).")
    return body["access_token"]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api", default="http://localhost/api/v1", help="gateway base URL")
    parser.add_argument("--admin-email", default="admin@example.com")
    parser.add_argument("--admin-password", default="admin-pass-123")
    parser.add_argument("--doctor-email", default="doctor@example.com")
    parser.add_argument("--doctor-password", default="doctor-pass-123")
    parser.add_argument("--clinic-name", default="Demo Clinic")
    args = parser.parse_args()
    api = args.api.rstrip("/")

    print("1. Admin account")
    admin_token = ensure_account(api, args.admin_email, args.admin_password, "admin")

    print("2. Clinic")
    status, clinics = call("GET", f"{api}/clinics", token=admin_token)
    existing = next((c for c in clinics or [] if c["name"] == args.clinic_name), None)
    if existing:
        clinic_id = existing["id"]
        print(f"  clinic '{args.clinic_name}' already exists (id {clinic_id})")
    else:
        status, body = call("POST", f"{api}/clinics", {"name": args.clinic_name}, admin_token)
        if status != 201:
            sys.exit(f"Creating the clinic failed ({status}): {body}")
        clinic_id = body["id"]
        print(f"  created clinic '{args.clinic_name}' (id {clinic_id})")

    print("3. Doctor account")
    doctor_token = ensure_account(api, args.doctor_email, args.doctor_password, "doctor")
    doctor_user_id = user_id_from_token(doctor_token)

    print("4. Add the doctor to the clinic")
    status, body = call(
        "POST", f"{api}/clinics/{clinic_id}/members",
        {"user_id": doctor_user_id, "role": "doctor"}, admin_token,
    )
    if status == 201:
        print(f"  added user {doctor_user_id} as doctor")
    elif status == 409:
        print(f"  user {doctor_user_id} is already a member")
    else:
        sys.exit(f"Adding the member failed ({status}): {body}")

    print("5. Doctor profile")
    profile = {"full_name": "Dr. Demo Doctor", "specialty": "General Practice", "clinic_id": clinic_id}
    status, body = call("POST", f"{api}/doctors", profile, doctor_token)
    if status == 201:
        print("  created profile linked to the clinic")
    elif status == 409:
        print("  profile already exists")
    else:
        sys.exit(f"Creating the doctor profile failed ({status}): {body}")

    print(f"""
Done. Open http://localhost/login and sign in as the doctor:
  email:    {args.doctor_email}
  password: {args.doctor_password}
Clinic '{args.clinic_name}' (id {clinic_id}) is ready; add patients from the dashboard.
Admin (API only): {args.admin_email} / {args.admin_password}""")


if __name__ == "__main__":
    main()
