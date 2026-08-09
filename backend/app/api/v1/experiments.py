from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.experiment import ExperimentDetailResponse, ExperimentResponse
from app.services import experiment_service

router = APIRouter()

@router.get(
    "",
    response_model=List[ExperimentResponse],
    status_code=status.HTTP_200_OK,
    summary="List evaluation experiments",
)
def list_experiments(
    search: Optional[str] = Query(None, description="Search term for name, ID, dataset, prompt, model"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    provider: Optional[str] = Query(None, description="Filter by provider (groq, gemini)"),
    model: Optional[str] = Query(None, description="Filter by model identifier"),
    prompt_version: Optional[int] = Query(None, description="Filter by prompt version"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by quality status (PASS, WARNING, FAIL)"),
    since: Optional[str] = Query(None, description="Filter experiments created after ISO date"),
    date_param: Optional[str] = Query(None, alias="date", description="Filter experiments by exact calendar date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """List all evaluation experiments ordered by creation date with optional filtering."""
    try:
        return experiment_service.list_experiments(
            db,
            search=search,
            dataset_id=dataset_id,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            status_filter=status_filter,
            since=since,
            date_str=date_param,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/{experiment_id}",
    response_model=ExperimentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get experiment detail",
)
def get_experiment_detail(
    experiment_id: str,
    category: Optional[str] = Query(None, description="Filter test cases by category"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter test cases by execution status"),
    search: Optional[str] = Query(None, description="Filter test cases by search query"),
    db: Session = Depends(get_db),
):
    """Retrieve detailed experiment results, category breakdowns, and test case telemetry."""
    detail = experiment_service.get_experiment_detail(
        db,
        experiment_id,
        category=category,
        status_filter=status_filter,
        search=search,
    )
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID '{experiment_id}' not found.",
        )
    return detail

@router.delete(
    "/{experiment_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete experiment",
)
def delete_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
):
    """Delete an experiment and its associated test case results and evaluation scores."""
    success = experiment_service.delete_experiment(db, experiment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID '{experiment_id}' not found.",
        )
    return {"id": experiment_id}
