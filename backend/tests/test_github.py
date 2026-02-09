"""
Tests for GitHub Export Service and Export Endpoint (Phase 6)

Verifies:
  1. Repo name validation
  2. File path sanitization
  3. create_repo API call
  4. create_initial_commit Git Data API flow
  5. export_project orchestration
  6. Export endpoint auth and ownership
  7. SSE streaming endpoint
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.github import (
    REPO_NAME_PATTERN,
    _sanitize_file_path,
    _validate_repo_name,
    create_initial_commit,
    create_repo,
    export_project,
)


def _make_response(status_code: int, json_data: dict) -> httpx.Response:
    """Create an httpx.Response with a dummy request so raise_for_status works."""
    resp = httpx.Response(
        status_code,
        json=json_data,
        request=httpx.Request("POST", "https://api.github.com/test"),
    )
    return resp


# ──────────────────────────────────────────────────────────────
# Validation helpers
# ──────────────────────────────────────────────────────────────


class TestRepoNameValidation:
    """Repo name validation tests"""

    def test_valid_names(self):
        assert _validate_repo_name("my-app") == "my-app"
        assert _validate_repo_name("cool_project123") == "cool_project123"
        assert _validate_repo_name("A.B.c") == "A.B.c"

    def test_invalid_starts_with_hyphen(self):
        with pytest.raises(ValueError, match="Invalid repository name"):
            _validate_repo_name("-bad-name")

    def test_invalid_starts_with_dot(self):
        with pytest.raises(ValueError, match="Invalid repository name"):
            _validate_repo_name(".hidden")

    def test_invalid_empty(self):
        with pytest.raises(ValueError, match="Invalid repository name"):
            _validate_repo_name("")

    def test_invalid_too_long(self):
        with pytest.raises(ValueError, match="Invalid repository name"):
            _validate_repo_name("a" * 101)

    def test_invalid_special_chars(self):
        with pytest.raises(ValueError, match="Invalid repository name"):
            _validate_repo_name("repo with spaces")


class TestFilePathSanitization:
    """File path sanitization tests"""

    def test_valid_path(self):
        assert _sanitize_file_path("src/app/page.tsx") == "src/app/page.tsx"

    def test_backslash_normalization(self):
        assert _sanitize_file_path("src\\app\\page.tsx") == "src/app/page.tsx"

    def test_rejects_traversal(self):
        with pytest.raises(ValueError, match="traversal not allowed"):
            _sanitize_file_path("../../../etc/passwd")

    def test_rejects_absolute_path(self):
        with pytest.raises(ValueError, match="traversal not allowed"):
            _sanitize_file_path("/etc/passwd")


# ──────────────────────────────────────────────────────────────
# create_repo
# ──────────────────────────────────────────────────────────────


class TestCreateRepo:
    """Tests for the create_repo GitHub API call"""

    @pytest.mark.asyncio
    async def test_create_repo_success(self):
        """Should POST to /user/repos and return repo metadata"""
        mock_response = _make_response(
            201,
            {
                "full_name": "testuser/my-app",
                "html_url": "https://github.com/testuser/my-app",
                "clone_url": "https://github.com/testuser/my-app.git",
                "default_branch": "main",
            },
        )

        with patch("app.services.github.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await create_repo(
                token="ghp_test123",
                name="my-app",
                description="Test app",
                private=True,
            )

            assert result["full_name"] == "testuser/my-app"
            assert result["html_url"] == "https://github.com/testuser/my-app"
            assert result["default_branch"] == "main"

            # Verify the POST call
            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args
            assert "/user/repos" in call_kwargs.args[0]
            assert call_kwargs.kwargs["json"]["name"] == "my-app"
            assert call_kwargs.kwargs["json"]["private"] is True

    @pytest.mark.asyncio
    async def test_create_repo_invalid_name(self):
        """Should raise ValueError for invalid repo name without API call"""
        with pytest.raises(ValueError, match="Invalid repository name"):
            await create_repo(token="ghp_test", name="-invalid")


# ──────────────────────────────────────────────────────────────
# create_initial_commit
# ──────────────────────────────────────────────────────────────


class TestCreateInitialCommit:
    """Tests for the Git Data API commit flow"""

    @pytest.mark.asyncio
    async def test_creates_blobs_tree_commit_ref(self):
        """Should call blob→tree→commit→ref in sequence"""
        blob_resp = _make_response(201, {"sha": "blob_sha_123"})
        tree_resp = _make_response(201, {"sha": "tree_sha_456"})
        commit_resp = _make_response(201, {"sha": "commit_sha_789"})
        ref_resp = _make_response(201, {"ref": "refs/heads/main"})

        call_index = {"i": 0}
        responses = [blob_resp, tree_resp, commit_resp, ref_resp]

        async def mock_post(url, **kwargs):
            idx = call_index["i"]
            call_index["i"] += 1
            return responses[idx]

        with patch("app.services.github.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await create_initial_commit(
                token="ghp_test",
                owner="testuser",
                repo="my-app",
                files={"src/index.ts": "console.log('hello')"},
            )

            assert result["commit_sha"] == "commit_sha_789"
            assert result["tree_sha"] == "tree_sha_456"

    @pytest.mark.asyncio
    async def test_rejects_traversal_paths(self):
        """Should reject file paths with directory traversal"""
        with pytest.raises(ValueError, match="traversal not allowed"):
            with patch("app.services.github.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client

                await create_initial_commit(
                    token="ghp_test",
                    owner="testuser",
                    repo="my-app",
                    files={"../../../etc/passwd": "malicious"},
                )


# ──────────────────────────────────────────────────────────────
# export_project
# ──────────────────────────────────────────────────────────────


class TestExportProject:
    """Tests for the export_project orchestrator"""

    @pytest.mark.asyncio
    async def test_export_project_success(self):
        """Should fetch files, create repo, and commit"""
        mock_files = [
            {"path": "src/app/page.tsx", "content": "export default function(){}"},
            {"path": "src/app/layout.tsx", "content": "export default function(){}"},
        ]

        with (
            patch(
                "app.services.database.DatabaseOperations.list_project_files",
                new_callable=AsyncMock,
                return_value=mock_files,
            ),
            patch(
                "app.services.github.create_repo",
                new_callable=AsyncMock,
                return_value={
                    "full_name": "user/my-app",
                    "html_url": "https://github.com/user/my-app",
                    "clone_url": "https://github.com/user/my-app.git",
                    "default_branch": "main",
                },
            ),
            patch(
                "app.services.github.create_initial_commit",
                new_callable=AsyncMock,
                return_value={"commit_sha": "abc123", "tree_sha": "def456"},
            ),
        ):
            result = await export_project(
                token="ghp_test",
                project_id="proj-1",
                repo_name="my-app",
            )

            assert result["repo_url"] == "https://github.com/user/my-app"
            assert result["files_exported"] == 2
            assert result["commit_sha"] == "abc123"

    @pytest.mark.asyncio
    async def test_export_project_no_files(self):
        """Should raise ValueError if no files exist"""
        with patch(
            "app.services.database.DatabaseOperations.list_project_files",
            new_callable=AsyncMock,
            return_value=[],
        ):
            with pytest.raises(ValueError, match="No files to export"):
                await export_project(
                    token="ghp_test",
                    project_id="proj-1",
                    repo_name="my-app",
                )

    @pytest.mark.asyncio
    async def test_export_project_empty_content(self):
        """Should raise ValueError if files have no content"""
        mock_files = [
            {"path": "src/index.ts", "content": ""},
        ]

        with patch(
            "app.services.database.DatabaseOperations.list_project_files",
            new_callable=AsyncMock,
            return_value=mock_files,
        ):
            with pytest.raises(ValueError, match="No files with content"):
                await export_project(
                    token="ghp_test",
                    project_id="proj-1",
                    repo_name="my-app",
                )


# ──────────────────────────────────────────────────────────────
# Export endpoint
# ──────────────────────────────────────────────────────────────

PROJECT_ID = "550e8400-e29b-41d4-a716-446655440000"
TEST_USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

SAMPLE_PROJECT = {
    "id": PROJECT_ID,
    "user_id": TEST_USER_ID,
    "title": "Test Project",
    "mode": "builder",
    "status": "in-progress",
}


class TestExportEndpoint:
    """Tests for POST /v1/projects/{id}/export/github"""

    def test_export_endpoint_success(self, client, auth_headers):
        """Should export project and return repo URL"""
        with (
            patch(
                "app.api.endpoints.projects.DatabaseOperations.get_project",
                new_callable=AsyncMock,
                return_value=SAMPLE_PROJECT,
            ),
            patch(
                "app.services.github.export_project",
                new_callable=AsyncMock,
                return_value={
                    "repo_url": "https://github.com/user/my-app",
                    "clone_url": "https://github.com/user/my-app.git",
                    "commit_sha": "abc123",
                    "files_exported": 3,
                },
            ),
        ):
            response = client.post(
                f"/v1/projects/{PROJECT_ID}/export/github",
                json={
                    "repo_name": "my-app",
                    "github_token": "ghp_test_token_123",
                    "private": True,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["repo_url"] == "https://github.com/user/my-app"
            assert data["files_exported"] == 3

    def test_export_requires_auth(self, client):
        """Should require authentication"""
        response = client.post(
            f"/v1/projects/{PROJECT_ID}/export/github",
            json={
                "repo_name": "my-app",
                "github_token": "ghp_test",
            },
        )
        assert response.status_code == 401

    def test_export_validates_repo_name(self, client, auth_headers):
        """Should reject invalid repo names via schema validation"""
        response = client.post(
            f"/v1/projects/{PROJECT_ID}/export/github",
            json={
                "repo_name": "-invalid name!",
                "github_token": "ghp_test",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_export_no_files_returns_400(self, client, auth_headers):
        """Should return 400 when project has no files"""
        with (
            patch(
                "app.api.endpoints.projects.DatabaseOperations.get_project",
                new_callable=AsyncMock,
                return_value=SAMPLE_PROJECT,
            ),
            patch(
                "app.services.github.export_project",
                new_callable=AsyncMock,
                side_effect=ValueError("No files to export — generate code first"),
            ),
        ):
            response = client.post(
                f"/v1/projects/{PROJECT_ID}/export/github",
                json={
                    "repo_name": "my-app",
                    "github_token": "ghp_test",
                },
                headers=auth_headers,
            )

            assert response.status_code == 400


# ──────────────────────────────────────────────────────────────
# SSE Streaming endpoint
# ──────────────────────────────────────────────────────────────


# Use valid UUIDs for SSE streaming tests (InputValidator.validate_uuid requires them)
STREAM_JOB_1 = "11111111-1111-1111-1111-111111111111"
STREAM_JOB_2 = "22222222-2222-2222-2222-222222222222"
STREAM_JOB_3 = "33333333-3333-3333-3333-333333333333"
STREAM_JOB_4 = "44444444-4444-4444-4444-444444444444"


class TestSSEStreaming:
    """Tests for GET /v1/agents/jobs/{job_id}/stream"""

    def test_stream_completed_job(self, client, auth_headers, fresh_job_store):
        """Should stream complete event for finished job"""
        from app.schemas.protocol import JobStatusType

        # Create and complete a job
        job = fresh_job_store.create_job(
            job_id=STREAM_JOB_1,
            project_id=PROJECT_ID,
            agent_type="research",
            input_context={},
        )
        fresh_job_store.update_job(
            STREAM_JOB_1,
            status=JobStatusType.COMPLETED,
            progress=100.0,
            result={"app_name": "Test"},
        )

        response = client.get(
            f"/v1/agents/jobs/{STREAM_JOB_1}/stream",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        # Parse SSE events
        text = response.text
        assert "event: complete" in text
        assert '"status": "completed"' in text
        assert '"progress": 100.0' in text

    def test_stream_failed_job(self, client, auth_headers, fresh_job_store):
        """Should stream error event for failed job"""
        from app.schemas.protocol import JobStatusType

        fresh_job_store.create_job(
            job_id=STREAM_JOB_2,
            project_id=PROJECT_ID,
            agent_type="research",
            input_context={},
        )
        fresh_job_store.update_job(
            STREAM_JOB_2,
            error="Agent crashed",
        )

        response = client.get(
            f"/v1/agents/jobs/{STREAM_JOB_2}/stream",
            headers=auth_headers,
        )

        assert response.status_code == 200
        text = response.text
        assert "event: error" in text
        assert "Agent crashed" in text

    def test_stream_nonexistent_job(self, client, auth_headers):
        """Should 404 for non-existent job"""
        response = client.get(
            "/v1/agents/jobs/00000000-0000-0000-0000-000000000000/stream",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_stream_requires_auth(self, client, fresh_job_store):
        """Should require authentication"""
        fresh_job_store.create_job(
            job_id=STREAM_JOB_3,
            project_id=PROJECT_ID,
            agent_type="research",
            input_context={},
        )

        response = client.get(f"/v1/agents/jobs/{STREAM_JOB_3}/stream")
        assert response.status_code == 401

    def test_stream_progress_event(self, client, auth_headers, fresh_job_store):
        """Should stream progress events for running jobs that then complete"""
        from app.schemas.protocol import JobStatusType

        fresh_job_store.create_job(
            job_id=STREAM_JOB_4,
            project_id=PROJECT_ID,
            agent_type="research",
            input_context={},
        )
        # Job is running with 50% progress, will immediately be seen
        fresh_job_store.update_job(
            STREAM_JOB_4,
            status=JobStatusType.RUNNING,
            progress=50.0,
        )

        # We'll patch asyncio.sleep and update the job to completed during streaming
        original_sleep = asyncio.sleep
        call_count = {"n": 0}

        async def fake_sleep(duration):
            call_count["n"] += 1
            if call_count["n"] >= 1:
                # Complete the job after first poll
                fresh_job_store.update_job(
                    STREAM_JOB_4,
                    status=JobStatusType.COMPLETED,
                    progress=100.0,
                    result={"done": True},
                )
            await original_sleep(0)  # Don't actually sleep

        with patch(
            "app.api.endpoints.agents.asyncio.sleep",
            side_effect=fake_sleep,
        ):
            response = client.get(
                f"/v1/agents/jobs/{STREAM_JOB_4}/stream",
                headers=auth_headers,
            )

        assert response.status_code == 200
        text = response.text
        # Should have a progress event followed by complete
        assert "event: progress" in text
        assert "event: complete" in text
