from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session, joinedload

from app.models.dataset import Dataset, TestCase
from app.models.experiment import Experiment
from app.schemas.dataset import (
    DatasetCreate,
    DatasetDetailResponse,
    DatasetResponse,
    DatasetUpdate,
    TestCaseCreate,
    TestCaseResponse,
)

def _build_dataset_response(dataset: Dataset) -> DatasetResponse:
    categories = sorted(list({c.category for c in dataset.cases if c.category}))
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description or "",
        case_count=len(dataset.cases),
        categories=categories,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )

def create_dataset(db: Session, payload: DatasetCreate) -> DatasetResponse:
    dataset = Dataset(
        name=payload.name,
        description=payload.description or "",
    )
    db.add(dataset)
    db.flush()  # Assigns dataset.id

    for case_data in payload.cases:
        test_case = TestCase(
            dataset_id=dataset.id,
            input=case_data.input,
            expected_output=case_data.expected_output,
            category=case_data.category,
            metadata_json=case_data.metadata or {},
        )
        db.add(test_case)

    db.commit()
    db.refresh(dataset)
    return _build_dataset_response(dataset)

def list_datasets(db: Session) -> List[DatasetResponse]:
    stmt = (
        select(Dataset)
        .options(joinedload(Dataset.cases))
        .order_by(Dataset.created_at.desc())
    )
    datasets = db.scalars(stmt).unique().all()
    return [_build_dataset_response(d) for d in datasets]

def get_dataset_detail(
    db: Session,
    dataset_id: str,
    search: Optional[str] = None,
    category: Optional[str] = None,
) -> Optional[DatasetDetailResponse]:
    stmt = select(Dataset).options(joinedload(Dataset.cases)).where(Dataset.id == dataset_id)
    dataset = db.scalars(stmt).first()
    if not dataset:
        return None

    all_cases = dataset.cases
    categories = sorted(list({c.category for c in all_cases if c.category}))
    case_count = len(all_cases)

    # Filter cases if search or category parameters are provided
    filtered_cases = all_cases
    if search:
        term = search.strip().lower()
        filtered_cases = [
            c for c in filtered_cases
            if term in (c.input or "").lower() or term in (c.expected_output or "").lower()
        ]
    if category:
        cat = category.strip().lower()
        filtered_cases = [c for c in filtered_cases if (c.category or "").lower() == cat]

    case_responses = [
        TestCaseResponse(
            id=c.id,
            input=c.input or "",
            expected_output=c.expected_output or "",
            category=c.category or "general",
            metadata=c.metadata_json or {},
        )
        for c in filtered_cases
    ]

    return DatasetDetailResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description or "",
        case_count=case_count,
        categories=categories,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        cases=case_responses,
    )

def add_test_case(
    db: Session,
    dataset_id: str,
    payload: TestCaseCreate,
) -> Optional[TestCaseResponse]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        return None

    test_case = TestCase(
        dataset_id=dataset_id,
        input=payload.input,
        expected_output=payload.expected_output,
        category=payload.category,
        metadata_json=payload.metadata or {},
    )
    db.add(test_case)
    dataset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(test_case)

    return TestCaseResponse(
        id=test_case.id,
        input=test_case.input,
        expected_output=test_case.expected_output,
        category=test_case.category,
        metadata=test_case.metadata_json or {},
    )

def update_test_case(
    db: Session,
    dataset_id: str,
    case_id: str,
    payload: TestCaseCreate,
) -> Optional[TestCaseResponse]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        return None

    test_case = db.get(TestCase, case_id)
    if not test_case or test_case.dataset_id != dataset_id:
        return None

    test_case.input = payload.input
    test_case.expected_output = payload.expected_output
    test_case.category = payload.category
    test_case.metadata_json = payload.metadata or {}
    dataset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(test_case)

    return TestCaseResponse(
        id=test_case.id,
        input=test_case.input,
        expected_output=test_case.expected_output,
        category=test_case.category,
        metadata=test_case.metadata_json or {},
    )

def delete_test_case(db: Session, dataset_id: str, case_id: str) -> bool:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        return False
    test_case = db.get(TestCase, case_id)
    if not test_case or test_case.dataset_id != dataset_id:
        return False
    db.delete(test_case)
    dataset.updated_at = datetime.utcnow()
    db.commit()
    return True

def import_test_cases(
    db: Session,
    dataset_id: str,
    cases: List[TestCaseCreate],
) -> Optional[int]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        return None

    for c in cases:
        test_case = TestCase(
            dataset_id=dataset_id,
            input=c.input,
            expected_output=c.expected_output,
            category=c.category,
            metadata_json=c.metadata or {},
        )
        db.add(test_case)

def update_dataset(
    db: Session,
    dataset_id: str,
    payload: DatasetUpdate,
) -> Optional[DatasetResponse]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        return None
    dataset.name = payload.name
    dataset.description = payload.description or ""
    dataset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(dataset)
    return _build_dataset_response(dataset)

def delete_dataset(db: Session, dataset_id: str) -> None:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise KeyError(f"Dataset with ID '{dataset_id}' not found.")

    ref_exp = db.scalars(select(Experiment).where(Experiment.dataset_id == dataset_id)).first()
    if ref_exp:
        raise ValueError(
            f"Cannot delete dataset '{dataset.name}' because it is referenced by existing experiment history."
        )

    db.delete(dataset)
    db.commit()
