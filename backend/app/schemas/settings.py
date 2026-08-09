from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.dataset import VALID_CATEGORIES

VALID_METRICS = {
    "exact_match",
    "keyword_match",
    "semantic_similarity",
    "llm_judge",
    "response_completeness",
}

class EvaluationDefaults(BaseModel):
    default_metrics: List[str] = Field(
        default=["semantic_similarity", "llm_judge", "response_completeness"],
        description="Default metrics pre-selected for new evaluation runs",
    )
    concurrency: int = Field(5, description="Concurrent evaluation execution limit (1-20)")
    judge_model: str = Field("llama-3.3-70b-versatile", description="Default LLM judge model")

    @field_validator("concurrency")
    @classmethod
    def validate_concurrency(cls, v: int) -> int:
        if v < 1 or v > 20:
            raise ValueError("Concurrency must be between 1 and 20.")
        return v

    @field_validator("default_metrics")
    @classmethod
    def validate_metrics(cls, v: List[str]) -> List[str]:
        for m in v:
            if m not in VALID_METRICS:
                raise ValueError(f"Invalid metric '{m}'. Must be one of: {', '.join(sorted(VALID_METRICS))}")
        return v

class RegressionThresholds(BaseModel):
    max_quality_regression_pct: float = Field(3.0, description="Max quality score drop %")
    max_factuality_regression_pct: float = Field(2.0, description="Max factuality drop %")
    max_latency_increase_pct: float = Field(15.0, description="Max latency increase %")
    max_cost_increase_pct: float = Field(20.0, description="Max cost increase %")
    critical_categories: List[str] = Field(
        default=["billing"], description="Critical zero-tolerance evaluation categories"
    )

    @field_validator(
        "max_quality_regression_pct",
        "max_factuality_regression_pct",
        "max_latency_increase_pct",
        "max_cost_increase_pct",
    )
    @classmethod
    def validate_non_negative(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("Regression thresholds cannot be negative.")
        return v

    @field_validator("critical_categories")
    @classmethod
    def validate_categories(cls, v: List[str]) -> List[str]:
        for cat in v:
            if cat not in VALID_CATEGORIES:
                raise ValueError(
                    f"Invalid critical category '{cat}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
                )
        return v

class ProviderStatusResponse(BaseModel):
    provider: str
    label: str
    configured: bool
    models: List[str]

class SettingsResponse(BaseModel):
    evaluation_defaults: EvaluationDefaults
    regression_thresholds: RegressionThresholds
    providers: List[ProviderStatusResponse]
