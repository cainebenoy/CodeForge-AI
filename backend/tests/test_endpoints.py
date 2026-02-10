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


def test_list_project_jobs(
    client, fresh_job_store, sample_project_id, auth_headers, test_user_id
):
    """Test listing jobs for a project"""
    for i in range(3):
        fresh_job_store.create_job(
            job_id=f"550e8400-e29b-41d4-a716-44665544000{i}",
            project_id=sample_project_id,
            agent_type="code",
            input_context={},
        )
    with patch(
        "app.services.database.DatabaseOperations.get_project",
        new_callable=AsyncMock,
        return_value={"id": sample_project_id, "user_id": test_user_id},
    ):
        response = client.get(
            f"/v1/agents/jobs/{sample_project_id}/list",
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


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


# ──────────────────────────────────────────────────────────────
# Refactor endpoint
# ──────────────────────────────────────────────────────────────


def test_refactor_file_success(client, sample_project_id, auth_headers, test_user_id):
    """POST /v1/projects/{id}/files/{path}/refactor should return refactored code"""
    from app.schemas.protocol import RefactorResult

    mock_refactor_result = RefactorResult(
        original_code="const x = 1;",
        refactored_code="const x: number = 1;",
        explanation="Added explicit type annotation for type safety.",
        full_file_content='import React from "react";\nconst x: number = 1;',
    )

    with (
        patch(
            "app.api.endpoints.projects.DatabaseOperations.get_project",
            new_callable=AsyncMock,
            return_value={"id": sample_project_id, "user_id": test_user_id},
        ),
        patch(
            "app.api.endpoints.projects.DatabaseOperations.get_file",
            new_callable=AsyncMock,
            return_value={
                "id": "file-1",
                "project_id": sample_project_id,
                "path": "src/app/page.tsx",
                "content": 'import React from "react";\nconst x = 1;',
                "language": "typescript",
            },
        ),
        patch(
            "app.agents.code_agent.run_refactor_agent",
            new_callable=AsyncMock,
            return_value=mock_refactor_result,
        ),
    ):
        response = client.post(
            f"/v1/projects/{sample_project_id}/files/src/app/page.tsx/refactor",
            json={
                "selected_code": "const x = 1;",
                "instruction": "Add TypeScript type annotation",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["refactored_code"] == "const x: number = 1;"
        assert "type annotation" in data["explanation"].lower()


def test_refactor_file_with_apply(
    client, sample_project_id, auth_headers, test_user_id
):
    """Refactor with apply=true should also update the file in DB"""
    from app.schemas.protocol import RefactorResult

    mock_refactor_result = RefactorResult(
        original_code="const x = 1;",
        refactored_code="const x: number = 1;",
        explanation="Added type annotation.",
        full_file_content='import React from "react";\nconst x: number = 1;',
    )

    with (
        patch(
            "app.api.endpoints.projects.DatabaseOperations.get_project",
            new_callable=AsyncMock,
            return_value={"id": sample_project_id, "user_id": test_user_id},
        ),
        patch(
            "app.api.endpoints.projects.DatabaseOperations.get_file",
            new_callable=AsyncMock,
            return_value={
                "id": "file-1",
                "project_id": sample_project_id,
                "path": "src/app/page.tsx",
                "content": 'import React from "react";\nconst x = 1;',
                "language": "typescript",
            },
        ),
        patch(
            "app.agents.code_agent.run_refactor_agent",
            new_callable=AsyncMock,
            return_value=mock_refactor_result,
        ),
        patch(
            "app.api.endpoints.projects.DatabaseOperations.update_file",
            new_callable=AsyncMock,
            return_value={
                "id": "file-1",
                "content": mock_refactor_result.full_file_content,
            },
        ) as mock_update,
    ):
        response = client.post(
            f"/v1/projects/{sample_project_id}/files/src/app/page.tsx/refactor?apply=true",
            json={
                "selected_code": "const x = 1;",
                "instruction": "Add type annotation",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        mock_update.assert_called_once()


def test_refactor_file_requires_auth(client, sample_project_id):
    """Refactor endpoint should require authentication"""
    response = client.post(
        f"/v1/projects/{sample_project_id}/files/src/app/page.tsx/refactor",
        json={
            "selected_code": "const x = 1;",
            "instruction": "Add type annotation",
        },
    )
    assert response.status_code == 401


def test_refactor_rejects_path_traversal(client, sample_project_id, auth_headers):
    """Refactor endpoint should reject path traversal.

    FastAPI normalises '../' in URL path segments before routing,
    returning 404 (no matching route).  This is a valid security
    outcome – the handler is never reached with a malicious path.
    """
    with patch(
        "app.api.endpoints.projects.DatabaseOperations.get_project",
        new_callable=AsyncMock,
        return_value={"id": sample_project_id, "user_id": "test"},
    ):
        response = client.post(
            f"/v1/projects/{sample_project_id}/files/../../../etc/passwd/refactor",
            json={
                "selected_code": "content",
                "instruction": "Refactor",
            },
            headers=auth_headers,
        )
        # FastAPI/Starlette resolves '..' before routing → 404
        assert response.status_code in (400, 404)


# ──────────────────────────────────────────────────────────────
# Clarification respond endpoint
# ──────────────────────────────────────────────────────────────


def test_respond_to_clarification_job_not_found(client, auth_headers):
    """POST /v1/agents/jobs/{id}/respond should 404 if job doesn't exist"""
    response = client.post(
        "/v1/agents/jobs/550e8400-e29b-41d4-a716-446655440000/respond",
        json={"answers": [{"question": "Q?", "answer": "A."}]},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_respond_to_clarification_no_pending_questions(
    client, fresh_job_store, sample_project_id, auth_headers
):
    """Should reject respond if job has no pending clarification"""
    from app.schemas.protocol import JobStatusType

    job = fresh_job_store.create_job(
        job_id="550e8400-e29b-41d4-a716-446655440001",
        project_id=sample_project_id,
        agent_type="research",
        input_context={},
    )
    # Complete the job with a regular result (no clarification)
    fresh_job_store.update_job(
        "550e8400-e29b-41d4-a716-446655440001",
        status=JobStatusType.COMPLETED,
        result={"app_name": "Test"},
    )

    response = client.post(
        "/v1/agents/jobs/550e8400-e29b-41d4-a716-446655440001/respond",
        json={"answers": [{"question": "Q?", "answer": "A."}]},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_respond_to_clarification_success(
    client, fresh_job_store, sample_project_id, auth_headers, test_user_id
):
    """Should create a follow-up job when responding to clarification"""
    from app.schemas.protocol import JobStatusType

    job = fresh_job_store.create_job(
        job_id="550e8400-e29b-41d4-a716-446655440001",
        project_id=sample_project_id,
        agent_type="research",
        input_context={"user_idea": "A CRM app"},
    )
    # Set up as a clarification job (WAITING_FOR_INPUT status)
    fresh_job_store.update_job(
        "550e8400-e29b-41d4-a716-446655440001",
        status=JobStatusType.WAITING_FOR_INPUT,
        result={
            "is_complete": False,
            "questions": [
                {
                    "question": "Need payments?",
                    "why": "Scope.",
                    "options": ["Yes", "No"],
                }
            ],
        },
    )
    # Set clarification data on the job object
    stored_job = fresh_job_store.get_job("550e8400-e29b-41d4-a716-446655440001")
    stored_job.clarification_data = {
        "original_context": {"user_idea": "A CRM app"},
        "project_id": sample_project_id,
    }

    with patch(
        "app.services.database.DatabaseOperations.get_project",
        new_callable=AsyncMock,
        return_value={"id": sample_project_id, "user_id": test_user_id},
    ):
        response = client.post(
            "/v1/agents/jobs/550e8400-e29b-41d4-a716-446655440001/respond",
            json={"answers": [{"question": "Need payments?", "answer": "No"}]},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    # The new job should be different from the original
    assert data["job_id"] != "550e8400-e29b-41d4-a716-446655440001"


def test_respond_requires_auth(client):
    """Respond endpoint should require authentication"""
    response = client.post(
        "/v1/agents/jobs/550e8400-e29b-41d4-a716-446655440001/respond",
        json={"answers": [{"question": "Q?", "answer": "A."}]},
    )
    assert response.status_code == 401


# ──────────────────────────────────────────────────────────────
# Builder pipeline endpoint
# ──────────────────────────────────────────────────────────────


def test_run_pipeline_requires_auth(client):
    """Pipeline endpoint should require authentication"""
    response = client.post(
        "/v1/agents/run-pipeline",
        json={
            "project_id": "550e8400-e29b-41d4-a716-446655440000",
            "agent_type": "builder",
            "input_context": {"user_idea": "A todo app"},
        },
    )
    assert response.status_code == 401


def test_run_pipeline_success(client, sample_project_id, auth_headers, test_user_id):
    """Pipeline endpoint should accept valid request and return queued job"""
    with patch(
        "app.services.database.DatabaseOperations.get_project",
        new_callable=AsyncMock,
        return_value={"id": sample_project_id, "user_id": test_user_id},
    ):
        response = client.post(
            "/v1/agents/run-pipeline",
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


# ──────────────────────────────────────────────────────────────
# Job ownership authorization
# ──────────────────────────────────────────────────────────────


def test_job_status_forbidden_for_wrong_user(
    client, fresh_job_store, sample_project_id, auth_headers
):
    """Job status endpoint should return 403 when job belongs to another user"""
    fresh_job_store.create_job(
        job_id="550e8400-e29b-41d4-a716-446655440099",
        project_id=sample_project_id,
        agent_type="research",
        input_context={},
        user_id="other-user-id",
    )
    response = client.get(
        "/v1/agents/jobs/550e8400-e29b-41d4-a716-446655440099",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_stream_forbidden_for_wrong_user(
    client, fresh_job_store, sample_project_id, auth_headers
):
    """Stream endpoint should return 403 when job belongs to another user"""
    fresh_job_store.create_job(
        job_id="550e8400-e29b-41d4-a716-446655440098",
        project_id=sample_project_id,
        agent_type="research",
        input_context={},
        user_id="other-user-id",
    )
    response = client.get(
        "/v1/agents/jobs/550e8400-e29b-41d4-a716-446655440098/stream",
        headers=auth_headers,
    )
    assert response.status_code == 403


# ──────────────────────────────────────────────────────────────
# Roadmap agent type
# ──────────────────────────────────────────────────────────────


def test_run_agent_roadmap_type(client, sample_project_id, auth_headers, test_user_id):
    """Run-agent endpoint should accept roadmap agent type"""
    with patch(
        "app.services.database.DatabaseOperations.get_project",
        new_callable=AsyncMock,
        return_value={"id": sample_project_id, "user_id": test_user_id},
    ):
        response = client.post(
            "/v1/agents/run-agent",
            json={
                "project_id": sample_project_id,
                "agent_type": "roadmap",
                "input_context": {"user_idea": "A learning roadmap app"},
            },
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
