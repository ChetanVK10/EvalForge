import json
import re
from typing import Any, Dict, Optional

from app.services.evaluators.base import BaseEvaluator, EvaluationInput, MetricResult

def _normalize_string(s: str) -> str:
    if not s:
        return ""
    # Strip leading/trailing whitespace and normalize to lowercase
    return s.strip().lower()

class ExactMatchEvaluator(BaseEvaluator):
    def __init__(self, threshold: float = 100.0):
        super().__init__(threshold=threshold)

    async def evaluate(
        self, eval_input: EvaluationInput, config: Optional[Dict[str, Any]] = None
    ) -> MetricResult:
        expected = _normalize_string(eval_input.expected_output)
        actual = _normalize_string(eval_input.model_output)

        matched = (expected == actual)
        score = 100.0 if matched else 0.0
        passed = (score >= self.threshold)

        reasoning = (
            "Exact match succeeded."
            if matched
            else f"Expected '{eval_input.expected_output.strip()}', but received '{eval_input.model_output.strip()}'."
        )

        return MetricResult(
            metric="exact_match",
            score=score,
            passed=passed,
            reasoning=reasoning,
            status="success",
        )

class ContainsEvaluator(BaseEvaluator):
    def __init__(self, threshold: float = 100.0, metric_name: str = "contains"):
        super().__init__(threshold=threshold)
        self.metric_name = metric_name

    async def evaluate(
        self, eval_input: EvaluationInput, config: Optional[Dict[str, Any]] = None
    ) -> MetricResult:
        expected = _normalize_string(eval_input.expected_output)
        actual = _normalize_string(eval_input.model_output)

        contained = (expected in actual) if expected else True
        score = 100.0 if contained else 0.0
        passed = (score >= self.threshold)

        reasoning = (
            f"Model output contains expected keyword '{eval_input.expected_output.strip()}'."
            if contained
            else f"Model output does not contain expected keyword '{eval_input.expected_output.strip()}'."
        )

        return MetricResult(
            metric=self.metric_name,
            score=score,
            passed=passed,
            reasoning=reasoning,
            status="success",
        )

class RegexEvaluator(BaseEvaluator):
    def __init__(self, threshold: float = 100.0):
        super().__init__(threshold=threshold)

    async def evaluate(
        self, eval_input: EvaluationInput, config: Optional[Dict[str, Any]] = None
    ) -> MetricResult:
        pattern = (config or {}).get("pattern") or eval_input.expected_output
        if not pattern:
            return MetricResult(
                metric="regex",
                score=0.0,
                passed=False,
                reasoning="No regex pattern provided.",
                status="error",
                error="Missing pattern configuration",
            )

        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            match = compiled.search(eval_input.model_output)
            matched = match is not None
            score = 100.0 if matched else 0.0
            passed = (score >= self.threshold)

            reasoning = (
                f"Model output matched regex pattern '{pattern}'."
                if matched
                else f"Model output did not match regex pattern '{pattern}'."
            )

            return MetricResult(
                metric="regex",
                score=score,
                passed=passed,
                reasoning=reasoning,
                status="success",
                details={"matched_text": match.group(0) if match else None},
            )
        except re.error as e:
            return MetricResult(
                metric="regex",
                score=0.0,
                passed=False,
                reasoning=f"Invalid regex pattern '{pattern}': {str(e)}",
                status="error",
                error=str(e),
            )

class JsonValidationEvaluator(BaseEvaluator):
    def __init__(self, threshold: float = 100.0):
        super().__init__(threshold=threshold)

    async def evaluate(
        self, eval_input: EvaluationInput, config: Optional[Dict[str, Any]] = None
    ) -> MetricResult:
        raw_text = eval_input.model_output.strip()
        # Clean markdown code block wraps ```json ... ``` if present
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()

        try:
            parsed = json.loads(raw_text)
        except Exception as e:
            return MetricResult(
                metric="json_validation",
                score=0.0,
                passed=False,
                reasoning=f"Output is not valid JSON: {str(e)}",
                status="success",
            )

        # Optional schema validation
        schema = (config or {}).get("schema")
        if schema:
            try:
                import jsonschema
                jsonschema.validate(instance=parsed, schema=schema)
            except ImportError:
                # Basic key validation if jsonschema package is unavailable
                if isinstance(schema, dict) and "required" in schema:
                    missing = [k for k in schema["required"] if k not in parsed]
                    if missing:
                        return MetricResult(
                            metric="json_validation",
                            score=0.0,
                            passed=False,
                            reasoning=f"JSON missing required schema keys: {', '.join(missing)}",
                            status="success",
                        )
            except Exception as e:
                return MetricResult(
                    metric="json_validation",
                    score=0.0,
                    passed=False,
                    reasoning=f"JSON schema validation failed: {str(e)}",
                    status="success",
                )

        return MetricResult(
            metric="json_validation",
            score=100.0,
            passed=True,
            reasoning="Output is valid JSON conforming to requirements.",
            status="success",
        )
