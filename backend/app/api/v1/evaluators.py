from typing import Any, Dict, List, Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.services.evaluators.base import EvaluationInput
from app.services.evaluators.engine import EvaluationEngine, EvaluationOutput

router = APIRouter()
engine = EvaluationEngine()

class TestEvaluationRequest(BaseModel):
    input: str = Field(..., description="Prompt input")
    expected_output: str = Field(..., description="Expected reference output")
    model_output: str = Field(..., description="Model output to evaluate")
    metrics: List[str] = Field(
        default=["exact_match", "contains", "semantic_similarity"],
        description="Metrics to evaluate",
    )
    category: Optional[str] = Field(None, description="Optional category")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Evaluator configuration")

@router.post(
    "/test",
    response_model=EvaluationOutput,
    status_code=status.HTTP_200_OK,
    summary="Evaluate single case",
)
async def test_evaluation(payload: TestEvaluationRequest):
    """Run requested metric evaluators on a test case without persisting results."""
    eval_input = EvaluationInput(
        input=payload.input,
        expected_output=payload.expected_output,
        model_output=payload.model_output,
        category=payload.category,
    )
    return await engine.evaluate(eval_input, payload.metrics, config=payload.config)
