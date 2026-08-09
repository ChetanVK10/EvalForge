from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.cache_service import cache_service

router = APIRouter()

@router.get("/ready", summary="Readiness check")
def readiness_check(db: Session = Depends(get_db)):
    """Database and optional Redis readiness check endpoint."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "redis": "unknown",
            },
        )

    redis_status = "connected" if cache_service.is_connected() else "degraded"

    return {
        "status": "ready",
        "database": "connected",
        "redis": redis_status,
    }
