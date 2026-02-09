"""
Tests for the Agent Orchestrator (LangGraph-based)

Verifies:
  1. AGENT_RESULT_COLUMN_MAP maps to correct DB columns
  2. run_agent_workflow dispatches via LangGraph
  3. Database persistence for research/wireframe results
  4. QA results NOT stored in projects table
  5. Timeout handling (AgentExecutionError)
  6. Error wrapping (generic → AgentExecutionError)
  7. run_builder_pipeline multi-step execution
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.orchestrator import (
    AGENT_RESULT_COLUMN_MAP,
    run_agent_workflow,
    run_builder_pipeline,
)
from app.core.exceptions import AgentExecutionError
from app.schemas.protocol import AgentRequest, RequirementsDoc, WireframeSpec

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
# run_agent_workflow — LangGraph dispatch
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_workflow_stores_result_in_db_for_research():
    """run_agent_workflow should call DatabaseOperations.update_project for research"""
    request = _make_request("research", {"user_idea": "test"})

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "requirements_spec": SAMPLE_REQUIREMENTS.model_dump(),
            "current_node": "research",
            "progress": 100.0,
        }
    )

    with (
        patch(
            "app.agents.graph.workflows.build_single_agent_graph",
            return_value=mock_graph,
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
    qa_result = {"passed": True, "score": 90, "issues": [], "summary": "All good"}

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "qa_result": qa_result,
            "current_node": "qa",
            "progress": 100.0,
        }
    )

    with (
        patch(
            "app.agents.graph.workflows.build_single_agent_graph",
            return_value=mock_graph,
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

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=asyncio.TimeoutError())

    with (
        patch(
            "app.agents.graph.workflows.build_single_agent_graph",
            return_value=mock_graph,
        ),
        patch("app.agents.orchestrator.DatabaseOperations"),
    ):
        with pytest.raises(AgentExecutionError):
            await run_agent_workflow("job-timeout", request)


@pytest.mark.asyncio
async def test_workflow_wraps_generic_exception():
    """Generic exceptions should be wrapped in AgentExecutionError"""
    request = _make_request("research", {"user_idea": "error test"})

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("LLM provider down"))

    with (
        patch(
            "app.agents.graph.workflows.build_single_agent_graph",
            return_value=mock_graph,
        ),
        patch("app.agents.orchestrator.DatabaseOperations"),
    ):
        with pytest.raises(AgentExecutionError):
            await run_agent_workflow("job-err", request)


@pytest.mark.asyncio
async def test_workflow_raises_on_no_result():
    """run_agent_workflow raises if agent produces no result in state"""
    request = _make_request("research", {"user_idea": "empty"})

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "current_node": "research",
            "progress": 100.0,
        }
    )

    with (
        patch(
            "app.agents.graph.workflows.build_single_agent_graph",
            return_value=mock_graph,
        ),
        patch("app.agents.orchestrator.DatabaseOperations"),
    ):
        with pytest.raises(AgentExecutionError, match="no result"):
            await run_agent_workflow("job-empty", request)


# ──────────────────────────────────────────────────────────────
# run_builder_pipeline
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_builder_pipeline_returns_all_outputs():
    """Builder pipeline should return requirements, architecture, code, qa results"""
    final_state = {
        "requirements_spec": SAMPLE_REQUIREMENTS.model_dump(),
        "architecture_spec": SAMPLE_WIREFRAME.model_dump(),
        "generated_code": {"files": [], "summary": "done", "dependencies": []},
        "qa_result": {"passed": True, "issues": [], "summary": "ok", "score": 95},
        "iteration_count": 1,
    }

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=final_state)

    with (
        patch(
            "app.agents.graph.workflows.build_builder_pipeline",
            return_value=mock_graph,
        ),
        patch("app.agents.orchestrator.DatabaseOperations") as mock_db,
    ):
        mock_db.update_project = AsyncMock()

        result = await run_builder_pipeline(
            job_id="job-builder",
            project_id="550e8400-e29b-41d4-a716-446655440000",
            input_context={"user_idea": "todo app"},
        )

        assert result["requirements_spec"]["app_name"] == "Test App"
        assert result["architecture_spec"] is not None
        assert result["generated_code"] is not None
        assert result["qa_result"]["passed"] is True
        assert result["iterations"] == 1

        # Should persist results to DB
        mock_db.update_project.assert_called_once()


@pytest.mark.asyncio
async def test_builder_pipeline_timeout():
    """Builder pipeline should raise AgentExecutionError on timeout"""
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=asyncio.TimeoutError())

    with (
        patch(
            "app.agents.graph.workflows.build_builder_pipeline",
            return_value=mock_graph,
        ),
        patch("app.agents.orchestrator.DatabaseOperations"),
    ):
        with pytest.raises(AgentExecutionError, match="timeout"):
            await run_builder_pipeline(
                job_id="job-timeout",
                project_id="550e8400-e29b-41d4-a716-446655440000",
                input_context={"user_idea": "slow"},
            )
