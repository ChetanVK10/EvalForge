import pytest
from sqlalchemy.orm import Session
from app.models.configuration import ModelConfiguration, Prompt, PromptVersion
from app.models.dataset import Dataset, TestCase
from app.models.experiment import EvaluationScore, Experiment, TestCaseResult
from app.services.regression_service import compare_experiments

@pytest.fixture
def test_data(db_session: Session):
    """Fixture providing dataset, model config, prompt version, and test cases."""
    dataset = Dataset(
        id="ds-test-reg",
        name="Regression Test Dataset",
        description="Dataset for testing regression engine",
    )
    db_session.add(dataset)

    case_1 = TestCase(
        id="tc-1",
        dataset_id="ds-test-reg",
        input="What is the capital of France?",
        expected_output="Paris",
        category="factuality",
    )
    case_2 = TestCase(
        id="tc-2",
        dataset_id="ds-test-reg",
        input="How do I reset my billing password?",
        expected_output="Go to account settings -> billing.",
        category="billing",
    )
    case_3 = TestCase(
        id="tc-3",
        dataset_id="ds-test-reg",
        input="Explain Quantum Computing simply.",
        expected_output="Quantum computing uses qubits...",
        category="general",
    )
    db_session.add_all([case_1, case_2, case_3])

    model_config = ModelConfiguration(
        id="mc-test-reg",
        name="Test Model Config",
        provider="groq",
        model="llama-3.3-70b-versatile",
    )
    db_session.add(model_config)

    prompt = Prompt(id="p-test-reg", name="Test Prompt", status="active")
    db_session.add(prompt)

    prompt_ver = PromptVersion(
        id="pv-test-reg",
        prompt_id="p-test-reg",
        version=1,
        system_prompt="You are a helpful assistant.",
        user_template="{{input}}",
    )
    db_session.add(prompt_ver)

    db_session.commit()
    return {
        "dataset_id": dataset.id,
        "model_config_id": model_config.id,
        "prompt_id": prompt.id,
        "prompt_version_id": prompt_ver.id,
    }

def create_experiment_helper(
    db_session: Session,
    exp_id: str,
    name: str,
    dataset_id: str,
    model_config_id: str,
    prompt_id: str,
    prompt_version_id: str,
    quality_score: float,
    avg_latency_ms: int,
    estimated_cost: float,
    status: str = "completed",
    cases_data: list = None,
) -> Experiment:
    exp = Experiment(
        id=exp_id,
        name=name,
        dataset_id=dataset_id,
        model_config_id=model_config_id,
        prompt_id=prompt_id,
        prompt_version_id=prompt_version_id,
        status=status,
        quality_score=quality_score,
        pass_rate=90.0,
        avg_latency_ms=avg_latency_ms,
        p95_latency_ms=avg_latency_ms + 50,
        total_tokens=1000,
        estimated_cost=estimated_cost,
        metrics_json=["semantic_similarity", "factuality"],
        snapshots_json={
            "dataset_name": "Regression Test Dataset",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt_name": "Test Prompt",
            "prompt_version": 1,
        },
    )
    db_session.add(exp)
    db_session.commit()

    if cases_data:
        for c in cases_data:
            res = TestCaseResult(
                id=c["id"],
                experiment_id=exp_id,
                test_case_id=c.get("test_case_id"),
                input=c["input"],
                expected_output=c["expected_output"],
                model_output=c.get("model_output", "Sample output"),
                category=c.get("category", "general"),
                status=c.get("status", "completed"),
                error=c.get("error"),
                provider="groq",
                model="llama-3.3-70b-versatile",
                latency_ms=avg_latency_ms,
                case_quality_score=c.get("score", 90.0),
            )
            db_session.add(res)
            db_session.commit()

            scores = c.get("scores", [])
            for s in scores:
                sc = EvaluationScore(
                    test_case_result_id=res.id,
                    metric=s["metric"],
                    score=s["score"],
                    passed=s.get("passed", True),
                    status=s.get("status", "success"),
                    reasoning=s.get("reasoning", "Good response"),
                )
                db_session.add(sc)
            db_session.commit()

    db_session.refresh(exp)
    return exp

def test_compare_validation_same_experiment(db_session: Session, test_data: dict):
    create_experiment_helper(
        db_session, "exp-1", "Baseline", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 90.0, 500, 0.01
    )
    with pytest.raises(ValueError, match="Baseline and candidate must be different experiments"):
        compare_experiments(db_session, "exp-1", "exp-1")

