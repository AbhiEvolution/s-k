from fastapi import APIRouter

from app.api.v1.endpoints import doctors, auth

api_router = APIRouter()

api_router.include_router(doctors.router)
api_router.include_router(auth.router)
