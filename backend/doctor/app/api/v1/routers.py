from fastapi import APIRouter

from app.api.v1.endpoints import doctors

api_router = APIRouter()
api_router.include_router(doctors.router)
