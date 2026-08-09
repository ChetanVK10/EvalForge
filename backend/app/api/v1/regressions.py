from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.regression import CompareRequest, RegressionComparisonResponse
from app.services.regression_service import compare_experiments

router = APIRouter()

@router.post("/compare", response_model=RegressionComparisonResponse)
def compare_experiments_post(
    payload: CompareRequest,
    db: Session = Depends(get_db),
) -> RegressionComparisonResponse:
    """Compare baseline and candidate experiments via POST payload."""
    try:
        return compare_experiments(
            db=db,
            baseline_id=payload.baseline_experiment_id,
            candidate_id=payload.candidate_experiment_id,
        )
    except ValueError as err:
        err_msg = str(err)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err_msg)

@router.get("/compare", response_model=RegressionComparisonResponse)
def compare_experiments_get(
    baseline_id: Optional[str] = Query(None, description="Baseline experiment ID"),
    candidate_id: Optional[str] = Query(None, description="Candidate experiment ID"),
    baseline_experiment_id: Optional[str] = Query(None, description="Alias for baseline experiment ID"),
    candidate_experiment_id: Optional[str] = Query(None, description="Alias for candidate experiment ID"),
    db: Session = Depends(get_db),
) -> RegressionComparisonResponse:
    """Compare baseline and candidate experiments via GET query params."""
    final_baseline_id = baseline_id or baseline_experiment_id
    final_candidate_id = candidate_id or candidate_experiment_id

    if not final_baseline_id or not final_baseline_id.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="baseline_id query parameter is required.",
        )
    if not final_candidate_id or not final_candidate_id.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="candidate_id query parameter is required.",
        )

    try:
        return compare_experiments(
            db=db,
            baseline_id=final_baseline_id.strip(),
            candidate_id=final_candidate_id.strip(),
        )
    except ValueError as err:
        err_msg = str(err)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err_msg)
