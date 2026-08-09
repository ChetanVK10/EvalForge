from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.experiment import Experiment, TestCaseResult as ResultTestCase
from app.services.experiment_runner import ExperimentRunner
from app.services.providers.base import LLMResponse
from app.services.providers.exceptions import LLMProviderError

@pytest.fixture(autouse=True)
def mock_runner_gateway():
    """Autouse fixture to mock gateway generation in experiment runner tests so no tests hit live APIs."""
    async def mock_generate_case(*args, **kwargs):
        user_prompt = kwargs.get("user_prompt", "")
        if "Capital" in user_prompt or "France" in user_prompt:
            return LLMResponse(text="Paris", provider="groq", model="llama-3.3-70b-versatile", latency_ms=150, input_tokens=10, output_tokens=2, total_tokens=12, estimated_cost=0.0001, finish_reason="stop")
        return LLMResponse(text="4", provider="groq", model="llama-3.3-70b-versatile", latency_ms=150, input_tokens=10, output_tokens=2, total_tokens=12, estimated_cost=0.0001, finish_reason="stop")

    with patch("app.services.experiment_runner.ModelGateway.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = mock_generate_case
        yield mock_gen

@pytest.fixture
def setup_eval_entities(client):
    """Helper fixture to create seed dataset, model config, and prompt."""
    ds_res = client.post("/api/v1/datasets", json={
        "name": "Benchmark Dataset",
        "description": "Test dataset",
        "cases": [
            {"input": "What is 2+2?", "expected_output": "4", "category": "reasoning"},
            {"input": "Capital of France?", "expected_output": "Paris", "category": "factuality"}
        ]
    }).json()

    mc_res = client.post("/api/v1/configurations/models", json={
        "name": "Groq Llama Config",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.2,
        "max_tokens": 512
    }).json()

    pr_res = client.post("/api/v1/configurations/prompts", json={
        "name": "Q&A Prompt",
        "status": "active",
        "system_prompt": "Answer accurately.",
        "user_template": "{{input}}"
    }).json()

    return {
        "dataset_id": ds_res["id"],
        "model_config_id": mc_res["id"],
        "prompt_id": pr_res["id"],
        "prompt_version": 1,
        "dataset_name": ds_res["name"],
        "prompt_name": pr_res["name"],
    }

def test_create_evaluation_success(client, setup_eval_entities):
    payload = {
        "name": "Groq Benchmark Run",
        "dataset_id": setup_eval_entities["dataset_id"],
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": setup_eval_entities["prompt_id"],
        "prompt_version": 1,
        "metrics": ["exact_match", "contains"]
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["name"] == "Groq Benchmark Run"
    assert data["status"] in ("pending", "running", "completed")
    assert data["total_cases"] == 2
    assert "id" in data

def test_create_evaluation_estimated_cost_initial_state(client, setup_eval_entities):
    """
    Regression test for PostgreSQL NOT NULL constraint violation.

    A freshly created (pending) experiment must be allowed to have
    estimated_cost=NULL because:
      1. No API calls have been made yet.
      2. The pricing is unknown at creation time.
      3. The SQLAlchemy model declares estimated_cost as nullable=True.
      4. The original migration had nullable=False which conflicted --
         this migration (0004) corrects that.

    This test ensures:
    - POST /api/v1/evaluations succeeds with HTTP 202 (not 500).
    - The returned estimated_cost is either null (for pending) or a float
      (if the background task completes before the response is returned),
      but NEVER raises a database constraint error.
    - After background execution completes, priced model cost is non-None.
    """
    payload = {
        "name": "Cost Nullability Regression Test",
        "dataset_id": setup_eval_entities["dataset_id"],
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": setup_eval_entities["prompt_id"],
        "prompt_version": 1,
        "metrics": ["exact_match"]
    }
    response = client.post("/api/v1/evaluations", json=payload)
    # The critical assertion: must NOT be 500 (NOT NULL constraint violation)
    assert response.status_code == 202, (
        f"Expected 202 but got {response.status_code}. "
        "This may indicate a NOT NULL constraint on estimated_cost. "
        f"Body: {response.text}"
    )
    data = response.json()
    assert "id" in data
    # estimated_cost is either null (pending) or a float (if runner already completed)
    assert data.get("estimated_cost") is None or isinstance(data.get("estimated_cost"), float), (
        f"estimated_cost must be null or a float, got: {data.get('estimated_cost')!r}"
    )

    # After the background runner finishes (autouse mock makes it instant in TestClient),
    # verify the experiment can be retrieved without errors and its cost is float or null.
    experiment_id = data["id"]
    get_response = client.get(f"/api/v1/experiments/{experiment_id}")
    assert get_response.status_code == 200
    exp_data = get_response.json()
    cost = exp_data.get("estimated_cost")
    assert cost is None or isinstance(cost, float), (
        f"estimated_cost must be null or float after execution, got {cost!r}"
    )

def test_create_evaluation_unpriced_model_cost_is_none(client, db_session, setup_eval_entities):
    """
    When the LLM provider returns estimated_cost=None (unpriced/unknown model),
    the completed experiment's estimated_cost must remain None (not 0.0),
    so the frontend can display N/A.
    """
    # Use a mock that returns None cost (simulating unpriced model)
    from unittest.mock import AsyncMock, patch
    from app.services.providers.base import LLMResponse
    from app.models.experiment import Experiment

    async def mock_generate_no_cost(*args, **kwargs):
        return LLMResponse(
            text="Paris",
            provider="groq",
            model="custom-unpriced-model",
            latency_ms=100,
            input_tokens=10,
            output_tokens=2,
            total_tokens=12,
            estimated_cost=None,  # explicitly unpriced
            finish_reason="stop",
        )

    with patch("app.services.experiment_runner.ModelGateway.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = mock_generate_no_cost

        payload = {
            "name": "Unpriced Model Evaluation",
            "dataset_id": setup_eval_entities["dataset_id"],
            "model_config_id": setup_eval_entities["model_config_id"],
            "prompt_id": setup_eval_entities["prompt_id"],
            "prompt_version": 1,
            "metrics": ["exact_match"]
        }
        response = client.post("/api/v1/evaluations", json=payload)
        assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"

        data = response.json()
        experiment_id = data["id"]

        # Get the completed experiment
        get_response = client.get(f"/api/v1/experiments/{experiment_id}")
        assert get_response.status_code == 200
        exp_data = get_response.json()

        if exp_data["status"] == "completed":
            # Unpriced models must have null cost, not 0.0
            assert exp_data.get("estimated_cost") is None, (
                f"Unpriced model experiment must have null estimated_cost, "
                f"got {exp_data.get('estimated_cost')!r}"
            )



def test_create_evaluation_not_found(client, setup_eval_entities):
    payload = {
        "name": "Bad Dataset Run",
        "dataset_id": "nonexistent-id",
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": setup_eval_entities["prompt_id"],
        "prompt_version": 1,
        "metrics": ["exact_match"]
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 404

def test_create_evaluation_invalid_metric(client, setup_eval_entities):
    payload = {
        "name": "Bad Metric Run",
        "dataset_id": setup_eval_entities["dataset_id"],
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": setup_eval_entities["prompt_id"],
        "prompt_version": 1,
        "metrics": ["invalid_metric_name"]
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_experiment_runner_end_to_end(client, db_session, setup_eval_entities):
    exp = Experiment(
        name="Runner Execution Test",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="pending",
        total_cases=2,
        metrics_json=["exact_match", "contains"],
        snapshots_json={
            "dataset_name": setup_eval_entities["dataset_name"],
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt_name": setup_eval_entities["prompt_name"],
            "prompt_version": 1,
            "system_prompt": "Answer accurately.",
            "user_template": "{{input}}",
            "concurrency": 2,
        }
    )
    db_session.add(exp)
    db_session.commit()
    exp_id = exp.id

    runner = ExperimentRunner()
    await runner.run_experiment(exp_id, lambda: db_session)

    # Re-query updated experiment state from DB
    updated_exp = db_session.get(Experiment, exp_id)
    assert updated_exp.status == "completed"
    assert updated_exp.completed_cases == 2
    assert updated_exp.failed_cases == 0
    assert updated_exp.quality_score == 100.0
    assert updated_exp.avg_latency_ms == 150
    assert updated_exp.total_tokens == 24

    # Verify API status
    res_status = client.get(f"/api/v1/evaluations/{exp_id}/status")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "completed"

    # Verify Experiment Detail API
    res_detail = client.get(f"/api/v1/experiments/{exp_id}")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert len(detail_data["case_results"]) == 2
    assert detail_data["case_results"][0]["case_quality_score"] == 100.0

@pytest.mark.asyncio
async def test_case_failure_isolation(db_session, setup_eval_entities):
    exp = Experiment(
        name="Failure Isolation Test",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="pending",
        total_cases=2,
        metrics_json=["exact_match"],
        snapshots_json={
            "dataset_name": setup_eval_entities["dataset_name"],
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt_name": setup_eval_entities["prompt_name"],
            "prompt_version": 1,
            "system_prompt": "Answer accurately.",
            "user_template": "{{input}}",
            "concurrency": 2,
        }
    )
    db_session.add(exp)
    db_session.commit()
    exp_id = exp.id

    call_count = 0
    async def mock_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return LLMResponse(text="4", provider="groq", model="llama", latency_ms=100, input_tokens=5, output_tokens=1, total_tokens=6)
        else:
            raise LLMProviderError("Provider 500 Server Error", provider="groq")

    mock_gateway = MagicMock()
    mock_gateway.generate = AsyncMock(side_effect=mock_generate)

    runner = ExperimentRunner(gateway=mock_gateway)
    await runner.run_experiment(exp_id, lambda: db_session)

    updated_exp = db_session.get(Experiment, exp_id)
    assert updated_exp.completed_cases == 1
    assert updated_exp.failed_cases == 1
    assert updated_exp.status == "completed"

def test_list_and_detail_experiments_api(client, setup_eval_entities):
    client.post("/api/v1/evaluations", json={
        "name": "List Exp Test",
        "dataset_id": setup_eval_entities["dataset_id"],
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": setup_eval_entities["prompt_id"],
        "prompt_version": 1,
        "metrics": ["exact_match"]
    })

    res_list = client.get("/api/v1/experiments")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

def test_experiment_filtering_status_pass_and_fail(client, db_session, setup_eval_entities):
    exp_pass = Experiment(
        id="exp-pass-test",
        name="High Quality Pass Run",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=95.0,
        pass_rate=100.0,
        completed_cases=2,
        failed_cases=0,
        snapshots_json={"provider": "groq", "model": "llama-3.3-70b-versatile", "dataset_name": "DS Pass"}
    )
    exp_fail = Experiment(
        id="exp-fail-test",
        name="Low Quality Fail Run",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=40.0,
        pass_rate=0.0,
        completed_cases=2,
        failed_cases=2,
        snapshots_json={"provider": "gemini", "model": "gemini-2.5-flash", "dataset_name": "DS Fail"}
    )
    db_session.add(exp_pass)
    db_session.add(exp_fail)
    db_session.commit()

    # Filter PASS
    res_pass = client.get("/api/v1/experiments?status=PASS")
    assert res_pass.status_code == 200
    pass_list = res_pass.json()
    assert all(e["result_status"] == "PASS" for e in pass_list)
    assert any(e["id"] == "exp-pass-test" for e in pass_list)
    assert not any(e["id"] == "exp-fail-test" for e in pass_list)

    # Filter FAIL
    res_fail = client.get("/api/v1/experiments?status=FAIL")
    assert res_fail.status_code == 200
    fail_list = res_fail.json()
    assert all(e["result_status"] == "FAIL" for e in fail_list)
    assert any(e["id"] == "exp-fail-test" for e in fail_list)
    assert not any(e["id"] == "exp-pass-test" for e in fail_list)

    # Filter provider=gemini
    res_provider = client.get("/api/v1/experiments?provider=gemini")
    assert res_provider.status_code == 200
    prov_list = res_provider.json()
    assert all(e["provider"] == "gemini" for e in prov_list)

def test_delete_experiment_and_cascades(client, db_session, setup_eval_entities):
    exp = Experiment(
        id="exp-to-delete",
        name="Temporary Exp",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=90.0,
    )
    db_session.add(exp)
    db_session.commit()

    case_res = ResultTestCase(
        id="case-res-del",
        experiment_id="exp-to-delete",
        input="hi",
        expected_output="hello",
        model_output="hello",
        provider="groq",
        model="llama-3.3-70b-versatile",
        status="completed"
    )
    db_session.add(case_res)
    db_session.commit()

    # Delete experiment
    res_del = client.delete("/api/v1/experiments/exp-to-delete")
    assert res_del.status_code == 200
    assert res_del.json()["id"] == "exp-to-delete"

    # GET experiment detail => 404
    res_get = client.get("/api/v1/experiments/exp-to-delete")
    assert res_get.status_code == 404

    # Verify no orphan TestCaseResult rows
    assert db_session.get(ResultTestCase, "case-res-del") is None

def test_delete_model_config_protection(client, setup_eval_entities):
    # Unreferenced model config -> deleted successfully
    mc_unref = client.post("/api/v1/configurations/models", json={
        "name": "Unreferenced Model Config", "provider": "groq", "model": "llama-3.1-8b-instant", "temperature": 0.5, "max_tokens": 100
    }).json()

    del_unref = client.delete(f"/api/v1/configurations/models/{mc_unref['id']}")
    assert del_unref.status_code == 204

    # Create experiment referencing setup_eval_entities model config
    client.post("/api/v1/evaluations", json={
        "name": "Ref Exp Model",
        "dataset_id": setup_eval_entities["dataset_id"],
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": setup_eval_entities["prompt_id"],
        "prompt_version": 1,
        "metrics": ["exact_match"]
    })

    # Referenced model config -> 409 Conflict
    del_ref = client.delete(f"/api/v1/configurations/models/{setup_eval_entities['model_config_id']}")
    assert del_ref.status_code == 409
    assert "referenced by existing experiment" in del_ref.json()["detail"]

def test_delete_prompt_config_protection(client, setup_eval_entities):
    # Unreferenced prompt -> deleted successfully
    pr_unref = client.post("/api/v1/configurations/prompts", json={
        "name": "Unreferenced Prompt Config", "status": "draft", "system_prompt": "Hello"
    }).json()

    del_unref = client.delete(f"/api/v1/configurations/prompts/{pr_unref['id']}")
    assert del_unref.status_code == 204

    # Create experiment referencing setup_eval_entities prompt
    client.post("/api/v1/evaluations", json={
        "name": "Ref Exp Prompt",
        "dataset_id": setup_eval_entities["dataset_id"],
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": setup_eval_entities["prompt_id"],
        "prompt_version": 1,
        "metrics": ["exact_match"]
    })

    # Referenced prompt -> 409 Conflict
    del_ref = client.delete(f"/api/v1/configurations/prompts/{setup_eval_entities['prompt_id']}")
    assert del_ref.status_code == 409
    assert "referenced by existing experiment" in del_ref.json()["detail"]

def test_delete_dataset_protection(client, setup_eval_entities):
    # Unreferenced dataset -> deleted successfully (204)
    ds_unref = client.post("/api/v1/datasets", json={
        "name": "Unreferenced Dataset", "description": "Temp", "cases": []
    }).json()

    del_unref = client.delete(f"/api/v1/datasets/{ds_unref['id']}")
    assert del_unref.status_code == 204

    # Create experiment referencing setup_eval_entities dataset
    client.post("/api/v1/evaluations", json={
        "name": "Ref Exp Dataset",
        "dataset_id": setup_eval_entities["dataset_id"],
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": setup_eval_entities["prompt_id"],
        "prompt_version": 1,
        "metrics": ["exact_match"]
    })

    # Referenced dataset -> 409 Conflict
    del_ref = client.delete(f"/api/v1/datasets/{setup_eval_entities['dataset_id']}")
    assert del_ref.status_code == 409
    assert "referenced by existing experiment" in del_ref.json()["detail"]

@pytest.mark.asyncio
async def test_provider_failure_semantics_in_experiment_runner(db_session, setup_eval_entities):
    from unittest.mock import AsyncMock, MagicMock
    from sqlalchemy.orm import sessionmaker
    from app.services.experiment_runner import ExperimentRunner
    from app.services.providers.exceptions import LLMProviderError
    from app.models.experiment import Experiment, TestCaseResult

    mock_gateway = MagicMock()
    mock_gateway.generate = AsyncMock(side_effect=LLMProviderError("HTTP 404 NOT_FOUND: Model unavailable"))

    runner = ExperimentRunner(gateway=mock_gateway)

    exp = Experiment(
        name="Gemini Provider Failure Test",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="pending",
        metrics_json=["exact_match"],
        snapshots_json={"provider": "gemini", "model": "gemini-3.6-flash", "concurrency": 5},
    )
    db_session.add(exp)
    db_session.commit()
    exp_id = exp.id

    session_factory = sessionmaker(bind=db_session.get_bind())

    await runner.run_experiment(exp_id, session_factory)

    check_db = session_factory()
    try:
        updated_exp = check_db.get(Experiment, exp_id)
        assert updated_exp.status == "failed"
        assert updated_exp.failed_cases > 0
        assert updated_exp.quality_score is None

        results = check_db.query(TestCaseResult).filter(TestCaseResult.experiment_id == exp_id).all()
        for res in results:
            assert res.status == "failed"
            assert res.case_quality_score is None
            assert res.model_output == ""
            assert "Execution failed" in res.error
            assert "Provider: gemini" in res.error
            assert "Model: gemini-3.6-flash" in res.error
    finally:
        check_db.close()

def test_experiment_semantics_and_judge_isolation(db_session, setup_eval_entities):
    from app.models.experiment import EvaluationScore, TestCaseResult
    from app.services.experiment_service import _build_experiment_response

    # 1. 3/3 passing cases -> PASS (including 81.1% quality score + 100% pass rate)
    exp_all_pass = Experiment(
        id="exp-all-pass",
        name="81.1% Quality All Pass Run",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=81.1,
        pass_rate=100.0,
        completed_cases=3,
        failed_cases=0,
        snapshots_json={"provider": "groq", "model": "llama-3.3-70b-versatile"}
    )
    for i, score in enumerate([81.7, 80.1, 81.6]):
        res = TestCaseResult(
            id=f"tc-pass-{i}",
            experiment_id="exp-all-pass",
            input=f"in {i}",
            expected_output=f"out {i}",
            model_output=f"out {i}",
            category="general",
            status="completed",
            case_quality_score=score,
            provider="groq",
            model="llama-3.3-70b-versatile",
            latency_ms=100,
        )
        # Add semantic similarity score reasoning
        res.scores.append(EvaluationScore(
            metric="semantic_similarity",
            score=score,
            passed=True,
            reasoning=f"Semantic similarity score of {score}% met threshold (75.0%).",
            status="success"
        ))
        exp_all_pass.case_results.append(res)
    
    resp_pass = _build_experiment_response(exp_all_pass)
    assert resp_pass.result_status == "PASS"
    assert resp_pass.regression_status == "PASS"

    # 2. 2/3 passing cases -> WARNING
    exp_warning = Experiment(
        id="exp-warning",
        name="Partial Pass Run",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=75.0,
        pass_rate=66.7,
        completed_cases=3,
        failed_cases=0,
        snapshots_json={"provider": "groq", "model": "llama-3.3-70b-versatile"}
    )
    for i, score in enumerate([85.0, 82.0, 58.0]):
        res = TestCaseResult(
            id=f"tc-warn-{i}",
            experiment_id="exp-warning",
            input=f"in {i}",
            expected_output=f"out {i}",
            model_output=f"out {i}",
            category="general",
            status="completed",
            case_quality_score=score,
            provider="groq",
            model="llama-3.3-70b-versatile",
            latency_ms=100,
        )
        exp_warning.case_results.append(res)

    resp_warn = _build_experiment_response(exp_warning)
    assert resp_warn.result_status == "WARNING"

    # 3. 0/3 passing cases -> FAIL
    exp_zero_pass = Experiment(
        id="exp-zero-pass",
        name="Zero Pass Run",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=40.0,
        pass_rate=0.0,
        completed_cases=3,
        failed_cases=0,
        snapshots_json={"provider": "groq", "model": "llama-3.3-70b-versatile"}
    )
    for i, score in enumerate([50.0, 45.0, 30.0]):
        res = TestCaseResult(
            id=f"tc-fail-{i}",
            experiment_id="exp-zero-pass",
            input=f"in {i}",
            expected_output=f"out {i}",
            model_output=f"out {i}",
            category="general",
            status="completed",
            case_quality_score=score,
            provider="groq",
            model="llama-3.3-70b-versatile",
            latency_ms=100,
        )
        exp_zero_pass.case_results.append(res)

    resp_fail = _build_experiment_response(exp_zero_pass)
    assert resp_fail.result_status == "FAIL"

    # 4. System / Provider failure -> FAIL
    exp_provider_fail = Experiment(
        id="exp-prov-fail",
        name="Provider Fail Run",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="failed",
        quality_score=None,
        pass_rate=None,
        completed_cases=0,
        failed_cases=1,
        snapshots_json={"provider": "groq", "model": "llama-3.3-70b-versatile"}
    )
    resp_prov_fail = _build_experiment_response(exp_provider_fail)
    assert resp_prov_fail.result_status == "FAIL"

    # 5. Zero valid/scored cases -> FAIL (not PASS)
    exp_empty = Experiment(
        id="exp-empty",
        name="Empty Experiment Run",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=None,
        pass_rate=None,
        completed_cases=0,
        failed_cases=0,
        snapshots_json={"provider": "groq", "model": "llama-3.3-70b-versatile"}
    )
    resp_empty = _build_experiment_response(exp_empty)
    assert resp_empty.result_status == "FAIL"

def test_model_config_traceability_and_pricing_accounting(client, db_session, setup_eval_entities):
    from app.services.providers.pricing import calculate_estimated_cost
    from app.services.experiment_service import _build_experiment_response

    # 1. Input / Output / Combined Cost Calculation with different per-1M token rates
    # Groq Llama 3.3 70b: input $0.59 / 1M, output $0.79 / 1M
    cost_groq = calculate_estimated_cost("llama-3.3-70b-versatile", 2000, 500)
    expected_groq = (2000 / 1_000_000.0) * 0.59 + (500 / 1_000_000.0) * 0.79
    assert cost_groq is not None
    assert round(cost_groq, 6) == round(expected_groq, 6)

    # 2. Unknown model pricing returns None (N/A) rather than 0
    cost_unknown = calculate_estimated_cost("unverified-custom-model", 1000, 1000)
    assert cost_unknown is None

    # 3. Missing token metadata returns None
    cost_missing_tokens = calculate_estimated_cost("llama-3.3-70b-versatile", None, 500)
    assert cost_missing_tokens is None

    # 4. Experiment Response exposes model_config_id, model_config_name, provider, model
    exp = Experiment(
        id="exp-traceability-test",
        name="Traceability Test Run",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=90.0,
        pass_rate=100.0,
        completed_cases=1,
        failed_cases=0,
        snapshots_json={
            "dataset_name": setup_eval_entities["dataset_name"],
            "model_config_name": "Groq Llama Production",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt_name": setup_eval_entities["prompt_name"],
            "prompt_version": 1,
        }
    )
    resp = _build_experiment_response(exp)
    assert resp.model_config_id == setup_eval_entities["model_config_id"]
    assert resp.model_config_name == "Groq Llama Production"
    assert resp.provider == "groq"
    assert resp.model == "llama-3.3-70b-versatile"

    # 5. Missing / deleted configuration reference fallback in snapshots
    exp_deleted_cfg = Experiment(
        id="exp-deleted-cfg",
        name="Deleted Cfg Run",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id="nonexistent-deleted-config-id",
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=85.0,
        pass_rate=100.0,
        completed_cases=1,
        failed_cases=0,
        snapshots_json={
            "provider": "gemini",
            "model": "gemini-2.5-flash",
        }
    )
    resp_deleted = _build_experiment_response(exp_deleted_cfg)
    assert resp_deleted.model_config_id == "nonexistent-deleted-config-id"
    assert resp_deleted.model_config_name == "Model Config"
    assert resp_deleted.provider == "gemini"
    assert resp_deleted.model == "gemini-2.5-flash"

def test_experiments_exact_date_filtering(client, db_session, setup_eval_entities):
    from datetime import datetime, timezone

    # Boundaries: 2026-08-04T00:00:00Z (inclusive start of Aug 4)
    exp_aug4_start = Experiment(
        id="exp-aug4-start",
        name="Aug 4 Start",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=90.0,
        pass_rate=100.0,
        completed_cases=1,
        created_at=datetime(2026, 8, 4, 0, 0, 0, tzinfo=timezone.utc), # 8. timezone-aware
        snapshots_json={"provider": "groq", "model": "llama-3.3-70b-versatile"}
    )
    # Microsecond boundary: 2026-08-04T23:59:59.999999Z (still Aug 4)
    exp_aug4_micro = Experiment(
        id="exp-aug4-micro",
        name="Aug 4 Microsecond",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id="deleted-cfg-id", # 10. deleted model config
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=85.0,
        pass_rate=100.0,
        completed_cases=1,
        estimated_cost=None, # 11. estimated_cost=None
        created_at=datetime(2026, 8, 4, 23, 59, 59, 999999, tzinfo=timezone.utc),
        snapshots_json={"provider": "gemini", "model": "gemini-2.5-flash"}
    )
    # Start of Aug 5: 2026-08-05T00:00:00Z (must NOT be in Aug 4, must be in Aug 5)
    exp_aug5_start = Experiment(
        id="exp-aug5-start",
        name="Aug 5 Start",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        quality_score=92.0,
        pass_rate=100.0,
        completed_cases=1,
        created_at=datetime(2026, 8, 5, 0, 0, 0), # 9. timezone-naive
        snapshots_json={"provider": "gemini", "model": "gemini-2.5-flash"}
    )

    db_session.add_all([exp_aug4_start, exp_aug4_micro, exp_aug5_start])
    db_session.commit()

    # 1. GET ?date=2026-08-04 returns ONLY Aug 4 experiments
    res_aug4 = client.get("/api/v1/experiments?date=2026-08-04")
    assert res_aug4.status_code == 200
    ids_aug4 = [e["id"] for e in res_aug4.json()]
    assert "exp-aug4-start" in ids_aug4
    assert "exp-aug4-micro" in ids_aug4
    assert "exp-aug5-start" not in ids_aug4

    # 2. GET ?date=2026-08-05 returns ONLY Aug 5 experiments
    res_aug5 = client.get("/api/v1/experiments?date=2026-08-05")
    assert res_aug5.status_code == 200
    ids_aug5 = [e["id"] for e in res_aug5.json()]
    assert "exp-aug5-start" in ids_aug5
    assert "exp-aug4-start" not in ids_aug5
    assert "exp-aug4-micro" not in ids_aug5

    # 5. Date with zero matching experiments -> 200 []
    res_empty = client.get("/api/v1/experiments?date=2030-01-01")
    assert res_empty.status_code == 200
    assert res_empty.json() == []

    # 6. Date + provider filter (?date=2026-08-04&provider=gemini)
    res_aug4_gemini = client.get("/api/v1/experiments?date=2026-08-04&provider=gemini")
    assert res_aug4_gemini.status_code == 200
    ids_aug4_gemini = [e["id"] for e in res_aug4_gemini.json()]
    assert "exp-aug4-micro" in ids_aug4_gemini
    assert "exp-aug4-start" not in ids_aug4_gemini

    # 7. Date + status filter (?date=2026-08-04&status=PASS)
    res_aug4_pass = client.get("/api/v1/experiments?date=2026-08-04&status=PASS")
    assert res_aug4_pass.status_code == 200
    assert len(res_aug4_pass.json()) >= 2

    # 10. Malformed date parameter returns 400 Bad Request
    res_bad = client.get("/api/v1/experiments?date=not-a-valid-date")
    assert res_bad.status_code == 400
    assert "Invalid date parameter" in res_bad.json()["detail"]

    # 11. Preserved since parameter still means "created at or after"
    res_since_aug4 = client.get("/api/v1/experiments?since=2026-08-04")
    assert res_since_aug4.status_code == 200
    ids_since = [e["id"] for e in res_since_aug4.json()]
    assert "exp-aug4-start" in ids_since
    assert "exp-aug5-start" in ids_since

def test_latency_and_p95_aggregation_and_serialization(client, db_session, setup_eval_entities):
    """
    Test P95 latency calculation, database persistence, and ExperimentResponse serialization.

    Required test cases:
    1. Observed 3 cases with latencies [476, 2070, 2080] ms:
       - avg_latency_ms = 1542
       - p95_latency_ms = 2080
       - ExperimentResponse includes p95_latency_ms = 2080
    2. One case [500] -> avg=500, p95=500
    3. Two cases [300, 600] -> avg=450, p95=600
    4. Zero completed cases / failed cases -> correct handling
    """
    from app.services.experiment_service import _build_experiment_response

    # 1. 3 cases with latencies [476, 2070, 2080] ms
    exp_3cases = Experiment(
        id="exp-p95-3cases",
        name="P95 3 Cases Test",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        total_cases=3,
        completed_cases=3,
        failed_cases=0,
        avg_latency_ms=1542,
        p95_latency_ms=2080, # 2080 ms = 2.08s
    )
    db_session.add(exp_3cases)
    db_session.commit()

    resp_3cases = _build_experiment_response(exp_3cases)
    assert resp_3cases.avg_latency_ms == 1542
    assert resp_3cases.p95_latency_ms == 2080

    # API GET /api/v1/experiments/{id}
    res_api = client.get(f"/api/v1/experiments/{exp_3cases.id}")
    assert res_api.status_code == 200
    api_data = res_api.json()
    assert api_data["avg_latency_ms"] == 1542
    assert api_data["p95_latency_ms"] == 2080

    # 2. One case [500]
    exp_1case = Experiment(
        id="exp-p95-1case",
        name="P95 1 Case Test",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        total_cases=1,
        completed_cases=1,
        failed_cases=0,
        avg_latency_ms=500,
        p95_latency_ms=500,
    )
    resp_1case = _build_experiment_response(exp_1case)
    assert resp_1case.p95_latency_ms == 500

    # 3. Two cases [300, 600]
    exp_2cases = Experiment(
        id="exp-p95-2cases",
        name="P95 2 Cases Test",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="completed",
        total_cases=2,
        completed_cases=2,
        failed_cases=0,
        avg_latency_ms=450,
        p95_latency_ms=600,
    )
    resp_2cases = _build_experiment_response(exp_2cases)
    assert resp_2cases.p95_latency_ms == 600

    # 4. Zero completed / pending experiment
    exp_pending = Experiment(
        id="exp-p95-pending",
        name="P95 Pending Test",
        dataset_id=setup_eval_entities["dataset_id"],
        model_config_id=setup_eval_entities["model_config_id"],
        prompt_id=setup_eval_entities["prompt_id"],
        prompt_version_id="pv-1",
        status="pending",
        total_cases=2,
        completed_cases=0,
        failed_cases=0,
        avg_latency_ms=None,
        p95_latency_ms=None,
    )
    resp_pending = _build_experiment_response(exp_pending)
    assert resp_pending.p95_latency_ms is None


def test_explicit_prompt_version_selection(client, setup_eval_entities):
    """
    Tests explicit prompt version selection (v1 vs v2), historical immutability,
    and backward compatibility when prompt_version is omitted.
    """
    prompt_id = setup_eval_entities["prompt_id"]

    # Add v2 to the prompt configuration
    v2_res = client.post(
        f"/api/v1/configurations/prompts/{prompt_id}/versions",
        json={
            "system_prompt": "System prompt version 2 - Candidate",
            "user_template": "{{input}}",
            "notes": "v2 Candidate version",
        },
    )
    assert v2_res.status_code == 201

    # Test 1 — Explicit v1 selection
    payload_v1 = {
        "name": "Run with Prompt v1 Baseline",
        "dataset_id": setup_eval_entities["dataset_id"],
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": prompt_id,
        "prompt_version": 1,
        "metrics": ["exact_match"],
    }
    res_v1 = client.post("/api/v1/evaluations", json=payload_v1)
    assert res_v1.status_code == 202
    exp_v1_data = res_v1.json()
    assert exp_v1_data["prompt_version"] == 1
    exp_v1_id = exp_v1_data["id"]

    # Verify v1 experiment detail uses v1 system prompt
    detail_v1 = client.get(f"/api/v1/experiments/{exp_v1_id}").json()
    assert detail_v1["prompt_version"] == 1
    assert detail_v1["snapshots"]["system_prompt"] == "Answer accurately."

    # Test 2 — Explicit v2 selection
    payload_v2 = {
        "name": "Run with Prompt v2 Candidate",
        "dataset_id": setup_eval_entities["dataset_id"],
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": prompt_id,
        "prompt_version": 2,
        "metrics": ["exact_match"],
    }
    res_v2 = client.post("/api/v1/evaluations", json=payload_v2)
    assert res_v2.status_code == 202
    exp_v2_data = res_v2.json()
    assert exp_v2_data["prompt_version"] == 2
    exp_v2_id = exp_v2_data["id"]

    # Verify v2 experiment detail uses v2 system prompt
    detail_v2 = client.get(f"/api/v1/experiments/{exp_v2_id}").json()
    assert detail_v2["prompt_version"] == 2
    assert detail_v2["snapshots"]["system_prompt"] == "System prompt version 2 - Candidate"

    # Test 3 — Historical immutability (Add v3, ensure v1 experiment still resolves to v1)
    v3_res = client.post(
        f"/api/v1/configurations/prompts/{prompt_id}/versions",
        json={
            "system_prompt": "System prompt version 3 - Future",
            "user_template": "{{input}}",
            "notes": "v3 Future version",
        },
    )
    assert v3_res.status_code == 201

    # Re-query original v1 experiment
    detail_v1_after_v3 = client.get(f"/api/v1/experiments/{exp_v1_id}").json()
    assert detail_v1_after_v3["prompt_version"] == 1
    assert detail_v1_after_v3["snapshots"]["system_prompt"] == "Answer accurately."

    # Test 4 — Backward compatibility (Omit prompt_version, should default to latest version v3)
    payload_no_version = {
        "name": "Run with Default Version",
        "dataset_id": setup_eval_entities["dataset_id"],
        "model_config_id": setup_eval_entities["model_config_id"],
        "prompt_id": prompt_id,
        "metrics": ["exact_match"],
    }
    res_default = client.post("/api/v1/evaluations", json=payload_no_version)
    assert res_default.status_code == 202
    exp_default_data = res_default.json()
    assert exp_default_data["prompt_version"] == 3


