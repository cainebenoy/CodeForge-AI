"""
Tests for project and file CRUD endpoints.

Covers: list projects (paginated), get/update/delete project,
get/update/delete file, authorization checks.
"""

from unittest.mock import AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_PROJECT_ID = "550e8400-e29b-41d4-a716-446655440000"


def _project_row(user_id: str, project_id: str = SAMPLE_PROJECT_ID, **overrides):
    """Build a fake project DB row."""
    base = {
        "id": project_id,
        "user_id": user_id,
        "title": "Test Project",
        "description": "desc",
        "mode": "builder",
        "status": "planning",
        "tech_stack": ["react"],
        "requirements_spec": None,
        "architecture_spec": None,
    }
    base.update(overrides)
    return base


def _file_row(project_id: str = SAMPLE_PROJECT_ID, **overrides):
    """Build a fake file DB row."""
    base = {
        "id": "file-1",
        "project_id": project_id,
        "path": "src/app/page.tsx",
        "content": "export default function Page() {}",
        "language": "typescript",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# List user projects
# ---------------------------------------------------------------------------


class TestListProjects:
    def test_list_projects_requires_auth(self, client):
        response = client.get("/v1/projects/")
        assert response.status_code == 401

    def test_list_projects_success(self, client, auth_headers, test_user_id):
        with patch(
            "app.services.database.DatabaseOperations.list_user_projects",
            new_callable=AsyncMock,
            return_value={
                "items": [_project_row(test_user_id)],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "has_more": False,
            },
        ):
            response = client.get("/v1/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["has_more"] is False

    def test_list_projects_with_filters(self, client, auth_headers, test_user_id):
        with patch(
            "app.services.database.DatabaseOperations.list_user_projects",
            new_callable=AsyncMock,
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 10,
                "has_more": False,
            },
        ) as mock_list:
            response = client.get(
                "/v1/projects/?mode=student&status=planning&page=2&page_size=10",
                headers=auth_headers,
            )
        assert response.status_code == 200
        mock_list.assert_awaited_once_with(
            user_id=test_user_id,
            page=2,
            page_size=10,
            mode="student",
            status="planning",
        )

    def test_list_projects_rejects_invalid_page_size(self, client, auth_headers):
        response = client.get(
            "/v1/projects/?page_size=100",
            headers=auth_headers,
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Delete (archive) project
# ---------------------------------------------------------------------------


class TestDeleteProject:
    def test_delete_project_requires_auth(self, client):
        response = client.delete(f"/v1/projects/{SAMPLE_PROJECT_ID}")
        assert response.status_code == 401

    def test_delete_project_success(self, client, auth_headers, test_user_id):
        with patch(
            "app.services.database.DatabaseOperations.delete_project",
            new_callable=AsyncMock,
            return_value=_project_row(test_user_id, status="archived"),
        ):
            response = client.delete(
                f"/v1/projects/{SAMPLE_PROJECT_ID}",
                headers=auth_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Project archived"
        assert data["project_id"] == SAMPLE_PROJECT_ID

    def test_delete_project_wrong_owner(self, client, auth_headers):
        """Simulates PermissionError from DB layer."""
        from app.core.exceptions import PermissionError as PermErr

        with patch(
            "app.services.database.DatabaseOperations.delete_project",
            new_callable=AsyncMock,
            side_effect=PermErr("You do not have access to this project"),
        ):
            response = client.delete(
                f"/v1/projects/{SAMPLE_PROJECT_ID}",
                headers=auth_headers,
            )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Get project with ownership check
# ---------------------------------------------------------------------------


class TestGetProject:
    def test_get_project_requires_auth(self, client):
        response = client.get(f"/v1/projects/{SAMPLE_PROJECT_ID}")
        assert response.status_code == 401

    def test_get_project_success(self, client, auth_headers, test_user_id):
        with patch(
            "app.services.database.DatabaseOperations.get_project",
            new_callable=AsyncMock,
            return_value=_project_row(test_user_id),
        ):
            response = client.get(
                f"/v1/projects/{SAMPLE_PROJECT_ID}",
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["id"] == SAMPLE_PROJECT_ID

    def test_get_project_not_found(self, client, auth_headers):
        from app.core.exceptions import ResourceNotFoundError

        with patch(
            "app.services.database.DatabaseOperations.get_project",
            new_callable=AsyncMock,
            side_effect=ResourceNotFoundError("Project", SAMPLE_PROJECT_ID),
        ):
            response = client.get(
                f"/v1/projects/{SAMPLE_PROJECT_ID}",
                headers=auth_headers,
            )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Single file CRUD
# ---------------------------------------------------------------------------


class TestGetFile:
    def test_get_file_success(self, client, auth_headers, test_user_id):
        with (
            patch(
                "app.services.database.DatabaseOperations.get_project",
                new_callable=AsyncMock,
                return_value=_project_row(test_user_id),
            ),
            patch(
                "app.services.database.DatabaseOperations.get_file",
                new_callable=AsyncMock,
                return_value=_file_row(),
            ),
        ):
            response = client.get(
                f"/v1/projects/{SAMPLE_PROJECT_ID}/files/src/app/page.tsx",
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["path"] == "src/app/page.tsx"

    def test_get_file_not_found(self, client, auth_headers, test_user_id):
        from app.core.exceptions import ResourceNotFoundError

        with (
            patch(
                "app.services.database.DatabaseOperations.get_project",
                new_callable=AsyncMock,
                return_value=_project_row(test_user_id),
            ),
            patch(
                "app.services.database.DatabaseOperations.get_file",
                new_callable=AsyncMock,
                side_effect=ResourceNotFoundError("File", "src/nope.tsx"),
            ),
        ):
            response = client.get(
                f"/v1/projects/{SAMPLE_PROJECT_ID}/files/src/nope.tsx",
                headers=auth_headers,
            )
        assert response.status_code == 404


class TestUpdateFile:
    def test_update_file_success(self, client, auth_headers, test_user_id):
        with (
            patch(
                "app.services.database.DatabaseOperations.get_project",
                new_callable=AsyncMock,
                return_value=_project_row(test_user_id),
            ),
            patch(
                "app.services.database.DatabaseOperations.update_file",
                new_callable=AsyncMock,
                return_value=_file_row(content="new content"),
            ),
        ):
            response = client.put(
                f"/v1/projects/{SAMPLE_PROJECT_ID}/files/src/app/page.tsx",
                json={"content": "new content"},
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["content"] == "new content"


class TestDeleteFile:
    def test_delete_file_success(self, client, auth_headers, test_user_id):
        with (
            patch(
                "app.services.database.DatabaseOperations.get_project",
                new_callable=AsyncMock,
                return_value=_project_row(test_user_id),
            ),
            patch(
                "app.services.database.DatabaseOperations.delete_file",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.delete(
                f"/v1/projects/{SAMPLE_PROJECT_ID}/files/src/app/page.tsx",
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["message"] == "File deleted"

    def test_delete_file_rejects_traversal(self, client, auth_headers, test_user_id):
        """Path containing '..' should be rejected by validation."""
        with patch(
            "app.services.database.DatabaseOperations.get_project",
            new_callable=AsyncMock,
            return_value=_project_row(test_user_id),
        ):
            response = client.delete(
                f"/v1/projects/{SAMPLE_PROJECT_ID}/files/src/..%2F..%2Fetc%2Fpasswd",
                headers=auth_headers,
            )
        # validate_file_path should reject the '..' in the path
        assert response.status_code in (400, 422, 500)


# ---------------------------------------------------------------------------
# Authorization: cannot access another user's project
# ---------------------------------------------------------------------------


class TestProjectAuthorization:
    def test_cannot_update_others_project(self, client, auth_headers):
        """Ownership mismatch returns 403."""
        from app.core.exceptions import PermissionError as PermErr

        with patch(
            "app.services.database.DatabaseOperations.get_project",
            new_callable=AsyncMock,
            side_effect=PermErr("You do not have access to this project"),
        ):
            response = client.put(
                f"/v1/projects/{SAMPLE_PROJECT_ID}",
                json={"title": "Hijacked"},
                headers=auth_headers,
            )
        assert response.status_code == 403

    def test_cannot_list_files_of_others_project(self, client, auth_headers):
        from app.core.exceptions import PermissionError as PermErr

        with patch(
            "app.services.database.DatabaseOperations.get_project",
            new_callable=AsyncMock,
            side_effect=PermErr("You do not have access to this project"),
        ):
            response = client.get(
                f"/v1/projects/{SAMPLE_PROJECT_ID}/files",
                headers=auth_headers,
            )
        assert response.status_code == 403
