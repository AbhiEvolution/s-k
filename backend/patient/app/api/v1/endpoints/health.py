from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def liveness():
  return {"status": "ok"}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
  db.execute(text("SELECT 1"))
  return {"status": "ready"}
