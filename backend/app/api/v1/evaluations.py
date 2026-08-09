from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.experiment import (
    CreateEvaluationPayload,
    EvaluationProgressResponse,
    ExperimentResponse,
)
from app.services import experiment_service

router = APIRouter()

@router.post(
    "",
    response_model=ExperimentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create & run evaluation experiment",
)
def create_evaluation(
    payload: CreateEvaluationPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create a new evaluation experiment and trigger asynchronous background execution."""
    try:
        return experiment_service.create_evaluation(db, payload, background_tasks)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

@router.get(
    "/{experiment_id}/status",
    response_model=EvaluationProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get evaluation execution progress",
)
def get_evaluation_status(
    experiment_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve progress metrics and status for a running evaluation."""
    progress = experiment_service.get_evaluation_status(db, experiment_id)
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID '{experiment_id}' not found.",
        )
    return progress
