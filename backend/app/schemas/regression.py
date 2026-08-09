from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

from app.schemas.experiment import ExperimentResponse

class CompareRequest(BaseModel):
    baseline_experiment_id: str = Field(..., description="ID of baseline experiment")
    candidate_experiment_id: str = Field(..., description="ID of candidate experiment")

    @field_validator("baseline_experiment_id", "candidate_experiment_id")
    @classmethod
    def validate_id_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Experiment ID cannot be blank.")
        return v.strip()

class RegressionMetric(BaseModel):
    key: str
    label: str
    baseline: float
    candidate: float
    delta_pct: float
    threshold_pct: float
    direction: Literal["higher_is_better", "lower_is_better"]
    unit: Literal["percent", "ms", "usd"]
    status: Literal["PASS", "FAIL", "WARNING"]

class CategoryRegression(BaseModel):
    category: str
    baseline: float
    candidate: float
    delta_pct: float
    critical: bool

class RegressionCase(BaseModel):
    case_id: str
    input: str
    expected_output: str
    category: str
    baseline_score: float
    candidate_score: float
    delta: float
    baseline_output: str
    candidate_output: str
    failure_reason: str = ""
    judge_explanation: str = ""
    metric_diagnostics: List[str] = Field(default_factory=list)

class PromotionGateRule(BaseModel):
    label: str
    limit: str
    actual: str
    passed: bool

class PromotionGate(BaseModel):
    passed: bool
    rules: List[PromotionGateRule]
    reasons: List[str]

class RegressionComparisonResponse(BaseModel):
    baseline: ExperimentResponse
    candidate: ExperimentResponse
    verdict: Literal["PASS", "FAIL", "WARNING"]
    summary: str
    metrics: List[RegressionMetric]
    categories: List[CategoryRegression]
    regressed_cases: List[RegressionCase]
    improved_cases: List[RegressionCase]
    promotion_gate: PromotionGate
