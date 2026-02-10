"""
LangGraph workflow definitions

Defines compiled StateGraph instances for:
- Single-agent execution (any individual agent)
- Builder pipeline (research → wireframe → code → qa with retry loop)

Each workflow is a compiled LangGraph that can be invoked with an
initial AgentGraphState and returns the final state.
"""

from typing import Any, Callable, Coroutine, Dict, Optional

from langgraph.graph import END, StateGraph

from app.agents.graph.nodes import (
    code_node,
    pedagogy_node,
    qa_node,
    research_node,
    roadmap_node,
    should_retry_code,
    wireframe_node,
)
from app.agents.graph.state import AgentGraphState
from app.core.config import settings
from app.core.logging import logger

# Type alias for progress callbacks
ProgressCallback = Optional[Callable[[float, str], Coroutine[Any, Any, None]]]


# ──────────────────────────────────────────────────────────────
# Node registry — maps agent_type to its node function
# ──────────────────────────────────────────────────────────────
AGENT_NODE_MAP = {
    "research": research_node,
    "wireframe": wireframe_node,
    "code": code_node,
    "qa": qa_node,
    "pedagogy": pedagogy_node,
    "roadmap": roadmap_node,
}

# Maps agent output keys to progress percentages for single-agent runs
SINGLE_AGENT_RESULT_KEYS = {
    "research": "requirements_spec",
    "wireframe": "architecture_spec",
    "code": "generated_code",
    "qa": "qa_result",
    "pedagogy": "pedagogy_response",
    "roadmap": "roadmap",
}


def _wrap_node_with_callback(
    node_fn: Callable,
    callback: ProgressCallback,
) -> Callable:
    """
    Wrap a node function so that after it returns,
    the progress callback is invoked with the updated progress value.
    """
    if callback is None:
        return node_fn

    async def _wrapped(state: AgentGraphState) -> Dict[str, Any]:
        result = await node_fn(state)
        progress = result.get("progress", 0.0)
        current = result.get("current_node", "unknown")
        try:
            await callback(progress, current)
        except Exception as e:
            logger.warning(f"Progress callback error: {e}")
        return result

    _wrapped.__name__ = node_fn.__name__
    return _wrapped


def build_single_agent_graph(
    agent_type: str,
    callback: ProgressCallback = None,
) -> Any:
    """
    Build a compiled graph that runs a single agent.

    Args:
        agent_type: One of 'research', 'wireframe', 'code', 'qa', 'pedagogy'
        callback: Optional async callback(progress, node_name) for progress updates

    Returns:
        Compiled LangGraph ready for `.ainvoke(state)`
    """
    if agent_type not in AGENT_NODE_MAP:
        raise ValueError(f"Unknown agent type: {agent_type}")

    node_fn = _wrap_node_with_callback(AGENT_NODE_MAP[agent_type], callback)

    graph = StateGraph(AgentGraphState)
    graph.add_node(agent_type, node_fn)
    graph.set_entry_point(agent_type)
    graph.add_edge(agent_type, END)

    logger.debug(f"Built single-agent graph for: {agent_type}")
    return graph.compile()


def build_builder_pipeline(
    callback: ProgressCallback = None,
) -> Any:
    """
    Build the full builder pipeline graph:

        research → wireframe → code → qa
                                 ↑      │
                                 └──────┘  (retry if QA fails, up to max_iterations)

    The code→qa loop is bounded by `max_iterations` in the state
    (defaults to settings.MAX_AGENT_ITERATIONS).

    Args:
        callback: Optional async callback(progress, node_name) for progress updates

    Returns:
        Compiled LangGraph ready for `.ainvoke(state)`
    """
    r_node = _wrap_node_with_callback(research_node, callback)
    w_node = _wrap_node_with_callback(wireframe_node, callback)
    c_node = _wrap_node_with_callback(code_node, callback)
    q_node = _wrap_node_with_callback(qa_node, callback)

    graph = StateGraph(AgentGraphState)

    # Add nodes
    graph.add_node("research", r_node)
    graph.add_node("wireframe", w_node)
    graph.add_node("code", c_node)
    graph.add_node("qa", q_node)

    # Linear edges
    graph.set_entry_point("research")
    graph.add_edge("research", "wireframe")
    graph.add_edge("wireframe", "code")
    graph.add_edge("code", "qa")

    # Conditional edge: QA → retry code or end
    graph.add_conditional_edges(
        "qa",
        should_retry_code,
        {
            "retry": "code",
            "end": END,
        },
    )

    # Safety bound: max recursion = iterations * 2 (code+qa per loop) + 5 (linear nodes + buffer)
    recursion_limit = settings.MAX_AGENT_ITERATIONS * 2 + 5

    logger.debug(f"Built builder pipeline graph (recursion_limit={recursion_limit})")
    return graph.compile()


def get_initial_state(
    project_id: str,
    agent_type: str,
    input_context: Dict[str, Any],
    job_id: str = "",
) -> AgentGraphState:
    """
    Create the initial state dict for a graph invocation.

    Args:
        project_id: UUID of the project
        agent_type: Agent type string
        input_context: Agent-specific context
        job_id: Job ID for progress tracking

    Returns:
        AgentGraphState ready for graph.ainvoke()
    """
    return AgentGraphState(
        project_id=project_id,
        job_id=job_id,
        agent_type=agent_type,
        input_context=input_context,
        requirements_spec=None,
        architecture_spec=None,
        generated_code=None,
        qa_result=None,
        pedagogy_response=None,
        roadmap=None,
        iteration_count=0,
        max_iterations=settings.MAX_AGENT_ITERATIONS,
        errors=[],
        progress=0.0,
        current_node="",
    )
