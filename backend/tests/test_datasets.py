def test_create_valid_dataset(client):
    payload = {
        "name": "Customer Support Benchmark",
        "description": "Core support test cases",
        "cases": []
    }
    response = client.post("/api/v1/datasets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Customer Support Benchmark"
    assert data["description"] == "Core support test cases"
    assert data["case_count"] == 0
    assert data["categories"] == []
    assert "id" in data

def test_create_dataset_with_cases(client):
    payload = {
        "name": "E-Commerce Evals",
        "description": "Billing and refund test cases",
        "cases": [
            {
                "input": "Where is my refund?",
                "expected_output": "Refunds process in 5-7 business days.",
                "category": "billing",
                "metadata": {"priority": "high"}
            },
            {
                "input": "How do I change my shipping address?",
                "expected_output": "Go to Account Settings > Addresses.",
                "category": "customer-support"
            }
        ]
    }
    response = client.post("/api/v1/datasets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "E-Commerce Evals"
    assert data["case_count"] == 2
    assert sorted(data["categories"]) == ["billing", "customer-support"]

def test_create_dataset_validation_errors(client):
    # Blank name
    res1 = client.post("/api/v1/datasets", json={"name": "   ", "cases": []})
    assert res1.status_code == 422

    # Blank input in case
    res2 = client.post("/api/v1/datasets", json={
        "name": "Valid Name",
        "cases": [{"input": "", "expected_output": "Valid expected", "category": "general"}]
    })
    assert res2.status_code == 422

    # Blank expected_output in case
    res3 = client.post("/api/v1/datasets", json={
        "name": "Valid Name",
        "cases": [{"input": "Valid input", "expected_output": "   ", "category": "general"}]
    })
    assert res3.status_code == 422

    # Invalid category
    res4 = client.post("/api/v1/datasets", json={
        "name": "Valid Name",
        "cases": [{"input": "Valid input", "expected_output": "Valid expected", "category": "nonexistent-category"}]
    })
    assert res4.status_code == 422

def test_list_datasets(client):
    client.post("/api/v1/datasets", json={"name": "Dataset Alpha"})
    client.post("/api/v1/datasets", json={"name": "Dataset Beta"})

    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Newest created dataset first
    assert data[0]["name"] == "Dataset Beta"
    assert data[1]["name"] == "Dataset Alpha"

def test_get_dataset_detail_existing(client):
    created = client.post("/api/v1/datasets", json={
        "name": "Detail Test",
        "cases": [
            {"input": "Input 1", "expected_output": "Expected 1", "category": "factuality"}
        ]
    }).json()

    response = client.get(f"/api/v1/datasets/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == "Detail Test"
    assert len(data["cases"]) == 1
    assert data["cases"][0]["input"] == "Input 1"
    assert data["cases"][0]["category"] == "factuality"

def test_get_dataset_detail_not_found(client):
    response = client.get("/api/v1/datasets/nonexistent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_dataset_detail_with_filters(client):
    created = client.post("/api/v1/datasets", json={
        "name": "Filter Test",
        "cases": [
            {"input": "Password reset help", "expected_output": "Reset link", "category": "account-management"},
            {"input": "Billing inquiry about invoice", "expected_output": "Invoice copy", "category": "billing"},
        ]
    }).json()

    # Search filter
    res_search = client.get(f"/api/v1/datasets/{created['id']}?search=invoice")
    assert res_search.status_code == 200
    assert len(res_search.json()["cases"]) == 1
    assert res_search.json()["cases"][0]["category"] == "billing"

    # Category filter
    res_cat = client.get(f"/api/v1/datasets/{created['id']}?category=account-management")
    assert res_cat.status_code == 200
    assert len(res_cat.json()["cases"]) == 1
    assert res_cat.json()["cases"][0]["input"] == "Password reset help"

def test_add_test_case(client):
    created = client.post("/api/v1/datasets", json={"name": "Add Case Test"}).json()

    case_payload = {
        "input": "How do I upgrade my plan?",
        "expected_output": "Go to Billing > Plans.",
        "category": "billing",
        "metadata": {"source": "faq"}
    }
    res_add = client.post(f"/api/v1/datasets/{created['id']}/cases", json=case_payload)
    assert res_add.status_code == 201
    case_data = res_add.json()
    assert case_data["input"] == "How do I upgrade my plan?"
    assert case_data["category"] == "billing"
    assert case_data["metadata"] == {"source": "faq"}

    # Verify updated case count
    res_get = client.get(f"/api/v1/datasets/{created['id']}")
    assert res_get.json()["case_count"] == 1

def test_add_test_case_not_found(client):
    response = client.post("/api/v1/datasets/nonexistent-id/cases", json={
        "input": "Input", "expected_output": "Output", "category": "general"
    })
    assert response.status_code == 404

def test_update_dataset_metadata(client):
    created = client.post("/api/v1/datasets", json={
        "name": "Old Dataset Name",
        "description": "Old description",
        "cases": [{"input": "Sample", "expected_output": "Sample output", "category": "general"}]
    }).json()

    res_put = client.put(f"/api/v1/datasets/{created['id']}", json={
        "name": "Customer Support Evaluation & Regression Set",
        "description": "Updated description"
    })
    assert res_put.status_code == 200
    data = res_put.json()
    assert data["name"] == "Customer Support Evaluation & Regression Set"
    assert data["description"] == "Updated description"
    assert data["case_count"] == 1

def test_delete_dataset(client):
    created = client.post("/api/v1/datasets", json={"name": "Delete Me"}).json()
    
    res_del = client.delete(f"/api/v1/datasets/{created['id']}")
    assert res_del.status_code == 204

    res_get = client.get(f"/api/v1/datasets/{created['id']}")
    assert res_get.status_code == 404

def test_delete_dataset_not_found(client):
    response = client.delete("/api/v1/datasets/nonexistent-id")
    assert response.status_code == 404
