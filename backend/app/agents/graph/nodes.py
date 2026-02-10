"""
LangGraph node functions for agent workflows

Each node wraps an existing LCEL agent and integrates it into the
LangGraph state machine. Nodes read input from AgentGraphState,
call the underlying agent, and write results back to the state.
"""

import json
from typing import Any, Dict

from app.agents.graph.state import AgentGraphState
from app.core.logging import logger

# ──────────────────────────────────────────────────────────────
# Node functions — each takes state, returns partial state update
# ──────────────────────────────────────────────────────────────


async def research_node(state: AgentGraphState) -> Dict[str, Any]:
    """Run the Research Agent and store requirements_spec in state."""
    from app.agents.research_agent import run_research_agent

    logger.info(f"[Graph] research_node — project={state.get('project_id')}")

    ctx = state.get("input_context", {})
    result = await run_research_agent(
        user_idea=ctx.get("user_idea", ""),
        target_audience=ctx.get("target_audience", ""),
    )

    result_dict = result.model_dump() if hasattr(result, "model_dump") else result
    return {
        "requirements_spec": result_dict,
        "current_node": "research",
        "progress": 20.0,
    }


async def wireframe_node(state: AgentGraphState) -> Dict[str, Any]:
    """Run the Wireframe Agent using requirements from state."""
    from app.agents.wireframe_agent import run_wireframe_agent

    logger.info(f"[Graph] wireframe_node — project={state.get('project_id')}")

    # Use requirements from previous node or from input_context
    requirements = state.get("requirements_spec")
    if requirements is None:
        requirements = state.get("input_context", {}).get("requirements", "")

    if isinstance(requirements, dict):
        requirements = json.dumps(requirements, indent=2)

    result = await run_wireframe_agent(requirements=str(requirements))

    result_dict = result.model_dump() if hasattr(result, "model_dump") else result
    return {
        "architecture_spec": result_dict,
        "current_node": "wireframe",
        "progress": 40.0,
    }


async def code_node(state: AgentGraphState) -> Dict[str, Any]:
    """Run the Code Agent using architecture from state."""
    from app.agents.code_agent import run_code_agent

    logger.info(
        f"[Graph] code_node — project={state.get('project_id')} "
        f"(iteration {state.get('iteration_count', 0) + 1})"
    )

    # Use architecture from previous node or from input_context
    architecture = state.get("architecture_spec")
    if architecture is None:
        architecture = state.get("input_context", {}).get("architecture", "")

    if isinstance(architecture, dict):
        architecture = json.dumps(architecture, indent=2)

    file_path = state.get("input_context", {}).get("file_path", "")

    result = await run_code_agent(
        architecture=str(architecture),
        file_path=file_path,
    )

    result_dict = result.model_dump() if hasattr(result, "model_dump") else result
    iteration = state.get("iteration_count", 0) + 1
    return {
        "generated_code": result_dict,
        "current_node": "code",
        "progress": 60.0,
        "iteration_count": iteration,
    }


async def qa_node(state: AgentGraphState) -> Dict[str, Any]:
    """Run the QA Agent on generated code from state."""
    from app.agents.qa_agent import run_qa_agent

    logger.info(f"[Graph] qa_node — project={state.get('project_id')}")

    generated = state.get("generated_code", {})

    # Review the first file (or all concatenated) from generated code
    files = generated.get("files", []) if isinstance(generated, dict) else []
    if files:
        code = files[0].get("content", "")
        file_path = files[0].get("file_path", "unknown")
    else:
        ctx = state.get("input_context", {})
        code = ctx.get("code", "")
        file_path = ctx.get("file_path", "unknown")

    result = await run_qa_agent(code=code, file_path=file_path)

    result_dict = result.model_dump() if hasattr(result, "model_dump") else result

    # If QA passed, store the successful pattern in RAG for future reference
    if result_dict.get("passed"):
        partial_state = dict(state)
        partial_state["qa_result"] = result_dict
        await _store_successful_pattern(partial_state)

    return {
        "qa_result": result_dict,
        "current_node": "qa",
        "progress": 80.0,
    }


async def _store_successful_pattern(state: AgentGraphState) -> None:
    """
    Store a successful code pattern in the RAG vector store.
    Called after QA passes — non-critical, failures are logged and swallowed.
    """
    try:
        from app.agents.core.memory import store_pattern

        qa_result = state.get("qa_result", {})
        generated = state.get("generated_code", {})
        requirements = state.get("requirements_spec", {})

        if not qa_result.get("passed"):
            return

        score = qa_result.get("score", 50.0) / 100.0
        description = generated.get("summary", "")
        if not description:
            description = requirements.get("elevator_pitch", "Generated code pattern")

        await store_pattern(
            project_type="code",
            metadata={
                "summary": generated.get("summary", ""),
                "description": description,
                "file_count": len(generated.get("files", [])),
                "dependencies": generated.get("dependencies", []),
                "qa_score": qa_result.get("score", 0),
            },
            description=description,
            success_score=score,
        )
        logger.info(f"Stored successful pattern (score={score:.2f})")
    except Exception as e:
        logger.warning(f"Failed to store pattern (non-critical): {e}")


async def pedagogy_node(state: AgentGraphState) -> Dict[str, Any]:
    """Run the Pedagogy Agent."""
    from app.agents.pedagogy_agent import run_pedagogy_agent

    logger.info(f"[Graph] pedagogy_node — project={state.get('project_id')}")

    ctx = state.get("input_context", {})
    result = await run_pedagogy_agent(
        student_question=ctx.get("question", ""),
        student_code=ctx.get("code", ""),
    )

    result_dict = result.model_dump() if hasattr(result, "model_dump") else result
    return {
        "pedagogy_response": result_dict,
        "current_node": "pedagogy",
        "progress": 100.0,
    }


async def roadmap_node(state: AgentGraphState) -> Dict[str, Any]:
    """Run the Roadmap Agent."""
    from app.agents.roadmap_agent import run_roadmap_agent

    logger.info(f"[Graph] roadmap_node — project={state.get('project_id')}")

    ctx = state.get("input_context", {})

    # Use requirements from state or from input_context
    requirements = state.get("requirements_spec")
    if requirements is None:
        requirements = ctx.get("requirements", "")
    if isinstance(requirements, dict):
        import json as _json

        requirements = _json.dumps(requirements, indent=2)

    result = await run_roadmap_agent(
        requirements_spec=str(requirements),
        skill_level=ctx.get("skill_level", "beginner"),
        focus_areas=ctx.get("focus_areas", ""),
    )

    result_dict = result.model_dump() if hasattr(result, "model_dump") else result
    return {
        "roadmap": result_dict,
        "current_node": "roadmap",
        "progress": 100.0,
    }


# ──────────────────────────────────────────────────────────────
# Conditional edge functions
# ──────────────────────────────────────────────────────────────


def should_retry_code(state: AgentGraphState) -> str:
    """
    Conditional edge after QA node.

    If QA failed AND we haven't hit the iteration limit,
    route back to code_node for another attempt.
    Otherwise, proceed to END.

    Returns:
        "retry" — route back to code_node
        "end"   — proceed to graph end
    """
    qa_result = state.get("qa_result", {})
    passed = qa_result.get("passed", True)
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 5)

    if not passed and iteration < max_iter:
        logger.info(
            f"[Graph] QA failed — retrying code generation "
            f"(attempt {iteration + 1}/{max_iter})"
        )
        return "retry"

    if not passed:
        logger.warning(f"[Graph] QA failed after {iteration} iterations — giving up")

    return "end"
