"""
Tests for LangGraph agent workflows

Verifies:
  1. Single-agent graph builds and invokes correctly
  2. Builder pipeline chains agents in order
  3. QA retry loop respects iteration limits
  4. Progress callbacks are invoked at each node
  5. should_retry_code conditional edge logic
  6. get_initial_state creates correct defaults
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.graph.nodes import should_retry_code
from app.agents.graph.state import AgentGraphState
from app.agents.graph.workflows import (
    SINGLE_AGENT_RESULT_KEYS,
    build_builder_pipeline,
    build_single_agent_graph,
    get_initial_state,
)
from app.schemas.protocol import (
    CodeGenerationResult,
    PedagogyResponse,
    QAResult,
    RequirementsDoc,
    WireframeSpec,
)

# ──────────────────────────────────────────────────────────────
# Sample data
# ──────────────────────────────────────────────────────────────

SAMPLE_REQUIREMENTS = RequirementsDoc(
    app_name="Test App",
    elevator_pitch="A test application for verifying graph workflows.",
    target_audience=[
        {"role": "Tester", "goal": "Test graphs", "pain_point": "Untested code"}
    ],
    core_features=[
        {"name": "Testing", "description": "Run tests", "priority": "must-have"}
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

SAMPLE_CODE = CodeGenerationResult(
    files=[
        {
            "file_path": "src/app/page.tsx",
            "content": "export default function Home() { return <h1>Hello</h1> }",
            "language": "typescript",
            "explanation": "Main page",
        }
    ],
    summary="Generated main page.",
    dependencies=["react"],
)

SAMPLE_QA_PASS = QAResult(
    passed=True,
    issues=[],
    summary="All checks passed.",
    score=95.0,
)

SAMPLE_QA_FAIL = QAResult(
    passed=False,
    issues=[],
    summary="Issues found.",
    score=40.0,
)


# ──────────────────────────────────────────────────────────────
# get_initial_state
# ──────────────────────────────────────────────────────────────


def test_initial_state_defaults():
    """get_initial_state should set correct defaults"""
    state = get_initial_state(
        project_id="abc-123",
        agent_type="research",
        input_context={"user_idea": "test"},
        job_id="job-1",
    )

    assert state["project_id"] == "abc-123"
    assert state["agent_type"] == "research"
    assert state["job_id"] == "job-1"
    assert state["input_context"] == {"user_idea": "test"}
    assert state["iteration_count"] == 0
    assert state["max_iterations"] == 5  # from settings default
    assert state["progress"] == 0.0
    assert state["errors"] == []
    assert state["requirements_spec"] is None


# ──────────────────────────────────────────────────────────────
# should_retry_code conditional edge
# ──────────────────────────────────────────────────────────────


def test_should_retry_code_when_qa_fails_under_limit():
    """Should return 'retry' when QA fails and under iteration limit"""
    state = AgentGraphState(
        qa_result={"passed": False, "score": 30},
        iteration_count=2,
        max_iterations=5,
    )
    assert should_retry_code(state) == "retry"


def test_should_retry_code_when_qa_passes():
    """Should return 'end' when QA passes"""
    state = AgentGraphState(
        qa_result={"passed": True, "score": 95},
        iteration_count=1,
        max_iterations=5,
    )
    assert should_retry_code(state) == "end"


def test_should_retry_code_when_at_limit():
    """Should return 'end' when at iteration limit even if QA failed"""
    state = AgentGraphState(
        qa_result={"passed": False, "score": 30},
        iteration_count=5,
        max_iterations=5,
    )
    assert should_retry_code(state) == "end"


def test_should_retry_code_missing_qa_result():
    """Should return 'end' when no QA result (defaults to passed=True)"""
    state = AgentGraphState(
        iteration_count=0,
        max_iterations=5,
    )
    assert should_retry_code(state) == "end"


# ──────────────────────────────────────────────────────────────
# SINGLE_AGENT_RESULT_KEYS
# ──────────────────────────────────────────────────────────────


def test_single_agent_result_keys_mapping():
    """Verify all agent types have result key mappings"""
    assert SINGLE_AGENT_RESULT_KEYS["research"] == "requirements_spec"
    assert SINGLE_AGENT_RESULT_KEYS["wireframe"] == "architecture_spec"
    assert SINGLE_AGENT_RESULT_KEYS["code"] == "generated_code"
    assert SINGLE_AGENT_RESULT_KEYS["qa"] == "qa_result"
    assert SINGLE_AGENT_RESULT_KEYS["pedagogy"] == "pedagogy_response"


# ──────────────────────────────────────────────────────────────
# build_single_agent_graph
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_single_agent_graph_research():
    """Single-agent graph should invoke research node and return state"""
    with patch(
        "app.agents.research_agent.run_research_agent",
        new_callable=AsyncMock,
        return_value=SAMPLE_REQUIREMENTS,
    ):
        graph = build_single_agent_graph("research")
        initial = get_initial_state(
            project_id="proj-1",
            agent_type="research",
            input_context={"user_idea": "test app"},
        )

        result = await graph.ainvoke(initial)

        assert result["requirements_spec"] is not None
        assert result["requirements_spec"]["app_name"] == "Test App"
        assert result["current_node"] == "research"
        assert result["progress"] == 20.0


@pytest.mark.asyncio
async def test_single_agent_graph_qa():
    """Single-agent graph for QA should return qa_result"""
    with patch(
        "app.agents.qa_agent.run_qa_agent",
        new_callable=AsyncMock,
        return_value=SAMPLE_QA_PASS,
    ):
        graph = build_single_agent_graph("qa")
        initial = get_initial_state(
            project_id="proj-1",
            agent_type="qa",
            input_context={"code": "const x = 1;", "file_path": "test.ts"},
        )

        result = await graph.ainvoke(initial)

        assert result["qa_result"]["passed"] is True
        assert result["qa_result"]["score"] == 95.0


def test_single_agent_graph_unknown_type():
    """Should raise ValueError for unknown agent type"""
    with pytest.raises(ValueError, match="Unknown agent type"):
        build_single_agent_graph("nonexistent")


@pytest.mark.asyncio
async def test_single_agent_graph_with_progress_callback():
    """Progress callback should be called during graph execution"""
    callback = AsyncMock()

    with patch(
        "app.agents.research_agent.run_research_agent",
        new_callable=AsyncMock,
        return_value=SAMPLE_REQUIREMENTS,
    ):
        graph = build_single_agent_graph("research", callback=callback)
        initial = get_initial_state(
            project_id="proj-1",
            agent_type="research",
            input_context={"user_idea": "test"},
        )

        await graph.ainvoke(initial)

        callback.assert_called_once_with(20.0, "research")


# ──────────────────────────────────────────────────────────────
# build_builder_pipeline
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_builder_pipeline_full_flow():
    """Builder pipeline should run research → wireframe → code → qa"""
    with (
        patch(
            "app.agents.research_agent.run_research_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_REQUIREMENTS,
        ),
        patch(
            "app.agents.wireframe_agent.run_wireframe_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_WIREFRAME,
        ),
        patch(
            "app.agents.code_agent.run_code_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_CODE,
        ),
        patch(
            "app.agents.qa_agent.run_qa_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_QA_PASS,
        ),
    ):
        graph = build_builder_pipeline()
        initial = get_initial_state(
            project_id="proj-1",
            agent_type="builder",
            input_context={"user_idea": "todo app"},
        )

        result = await graph.ainvoke(initial)

        assert result["requirements_spec"]["app_name"] == "Test App"
        assert result["architecture_spec"] is not None
        assert result["generated_code"] is not None
        assert result["qa_result"]["passed"] is True
        assert result["iteration_count"] == 1


@pytest.mark.asyncio
async def test_builder_pipeline_retries_code_on_qa_failure():
    """Builder pipeline should retry code generation when QA fails"""
    # QA fails first time, passes second time
    qa_results = [SAMPLE_QA_FAIL, SAMPLE_QA_PASS]
    qa_call_count = {"n": 0}

    async def mock_qa(*args, **kwargs):
        idx = min(qa_call_count["n"], len(qa_results) - 1)
        qa_call_count["n"] += 1
        return qa_results[idx]

    with (
        patch(
            "app.agents.research_agent.run_research_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_REQUIREMENTS,
        ),
        patch(
            "app.agents.wireframe_agent.run_wireframe_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_WIREFRAME,
        ),
        patch(
            "app.agents.code_agent.run_code_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_CODE,
        ),
        patch(
            "app.agents.qa_agent.run_qa_agent",
            side_effect=mock_qa,
        ),
    ):
        graph = build_builder_pipeline()
        initial = get_initial_state(
            project_id="proj-1",
            agent_type="builder",
            input_context={"user_idea": "todo app"},
        )

        result = await graph.ainvoke(initial)

        # Should have iterated twice (code ran twice)
        assert result["iteration_count"] == 2
        # Final QA should pass
        assert result["qa_result"]["passed"] is True


@pytest.mark.asyncio
async def test_builder_pipeline_respects_iteration_limit():
    """Builder pipeline should stop retrying after max_iterations"""
    with (
        patch(
            "app.agents.research_agent.run_research_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_REQUIREMENTS,
        ),
        patch(
            "app.agents.wireframe_agent.run_wireframe_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_WIREFRAME,
        ),
        patch(
            "app.agents.code_agent.run_code_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_CODE,
        ),
        patch(
            "app.agents.qa_agent.run_qa_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_QA_FAIL,  # Always fails
        ),
    ):
        graph = build_builder_pipeline()
        initial = get_initial_state(
            project_id="proj-1",
            agent_type="builder",
            input_context={"user_idea": "todo app"},
        )
        # Set low iteration limit for faster test
        initial["max_iterations"] = 2

        result = await graph.ainvoke(initial)

        # Should stop at max_iterations
        assert result["iteration_count"] == 2
        # QA should still be failed
        assert result["qa_result"]["passed"] is False


@pytest.mark.asyncio
async def test_builder_pipeline_progress_callbacks():
    """Builder pipeline should invoke progress callback at each node"""
    callback = AsyncMock()

    with (
        patch(
            "app.agents.research_agent.run_research_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_REQUIREMENTS,
        ),
        patch(
            "app.agents.wireframe_agent.run_wireframe_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_WIREFRAME,
        ),
        patch(
            "app.agents.code_agent.run_code_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_CODE,
        ),
        patch(
            "app.agents.qa_agent.run_qa_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_QA_PASS,
        ),
    ):
        graph = build_builder_pipeline(callback=callback)
        initial = get_initial_state(
            project_id="proj-1",
            agent_type="builder",
            input_context={"user_idea": "todo app"},
        )

        await graph.ainvoke(initial)

        # Should have been called 4 times: research, wireframe, code, qa
        assert callback.call_count == 4
        # Verify progress values increased
        progress_values = [call.args[0] for call in callback.call_args_list]
        assert progress_values == [20.0, 40.0, 60.0, 80.0]


# ──────────────────────────────────────────────────────────────
# Roadmap agent type in SINGLE_AGENT_RESULT_KEYS
# ──────────────────────────────────────────────────────────────


def test_roadmap_agent_in_single_agent_result_keys():
    """Roadmap agent type should be registered in SINGLE_AGENT_RESULT_KEYS"""
    assert "roadmap" in SINGLE_AGENT_RESULT_KEYS


# ──────────────────────────────────────────────────────────────
# RAG pattern storage on QA pass
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_store_successful_pattern_called_on_qa_pass():
    """_store_successful_pattern should be called when QA passes"""
    with (
        patch(
            "app.agents.research_agent.run_research_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_REQUIREMENTS,
        ),
        patch(
            "app.agents.wireframe_agent.run_wireframe_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_WIREFRAME,
        ),
        patch(
            "app.agents.code_agent.run_code_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_CODE,
        ),
        patch(
            "app.agents.qa_agent.run_qa_agent",
            new_callable=AsyncMock,
            return_value=SAMPLE_QA_PASS,
        ),
        patch(
            "app.agents.graph.nodes._store_successful_pattern",
            new_callable=AsyncMock,
        ) as mock_store,
    ):
        graph = build_builder_pipeline()
        initial = get_initial_state(
            project_id="proj-1",
            agent_type="builder",
            input_context={"user_idea": "todo app"},
        )

        result = await graph.ainvoke(initial)

        # QA passed → _store_successful_pattern should have been called
        mock_store.assert_awaited_once()
