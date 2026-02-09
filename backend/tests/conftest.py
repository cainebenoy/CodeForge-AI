"""
Test configuration and fixtures

Environment variables are set BEFORE any app imports so that
Settings() (which runs at module-load time) receives test values
and the Supabase client is replaced with a mock.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

# ──────────────────────────────────────────────────────────────
# 1. Test environment variables (must precede all app imports)
# ──────────────────────────────────────────────────────────────
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key-do-not-use")
os.environ.setdefault(
    "SUPABASE_JWT_SECRET", "test-jwt-secret-super-secret-at-least-32-chars-long"
)
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("REDIS_URL", "")  # Empty → in-memory job store

# ──────────────────────────────────────────────────────────────
# 2. Mock Supabase client to prevent real connections in tests
# ──────────────────────────────────────────────────────────────
_mock_supabase_client = MagicMock()
patch("supabase.create_client", return_value=_mock_supabase_client).start()

# Now safe to import app modules
import time

import jwt
import pytest
from fastapi.testclient import TestClient

import app.services.job_queue as _jq_module
from app.main import app
from app.services.job_queue import InMemoryJobStore

# Test JWT secret — must match SUPABASE_JWT_SECRET in env
_TEST_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]

# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────


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
        "input_context": {"user_idea": "A todo app with AI tagging"},
    }


@pytest.fixture
def test_user_id():
    """Consistent test user UUID."""
    return "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


@pytest.fixture
def auth_headers(test_user_id):
    """
    Authorization header with a valid Supabase-style JWT
    for the test user. Use with ``client.get(..., headers=auth_headers)``.
    """
    token = jwt.encode(
        {
            "sub": test_user_id,
            "email": "testuser@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        },
        _TEST_JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def fresh_job_store():
    """
    Reset the global job store to a fresh InMemoryJobStore before each test.
    Ensures tests are isolated — no leftover jobs from previous tests.
    """
    store = InMemoryJobStore()
    _jq_module._job_store = store
    yield store
    _jq_module._job_store = None


@pytest.fixture
def mock_supabase():
    """Provide the mock Supabase client for direct assertions"""
    _mock_supabase_client.reset_mock()
    return _mock_supabase_client


def mock_lcel_chain(agent_module_path: str, return_value):
    """
    Create context-manager patches for a LangChain LCEL chain
    (prompt | llm | parser) so that chain.ainvoke() returns *return_value*.

    Usage:
        with mock_lcel_chain("app.agents.research_agent", SAMPLE_RESULT) as mocks:
            result = await run_research_agent("idea")

    The ``mocks`` dict contains ``model``, ``parser``, ``prompt``, and ``chain`` keys.
    """
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        # Ensure the target module is imported before patching
        import importlib

        importlib.import_module(agent_module_path)

        final_chain = MagicMock()
        final_chain.ainvoke = AsyncMock(return_value=return_value)

        # prompt | llm → step;  step | parser → final_chain
        step = MagicMock()
        step.__or__ = MagicMock(return_value=final_chain)

        prompt_mock = MagicMock()
        prompt_mock.__or__ = MagicMock(return_value=step)

        with (
            patch(f"{agent_module_path}.get_optimal_model") as m_model,
            patch(f"{agent_module_path}.PydanticOutputParser") as m_parser,
            patch(f"{agent_module_path}.ChatPromptTemplate") as m_cpt,
        ):
            m_cpt.from_messages.return_value = prompt_mock
            yield {
                "model": m_model,
                "parser": m_parser,
                "prompt": m_cpt,
                "chain": final_chain,
            }

    return _ctx()
