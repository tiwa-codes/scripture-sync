"""
Tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns status"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "status" in data
    assert data["status"] == "running"


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "locked" in data
    assert "active_connections" in data


def test_verses_endpoint(client):
    """Test verses listing endpoint"""
    response = client.get("/verses/")
    assert response.status_code == 200
    data = response.json()
    assert "verses" in data
    assert isinstance(data["verses"], list)


def test_search_endpoint(client):
    """Test search endpoint"""
    response = client.get("/search?q=God+so+loved")
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert "latency_ms" in data


def test_search_reference_query(client):
    """Ensure scripture references resolve directly"""
    response = client.get("/search?q=Genesis+1:1")
    assert response.status_code == 200
    data = response.json()
    assert data["matches"], "Expected at least one reference match"
    match = data["matches"][0]
    assert match["book"] == "Genesis"
    assert match["chapter"] == 1
    assert match["verse"] == 1


def test_lock_endpoint(client):
    """Test lock endpoint"""
    response = client.post(
        "/lock",
        json={"locked": True, "verse_id": 1}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["locked"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
