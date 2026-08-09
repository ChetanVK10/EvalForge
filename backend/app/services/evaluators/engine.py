from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.services.evaluators.base import BaseEvaluator, EvaluationInput, MetricResult
from app.services.evaluators.deterministic import (
    ContainsEvaluator,
    ExactMatchEvaluator,
    JsonValidationEvaluator,
    RegexEvaluator,
)
from app.services.evaluators.judge import LLMJudgeEvaluator
from app.services.evaluators.semantic import SemanticSimilarityEvaluator
from app.services.providers.gateway import ModelGateway

class EvaluationOutput(BaseModel):
    results: List[MetricResult]
    aggregate_score: Optional[float] = Field(None, description="Average quality score across successful evaluators")

def compute_aggregate_score(results: List[MetricResult]) -> Optional[float]:
    """Calculate arithmetic mean of score across all successful evaluator metrics."""
    successful_scores = [r.score for r in results if r.status == "success"]
    if not successful_scores:
        return None
    return round(sum(successful_scores) / len(successful_scores), 2)

class EvaluationEngine:
    def __init__(self, gateway: Optional[ModelGateway] = None):
        self.gateway = gateway or ModelGateway()

    def get_evaluator(self, metric: str) -> Optional[BaseEvaluator]:
        m = (metric or "").strip().lower()
        if m == "exact_match":
            return ExactMatchEvaluator()
        elif m in ("contains", "keyword_match"):
            return ContainsEvaluator(metric_name=m)
        elif m == "regex":
            return RegexEvaluator()
        elif m == "json_validation":
            return JsonValidationEvaluator()
        elif m == "semantic_similarity":
            return SemanticSimilarityEvaluator()
        elif m in ("llm_judge", "response_completeness"):
            return LLMJudgeEvaluator(gateway=self.gateway, metric_name=m)
        return None

    async def evaluate(
        self,
        eval_input: EvaluationInput,
        metrics: List[str],
        config: Optional[Dict[str, Any]] = None,
    ) -> EvaluationOutput:
        """Run requested metric evaluators against evaluation input with failure isolation."""
        results: List[MetricResult] = []

        for metric in metrics:
            evaluator = self.get_evaluator(metric)
            if not evaluator:
                results.append(
                    MetricResult(
                        metric=metric,
                        score=0.0,
                        passed=False,
                        reasoning=f"Unknown or unsupported metric '{metric}'.",
                        status="error",
                        error=f"Unsupported metric '{metric}'",
                    )
                )
                continue

            try:
                res = await evaluator.evaluate(eval_input, config=config)
                results.append(res)
            except Exception as e:
                # Isolate individual evaluator crashes so other metrics complete successfully
                results.append(
                    MetricResult(
                        metric=metric,
                        score=0.0,
                        passed=False,
                        reasoning=f"Evaluator '{metric}' crashed: {str(e)}",
                        status="error",
                        error=str(e),
                    )
                )

        aggregate = compute_aggregate_score(results)
        return EvaluationOutput(results=results, aggregate_score=aggregate)
