import json
from typing import Any, Dict, Optional

from app.services.evaluators.base import BaseEvaluator, EvaluationInput, MetricResult
from app.services.providers.exceptions import LLMProviderError
from app.services.providers.gateway import ModelGateway

SYSTEM_JUDGE_RUBRIC = """You are an expert AI Evaluation Judge.
Evaluate the generated Model Output against the User Input and Expected Reference Output.

Rate each requested dimension on a strict scale of 0 to 100:
- correctness: Accuracy of information compared to reference
- relevance: Direct applicability to the user input
- instruction_following: Adherence to formatting, constraints, and instructions
- completeness: Coverage of required details without omitting key points
- groundedness: Factual grounding without hallucinating unverified facts

CRITICAL: Return ONLY a valid, raw JSON object (no markdown, no code blocks) with the following structure:
{
  "correctness": <int 0-100>,
  "relevance": <int 0-100>,
  "instruction_following": <int 0-100>,
  "completeness": <int 0-100>,
  "groundedness": <int 0-100>,
  "reasoning": "<short concise justification>"
}"""

def _extract_json_from_text(text: str) -> Optional[dict]:
    """Helper to safely parse JSON from raw text or markdown fenced blocks."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        # Try extracting text between first { and last }
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(cleaned[start : end + 1])
            except Exception:
                pass
        return None

class LLMJudgeEvaluator(BaseEvaluator):
    def __init__(
        self,
        threshold: float = 80.0,
        gateway: Optional[ModelGateway] = None,
        provider: str = "groq",
        model: str = "llama-3.3-70b-versatile",
        metric_name: str = "llm_judge",
    ):
        super().__init__(threshold=threshold)
        self._gateway = gateway
        self.provider = provider
        self.model = model
        self.metric_name = metric_name

    async def evaluate(
        self, eval_input: EvaluationInput, config: Optional[Dict[str, Any]] = None
    ) -> MetricResult:
        cfg = config or {}
        provider = cfg.get("provider") or self.provider
        model = cfg.get("model") or self.model
        metric_name = cfg.get("metric_name") or self.metric_name

        user_content = f"""USER INPUT:
{eval_input.input}

EXPECTED REFERENCE OUTPUT:
{eval_input.expected_output}

MODEL OUTPUT TO EVALUATE:
{eval_input.model_output}
"""

        gw = self._gateway or ModelGateway()
        try:
            llm_res = await gw.generate(
                provider=provider,
                model=model,
                system_prompt=SYSTEM_JUDGE_RUBRIC,
                user_prompt=user_content,
                temperature=0.0,
                max_tokens=512,
            )
        except LLMProviderError as e:
            return MetricResult(
                metric=metric_name,
                score=0.0,
                passed=False,
                reasoning=f"LLM Judge execution failed due to provider error: {e.message}",
                status="error",
                error=e.message,
            )
        except Exception as e:
            return MetricResult(
                metric=metric_name,
                score=0.0,
                passed=False,
                reasoning=f"LLM Judge execution failed: {str(e)}",
                status="error",
                error=str(e),
            )

        parsed_json = _extract_json_from_text(llm_res.text)
        if not parsed_json or not isinstance(parsed_json, dict):
            return MetricResult(
                metric=metric_name,
                score=0.0,
                passed=False,
                reasoning=f"LLM Judge returned non-parseable response: '{llm_res.text[:100]}...'",
                status="error",
                error="Malformed LLM judge JSON response",
            )

        # Parse dimension scores
        dimensions = ["correctness", "relevance", "instruction_following", "completeness", "groundedness"]
        valid_scores = []
        dim_details = {}

        for d in dimensions:
            val = parsed_json.get(d)
            if val is not None:
                try:
                    score_val = max(0.0, min(100.0, float(val)))
                    dim_details[d] = score_val
                    valid_scores.append(score_val)
                except (ValueError, TypeError):
                    pass

        if not valid_scores:
            return MetricResult(
                metric=metric_name,
                score=0.0,
                passed=False,
                reasoning="LLM Judge JSON output contained no valid numeric dimension scores.",
                status="error",
                error="Missing dimension scores in LLM judge JSON",
            )

        avg_score = round(sum(valid_scores) / len(valid_scores), 2)
        passed = (avg_score >= self.threshold)
        reasoning = str(parsed_json.get("reasoning") or f"LLM Judge score: {avg_score}/100")

        return MetricResult(
            metric=metric_name,
            score=avg_score,
            passed=passed,
            reasoning=reasoning,
            status="success",
            details={
                "dimensions": dim_details,
                "judge_provider": provider,
                "judge_model": model,
                "latency_ms": llm_res.latency_ms,
            },
        )
