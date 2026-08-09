def test_get_settings_defaults(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.GROQ_API_KEY", "")
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "")

    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    data = response.json()

    assert "evaluation_defaults" in data
    assert data["evaluation_defaults"]["concurrency"] == 5
    assert data["evaluation_defaults"]["judge_model"] == "llama-3.3-70b-versatile"
    assert "semantic_similarity" in data["evaluation_defaults"]["default_metrics"]

    assert "regression_thresholds" in data
    assert data["regression_thresholds"]["max_quality_regression_pct"] == 3.0
    assert data["regression_thresholds"]["critical_categories"] == ["billing"]

    assert "providers" in data
    assert len(data["providers"]) == 2
    providers_by_name = {p["provider"]: p for p in data["providers"]}
    assert "groq" in providers_by_name
    assert "gemini" in providers_by_name
    assert providers_by_name["groq"]["configured"] is False
    assert providers_by_name["gemini"]["configured"] is False
    assert "gemini-3.6-flash" in providers_by_name["gemini"]["models"]
    assert "gemini-3.5-flash" in providers_by_name["gemini"]["models"]
    assert "gemini-3.5-flash-lite" in providers_by_name["gemini"]["models"]

def test_update_evaluation_defaults(client):
    new_eval_defaults = {
        "default_metrics": ["exact_match", "llm_judge"],
        "concurrency": 8,
        "judge_model": "gemini-3.5-flash-lite"
    }
    response = client.put("/api/v1/settings/evaluation", json=new_eval_defaults)
    assert response.status_code == 200
    data = response.json()
    assert data["concurrency"] == 8
    assert data["judge_model"] == "gemini-3.5-flash-lite"
    assert data["default_metrics"] == ["exact_match", "llm_judge"]

    # Verify that updating evaluation defaults did NOT reset regression thresholds
    settings = client.get("/api/v1/settings").json()
    assert settings["evaluation_defaults"]["concurrency"] == 8
    assert settings["regression_thresholds"]["max_quality_regression_pct"] == 3.0

def test_update_regression_thresholds(client):
    new_thresholds = {
        "max_quality_regression_pct": 5.0,
        "max_factuality_regression_pct": 3.0,
        "max_latency_increase_pct": 25.0,
        "max_cost_increase_pct": 30.0,
        "critical_categories": ["billing", "safety"]
    }
    response = client.put("/api/v1/settings/regression", json=new_thresholds)
    assert response.status_code == 200
    data = response.json()
    assert data["max_quality_regression_pct"] == 5.0
    assert data["critical_categories"] == ["billing", "safety"]

    # Verify GET /api/v1/settings/regression
    get_res = client.get("/api/v1/settings/regression")
    assert get_res.status_code == 200
    assert get_res.json()["max_quality_regression_pct"] == 5.0

    # Verify that updating regression thresholds did NOT reset evaluation defaults
    settings = client.get("/api/v1/settings").json()
    assert settings["regression_thresholds"]["max_quality_regression_pct"] == 5.0

def test_settings_validation_errors(client):
    # Invalid concurrency (< 1)
    res1 = client.put("/api/v1/settings/evaluation", json={
        "default_metrics": ["exact_match"], "concurrency": 0, "judge_model": "m"
    })
    assert res1.status_code == 422

    # Invalid concurrency (> 20)
    res2 = client.put("/api/v1/settings/evaluation", json={
        "default_metrics": ["exact_match"], "concurrency": 25, "judge_model": "m"
    })
    assert res2.status_code == 422

    # Invalid metric
    res3 = client.put("/api/v1/settings/evaluation", json={
        "default_metrics": ["invalid_metric_key"], "concurrency": 5, "judge_model": "m"
    })
    assert res3.status_code == 422

    # Negative regression threshold
    res4 = client.put("/api/v1/settings/regression", json={
        "max_quality_regression_pct": -2.0,
        "max_factuality_regression_pct": 2.0,
        "max_latency_increase_pct": 15.0,
        "max_cost_increase_pct": 20.0,
        "critical_categories": ["billing"]
    })
    assert res4.status_code == 422

    # Invalid critical category
    res5 = client.put("/api/v1/settings/regression", json={
        "max_quality_regression_pct": 3.0,
        "max_factuality_regression_pct": 2.0,
        "max_latency_increase_pct": 15.0,
        "max_cost_increase_pct": 20.0,
        "critical_categories": ["invalid_cat"]
    })
    assert res5.status_code == 422
