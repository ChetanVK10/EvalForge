from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.settings import (
    EvaluationDefaults,
    RegressionThresholds,
    SettingsResponse,
)
from app.services import settings_service

router = APIRouter()

@router.get(
    "",
    response_model=SettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workspace settings",
)
def get_settings(db: Session = Depends(get_db)):
    """Retrieve workspace evaluation defaults, regression thresholds, and provider status."""
    return settings_service.get_settings(db)

@router.get(
    "/regression",
    response_model=RegressionThresholds,
    status_code=status.HTTP_200_OK,
    summary="Get regression thresholds",
)
def get_regression_thresholds(db: Session = Depends(get_db)):
    """Retrieve workspace regression threshold rules."""
    settings_obj = settings_service.get_settings(db)
    return settings_obj.regression_thresholds

@router.put(
    "/regression",
    response_model=RegressionThresholds,
    status_code=status.HTTP_200_OK,
    summary="Update regression thresholds",
)
def update_regression_thresholds(
    payload: RegressionThresholds,
    db: Session = Depends(get_db),
):
    """Update workspace regression threshold rules."""
    return settings_service.update_regression_thresholds(db, payload)

@router.put(
    "/evaluation",
    response_model=EvaluationDefaults,
    status_code=status.HTTP_200_OK,
    summary="Update evaluation defaults",
)
def update_evaluation_defaults(
    payload: EvaluationDefaults,
    db: Session = Depends(get_db),
):
    """Update workspace evaluation defaults."""
    return settings_service.update_evaluation_defaults(db, payload)
