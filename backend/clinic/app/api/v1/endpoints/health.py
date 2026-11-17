from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def liveness():
    """Is the process up? Kubernetes liveness probe."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    """Can it reach the database? Kubernetes readiness probe."""
    db.execute(text("SELECT 1"))
    return {"status": "ready"}
