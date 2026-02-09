"""
Agent Orchestrator - coordinates agent workflows
Delegates to LangChain-based agents with Pydantic-enforced outputs
Handles timeouts, error handling, and database persistence
"""

import asyncio
import json
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
) -> Optional[Dict[str, Any]]:
    """
    Execute agent workflow asynchronously with proper error handling and timeouts

    Delegates to the LangChain-based agent implementations which enforce
    Pydantic schemas on all LLM outputs — preventing hallucinated JSON structures.

    Args:
        job_id: Unique job identifier
        request: Agent request with type and context

    Returns:
        Agent result dictionary (Pydantic model serialized to dict)

    Security:
        - All inputs validated via Pydantic schema
        - All outputs validated via Pydantic schema (enforced by PydanticOutputParser)
        - Timeouts prevent resource exhaustion (5 min max)
        - Error messages sanitized (no stack traces to client)
        - Database operations use RLS
    """
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
        # Route to appropriate LangChain agent with timeout
        result = await asyncio.wait_for(
            _dispatch_agent(request),
            timeout=timeout,
        )

        # Serialize Pydantic model to dict for storage
        if hasattr(result, "model_dump"):
            result_dict = result.model_dump()
        else:
            result_dict = result

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


async def _dispatch_agent(request: AgentRequest) -> Any:
    """
    Dispatch to the correct LangChain-based agent.

    Each agent uses PydanticOutputParser for enforced structured output.
    This is the SINGLE dispatch point — no duplicate LLM call logic.
    """
    agent_type = request.agent_type
    context = request.input_context

    if agent_type == "research":
        from app.agents.research_agent import run_research_agent

        return await run_research_agent(
            user_idea=context.get("user_idea", ""),
            target_audience=context.get("target_audience", ""),
        )

    elif agent_type == "wireframe":
        from app.agents.wireframe_agent import run_wireframe_agent

        # Requirements can be passed as dict or string
        requirements = context.get("requirements", "")
        if isinstance(requirements, dict):
            requirements = json.dumps(requirements, indent=2)
        return await run_wireframe_agent(requirements=requirements)

    elif agent_type == "code":
        from app.agents.code_agent import run_code_agent

        architecture = context.get("architecture", "")
        if isinstance(architecture, dict):
            architecture = json.dumps(architecture, indent=2)
        return await run_code_agent(
            architecture=architecture,
            file_path=context.get("file_path", ""),
        )

    elif agent_type == "qa":
        from app.agents.qa_agent import run_qa_agent

        return await run_qa_agent(
            code=context.get("code", ""),
            file_path=context.get("file_path", ""),
        )

    elif agent_type == "pedagogy":
        from app.agents.pedagogy_agent import run_pedagogy_agent

        return await run_pedagogy_agent(
            student_question=context.get("question", ""),
            student_code=context.get("code", ""),
        )

    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
