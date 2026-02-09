"""
LangGraph state definitions for agent workflows

TypedDict-based state objects passed between graph nodes.
Each node reads from and writes to this shared state.
"""

from typing import Any, Dict, List, Optional, TypedDict


class AgentGraphState(TypedDict, total=False):
    """
    Shared state for the agent workflow graph.

    All nodes read from and write to this state dict.
    Fields use `total=False` so nodes only need to set relevant keys.
    """

    # ── Identifiers ──
    project_id: str
    job_id: str
    agent_type: str

    # ── Input ──
    input_context: Dict[str, Any]

    # ── Agent outputs (accumulated as pipeline progresses) ──
    requirements_spec: Optional[Dict[str, Any]]
    architecture_spec: Optional[Dict[str, Any]]
    generated_code: Optional[Dict[str, Any]]
    qa_result: Optional[Dict[str, Any]]
    pedagogy_response: Optional[Dict[str, Any]]
    roadmap: Optional[Dict[str, Any]]

    # ── Control flow ──
    iteration_count: int
    max_iterations: int
    errors: List[str]

    # ── Progress tracking ──
    progress: float
    current_node: str
