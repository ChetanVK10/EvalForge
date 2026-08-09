from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = {
    "factuality",
    "reasoning",
    "summarization",
    "customer-support",
    "instruction-following",
    "safety",
    "billing",
    "technical",
    "account-management",
    "general",
}

class TestCaseCreate(BaseModel):
    input: str = Field(..., description="Test case input prompt")
    expected_output: str = Field(..., description="Expected reference response")
    category: str = Field("general", description="Evaluation category")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata key-values")

    @field_validator("input")
    @classmethod
    def validate_input_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Test case input prompt cannot be blank")
        return v.strip()

    @field_validator("expected_output")
    @classmethod
    def validate_expected_output_not_empty(cls, v: str) -> str:
        if v is None or not v.strip():
            raise ValueError("Test case expected output cannot be blank")
        return v.strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        cat = (v or "general").strip().lower()
        if cat not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid evaluation category '{v}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
            )
        return cat

class TestCaseResponse(BaseModel):
    id: str
    input: str
    expected_output: str
    category: str
    metadata: Dict[str, Any]

    model_config = {"from_attributes": True}

class DatasetCreate(BaseModel):
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field("", description="Optional dataset description")
    cases: List[TestCaseCreate] = Field(default_factory=list, description="Initial test cases")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Dataset name cannot be blank")
        return v.strip()

class DatasetUpdate(BaseModel):
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field("", description="Optional dataset description")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Dataset name cannot be blank")
        return v.strip()

class DatasetResponse(BaseModel):
    id: str
    name: str
    description: str
    case_count: int
    categories: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class DatasetDetailResponse(DatasetResponse):
    cases: List[TestCaseResponse]