def test_compare_validation_not_found(db_session: Session, test_data: dict):
    create_experiment_helper(
        db_session, "exp-1", "Baseline", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 90.0, 500, 0.01
    )
    with pytest.raises(ValueError, match="Candidate experiment 'exp-2' was not found"):
        compare_experiments(db_session, "exp-1", "exp-2")

def test_compare_validation_incomplete_status(db_session: Session, test_data: dict):
    create_experiment_helper(
        db_session, "exp-1", "Baseline", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 90.0, 500, 0.01, status="running"
    )
    create_experiment_helper(
        db_session, "exp-2", "Candidate", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 92.0, 520, 0.01, status="completed"
    )
    with pytest.raises(ValueError, match="is not completed"):
        compare_experiments(db_session, "exp-1", "exp-2")

def test_compare_validation_dataset_mismatch(db_session: Session, test_data: dict):
    ds2 = Dataset(id="ds-other", name="Other Dataset")
    db_session.add(ds2)
    db_session.commit()

    create_experiment_helper(
        db_session, "exp-1", "Baseline", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 90.0, 500, 0.01
    )
    create_experiment_helper(
        db_session, "exp-2", "Candidate", "ds-other", test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 92.0, 520, 0.01
    )
    with pytest.raises(ValueError, match="Experiments must run on the same dataset"):
        compare_experiments(db_session, "exp-1", "exp-2")

def test_compare_passing_promotion_gate(db_session: Session, test_data: dict):
    cases_baseline = [
        {
            "id": "res-b-1", "test_case_id": "tc-1", "input": "Q1", "expected_output": "A1",
            "category": "factuality", "score": 90.0, "status": "completed",
            "scores": [{"metric": "semantic_similarity", "score": 90.0, "passed": True}]
        },
        {
            "id": "res-b-2", "test_case_id": "tc-2", "input": "Q2", "expected_output": "A2",
            "category": "billing", "score": 92.0, "status": "completed",
            "scores": [{"metric": "semantic_similarity", "score": 92.0, "passed": True}]
        },
    ]
    cases_candidate = [
        {
            "id": "res-c-1", "test_case_id": "tc-1", "input": "Q1", "expected_output": "A1",
            "category": "factuality", "score": 92.0, "status": "completed",
            "scores": [{"metric": "semantic_similarity", "score": 92.0, "passed": True}]
        },
        {
            "id": "res-c-2", "test_case_id": "tc-2", "input": "Q2", "expected_output": "A2",
            "category": "billing", "score": 94.0, "status": "completed",
            "scores": [{"metric": "semantic_similarity", "score": 94.0, "passed": True}]
        },
    ]

    create_experiment_helper(
        db_session, "exp-pass-base", "Baseline Run", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 91.0, 500, 0.010, cases_data=cases_baseline
    )
    create_experiment_helper(
        db_session, "exp-pass-cand", "Candidate Run", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 93.0, 480, 0.009, cases_data=cases_candidate
    )

    result = compare_experiments(db_session, "exp-pass-base", "exp-pass-cand")
    assert result.verdict == "PASS"
    assert result.promotion_gate.passed is True
    assert len(result.promotion_gate.reasons) == 0
    assert len(result.regressed_cases) == 0
    assert result.metrics[0].key == "overall_quality"
    assert result.metrics[0].delta_pct == 2.0

def test_compare_quality_regression_fails_gate(db_session: Session, test_data: dict):
    cases_baseline = [
        {"id": "res-b-1", "test_case_id": "tc-1", "input": "Q1", "expected_output": "A1", "category": "factuality", "score": 95.0}
    ]
    cases_candidate = [
        {"id": "res-c-1", "test_case_id": "tc-1", "input": "Q1", "expected_output": "A1", "category": "factuality", "score": 85.0}
    ]

    create_experiment_helper(
        db_session, "exp-q-base", "Baseline", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 95.0, 500, 0.01, cases_data=cases_baseline
    )
    create_experiment_helper(
        db_session, "exp-q-cand", "Candidate", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 88.0, 500, 0.01, cases_data=cases_candidate
    )

    result = compare_experiments(db_session, "exp-q-base", "exp-q-cand")
    assert result.verdict == "FAIL"
    assert result.promotion_gate.passed is False
    assert any("Overall quality decreased" in r for r in result.promotion_gate.reasons)

