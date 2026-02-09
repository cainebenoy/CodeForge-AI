"""
Agent Orchestrator - coordinates agent workflows via LangGraph

Routes agent requests through LangGraph StateGraph pipelines.
Supports both single-agent execution and multi-step builder pipelines
with Code→QA retry loops.

Handles timeouts, error handling, database persistence, and progress tracking.
"""

import asyncio
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.exceptions import AgentExecutionError
from app.core.logging import logger
from app.schemas.protocol import AgentRequest
from app.services.database import DatabaseOperations

# Mapping from agent_type to the correct DB column name
# This prevents the previous bug where 'research_result' was stored instead of 'requirements_spec'
AGENT_RESULT_COLUMN_MAP = {
    "research": "requirements_spec",
    "wireframe": "architecture_spec",
    # code, qa, pedagogy don't have dedicated DB columns — results stored in job queue
}


async def run_agent_workflow(
    job_id: str,
    request: AgentRequest,
    progress_callback=None,
) -> Optional[Dict[str, Any]]:
    """
    Execute agent workflow via LangGraph with proper error handling and timeouts.

    Uses LangGraph StateGraph to route to the correct agent node(s).
    Supports single-agent runs and full builder pipelines.

    Args:
        job_id: Unique job identifier
        request: Agent request with type and context
        progress_callback: Optional async callback(progress, node_name)

    Returns:
        Agent result dictionary (Pydantic model serialized to dict)

    Security:
        - All inputs validated via Pydantic schema
        - All outputs validated via Pydantic schema (enforced by PydanticOutputParser)
        - Timeouts prevent resource exhaustion (5 min max)
        - Error messages sanitized (no stack traces to client)
        - Database operations use RLS
    """
    from app.agents.graph.workflows import (
        SINGLE_AGENT_RESULT_KEYS,
        build_single_agent_graph,
        get_initial_state,
    )

    logger.info(f"Starting agent workflow: job={job_id}, type={request.agent_type}")

    # Timeout configuration per agent type (seconds)
    timeouts = {
        "research": 180,
        "wireframe": 240,
        "code": 300,
        "qa": 120,
        "pedagogy": 120,
    }
    timeout = timeouts.get(request.agent_type, settings.AGENT_TIMEOUT)

    try:
        # Build LangGraph and initial state
        graph = build_single_agent_graph(
            agent_type=request.agent_type,
            callback=progress_callback,
        )
        initial_state = get_initial_state(
            project_id=request.project_id,
            agent_type=request.agent_type,
            input_context=request.input_context,
            job_id=job_id,
        )

        # Execute graph with timeout
        final_state = await asyncio.wait_for(
            graph.ainvoke(initial_state),
            timeout=timeout,
        )

        # Extract the result from the correct state key
        result_key = SINGLE_AGENT_RESULT_KEYS.get(request.agent_type)
        result_dict = final_state.get(result_key) if result_key else None

        if result_dict is None:
            raise AgentExecutionError(request.agent_type, "Agent produced no result")

        # Store result in database if it maps to a DB column
        db_column = AGENT_RESULT_COLUMN_MAP.get(request.agent_type)
        if db_column:
            await DatabaseOperations.update_project(
                request.project_id,
                {
                    "status": "in-progress",
                    db_column: result_dict,
                },
            )

        logger.info(f"Agent workflow completed: job={job_id}")
        return result_dict

    except asyncio.TimeoutError:
        error_msg = f"Agent execution timeout ({timeout}s)"
        logger.error(f"Timeout for job {job_id}: {error_msg}")
        raise AgentExecutionError(request.agent_type, error_msg)

    except AgentExecutionError:
        raise

    except Exception as e:
        error_msg = f"Agent execution failed: {str(e)}"
        logger.error(f"Error in job {job_id}: {error_msg}")
        raise AgentExecutionError(request.agent_type, error_msg)


async def run_builder_pipeline(
    job_id: str,
    project_id: str,
    input_context: Dict[str, Any],
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Execute the full builder pipeline: research → wireframe → code → qa (with retry).

    This is the multi-step workflow that generates a complete project from an idea.
    The Code→QA loop retries up to MAX_AGENT_ITERATIONS times if QA fails.

    Args:
        job_id: Unique job identifier
        project_id: UUID of the project
        input_context: Must contain 'user_idea' at minimum
        progress_callback: Optional async callback(progress, node_name)

    Returns:
        Final state dict with all agent outputs

    Security:
        - Bounded by MAX_AGENT_ITERATIONS to prevent infinite loops
        - Total timeout of AGENT_TIMEOUT * 3 for the full pipeline
    """
    from app.agents.graph.workflows import (
        build_builder_pipeline,
        get_initial_state,
    )

    logger.info(f"Starting builder pipeline: job={job_id}, project={project_id}")

    total_timeout = settings.AGENT_TIMEOUT * 3  # ~15 min for full pipeline

    try:
        graph = build_builder_pipeline(callback=progress_callback)
        initial_state = get_initial_state(
            project_id=project_id,
            agent_type="builder",
            input_context=input_context,
            job_id=job_id,
        )

        final_state = await asyncio.wait_for(
            graph.ainvoke(initial_state),
            timeout=total_timeout,
        )

        # Persist all results to database
        update_data = {"status": "in-progress"}
        if final_state.get("requirements_spec"):
            update_data["requirements_spec"] = final_state["requirements_spec"]
        if final_state.get("architecture_spec"):
            update_data["architecture_spec"] = final_state["architecture_spec"]

        await DatabaseOperations.update_project(project_id, update_data)

        logger.info(f"Builder pipeline completed: job={job_id}")
        return {
            "requirements_spec": final_state.get("requirements_spec"),
            "architecture_spec": final_state.get("architecture_spec"),
            "generated_code": final_state.get("generated_code"),
            "qa_result": final_state.get("qa_result"),
            "iterations": final_state.get("iteration_count", 0),
        }

    except asyncio.TimeoutError:
        error_msg = f"Builder pipeline timeout ({total_timeout}s)"
        logger.error(f"Timeout for job {job_id}: {error_msg}")
        raise AgentExecutionError("builder", error_msg)

    except AgentExecutionError:
        raise

    except Exception as e:
        error_msg = f"Builder pipeline failed: {str(e)}"
        logger.error(f"Error in job {job_id}: {error_msg}")
        raise AgentExecutionError("builder", error_msg)
