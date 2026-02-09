"""
Tests for the Agent Orchestrator

Verifies:
  1. Correct agent dispatch based on agent_type
  2. Pydantic model_dump serialisation before DB storage
  3. AGENT_RESULT_COLUMN_MAP maps to correct DB columns
  4. Timeout handling
  5. Error wrapping (AgentExecutionError)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.orchestrator import (
    AGENT_RESULT_COLUMN_MAP,
    _dispatch_agent,
    run_agent_workflow,
)
from app.core.exceptions import AgentExecutionError
from app.schemas.protocol import AgentRequest, AgentType, RequirementsDoc, WireframeSpec

# ──────────────────────────────────────────────────────────────
# Fixtures & helpers
# ──────────────────────────────────────────────────────────────

SAMPLE_REQUIREMENTS = RequirementsDoc(
    app_name="Test App",
    elevator_pitch="A test application for verifying orchestrator dispatch logic.",
    target_audience=[
        {
            "role": "Tester",
            "goal": "Verify orchestrator",
            "pain_point": "Untested code",
        }
    ],
    core_features=[
        {
            "name": "Testing",
            "description": "Automated tests",
            "priority": "must-have",
        }
    ],
    recommended_stack=["pytest"],
)

SAMPLE_WIREFRAME = WireframeSpec(
    site_map=[
        {
            "path": "/home",
            "description": "Home page",
            "components": [{"name": "Hero", "props": [], "children": []}],
        }
    ],
    global_state_needs=[],
    theme_colors=["#000000"],
)


def _make_request(agent_type: str, context: dict = None) -> AgentRequest:
    return AgentRequest(
        project_id="550e8400-e29b-41d4-a716-446655440000",
        agent_type=agent_type,
        input_context=context or {},
    )


# ──────────────────────────────────────────────────────────────
# AGENT_RESULT_COLUMN_MAP
# ──────────────────────────────────────────────────────────────


def test_agent_result_column_map():
    """Verify the column mapping matches expected DB schema"""
    assert AGENT_RESULT_COLUMN_MAP["research"] == "requirements_spec"
    assert AGENT_RESULT_COLUMN_MAP["wireframe"] == "architecture_spec"
    # code, qa, pedagogy have no dedicated column
    assert "code" not in AGENT_RESULT_COLUMN_MAP
    assert "qa" not in AGENT_RESULT_COLUMN_MAP
    assert "pedagogy" not in AGENT_RESULT_COLUMN_MAP


# ──────────────────────────────────────────────────────────────
# _dispatch_agent routing
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatch_routes_to_research_agent():
    """_dispatch_agent should call run_research_agent for 'research' type"""
    request = _make_request("research", {"user_idea": "todo app"})

    # Import agent module first so patch can find it
    import app.agents.research_agent  # noqa: F401

    with patch(
        "app.agents.research_agent.run_research_agent",
        new_callable=AsyncMock,
        return_value=SAMPLE_REQUIREMENTS,
    ) as mock_agent:
        result = await _dispatch_agent(request)

        mock_agent.assert_called_once_with(
            user_idea="todo app",
            target_audience="",
        )
        assert isinstance(result, RequirementsDoc)


@pytest.mark.asyncio
async def test_dispatch_routes_to_wireframe_agent():
    """_dispatch_agent should call run_wireframe_agent for 'wireframe' type"""
    request = _make_request("wireframe", {"requirements": "some reqs"})

    # Import agent module first so patch can find it
    import app.agents.wireframe_agent  # noqa: F401

    with patch(
        "app.agents.wireframe_agent.run_wireframe_agent",
        new_callable=AsyncMock,
        return_value=SAMPLE_WIREFRAME,
    ) as mock_agent:
        result = await _dispatch_agent(request)

        mock_agent.assert_called_once_with(requirements="some reqs")
        assert isinstance(result, WireframeSpec)


@pytest.mark.asyncio
async def test_dispatch_unknown_agent_raises():
    """_dispatch_agent should raise ValueError for unknown agent types"""
    # Build request manually to bypass enum validation
    request = MagicMock()
    request.agent_type = "nonexistent"
    request.input_context = {}

    with pytest.raises(ValueError, match="Unknown agent type"):
        await _dispatch_agent(request)


# ──────────────────────────────────────────────────────────────
# run_agent_workflow integration
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_workflow_stores_result_in_db_for_research():
    """run_agent_workflow should call DatabaseOperations.update_project for research"""
    request = _make_request("research", {"user_idea": "test"})

    with (
        patch(
            "app.agents.orchestrator._dispatch_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_REQUIREMENTS,
        ),
        patch("app.agents.orchestrator.DatabaseOperations") as mock_db,
    ):
        mock_db.update_project = AsyncMock()

        result = await run_agent_workflow("job-1", request)

        # Should store in the requirements_spec column
        mock_db.update_project.assert_called_once()
        call_args = mock_db.update_project.call_args
        assert call_args[0][0] == request.project_id
        update_data = call_args[0][1]
        assert "requirements_spec" in update_data
        assert update_data["status"] == "in-progress"

        # Result should be a dict (serialised from Pydantic model)
        assert isinstance(result, dict)
        assert result["app_name"] == "Test App"


@pytest.mark.asyncio
async def test_workflow_does_not_store_qa_result_in_db():
    """QA results should NOT be stored in the projects table (no DB column)"""
    request = _make_request("qa", {"code": "x=1", "file_path": "test.py"})
    mock_qa = MagicMock()
    mock_qa.model_dump.return_value = {"passed": True, "score": 90}

    with (
        patch(
            "app.agents.orchestrator._dispatch_agent",
            new_callable=AsyncMock,
            return_value=mock_qa,
        ),
        patch("app.agents.orchestrator.DatabaseOperations") as mock_db,
    ):
        mock_db.update_project = AsyncMock()

        await run_agent_workflow("job-2", request)

        # Should NOT call update_project since qa has no DB column
        mock_db.update_project.assert_not_called()


@pytest.mark.asyncio
async def test_workflow_timeout_raises_agent_execution_error():
    """run_agent_workflow should raise AgentExecutionError on timeout"""
    request = _make_request("research", {"user_idea": "slow"})

    # Simulate asyncio.TimeoutError being raised by wait_for inside run_agent_workflow
    with (
        patch(
            "app.agents.orchestrator._dispatch_agent",
            new_callable=AsyncMock,
            side_effect=asyncio.TimeoutError(),
        ),
        patch("app.agents.orchestrator.DatabaseOperations"),
    ):
        with pytest.raises(AgentExecutionError):
            await run_agent_workflow("job-timeout", request)


@pytest.mark.asyncio
async def test_workflow_wraps_generic_exception():
    """Generic exceptions should be wrapped in AgentExecutionError"""
    request = _make_request("research", {"user_idea": "error test"})

    with (
        patch(
            "app.agents.orchestrator._dispatch_agent",
            new_callable=AsyncMock,
            side_effect=RuntimeError("LLM provider down"),
        ),
        patch("app.agents.orchestrator.DatabaseOperations"),
    ):
        with pytest.raises(AgentExecutionError):
            await run_agent_workflow("job-err", request)
