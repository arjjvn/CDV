import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from Backend.database_dependency import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
def check_health(db: Session = Depends(get_db)):
    """Health check endpoint checking DB, DL model, ML model, and API status."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Health check DB error: %s", exc)
        db_status = f"unhealthy: {str(exc)}"

    dl_status = "ready"
    try:
        from Backend.dl_model import load_dl_model
        load_dl_model()
    except Exception as exc:
        dl_status = f"unavailable: {str(exc)}"

    ml_status = "ready"
    try:
        from Backend.ml_model import load_volunteer_model
        load_volunteer_model()
    except Exception as exc:
        ml_status = f"unavailable: {str(exc)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "Community Disaster Volunteer Hub (CDVH)",
        "version": "1.0.0",
        "database": db_status,
        "dl_urgency_model": dl_status,
        "ml_volunteer_matcher": ml_status,
    }
