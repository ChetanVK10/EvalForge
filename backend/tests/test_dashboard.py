import pytest
from sqlalchemy.orm import Session

from app.models.configuration import ModelConfiguration, Prompt, PromptVersion
from app.models.dataset import Dataset
from app.models.experiment import Experiment

@pytest.fixture
def dashboard_test_data(db_session: Session):
    dataset = Dataset(id="ds-dash-1", name="Dash Dataset")
    db_session.add(dataset)

    model_config = ModelConfiguration(
        id="mc-dash-1", name="Dash Model Config", provider="groq", model="llama-3.3-70b-versatile"
    )
    db_session.add(model_config)

    prompt = Prompt(id="p-dash-1", name="Dash Prompt", status="active")
    db_session.add(prompt)

    prompt_ver = PromptVersion(
        id="pv-dash-1", prompt_id="p-dash-1", version=1, system_prompt="Sys", user_template="{{input}}"
    )
    db_session.add(prompt_ver)
    db_session.commit()

    exp1 = Experiment(
        id="exp-dash-1",
        name="Dashboard Run 1",
        dataset_id=dataset.id,
        model_config_id=model_config.id,
        prompt_id=prompt.id,
        prompt_version_id=prompt_ver.id,
        status="completed",
        quality_score=92.5,
        pass_rate=100.0,
        completed_cases=1,
        failed_cases=0,
        avg_latency_ms=450,
        estimated_cost=0.015,
        metrics_json=["exact_match"],
        snapshots_json={"dataset_name": "Dash Dataset", "provider": "groq", "model": "llama-3.3-70b-versatile"},
    )
    exp2 = Experiment(
        id="exp-dash-2",
        name="Dashboard Run 2",
        dataset_id=dataset.id,
        model_config_id=model_config.id,
        prompt_id=prompt.id,
        prompt_version_id=prompt_ver.id,
        status="completed",
        quality_score=82.0,
        pass_rate=0.0,
        completed_cases=1,
        failed_cases=1,
        avg_latency_ms=600,
        estimated_cost=0.020,
        metrics_json=["exact_match"],
        snapshots_json={"dataset_name": "Dash Dataset", "provider": "groq", "model": "llama-3.3-70b-versatile"},
    )
    db_session.add_all([exp1, exp2])
    db_session.commit()

    return {"exp1_id": exp1.id, "exp2_id": exp2.id}

from app.services.cache_service import cache_service

def test_get_dashboard_summary(client, db_session: Session, dashboard_test_data: dict):
    cache_service.delete("dashboard:summary:v1")
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()

    assert data["total_experiments"] >= 2
    assert data["avg_quality_score"] > 0
    assert data["avg_latency_ms"] > 0
    assert data["estimated_cost"] > 0
    assert len(data["recent_experiments"]) >= 2
    assert len(data["alerts"]) >= 1
    assert data["alerts"][0]["severity"] == "FAIL"
