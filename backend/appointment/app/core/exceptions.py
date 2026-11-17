from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppointmentNotFoundError(Exception):
    """Also used for "exists but you may not see it": outsiders learn nothing."""


class NotFoundError(Exception):
    """A referenced doctor or patient does not exist (or is not visible to the caller)."""


class InvalidRequestError(Exception):
    """The request is well-formed but breaks a business rule -> 422."""


class ConflictError(Exception):
    """The request conflicts with current state -> 409."""


class SlotUnavailableError(ConflictError):
    """Someone (or something) already holds that time -> 409."""


def register_exception_handlers(app: FastAPI) -> None:
    from app.core.clients import NotClinicMemberError, ServiceUnavailableError

    def handler(status_code: int, message: str | None = None):
        async def _handle(request: Request, exc: Exception) -> JSONResponse:
            return JSONResponse(status_code=status_code, content={"detail": message or str(exc)})

        return _handle

    app.add_exception_handler(AppointmentNotFoundError, handler(404, "Appointment not found"))
    app.add_exception_handler(NotFoundError, handler(404))
    app.add_exception_handler(InvalidRequestError, handler(422))
    app.add_exception_handler(ConflictError, handler(409))  # also covers SlotUnavailableError
    app.add_exception_handler(NotClinicMemberError, handler(403, "You are not a member of that clinic"))
    app.add_exception_handler(ServiceUnavailableError, handler(503, "A required service is unavailable"))
