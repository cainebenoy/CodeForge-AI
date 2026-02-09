"""
Agent API endpoints
Handles agent job management: triggering, polling, and completion
"""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends

from app.core.auth import CurrentUser, get_current_user
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.logging import logger
from app.schemas.protocol import (
    AgentRequest,
    AgentResponse,
    AgentType,
    JobStatus,
    JobStatusType,
)
from app.services.job_queue import job_store
from app.services.validation import InputValidator

router = APIRouter(tags=["agents"])


async def validate_agent_request(request: AgentRequest) -> AgentRequest:
    """Validate agent request input"""
    # UUID validation
    InputValidator.validate_uuid(request.project_id)

    # Context size validation
    import json

    context_size = len(json.dumps(request.input_context))
    if context_size > 50000:
        raise ValidationError("input_context", "Context exceeds 50KB limit")

    logger.info(
        f"Validated agent request: project={request.project_id}, "
        f"agent={request.agent_type}, context_size={context_size}"
    )
    return request


@router.post("/run-agent", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest = Depends(validate_agent_request),
    user: CurrentUser = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
) -> AgentResponse:
    """
    Trigger an AI agent to run asynchronously

    Request body:
    - project_id: UUID of project to work on
    - agent_type: One of 'research', 'wireframe', 'code', 'qa', 'pedagogy'
    - input_context: Agent-specific context dictionary

    Returns job_id immediately for status polling via GET /v1/jobs/{job_id}

    Security:
    - Input validated and sanitized via Pydantic schema
    - UUID format enforced
    - Context size limited to 50KB
    - Rate limiting applied at middleware level
    - Input context recursively sanitized
    """
    job_id = str(uuid4())

    try:
        # Verify user owns the project before running agent
        from app.services.database import DatabaseOperations

        await DatabaseOperations.get_project(request.project_id, user_id=user.id)

        # Sanitize context
        sanitized_context = InputValidator.sanitize_dict(request.input_context)

        # Create job
        job = job_store.create_job(
            job_id=job_id,
            project_id=request.project_id,
            agent_type=request.agent_type,
            input_context=sanitized_context,
        )

        logger.info(
            f"Created agent job: {job_id} (type={request.agent_type}, "
            f"project={request.project_id})"
        )

        # Add background task to execute agent
        # In production, use Celery, RQ, or dedicated job queue
        if background_tasks:
            background_tasks.add_task(
                execute_agent_background,
                job_id=job_id,
                request=request,
            )

        # Estimate time based on agent type
        time_estimates = {
            "research": "2-3 minutes",
            "wireframe": "3-5 minutes",
            "code": "5-10 minutes",
            "qa": "1-2 minutes",
            "pedagogy": "1-2 minutes",
        }

        return AgentResponse(
            job_id=job_id,
            status=JobStatusType.QUEUED,
            estimated_time=time_estimates.get(request.agent_type, "2-5 minutes"),
        )

    except Exception as e:
        logger.error(f"Error creating agent job: {str(e)}")
        raise


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> JobStatus:
    """
    Get the status of an agent job

    Returns job status with:
    - status: One of 'queued', 'running', 'completed', 'failed'
    - progress: Completion percentage (0-100)
    - result: Agent output (if completed)
    - error: Error message (if failed)

    Status values:
    - queued: Job is waiting in queue
    - running: Agent is actively working
    - completed: Finished successfully
    - failed: Error occurred during execution

    Polling interval: 1-5 seconds recommended
    """
    # Validate job_id is a valid UUID
    InputValidator.validate_uuid(job_id)

    job = job_store.get_job(job_id)
    if not job:
        raise ResourceNotFoundError("Job", job_id)

    logger.debug(f"Retrieved job status: {job_id} ({job.status})")

    return JobStatus(
        job_id=job.job_id,
        status=job.status,
        agent_type=job.agent_type,
        project_id=job.project_id,
        result=job.result,
        error=job.error,
        progress=job.progress,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("/jobs/{project_id}/list")
async def list_project_jobs(
    project_id: str,
    limit: int = 50,
    user: CurrentUser = Depends(get_current_user),
):
    """
    List all jobs for a project

    Query parameters:
    - limit: Maximum number of jobs to return (max 100)

    Returns: List of jobs sorted by creation date (newest first)
    """
    if limit > 100:
        raise ValidationError("limit", "Maximum limit is 100")

    InputValidator.validate_uuid(project_id)

    jobs = job_store.get_project_jobs(project_id, limit=limit)

    return {
        "project_id": project_id,
        "count": len(jobs),
        "jobs": [job.to_dict() for job in jobs],
    }


async def execute_agent_background(job_id: str, request: AgentRequest):
    """
    Execute agent in background
    Updates job status as it progresses
    """
    try:
        logger.info(f"Starting background execution for job {job_id}")

        # Update status to running
        job_store.update_job(job_id, status=JobStatusType.RUNNING, progress=10)

        # Import agent implementations when needed (avoid circular imports)
        from app.agents.orchestrator import run_agent_workflow

        # Execute agent (this should be async in future)
        result = await run_agent_workflow(
            job_id=job_id,
            request=request,
        )

        # Update job with result
        job_store.update_job(
            job_id,
            status=JobStatusType.COMPLETED,
            progress=100,
            result=result,
        )

        logger.info(f"Completed job {job_id}")

    except Exception as e:
        logger.error(f"Agent job failed: {job_id} - {str(e)}")
        job_store.update_job(job_id, error=str(e), progress=0)
