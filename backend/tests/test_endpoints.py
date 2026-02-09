"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_run_agent_invalid_agent_type(client, sample_project_id):
    """Test agent endpoint with invalid agent type"""
    response = client.post(
        "/v1/run-agent",
        json={
            "project_id": sample_project_id,
            "agent_type": "invalid",
            "input_context": {"test": "data"}
        }
    )
    assert response.status_code == 422  # Validation error


def test_run_agent_invalid_uuid(client):
    """Test agent endpoint with invalid UUID"""
    response = client.post(
        "/v1/run-agent",
        json={
            "project_id": "not-a-uuid",
            "agent_type": "research",
            "input_context": {}
        }
    )
    assert response.status_code == 422  # Validation error


def test_run_agent_success(client, sample_project_id):
    """Test successful agent trigger"""
    response = client.post(
        "/v1/run-agent",
        json={
            "project_id": sample_project_id,
            "agent_type": "research",
            "input_context": {"user_idea": "An AI todo app"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"


def test_get_job_status_not_found(client):
    """Test getting status of non-existent job"""
    response = client.get(
        "/v1/jobs/550e8400-e29b-41d4-a716-446655440000"
    )
    assert response.status_code == 404


def test_validation_error_response_format(client):
    """Test validation error response format"""
    response = client.post(
        "/v1/run-agent",
        json={
            "project_id": "invalid",
            "agent_type": "invalid",
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"] == "VALIDATION_ERROR"
