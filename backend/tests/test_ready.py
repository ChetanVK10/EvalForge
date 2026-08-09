from unittest.mock import MagicMock
from app.core.database import get_db
from app.main import app

def test_readiness_endpoint_connected(client):
    mock_db = MagicMock()
    mock_db.execute.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
    finally:
        app.dependency_overrides.clear()

def test_readiness_endpoint_disconnected(client):
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("Database connection failed")

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["database"] == "disconnected"
    finally:
        app.dependency_overrides.clear()
