"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_project_id():
    """Sample UUID for testing"""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_agent_request():
    """Sample agent request payload"""
    return {
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "agent_type": "research",
        "input_context": {
            "user_idea": "A todo app with AI tagging"
        }
    }
