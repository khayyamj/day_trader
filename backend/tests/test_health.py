"""Tests for health endpoint."""
import pytest


@pytest.mark.unit
def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "trading-api"
    assert "version" in data


@pytest.mark.unit
def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data


@pytest.mark.unit
def test_request_timing_header(client):
    """Test that request timing header is added."""
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Process-Time" in response.headers
    # Verify it's a valid float
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0
