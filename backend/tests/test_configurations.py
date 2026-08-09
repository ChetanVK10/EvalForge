def test_create_groq_model_config(client):
    payload = {
        "name": "Groq Llama Candidate",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.2,
        "max_tokens": 1024
    }
    response = client.post("/api/v1/configurations/models", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Groq Llama Candidate"
    assert data["provider"] == "groq"
    assert data["model"] == "llama-3.3-70b-versatile"
    assert data["temperature"] == 0.2
    assert data["max_tokens"] == 1024
    assert "id" in data

def test_create_gemini_model_config(client):
    payload = {
        "name": "Gemini Flash Baseline",
        "provider": "gemini",
        "model": "gemini-3.6-flash",
        "temperature": 0.7,
        "max_tokens": 2048
    }
    response = client.post("/api/v1/configurations/models", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "gemini"
    assert data["model"] == "gemini-3.6-flash"

    # Test alternative Gemini 3.5 Flash
    res_35 = client.post("/api/v1/configurations/models", json={
        "name": "Gemini 3.5 Flash Config", "provider": "gemini", "model": "gemini-3.5-flash", "temperature": 0.2, "max_tokens": 1024
    })
    assert res_35.status_code == 201
    assert res_35.json()["model"] == "gemini-3.5-flash"

    # Test lightweight Gemini 3.5 Flash Lite
    res_lite = client.post("/api/v1/configurations/models", json={
        "name": "Gemini Lite Config", "provider": "gemini", "model": "gemini-3.5-flash-lite", "temperature": 0.1, "max_tokens": 512
    })
    assert res_lite.status_code == 201
    assert res_lite.json()["model"] == "gemini-3.5-flash-lite"

def test_model_config_validation(client):
    # Invalid provider
    res1 = client.post("/api/v1/configurations/models", json={
        "name": "Invalid Provider Config", "provider": "openai", "model": "gpt-4", "temperature": 0.5, "max_tokens": 100
    })
    assert res1.status_code == 422

    # Invalid temperature (< 0)
    res2 = client.post("/api/v1/configurations/models", json={
        "name": "Bad Temp", "provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": -0.5, "max_tokens": 100
    })
    assert res2.status_code == 422

    # Invalid temperature (> 2.0)
    res3 = client.post("/api/v1/configurations/models", json={
        "name": "Bad Temp High", "provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": 2.5, "max_tokens": 100
    })
    assert res3.status_code == 422

    # Invalid max_tokens
    res4 = client.post("/api/v1/configurations/models", json={
        "name": "Zero Tokens", "provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": 0.5, "max_tokens": 0
    })
    assert res4.status_code == 422

    # Blank name
    res5 = client.post("/api/v1/configurations/models", json={
        "name": "   ", "provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": 0.5, "max_tokens": 100
    })
    assert res5.status_code == 422

    # Incompatible Gemini provider + Groq model
    res6 = client.post("/api/v1/configurations/models", json={
        "name": "Invalid Gemini Groq Model", "provider": "gemini", "model": "llama-3.3-70b-versatile", "temperature": 0.2, "max_tokens": 1024
    })
    assert res6.status_code == 422

    # Incompatible Groq provider + Gemini model
    res7 = client.post("/api/v1/configurations/models", json={
        "name": "Invalid Groq Gemini Model", "provider": "groq", "model": "gemini-3.6-flash", "temperature": 0.2, "max_tokens": 1024
    })
    assert res7.status_code == 422

def test_list_model_configs(client):
    client.post("/api/v1/configurations/models", json={"name": "Config A", "provider": "groq", "model": "llama-3.3-70b-versatile", "temperature": 0.2, "max_tokens": 100})
    client.post("/api/v1/configurations/models", json={"name": "Config B", "provider": "gemini", "model": "gemini-3.6-flash", "temperature": 0.5, "max_tokens": 200})

    response = client.get("/api/v1/configurations/models")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_create_prompt_configuration(client):
    payload = {
        "name": "Customer Support System Prompt",
        "status": "draft",
        "system_prompt": "You are a helpful customer support agent.",
        "user_template": "{{input}}",
        "notes": "Initial draft"
    }
    response = client.post("/api/v1/configurations/prompts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Customer Support System Prompt"
    assert data["status"] == "draft"
    assert data["latest_version"] == 1
    assert len(data["versions"]) == 1
    assert data["versions"][0]["version"] == 1
    assert data["versions"][0]["system_prompt"] == "You are a helpful customer support agent."
    assert data["versions"][0]["user_template"] == "{{input}}"

def test_list_prompts(client):
    client.post("/api/v1/configurations/prompts", json={"name": "Prompt Alpha", "status": "draft", "system_prompt": "Sys 1"})
    client.post("/api/v1/configurations/prompts", json={"name": "Prompt Beta", "status": "active", "system_prompt": "Sys 2"})

    response = client.get("/api/v1/configurations/prompts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_add_prompt_version(client):
    created = client.post("/api/v1/configurations/prompts", json={
        "name": "Versioned Prompt", "status": "active", "system_prompt": "Version 1 System"
    }).json()

    # Add Version 2
    res_v2 = client.post(f"/api/v1/configurations/prompts/{created['id']}/versions", json={
        "system_prompt": "Version 2 System Prompt with refund rules",
        "user_template": "Customer Question:\n{{input}}",
        "notes": "Added refund rules"
    })
    assert res_v2.status_code == 201
    v2_data = res_v2.json()
    assert v2_data["version"] == 2
    assert v2_data["system_prompt"] == "Version 2 System Prompt with refund rules"

    # Verify updated prompt detail
    res_get = client.get(f"/api/v1/configurations/prompts/{created['id']}")
    assert res_get.status_code == 200
    prompt_data = res_get.json()
    assert prompt_data["latest_version"] == 2
    assert len(prompt_data["versions"]) == 2

def test_update_prompt_version(client):
    created = client.post("/api/v1/configurations/prompts", json={
        "name": "Editable Prompt", "status": "draft", "system_prompt": "Original Sys Prompt"
    }).json()

    res_put = client.put(f"/api/v1/configurations/prompts/{created['id']}/versions/1", json={
        "system_prompt": "Updated Sys Prompt",
        "user_template": "{{input}}",
        "notes": "Typo fix"
    })
    assert res_put.status_code == 200
    assert res_put.json()["system_prompt"] == "Updated Sys Prompt"
    assert res_put.json()["notes"] == "Typo fix"

def test_update_prompt_configuration_name(client):
    created = client.post("/api/v1/configurations/prompts", json={
        "name": "Original Prompt Name", "status": "draft", "system_prompt": "Sys Prompt"
    }).json()

    res_put = client.put(f"/api/v1/configurations/prompts/{created['id']}", json={
        "name": "Customer Support Policy Prompt"
    })
    assert res_put.status_code == 200
    updated = res_put.json()
    assert updated["name"] == "Customer Support Policy Prompt"
    assert updated["latest_version"] == 1

def test_prompt_not_found(client):
    res1 = client.get("/api/v1/configurations/prompts/nonexistent-id")
    assert res1.status_code == 404

    res2 = client.post("/api/v1/configurations/prompts/nonexistent-id/versions", json={
        "system_prompt": "Sys", "user_template": "{{input}}"
    })
    assert res2.status_code == 404

def test_prompt_validation_errors(client):
    # Blank prompt name
    res1 = client.post("/api/v1/configurations/prompts", json={
        "name": "   ", "status": "draft", "system_prompt": "Sys"
    })
    assert res1.status_code == 422

    # Blank system prompt
    res2 = client.post("/api/v1/configurations/prompts", json={
        "name": "Valid Name", "status": "draft", "system_prompt": "   "
    })
    assert res2.status_code == 422

    # Invalid status
    res3 = client.post("/api/v1/configurations/prompts", json={
        "name": "Valid Name", "status": "published", "system_prompt": "Sys"
    })
    assert res3.status_code == 422

def test_update_model_configuration_success_and_validation(client):
    # Create initial Groq model config
    created = client.post("/api/v1/configurations/models", json={
        "name": "Groq Initial Config",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.2,
        "max_tokens": 1024
    }).json()

    config_id = created["id"]

    # 1. Successful update: name, model, temperature, max_tokens
    res_update = client.put(f"/api/v1/configurations/models/{config_id}", json={
        "name": "Groq Updated Config",
        "model": "llama-3.1-8b-instant",
        "temperature": 0.5,
        "max_tokens": 2048
    })
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["name"] == "Groq Updated Config"
    assert updated_data["provider"] == "groq"  # Provider remains unchanged
    assert updated_data["model"] == "llama-3.1-8b-instant"
    assert updated_data["temperature"] == 0.5
    assert updated_data["max_tokens"] == 2048

    # 2. Incompatible model for provider (Gemini model for Groq config) -> 400
    res_incompatible = client.put(f"/api/v1/configurations/models/{config_id}", json={
        "name": "Groq Invalid Model",
        "model": "gemini-3.6-flash",
        "temperature": 0.5,
        "max_tokens": 2048
    })
    assert res_incompatible.status_code == 400
    assert "not compatible with provider 'groq'" in res_incompatible.json()["detail"]

    # 3. Invalid temperature (< 0.0) -> 422
    res_bad_temp = client.put(f"/api/v1/configurations/models/{config_id}", json={
        "name": "Bad Temp",
        "model": "llama-3.1-8b-instant",
        "temperature": -0.1,
        "max_tokens": 1024
    })
    assert res_bad_temp.status_code == 422

    # 4. Invalid max_tokens (<= 0) -> 422
    res_bad_tokens = client.put(f"/api/v1/configurations/models/{config_id}", json={
        "name": "Bad Tokens",
        "model": "llama-3.1-8b-instant",
        "temperature": 0.2,
        "max_tokens": 0
    })
    assert res_bad_tokens.status_code == 422

    # 5. Nonexistent configuration -> 404
    res_404 = client.put("/api/v1/configurations/models/nonexistent-config-id", json={
        "name": "Ghost Config",
        "model": "llama-3.1-8b-instant",
        "temperature": 0.2,
        "max_tokens": 1024
    })
    assert res_404.status_code == 404

def test_update_model_configuration_preserves_historical_experiments(client, db_session):
    from app.models.experiment import Experiment

    # Create model config
    mc = client.post("/api/v1/configurations/models", json={
        "name": "Original Config Name",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.2,
        "max_tokens": 1024
    }).json()

    # Create dataset & prompt to link experiment
    ds = client.post("/api/v1/datasets", json={
        "name": "Trace DS", "cases": [{"input": "i", "expected_output": "o"}]
    }).json()
    pr = client.post("/api/v1/configurations/prompts", json={
        "name": "Trace Prompt", "system_prompt": "sys"
    }).json()

    # Create historical experiment with snapshots
    exp = Experiment(
        id="exp-history-trace-test",
        name="Historical Experiment Run",
        dataset_id=ds["id"],
        model_config_id=mc["id"],
        prompt_id=pr["id"],
        prompt_version_id="pv-1",
        status="completed",
        snapshots_json={
            "dataset_name": "Trace DS",
            "model_config_name": "Original Config Name",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.2,
            "max_tokens": 1024,
            "prompt_name": "Trace Prompt",
            "prompt_version": 1,
        }
    )
    db_session.add(exp)
    db_session.commit()

    # Update model configuration (change name, model, temperature, max_tokens)
    res_update = client.put(f"/api/v1/configurations/models/{mc['id']}", json={
        "name": "NEW Edited Config Name",
        "model": "llama-3.1-8b-instant",
        "temperature": 0.9,
        "max_tokens": 4096
    })
    assert res_update.status_code == 200

    # Retrieve historical experiment via API
    res_exp = client.get(f"/api/v1/experiments/{exp.id}")
    assert res_exp.status_code == 200
    exp_data = res_exp.json()

    # Historical experiment response MUST preserve execution-time snapshots!
    assert exp_data["model_config_name"] == "Original Config Name"
    assert exp_data["model"] == "llama-3.3-70b-versatile"
    assert exp_data["provider"] == "groq"

