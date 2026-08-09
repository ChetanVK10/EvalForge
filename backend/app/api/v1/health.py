from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", summary="Health check")
def health_check():
    """Application health status endpoint. Independent of database connectivity."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": "0.1.0",
    }
