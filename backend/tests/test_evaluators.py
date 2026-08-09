from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.evaluators.base import EvaluationInput, MetricResult
from app.services.evaluators.deterministic import (
    ContainsEvaluator,
    ExactMatchEvaluator,
    JsonValidationEvaluator,
    RegexEvaluator,
)
from app.services.evaluators.engine import EvaluationEngine, compute_aggregate_score
from app.services.evaluators.judge import LLMJudgeEvaluator
from app.services.evaluators.semantic import SemanticSimilarityEvaluator
from app.services.providers.base import LLMResponse
from app.services.providers.exceptions import LLMProviderError

# ---------------------------------------------------------------------------
# Exact Match Evaluator Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exact_match_evaluator():
    evaluator = ExactMatchEvaluator()

    # Identical
    res1 = await evaluator.evaluate(
        EvaluationInput(input="q", expected_output="Paris", model_output="Paris")
    )
    assert res1.score == 100.0
    assert res1.passed is True

    # Case & whitespace normalized match
    res2 = await evaluator.evaluate(
        EvaluationInput(input="q", expected_output="Paris ", model_output="  paris")
    )
    assert res2.score == 100.0
    assert res2.passed is True

    # Different
    res3 = await evaluator.evaluate(
        EvaluationInput(input="q", expected_output="Paris", model_output="London")
    )
    assert res3.score == 0.0
    assert res3.passed is False

# ---------------------------------------------------------------------------
# Contains Evaluator Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_contains_evaluator():
    evaluator = ContainsEvaluator()

    res1 = await evaluator.evaluate(
        EvaluationInput(
            input="q",
            expected_output="Paris",
            model_output="The capital of France is Paris.",
        )
    )
    assert res1.score == 100.0
    assert res1.passed is True

    res2 = await evaluator.evaluate(
        EvaluationInput(
            input="q",
            expected_output="Berlin",
            model_output="The capital of France is Paris.",
        )
    )
    assert res2.score == 0.0
    assert res2.passed is False

# ---------------------------------------------------------------------------
# Regex Evaluator Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_regex_evaluator():
    evaluator = RegexEvaluator()

    # Valid pattern match
    res1 = await evaluator.evaluate(
        EvaluationInput(input="q", expected_output="ORD-[0-9]{6}", model_output="Order: ORD-123456")
    )
    assert res1.score == 100.0
    assert res1.passed is True

    # Non-matching pattern
    res2 = await evaluator.evaluate(
        EvaluationInput(input="q", expected_output="ORD-[0-9]{6}", model_output="Order: XYZ-123")
    )
    assert res2.score == 0.0
    assert res2.passed is False

    # Invalid regex pattern error handling
    res3 = await evaluator.evaluate(
        EvaluationInput(input="q", expected_output="[invalid(regex", model_output="Output")
    )
    assert res3.status == "error"
    assert "Invalid regex pattern" in res3.reasoning

# ---------------------------------------------------------------------------
# JSON Validation Evaluator Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_json_validation_evaluator():
    evaluator = JsonValidationEvaluator()

    # Valid raw JSON
    res1 = await evaluator.evaluate(
        EvaluationInput(input="q", expected_output="{}", model_output='{"status": "ok", "value": 42}')
    )
    assert res1.score == 100.0
    assert res1.passed is True

    # Fenced JSON block
    res2 = await evaluator.evaluate(
        EvaluationInput(input="q", expected_output="{}", model_output='```json\n{"status": "ok"}\n```')
    )
    assert res2.score == 100.0
    assert res2.passed is True

    # Invalid JSON
    res3 = await evaluator.evaluate(
        EvaluationInput(input="q", expected_output="{}", model_output="Not JSON content")
    )
    assert res3.score == 0.0
    assert res3.passed is False

    # Schema validation match
    schema = {
        "type": "object",
        "required": ["answer", "confidence"],
        "properties": {"answer": {"type": "string"}, "confidence": {"type": "number"}},
    }
    res4 = await evaluator.evaluate(
        EvaluationInput(
            input="q",
            expected_output="{}",
            model_output='{"answer": "Paris", "confidence": 0.95}',
        ),
        config={"schema": schema},
    )
    assert res4.score == 100.0
    assert res4.passed is True

    # Schema validation failure (missing required key)
    res5 = await evaluator.evaluate(
        EvaluationInput(
            input="q", expected_output="{}", model_output='{"answer": "Paris"}'
        ),
        config={"schema": schema},
    )
    assert res5.score == 0.0
    assert res5.passed is False

