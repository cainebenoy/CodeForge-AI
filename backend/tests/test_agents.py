"""
Tests for LangChain-based agents

Each agent follows the same LCEL pattern (prompt | llm | parser).
We mock the chain so that ainvoke() returns a pre-built Pydantic model,
verifying that the agent functions:
  1. Call get_optimal_model with the correct agent type
  2. Return a Pydantic-validated output (no hallucinated fields)
  3. Handle inputs correctly (empty strings, missing optional fields)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.protocol import (
    CodeGenerationResult,
    PedagogyResponse,
    QAResult,
    RequirementsDoc,
    WireframeSpec,
)

# Import the shared LCEL-chain mock helper from conftest
from tests.conftest import mock_lcel_chain

# ──────────────────────────────────────────────────────────────
# Sample valid Pydantic model instances used as mock returns
# ──────────────────────────────────────────────────────────────

SAMPLE_REQUIREMENTS = RequirementsDoc(
    app_name="Smart Todo",
    elevator_pitch="An AI-powered todo app that automatically tags and prioritises tasks for busy professionals.",
    target_audience=[
        {
            "role": "Busy professional",
            "goal": "Stay organised efficiently",
            "pain_point": "Manual task categorisation wastes time",
        }
    ],
    core_features=[
        {
            "name": "Auto-tagging",
            "description": "AI automatically tags tasks on creation",
            "priority": "must-have",
        }
    ],
    recommended_stack=["Next.js", "Supabase", "OpenAI"],
)

SAMPLE_WIREFRAME = WireframeSpec(
    site_map=[
        {
            "path": "/dashboard",
            "description": "Main dashboard view",
            "components": [
                {"name": "TaskList", "props": ["tasks"], "children": ["TaskItem"]}
            ],
        }
    ],
    global_state_needs=["user", "tasks"],
    theme_colors=["#FF5733", "#33FF57"],
)

SAMPLE_CODE_RESULT = CodeGenerationResult(
    files=[
        {
            "file_path": "src/app/page.tsx",
            "content": "export default function Home() { return <h1>Hello</h1> }",
            "language": "typescript",
            "explanation": "Main page component",
        }
    ],
    summary="Generated the main page component with TypeScript and React.",
    dependencies=["react", "next"],
)

SAMPLE_QA_RESULT = QAResult(
    passed=True,
    issues=[],
    summary="Code passes all quality checks with no issues found.",
    score=95.0,
)

SAMPLE_PEDAGOGY = PedagogyResponse(
    encouragement="Great question! You're thinking in the right direction.",
    steps=[
        {
            "step_number": 1,
            "question": "What happens when a component re-renders?",
            "hint": "Think about the virtual DOM diffing process.",
            "concept": "React reconciliation",
        }
    ],
    key_concept="React component lifecycle and re-rendering",
    further_exploration=["useEffect cleanup", "memo optimisation"],
)


# ──────────────────────────────────────────────────────────────
# Research Agent
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_research_agent_returns_requirements_doc():
    """Research agent should return a valid RequirementsDoc"""
    with mock_lcel_chain("app.agents.research_agent", SAMPLE_REQUIREMENTS) as mocks:
        from app.agents.research_agent import run_research_agent

        result = await run_research_agent("An AI todo app", "Students")

        assert isinstance(result, RequirementsDoc)
        assert result.app_name == "Smart Todo"
        mocks["model"].assert_called_once_with("research")


@pytest.mark.asyncio
async def test_research_agent_default_audience():
    """Research agent should default target_audience to 'General users'"""
    with mock_lcel_chain("app.agents.research_agent", SAMPLE_REQUIREMENTS) as mocks:
        from app.agents.research_agent import run_research_agent

        result = await run_research_agent("A weather app")

        # The chain was invoked — verify target_audience default
        call_args = mocks["chain"].ainvoke.call_args
        assert call_args[0][0]["target_audience"] == "General users"


# ──────────────────────────────────────────────────────────────
# Wireframe Agent
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_wireframe_agent_returns_wireframe_spec():
    """Wireframe agent should return a valid WireframeSpec"""
    with mock_lcel_chain("app.agents.wireframe_agent", SAMPLE_WIREFRAME) as mocks:
        from app.agents.wireframe_agent import run_wireframe_agent

        result = await run_wireframe_agent('{"features": ["dashboard"]}')

        assert isinstance(result, WireframeSpec)
        assert len(result.site_map) == 1
        mocks["model"].assert_called_once_with("wireframe")


# ──────────────────────────────────────────────────────────────
# Code Agent
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_code_agent_returns_code_generation_result():
    """Code agent should return a valid CodeGenerationResult"""
    with mock_lcel_chain("app.agents.code_agent", SAMPLE_CODE_RESULT) as mocks:
        from app.agents.code_agent import run_code_agent

        result = await run_code_agent('{"site_map": []}', "src/app/page.tsx")

        assert isinstance(result, CodeGenerationResult)
        assert len(result.files) == 1
        assert result.files[0].file_path == "src/app/page.tsx"
        mocks["model"].assert_called_once_with("code")


@pytest.mark.asyncio
async def test_code_agent_default_file_path():
    """Code agent with empty file_path generates all files"""
    with mock_lcel_chain("app.agents.code_agent", SAMPLE_CODE_RESULT) as mocks:
        from app.agents.code_agent import run_code_agent

        await run_code_agent('{"site_map": []}')

        call_args = mocks["chain"].ainvoke.call_args
        assert "all files needed" in call_args[0][0]["file_path"]


# ──────────────────────────────────────────────────────────────
# QA Agent
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_qa_agent_returns_qa_result():
    """QA agent should return a valid QAResult"""
    with mock_lcel_chain("app.agents.qa_agent", SAMPLE_QA_RESULT) as mocks:
        from app.agents.qa_agent import run_qa_agent

        result = await run_qa_agent("const x = 1;", "src/utils.ts")

        assert isinstance(result, QAResult)
        assert result.passed is True
        assert result.score == 95.0
        mocks["model"].assert_called_once_with("qa")


# ──────────────────────────────────────────────────────────────
# Pedagogy Agent
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pedagogy_agent_returns_pedagogy_response():
    """Pedagogy agent should return a valid PedagogyResponse"""
    with mock_lcel_chain("app.agents.pedagogy_agent", SAMPLE_PEDAGOGY) as mocks:
        from app.agents.pedagogy_agent import run_pedagogy_agent

        result = await run_pedagogy_agent(
            "How does useEffect work?", "const [x, setX] = useState(0)"
        )

        assert isinstance(result, PedagogyResponse)
        assert len(result.steps) == 1
        assert result.steps[0].concept == "React reconciliation"
        mocks["model"].assert_called_once_with("pedagogy")


@pytest.mark.asyncio
async def test_pedagogy_agent_no_student_code():
    """Pedagogy agent handles missing student code gracefully"""
    with mock_lcel_chain("app.agents.pedagogy_agent", SAMPLE_PEDAGOGY) as mocks:
        from app.agents.pedagogy_agent import run_pedagogy_agent

        await run_pedagogy_agent("What is recursion?")

        call_args = mocks["chain"].ainvoke.call_args
        assert call_args[0][0]["student_code"] == "(no code provided)"
