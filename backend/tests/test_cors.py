from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cors_allowed_origin_localhost_8080():
    """Verify that http://localhost:8080 receives Access-Control-Allow-Origin header."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:8080"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8080"

def test_cors_options_preflight_localhost_8080():
    """Verify OPTIONS preflight request for http://localhost:8080 succeeds with CORS headers."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8080"
    assert "GET" in response.headers.get("access-control-allow-methods", "")

def test_cors_allowed_origin_localhost_5173():
    """Verify that http://localhost:5173 receives Access-Control-Allow-Origin header."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

def test_cors_allowed_origin_localhost_3000():
    """Verify that http://localhost:3000 receives Access-Control-Allow-Origin header."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_allowed_origin_localhost_3002():
    """Verify that http://localhost:3002 receives Access-Control-Allow-Origin header."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3002"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3002"

def test_cors_allowed_origin_localhost_3003():
    """Verify that http://localhost:3003 receives Access-Control-Allow-Origin header."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3003"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3003"

def test_cors_options_preflight_localhost_3003_dashboard():
    """Verify OPTIONS preflight request for http://localhost:3003 to /api/v1/dashboard succeeds with CORS headers."""
    response = client.options(
        "/api/v1/dashboard",
        headers={
            "Origin": "http://localhost:3003",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3003"
    assert "GET" in response.headers.get("access-control-allow-methods", "")

def test_cors_options_preflight_localhost_3002_dashboard():
    """Verify OPTIONS preflight request for http://localhost:3002 to /api/v1/dashboard succeeds with CORS headers."""
    response = client.options(
        "/api/v1/dashboard",
        headers={
            "Origin": "http://localhost:3002",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3002"
    assert "GET" in response.headers.get("access-control-allow-methods", "")

def test_cors_unconfigured_origin_rejected():
    """Verify that an arbitrary unconfigured origin does NOT receive CORS access."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://unauthorized-domain.com"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") != "http://unauthorized-domain.com"
