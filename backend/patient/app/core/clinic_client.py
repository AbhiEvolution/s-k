import os

import httpx

CLINIC_SERVICE_URL = os.getenv("CLINIC_SERVICE_URL", "http://localhost:8002")
CLINIC_SERVICE_TIMEOUT = float(os.getenv("CLINIC_SERVICE_TIMEOUT_SECONDS", "3"))

# Any member of the clinic may work with its patients.
CLINIC_ROLES = {"clinic_admin", "doctor", "staff"}


class NotClinicMemberError(Exception):
  pass


class ClinicServiceUnavailableError(Exception):
  pass


def verify_membership(clinic_id: int, user_id: int, token: str) -> None:
  """Ask the clinic service whether this user belongs to the clinic.

  The caller's own token is forwarded, and the clinic service applies its
  normal rules. Raises NotClinicMemberError or ClinicServiceUnavailableError.
  """
  try:
    response = httpx.get(
      f"{CLINIC_SERVICE_URL}/api/v1/clinics/{clinic_id}/members",
      headers={"Authorization": f"Bearer {token}"},
      timeout=CLINIC_SERVICE_TIMEOUT,
    )
  except httpx.HTTPError:
    raise ClinicServiceUnavailableError()

  if response.status_code in (401, 403, 404):
    raise NotClinicMemberError()
  if response.status_code != 200:
    raise ClinicServiceUnavailableError()

  if not any(
    member["user_id"] == user_id and member["role"] in CLINIC_ROLES
    for member in response.json()
  ):
    raise NotClinicMemberError()
