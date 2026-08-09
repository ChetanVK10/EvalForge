from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class EvaluationInput(BaseModel):
    input: str = Field(..., description="Prompt input to the model")
    expected_output: str = Field(..., description="Expected reference output")
    model_output: str = Field(..., description="Actual generated output from model")
    category: Optional[str] = Field(None, description="Evaluation category")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

class MetricResult(BaseModel):
    metric: str = Field(..., description="Metric key")
    score: float = Field(..., description="Score normalized from 0.0 to 100.0")
    passed: bool = Field(..., description="Whether score meets pass threshold")
    reasoning: Optional[str] = Field(None, description="Human-readable explanation")
    status: str = Field("success", description="Execution status: success or error")
    error: Optional[str] = Field(None, description="Error message if evaluator failed")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional metric details")

class BaseEvaluator(ABC):
    def __init__(self, threshold: float = 80.0):
        self.threshold = threshold

    @abstractmethod
    async def evaluate(
        self, eval_input: EvaluationInput, config: Optional[Dict[str, Any]] = None
    ) -> MetricResult:
        """Evaluate model output against expected output or rubric."""
        pass