# ---------------------------------------------------------------------------
# Semantic Similarity Evaluator Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_semantic_similarity_evaluator():
    evaluator = SemanticSimilarityEvaluator(threshold=75.0)

    # 1. Identical strings -> near-maximum similarity (~100%)
    res1 = await evaluator.evaluate(
        EvaluationInput(
            input="q",
            expected_output="Refunds are processed within 5-7 business days",
            model_output="Refunds are processed within 5-7 business days",
        )
    )
    assert res1.score >= 99.0
    assert res1.passed is True
    assert "Semantic similarity score" in res1.reasoning
    assert res1.details.get("algorithm") == "TF-IDF N-gram Cosine Similarity"

    # 2. Obvious paraphrases -> reasonable similarity according to configured model
    res2 = await evaluator.evaluate(
        EvaluationInput(
            input="q",
            expected_output="Refunds are processed within 5-7 business days",
            model_output="Our standard refund processing time is 5-7 business days from the date the return is received.",
        )
    )
    assert res2.score > 20.0
    assert res2.metric == "semantic_similarity"

    # 3. Unrelated strings -> materially lower similarity
    res3 = await evaluator.evaluate(
        EvaluationInput(
            input="q",
            expected_output="Refunds are processed within 5-7 business days",
            model_output="Quantum physics explores subatomic wave function collapse.",
        )
    )
    assert res3.score < res2.score
    assert res3.passed is False

    # 4. Expected and actual text passed correctly
    assert res1.metric == "semantic_similarity"

    # 5. Raw cosine -> percentage transformation math verification (1.0 raw = 100.0%)
    # Verified by identical input giving 100.0%
    assert res1.score == 100.0

    # 6. Threshold application verification (75.0% threshold)
    evaluator_high = SemanticSimilarityEvaluator(threshold=90.0)
    res_thresh = await evaluator_high.evaluate(
        EvaluationInput(
            input="q",
            expected_output="Refunds are processed within 5-7 business days",
            model_output="Our standard refund processing time is 5-7 business days",
        )
    )
    # If score < 90.0, passed must be False
    if res_thresh.score < 90.0:
        assert res_thresh.passed is False
    else:
        assert res_thresh.passed is True

# ---------------------------------------------------------------------------
# LLM Judge Evaluator Tests (Mocked ModelGateway)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_llm_judge_evaluator_mock():
    mock_gateway = MagicMock()
    judge_json = """{
        "correctness": 90,
        "relevance": 95,
        "instruction_following": 85,
        "completeness": 90,
        "groundedness": 100,
        "reasoning": "Accurate and complete answer."
    }"""
    mock_gateway.generate = AsyncMock(
        return_value=LLMResponse(
            text=judge_json, provider="groq", model="llama-3.3-70b-versatile", latency_ms=250
        )
    )

    evaluator = LLMJudgeEvaluator(gateway=mock_gateway, threshold=80.0)
    res = await evaluator.evaluate(
        EvaluationInput(input="Q", expected_output="A", model_output="A")
    )

    assert res.status == "success"
    assert res.score == 92.0  # (90+95+85+90+100)/5 = 92.0
    assert res.passed is True
    assert res.reasoning == "Accurate and complete answer."
    assert res.details["dimensions"]["correctness"] == 90.0

@pytest.mark.asyncio
async def test_llm_judge_provider_failure_isolation():
    mock_gateway = MagicMock()
    mock_gateway.generate = AsyncMock(
        side_effect=LLMProviderError("Provider unavailable", provider="groq")
    )

    evaluator = LLMJudgeEvaluator(gateway=mock_gateway)
    res = await evaluator.evaluate(
        EvaluationInput(input="Q", expected_output="A", model_output="A")
    )

    assert res.status == "error"
    assert res.score == 0.0
    assert res.passed is False
    assert "Provider unavailable" in res.error

# ---------------------------------------------------------------------------
# Evaluation Engine & Diagnostic Endpoint Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluation_engine_multi_metric():
    mock_gateway = MagicMock()
    mock_gateway.generate = AsyncMock(
        return_value=LLMResponse(
            text='{"correctness": 100, "relevance": 100, "instruction_following": 100, "completeness": 100, "groundedness": 100, "reasoning": "Perfect"}',
            provider="groq",
            model="llama-3.3-70b-versatile",
            latency_ms=200,
        )
    )

    engine = EvaluationEngine(gateway=mock_gateway)
    eval_input = EvaluationInput(
        input="What is 2+2?", expected_output="4", model_output="4"
    )

    output = await engine.evaluate(
        eval_input, metrics=["exact_match", "contains", "semantic_similarity", "llm_judge"]
    )

    assert len(output.results) == 4
    assert output.results[0].metric == "exact_match"
    assert output.results[0].score == 100.0
    assert output.aggregate_score == 100.0

def test_compute_aggregate_score():
    results = [
        MetricResult(metric="m1", score=100.0, passed=True, status="success"),
        MetricResult(metric="m2", score=50.0, passed=False, status="success"),
        MetricResult(metric="m3", score=0.0, passed=False, status="error", error="Crashed"),
    ]
    # Ignores error metric, averages 100.0 and 50.0 = 75.0
    assert compute_aggregate_score(results) == 75.0

def test_evaluator_diagnostic_endpoint(client):
    payload = {
        "input": "Where is Paris?",
        "expected_output": "France",
        "model_output": "Paris is in France.",
        "metrics": ["contains", "exact_match"]
    }
    response = client.post("/api/v1/evaluators/test", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["metric"] == "contains"
    assert data["results"][0]["score"] == 100.0
    assert data["results"][1]["metric"] == "exact_match"
    assert data["results"][1]["score"] == 0.0
    assert data["aggregate_score"] == 50.0
