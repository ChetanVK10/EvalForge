from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.dataset import (
    DatasetCreate,
    DatasetDetailResponse,
    DatasetResponse,
    DatasetUpdate,
    TestCaseCreate,
    TestCaseResponse,
)
from app.services import dataset_service

router = APIRouter()

class ImportCasesPayload(BaseModel):
    cases: List[TestCaseCreate]

@router.post(
    "",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create dataset",
)
def create_dataset(
    payload: DatasetCreate,
    db: Session = Depends(get_db),
):
    """Create a new evaluation dataset, optionally including initial test cases."""
    return dataset_service.create_dataset(db, payload)

@router.put(
    "/{dataset_id}",
    response_model=DatasetResponse,
    status_code=status.HTTP_200_OK,
    summary="Update dataset metadata",
)
def update_dataset(
    dataset_id: str,
    payload: DatasetUpdate,
    db: Session = Depends(get_db),
):
    """Update dataset name and description."""
    result = dataset_service.update_dataset(db, dataset_id, payload)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return result

@router.get(
    "",
    response_model=List[DatasetResponse],
    status_code=status.HTTP_200_OK,
    summary="List datasets",
)
def list_datasets(
    db: Session = Depends(get_db),
):
    """List all evaluation datasets ordered by creation date (newest first)."""
    return dataset_service.list_datasets(db)

@router.get(
    "/{dataset_id}",
    response_model=DatasetDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dataset detail",
)
def get_dataset_detail(
    dataset_id: str,
    search: Optional[str] = Query(None, description="Filter cases by input or expected output"),
    category: Optional[str] = Query(None, description="Filter cases by category"),
    db: Session = Depends(get_db),
):
    """Get dataset detail and test cases with optional search and category filters."""
    result = dataset_service.get_dataset_detail(db, dataset_id, search=search, category=category)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return result

@router.post(
    "/{dataset_id}/cases",
    response_model=TestCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add test case to dataset",
)
def add_test_case(
    dataset_id: str,
    payload: TestCaseCreate,
    db: Session = Depends(get_db),
):
    """Add a new test case to an existing dataset."""
    result = dataset_service.add_test_case(db, dataset_id, payload)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return result

@router.put(
    "/{dataset_id}/cases/{case_id}",
    response_model=TestCaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update test case in dataset",
)
def update_test_case(
    dataset_id: str,
    case_id: str,
    payload: TestCaseCreate,
    db: Session = Depends(get_db),
):
    """Update an existing test case in a dataset."""
    result = dataset_service.update_test_case(db, dataset_id, case_id, payload)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case '{case_id}' in dataset '{dataset_id}' not found.",
        )
    return result

@router.delete(
    "/{dataset_id}/cases/{case_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete test case from dataset",
)
def delete_test_case(
    dataset_id: str,
    case_id: str,
    db: Session = Depends(get_db),
):
    """Delete a test case from a dataset."""
    success = dataset_service.delete_test_case(db, dataset_id, case_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case '{case_id}' in dataset '{dataset_id}' not found.",
        )
    return {"id": case_id}

@router.post(
    "/{dataset_id}/import",
    status_code=status.HTTP_200_OK,
    summary="Import multiple test cases",
)
def import_test_cases(
    dataset_id: str,
    payload: ImportCasesPayload,
    db: Session = Depends(get_db),
):
    """Bulk import test cases into an existing dataset."""
    count = dataset_service.import_test_cases(db, dataset_id, payload.cases)
    if count is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return {"imported": count}

@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete dataset",
)
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """Delete a dataset and all associated test cases if unreferenced by experiments."""
    try:
        dataset_service.delete_dataset(db, dataset_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
