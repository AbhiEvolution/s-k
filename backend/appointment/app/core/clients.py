"""Calls to the other services. The caller's own token is forwarded each time,
so each service applies its normal access rules. We keep NO copy of their data;
appointments store ids only."""
import httpx

from app.core.config import get_settings

# Any member of the clinic may manage its appointments.
CLINIC_ROLES = {"clinic_admin", "doctor", "staff"}


class NotClinicMemberError(Exception):
    pass


class ServiceUnavailableError(Exception):
    pass


def _get(url: str, token: str) -> httpx.Response:
    try:
        return httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=get_settings().service_timeout_seconds,
        )
    except httpx.HTTPError:
        raise ServiceUnavailableError()


def verify_membership(clinic_id: int, user_id: int, token: str) -> None:
    """Raises NotClinicMemberError unless the caller belongs to the clinic."""
    response = _get(
        f"{get_settings().clinic_service_url}/api/v1/clinics/{clinic_id}/members", token
    )
    if response.status_code in (401, 403, 404):
        raise NotClinicMemberError()
    if response.status_code != 200:
        raise ServiceUnavailableError()

    if not any(
        member["user_id"] == user_id and member["role"] in CLINIC_ROLES
        for member in response.json()
    ):
        raise NotClinicMemberError()


def fetch_doctor(doctor_id: int, token: str) -> dict | None:
    """Public doctor card {id, full_name, specialty, clinic_id}, or None."""
    response = _get(f"{get_settings().doctor_service_url}/api/v1/doctors/{doctor_id}", token)
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise ServiceUnavailableError()
    return response.json()


def fetch_my_doctor(token: str) -> dict | None:
    """The caller's own doctor profile, or None if they have none."""
    response = _get(f"{get_settings().doctor_service_url}/api/v1/doctors/me", token)
    if response.status_code in (403, 404):
        return None
    if response.status_code != 200:
        raise ServiceUnavailableError()
    return response.json()


def fetch_patient(patient_id: int, token: str) -> dict | None:
    """A patient record, or None if it does not exist or the caller cannot see it."""
    response = _get(f"{get_settings().patient_service_url}/api/v1/patients/{patient_id}", token)
    if response.status_code in (403, 404):
        return None
    if response.status_code != 200:
        raise ServiceUnavailableError()
    return response.json()