def test_compare_latency_and_cost_breach(db_session: Session, test_data: dict):
    create_experiment_helper(
        db_session, "exp-telemetry-base", "Baseline", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 90.0, 400, 0.010
    )
    # 50% latency increase (threshold default 15%), 50% cost increase (threshold default 20%)
    create_experiment_helper(
        db_session, "exp-telemetry-cand", "Candidate", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 90.0, 600, 0.015
    )

    result = compare_experiments(db_session, "exp-telemetry-base", "exp-telemetry-cand")
    assert result.verdict == "FAIL"
    assert any("Average latency increased" in r for r in result.promotion_gate.reasons)
    assert any("Estimated cost increased" in r for r in result.promotion_gate.reasons)

def test_case_level_regressions_and_improvements(db_session: Session, test_data: dict):
    cases_baseline = [
        # tc-1: Score drops by 15.0 points -> Regressed case
        {
            "id": "res-b-1", "test_case_id": "tc-1", "input": "Q1", "expected_output": "A1",
            "category": "factuality", "score": 90.0, "status": "completed",
            "scores": [{"metric": "semantic_similarity", "score": 90.0, "passed": True}]
        },
        # tc-2: Score increases by 12.0 points -> Improved case
        {
            "id": "res-b-2", "test_case_id": "tc-2", "input": "Q2", "expected_output": "A2",
            "category": "billing", "score": 75.0, "status": "completed",
            "scores": [{"metric": "semantic_similarity", "score": 75.0, "passed": True}]
        },
        # tc-3: Baseline passed (72.0), candidate fails execution -> Regressed case (pass -> fail)
        {
            "id": "res-b-3", "test_case_id": "tc-3", "input": "Q3", "expected_output": "A3",
            "category": "general", "score": 72.0, "status": "completed",
            "scores": [{"metric": "semantic_similarity", "score": 72.0, "passed": True}]
        },
    ]
    cases_candidate = [
        {
            "id": "res-c-1", "test_case_id": "tc-1", "input": "Q1", "expected_output": "A1",
            "category": "factuality", "score": 75.0, "status": "completed",
            "scores": [{"metric": "semantic_similarity", "score": 75.0, "passed": False}]
        },
        {
            "id": "res-c-2", "test_case_id": "tc-2", "input": "Q2", "expected_output": "A2",
            "category": "billing", "score": 87.0, "status": "completed",
            "scores": [{"metric": "semantic_similarity", "score": 87.0, "passed": True}]
        },
        {
            "id": "res-c-3", "test_case_id": "tc-3", "input": "Q3", "expected_output": "A3",
            "category": "general", "score": 0.0, "status": "failed", "error": "Provider connection timeout",
            "scores": []
        },
    ]

    create_experiment_helper(
        db_session, "exp-cases-base", "Baseline", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 85.0, 500, 0.01, cases_data=cases_baseline
    )
    create_experiment_helper(
        db_session, "exp-cases-cand", "Candidate", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 80.0, 500, 0.01, cases_data=cases_candidate
    )

    result = compare_experiments(db_session, "exp-cases-base", "exp-cases-cand")
    assert len(result.regressed_cases) == 2
    assert len(result.improved_cases) == 1
    assert result.improved_cases[0].case_id == "tc-2"
    assert result.improved_cases[0].delta == 12.0

def test_api_compare_post_endpoint(client, db_session: Session, test_data: dict):
    create_experiment_helper(
        db_session, "exp-post-b", "Baseline", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 90.0, 500, 0.01
    )
    create_experiment_helper(
        db_session, "exp-post-c", "Candidate", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 92.0, 480, 0.01
    )

    response = client.post(
        "/api/v1/regressions/compare",
        json={"baseline_experiment_id": "exp-post-b", "candidate_experiment_id": "exp-post-c"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "PASS"
    assert data["baseline"]["id"] == "exp-post-b"
    assert data["candidate"]["id"] == "exp-post-c"

def test_api_compare_get_endpoint(client, db_session: Session, test_data: dict):
    create_experiment_helper(
        db_session, "exp-get-b", "Baseline", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 90.0, 500, 0.01
    )
    create_experiment_helper(
        db_session, "exp-get-c", "Candidate", test_data["dataset_id"], test_data["model_config_id"],
        test_data["prompt_id"], test_data["prompt_version_id"], 92.0, 480, 0.01
    )

    response = client.get("/api/v1/regressions/compare?baseline_id=exp-get-b&candidate_id=exp-get-c")
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "PASS"
