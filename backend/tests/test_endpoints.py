"""
Tests for API endpoints
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_run_agent_requires_auth(client, sample_project_id):
    """Test agent endpoint rejects unauthenticated requests"""
    response = client.post(
        "/v1/agents/run-agent",
        json={
            "project_id": sample_project_id,
            "agent_type": "research",
            "input_context": {},
        },
    )
    assert response.status_code == 401


def test_run_agent_invalid_agent_type(client, sample_project_id, auth_headers):
    """Test agent endpoint with invalid agent type"""
    response = client.post(
        "/v1/agents/run-agent",
        json={
            "project_id": sample_project_id,
            "agent_type": "invalid",
            "input_context": {"test": "data"},
        },
        headers=auth_headers,
    )
    assert response.status_code == 422  # Validation error


def test_run_agent_invalid_uuid(client, auth_headers):
    """Test agent endpoint with invalid UUID"""
    response = client.post(
        "/v1/agents/run-agent",
        json={
            "project_id": "not-a-uuid",
            "agent_type": "research",
            "input_context": {},
        },
        headers=auth_headers,
    )
    assert response.status_code == 422  # Validation error


def test_run_agent_success(client, sample_project_id, auth_headers, test_user_id):
    """Test successful agent trigger"""
    with patch(
        "app.services.database.DatabaseOperations.get_project",
        new_callable=AsyncMock,
        return_value={"id": sample_project_id, "user_id": test_user_id},
    ):
        response = client.post(
            "/v1/agents/run-agent",
            json={
                "project_id": sample_project_id,
                "agent_type": "research",
                "input_context": {"user_idea": "An AI todo app"},
            },
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"


def test_get_job_status_not_found(client, auth_headers):
    """Test getting status of non-existent job"""
    response = client.get(
        "/v1/agents/jobs/550e8400-e29b-41d4-a716-446655440000",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_get_job_status_found(client, fresh_job_store, sample_project_id, auth_headers):
    """Test getting status of an existing job"""
    fresh_job_store.create_job(
        job_id="550e8400-e29b-41d4-a716-446655440001",
        project_id=sample_project_id,
        agent_type="research",
        input_context={},
    )
    response = client.get(
        "/v1/agents/jobs/550e8400-e29b-41d4-a716-446655440001",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["agent_type"] == "research"


def test_list_project_jobs(client, fresh_job_store, sample_project_id, auth_headers):
    """Test listing jobs for a project"""
    for i in range(3):
        fresh_job_store.create_job(
            job_id=f"550e8400-e29b-41d4-a716-44665544000{i}",
            project_id=sample_project_id,
            agent_type="code",
            input_context={},
        )
    response = client.get(
        f"/v1/agents/jobs/{sample_project_id}/list",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3


def test_validation_error_response_format(client, auth_headers):
    """Test validation error response format"""
    response = client.post(
        "/v1/agents/run-agent",
        json={
            "project_id": "invalid",
            "agent_type": "invalid",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"] == "VALIDATION_ERROR"


def test_create_file_body_based(client, sample_project_id, auth_headers, test_user_id):
    """Test file creation endpoint uses request body (not query params)"""
    with (
        patch(
            "app.api.endpoints.projects.DatabaseOperations.get_project",
            new_callable=AsyncMock,
            return_value={"id": sample_project_id, "user_id": test_user_id},
        ),
        patch(
            "app.api.endpoints.projects.DatabaseOperations.create_file",
            new_callable=AsyncMock,
            return_value={
                "id": "file-1",
                "project_id": sample_project_id,
                "path": "src/app/page.tsx",
                "content": "export default function() {}",
                "language": "typescript",
            },
        ),
    ):
        response = client.post(
            f"/v1/projects/{sample_project_id}/files",
            json={
                "path": "src/app/page.tsx",
                "content": "export default function() {}",
                "language": "typescript",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["path"] == "src/app/page.tsx"


def test_create_file_rejects_path_traversal(client, sample_project_id, auth_headers):
    """Test file creation rejects path traversal attempts"""
    response = client.post(
        f"/v1/projects/{sample_project_id}/files",
        json={
            "path": "../../../etc/passwd",
            "content": "malicious",
            "language": "typescript",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_file_requires_src_prefix(client, sample_project_id, auth_headers):
    """Test file creation requires paths starting with src/"""
    response = client.post(
        f"/v1/projects/{sample_project_id}/files",
        json={
            "path": "public/index.html",
            "content": "<html></html>",
            "language": "html",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422
