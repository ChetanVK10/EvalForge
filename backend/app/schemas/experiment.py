from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

VALID_EXPERIMENT_METRICS = {
    "exact_match",
    "contains",
    "keyword_match",
    "regex",
    "json_validation",
    "semantic_similarity",
    "llm_judge",
    "response_completeness",
}

class CreateEvaluationPayload(BaseModel):
    name: str = Field(..., description="Experiment name")
    dataset_id: str = Field(..., description="Target evaluation dataset ID")
    model_config_id: str = Field(..., description="Model configuration ID")
    prompt_id: str = Field(..., description="Prompt configuration ID")
    prompt_version: Optional[int] = Field(None, description="Prompt version number")
    prompt_version_id: Optional[str] = Field(None, description="Prompt version ID")
    metrics: List[str] = Field(..., description="Selected evaluation metrics")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Experiment name cannot be blank.")
        return v.strip()

    @field_validator("metrics")
    @classmethod
    def validate_metrics(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError("Select at least one evaluation metric.")
        for m in v:
            if m not in VALID_EXPERIMENT_METRICS:
                raise ValueError(
                    f"Invalid evaluation metric '{m}'. Supported: {', '.join(sorted(VALID_EXPERIMENT_METRICS))}"
                )
        return v

class EvaluationProgressResponse(BaseModel):
    experiment_id: str
    status: str
    stage: str
    message: str
    total_cases: int
    completed_cases: int
    failed_cases: int
    progress_pct: float

class EvaluationScoreResponse(BaseModel):
    id: str
    metric: str
    score: float
    passed: bool
    reasoning: Optional[str] = None
    status: str = "success"
    error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}

class TestCaseResultResponse(BaseModel):
    id: str
    test_case_id: Optional[str] = None
    input: str
    expected_output: str
    model_output: str
    category: str
    status: str
    error: Optional[str] = None
    provider: str
    model: str
    latency_ms: int
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    case_quality_score: Optional[float] = None
    scores: List[EvaluationScoreResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}

class CategoryPerformanceResponse(BaseModel):
    category: str
    score: float
    case_count: int
    failed_cases: int

class ExperimentResponse(BaseModel):
    id: str
    name: str
    dataset_id: str
    dataset_name: str
    model_config_id: str
    model_config_name: Optional[str] = None
    provider: str
    model: str
    prompt_id: str
    prompt_name: str
    prompt_version: int
    metrics: List[str]
    quality_score: Optional[float] = None
    pass_rate: Optional[float] = None
    avg_latency_ms: Optional[int] = None
    p95_latency_ms: Optional[int] = None
    total_tokens: int = 0
    estimated_cost: Optional[float] = None
    result_status: str = "PASS"
    regression_status: str = "PASS"
    status: str
    total_cases: int
    completed_cases: int
    failed_cases: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class ExperimentDetailResponse(ExperimentResponse):
    snapshots: Dict[str, Any] = Field(default_factory=dict)
    category_scores: Dict[str, float] = Field(default_factory=dict)
    category_breakdown: List[CategoryPerformanceResponse] = Field(default_factory=list)
    case_results: List[TestCaseResultResponse] = Field(default_factory=list)
