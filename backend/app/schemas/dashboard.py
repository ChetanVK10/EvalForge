from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.experiment import ExperimentResponse

class MetricOverTime(BaseModel):
    date: str
    score: Optional[float] = None
    latency: Optional[int] = None
    cost: Optional[float] = None

class DashboardAlert(BaseModel):
    id: str
    severity: str  # PASS, WARNING, FAIL
    message: str
    experiment_id: str
    created_at: str

class DashboardSummaryResponse(BaseModel):
    total_experiments: int
    evaluations_this_week: int
    avg_quality_score: float
    avg_latency_ms: int
    estimated_cost: float
    regression_pass_rate: float
    quality_over_time: List[MetricOverTime] = Field(default_factory=list)
    latency_over_time: List[MetricOverTime] = Field(default_factory=list)
    cost_over_time: List[MetricOverTime] = Field(default_factory=list)
    recent_experiments: List[ExperimentResponse] = Field(default_factory=list)
    alerts: List[DashboardAlert] = Field(default_factory=list)
