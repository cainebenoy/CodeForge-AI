"""
Tests for Student Mode API (Phase 5)

Verifies:
  1. Roadmap creation with agent invocation
  2. Roadmap retrieval and progress updates
  3. Session create/list
  4. Progress computation
  5. Auth enforcement and ownership checks
  6. Student-mode-only validation
  7. Roadmap agent LCEL chain
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.protocol import LearningModule, LearningRoadmap
from tests.conftest import mock_lcel_chain

# ──────────────────────────────────────────────────────────────
# Sample data
# ──────────────────────────────────────────────────────────────

STUDENT_PROJECT_ID = "550e8400-e29b-41d4-a716-446655440000"

SAMPLE_STUDENT_PROJECT = {
    "id": STUDENT_PROJECT_ID,
    "user_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "title": "Learn React",
    "mode": "student",
    "status": "planning",
    "requirements_spec": {
        "app_name": "Todo App",
        "features": ["add tasks", "mark complete"],
    },
}

BUILDER_PROJECT = {
    "id": STUDENT_PROJECT_ID,
    "user_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "title": "Build Fast",
    "mode": "builder",
    "status": "planning",
}

SAMPLE_ROADMAP = LearningRoadmap(
    modules=[
        LearningModule(
            title="React Basics",
            description="Learn the fundamentals of React components and JSX.",
            concepts=["JSX", "Components", "Props"],
            exercises=["Create a Hello World component"],
            estimated_hours=4.0,
        ),
        LearningModule(
            title="State Management",
            description="Understand React state with useState and context.",
            concepts=["useState", "useEffect", "Context API"],
            exercises=["Build a counter app"],
            estimated_hours=6.0,
        ),
    ],
    total_estimated_hours=10.0,
    prerequisites=["JavaScript basics", "HTML/CSS"],
    learning_objectives=["Build a complete React application"],
)

SAMPLE_ROADMAP_DB = {
    "id": "rrrrrrrr-rrrr-rrrr-rrrr-rrrrrrrrrrrr",
    "project_id": STUDENT_PROJECT_ID,
    "modules": SAMPLE_ROADMAP.model_dump()["modules"],
    "current_step_index": 0,
    "created_at": "2025-01-01T00:00:00Z",
}


def _mock_db_for_student():
    """Set up mock DatabaseOperations for student tests"""
    return patch("app.api.endpoints.student.DatabaseOperations")


# ──────────────────────────────────────────────────────────────
# Roadmap Agent
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_roadmap_agent_returns_learning_roadmap():
    """Roadmap agent should return a valid LearningRoadmap"""
    with mock_lcel_chain("app.agents.roadmap_agent", SAMPLE_ROADMAP) as mocks:
        from app.agents.roadmap_agent import run_roadmap_agent

        result = await run_roadmap_agent(
            requirements_spec='{"app_name": "Todo"}',
            skill_level="beginner",
        )

        assert isinstance(result, LearningRoadmap)
        assert len(result.modules) == 2
        assert result.total_estimated_hours == 10.0
        mocks["model"].assert_called_once_with("pedagogy")


# ──────────────────────────────────────────────────────────────
# Roadmap endpoints
# ──────────────────────────────────────────────────────────────


class TestRoadmapEndpoints:
    """Roadmap CRUD endpoint tests"""

    def test_create_roadmap(self, client, auth_headers):
        """POST /v1/student/{id}/roadmap should create a roadmap"""
        with (
            _mock_db_for_student() as mock_db,
            patch(
                "app.agents.roadmap_agent.run_roadmap_agent",
                new_callable=AsyncMock,
                return_value=SAMPLE_ROADMAP,
            ),
        ):
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)
            mock_db.create_roadmap = AsyncMock(return_value=SAMPLE_ROADMAP_DB)

            response = client.post(
                f"/v1/student/{STUDENT_PROJECT_ID}/roadmap",
                json={"skill_level": "beginner"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_modules"] == 2
            assert data["total_estimated_hours"] == 10.0

    def test_create_roadmap_no_requirements(self, client, auth_headers):
        """Should fail if project has no requirements_spec"""
        project_no_reqs = {**SAMPLE_STUDENT_PROJECT, "requirements_spec": None}

        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=project_no_reqs)

            response = client.post(
                f"/v1/student/{STUDENT_PROJECT_ID}/roadmap",
                json={"skill_level": "beginner"},
                headers=auth_headers,
            )

            assert response.status_code == 400

    def test_create_roadmap_builder_mode_rejected(self, client, auth_headers):
        """Should reject roadmap creation for builder-mode projects"""
        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=BUILDER_PROJECT)

            response = client.post(
                f"/v1/student/{STUDENT_PROJECT_ID}/roadmap",
                json={"skill_level": "beginner"},
                headers=auth_headers,
            )

            assert response.status_code == 400

    def test_get_roadmap(self, client, auth_headers):
        """GET /v1/student/{id}/roadmap should return the roadmap"""
        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)
            mock_db.get_roadmap = AsyncMock(return_value=SAMPLE_ROADMAP_DB)

            response = client.get(
                f"/v1/student/{STUDENT_PROJECT_ID}/roadmap",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == SAMPLE_ROADMAP_DB["id"]

    def test_get_roadmap_not_found(self, client, auth_headers):
        """GET /v1/student/{id}/roadmap should 404 if no roadmap"""
        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)
            mock_db.get_roadmap = AsyncMock(return_value=None)

            response = client.get(
                f"/v1/student/{STUDENT_PROJECT_ID}/roadmap",
                headers=auth_headers,
            )

            assert response.status_code == 404

    def test_update_roadmap_progress(self, client, auth_headers):
        """PUT /v1/student/{id}/roadmap/progress should update step index"""
        updated = {**SAMPLE_ROADMAP_DB, "current_step_index": 1}

        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)
            mock_db.get_roadmap = AsyncMock(return_value=SAMPLE_ROADMAP_DB)
            mock_db.update_roadmap_progress = AsyncMock(return_value=updated)

            response = client.put(
                f"/v1/student/{STUDENT_PROJECT_ID}/roadmap/progress",
                json={"step_index": 1},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["current_step_index"] == 1

    def test_update_roadmap_progress_out_of_range(self, client, auth_headers):
        """Should reject step_index beyond module count"""
        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)
            mock_db.get_roadmap = AsyncMock(return_value=SAMPLE_ROADMAP_DB)

            response = client.put(
                f"/v1/student/{STUDENT_PROJECT_ID}/roadmap/progress",
                json={"step_index": 99},
                headers=auth_headers,
            )

            assert response.status_code == 400

    def test_roadmap_requires_auth(self, client):
        """Roadmap endpoints should require authentication"""
        response = client.get(
            f"/v1/student/{STUDENT_PROJECT_ID}/roadmap",
        )
        assert response.status_code == 401


# ──────────────────────────────────────────────────────────────
# Session endpoints
# ──────────────────────────────────────────────────────────────


class TestSessionEndpoints:
    """Daily session CRUD tests"""

    def test_create_session(self, client, auth_headers):
        """POST /v1/student/{id}/sessions should create a session"""
        session_data = {
            "id": "ssssssss-ssss-ssss-ssss-ssssssssssss",
            "project_id": STUDENT_PROJECT_ID,
            "transcript": [{"role": "student", "content": "What is JSX?"}],
            "concepts_covered": ["JSX"],
            "created_at": "2025-01-01T00:00:00Z",
        }

        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)
            mock_db.create_session = AsyncMock(return_value=session_data)

            response = client.post(
                f"/v1/student/{STUDENT_PROJECT_ID}/sessions",
                json={
                    "transcript": [{"role": "student", "content": "What is JSX?"}],
                    "concepts_covered": ["JSX"],
                    "duration_minutes": 30,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["concepts_covered"] == ["JSX"]

    def test_list_sessions(self, client, auth_headers):
        """GET /v1/student/{id}/sessions should list sessions"""
        sessions = [
            {
                "id": "s1",
                "project_id": STUDENT_PROJECT_ID,
                "transcript": [],
                "concepts_covered": ["JSX"],
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "s2",
                "project_id": STUDENT_PROJECT_ID,
                "transcript": [],
                "concepts_covered": ["Hooks"],
                "created_at": "2025-01-02T00:00:00Z",
            },
        ]

        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)
            mock_db.list_sessions = AsyncMock(return_value=sessions)

            response = client.get(
                f"/v1/student/{STUDENT_PROJECT_ID}/sessions",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2

    def test_list_sessions_limit_validation(self, client, auth_headers):
        """Should reject limit > 100"""
        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)

            response = client.get(
                f"/v1/student/{STUDENT_PROJECT_ID}/sessions?limit=200",
                headers=auth_headers,
            )

            assert response.status_code == 400


# ──────────────────────────────────────────────────────────────
# Progress endpoint
# ──────────────────────────────────────────────────────────────


class TestProgressEndpoint:
    """Student progress computation tests"""

    def test_get_progress(self, client, auth_headers):
        """GET /v1/student/{id}/progress should return computed progress"""
        sessions = [
            {"duration_minutes": 30, "concepts_covered": ["JSX"]},
            {"duration_minutes": 45, "concepts_covered": ["Hooks"]},
        ]

        roadmap_at_step_1 = {**SAMPLE_ROADMAP_DB, "current_step_index": 1}

        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)
            mock_db.get_roadmap = AsyncMock(return_value=roadmap_at_step_1)
            mock_db.list_sessions = AsyncMock(return_value=sessions)

            response = client.get(
                f"/v1/student/{STUDENT_PROJECT_ID}/progress",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["completed_modules"] == 1
            assert data["total_modules"] == 2
            assert data["percent_complete"] == 50.0
            assert data["total_sessions"] == 2
            assert data["total_time_minutes"] == 75
            assert data["current_module"] == "State Management"

    def test_get_progress_no_roadmap(self, client, auth_headers):
        """Should 404 if no roadmap exists"""
        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)
            mock_db.get_roadmap = AsyncMock(return_value=None)

            response = client.get(
                f"/v1/student/{STUDENT_PROJECT_ID}/progress",
                headers=auth_headers,
            )

            assert response.status_code == 404

    def test_get_progress_zero_modules(self, client, auth_headers):
        """Should handle empty modules gracefully"""
        empty_roadmap = {**SAMPLE_ROADMAP_DB, "modules": [], "current_step_index": 0}

        with _mock_db_for_student() as mock_db:
            mock_db.get_project = AsyncMock(return_value=SAMPLE_STUDENT_PROJECT)
            mock_db.get_roadmap = AsyncMock(return_value=empty_roadmap)
            mock_db.list_sessions = AsyncMock(return_value=[])

            response = client.get(
                f"/v1/student/{STUDENT_PROJECT_ID}/progress",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["percent_complete"] == 0.0
            assert data["total_modules"] == 0
