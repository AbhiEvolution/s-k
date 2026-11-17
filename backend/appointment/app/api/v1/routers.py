from fastapi import APIRouter

from app.api.v1.endpoints import appointments, availability

api_router = APIRouter()
# availability first: its fixed paths (/availability, /slots) must be matched
# before the /{appointment_id} route.
api_router.include_router(availability.router)
api_router.include_router(appointments.router)
