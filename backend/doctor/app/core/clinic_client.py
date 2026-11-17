import httpx

from app.core.config import get_settings

# Roles inside a clinic that may be linked to a doctor profile.
ALLOWED_CLINIC_ROLES = {"doctor", "clinic_admin"}


class NotClinicMemberError(Exception):
    pass


class ClinicServiceUnavailableError(Exception):
    pass


# Any member of a clinic may see its list of doctors.
ANY_CLINIC_ROLE = {"clinic_admin", "doctor", "staff"}


def verify_membership(
    clinic_id: int, user_id: int, token: str, allowed_roles: set[str] = ALLOWED_CLINIC_ROLES
) -> None:
    """Ask the clinic service: is this user really a doctor in this clinic?

    We forward the caller's own token. The clinic service decides with its
    normal rules (404 if you are not a member, so we learn nothing extra).
    Raises NotClinicMemberError or ClinicServiceUnavailableError.
    """
    settings = get_settings()
    try:
        response = httpx.get(
            f"{settings.clinic_service_url}/api/v1/clinics/{clinic_id}/members",
            headers={"Authorization": f"Bearer {token}"},
            timeout=settings.clinic_service_timeout_seconds,
        )
    except httpx.HTTPError:
        raise ClinicServiceUnavailableError()

    if response.status_code in (401, 403, 404):
        raise NotClinicMemberError()
    if response.status_code != 200:
        raise ClinicServiceUnavailableError()

    is_doctor_here = any(
        member["user_id"] == user_id and member["role"] in allowed_roles
        for member in response.json()
    )
    if not is_doctor_here:
        raise NotClinicMemberError()
