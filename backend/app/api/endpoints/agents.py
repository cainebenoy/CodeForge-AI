"""
Agent API endpoints
Handles agent job management: triggering, polling, streaming, and completion
"""

import asyncio
import json
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from app.core.auth import CurrentUser, get_current_user
from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.logging import logger
from app.schemas.protocol import (
    AgentRequest,
    AgentResponse,
    AgentType,
    ClarificationAnswer,
    JobStatus,
    JobStatusType,
)
from app.services.database import DatabaseOperations
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

        # Create job in memory/Redis store (fast polling)
        job = job_store.create_job(
            job_id=job_id,
            project_id=request.project_id,
            agent_type=request.agent_type,
            input_context=sanitized_context,
            user_id=user.id,
        )

        # Persist to DB for Supabase Realtime (best-effort)
        try:
            await DatabaseOperations.create_agent_job(
                job_id=job_id,
                project_id=request.project_id,
                user_id=user.id,
                agent_type=request.agent_type.value
                if hasattr(request.agent_type, "value")
                else request.agent_type,
            )

            # Log User Message to Chat (Realtime)
            user_msg_content = request.input_context.get("user_message")
            if user_msg_content and isinstance(user_msg_content, str):
                await DatabaseOperations.create_chat_message(
                    project_id=request.project_id,
                    role="user",
                    content=user_msg_content,
                )

        except Exception as db_err:
            logger.warning(f"Could not persist job to DB: {db_err}")

        # Dispatch agent execution.
        # Use Celery when available (persistent, survives restarts, cancellable).
        # Fall back to FastAPI BackgroundTasks for dev without Redis/Celery.
        dispatched_via = "background_task"
        try:
            from app.workers.tasks import execute_single_agent_task

            celery_result = execute_single_agent_task.delay(
                job_id=job_id,
                project_id=request.project_id,
                agent_type=request.agent_type.value
                if hasattr(request.agent_type, "value")
                else request.agent_type,
                input_context=sanitized_context,
                user_id=user.id,
            )
            # Store Celery task ID in job for cancel/monitoring
            job_store.update_job(
                job_id,
                result={"_celery_task_id": celery_result.id},
            )
            dispatched_via = "celery"
        except Exception as celery_err:
            logger.warning(
                f"Celery dispatch failed ({celery_err}), "
                "falling back to BackgroundTasks"
            )
            if background_tasks:
                background_tasks.add_task(
                    execute_agent_background,
                    job_id=job_id,
                    request=request,
                )

        logger.info(f"Dispatched agent job {job_id} via {dispatched_via}")

        # Estimate time based on agent type
        time_estimates = {
            "research": "2-3 minutes",
            "wireframe": "3-5 minutes",
            "code": "5-10 minutes",
            "qa": "1-2 minutes",
            "pedagogy": "1-2 minutes",
            "roadmap": "2-3 minutes",
        }

        return AgentResponse(
            job_id=job_id,
            status=JobStatusType.QUEUED,
            estimated_time=time_estimates.get(request.agent_type, "2-5 minutes"),
        )

    except Exception as e:
        logger.error(f"Error creating agent job: {str(e)}")
        raise


@router.post("/run-pipeline", response_model=AgentResponse)
async def run_pipeline(
    request: AgentRequest,
    user: CurrentUser = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
) -> AgentResponse:
    """
    Trigger the full builder pipeline: research → wireframe → code → qa.

    Runs all agents sequentially with a code→qa retry loop.
    The agent_type field in the request is ignored (always runs full pipeline).

    Request body:
    - project_id: UUID of project to build
    - input_context: Must contain 'user_idea' at minimum

    Returns job_id for status polling via GET /v1/agents/jobs/{job_id}

    Security:
    - Auth required
    - Ownership verified
    - Input validated and sanitized
    """
    job_id = str(uuid4())

    try:
        await DatabaseOperations.get_project(request.project_id, user_id=user.id)

        sanitized_context = InputValidator.sanitize_dict(request.input_context)

        job = job_store.create_job(
            job_id=job_id,
            project_id=request.project_id,
            agent_type="builder",
            input_context=sanitized_context,
            user_id=user.id,
        )

        # Persist to DB for Supabase Realtime
        try:
            await DatabaseOperations.create_agent_job(
                job_id=job_id,
                project_id=request.project_id,
                user_id=user.id,
                agent_type="builder",
            )
        except Exception as db_err:
            logger.warning(f"Could not persist pipeline job to DB: {db_err}")

        logger.info(
            f"Created builder pipeline job: {job_id} (project={request.project_id})"
        )

        # Dispatch via Celery (preferred) or BackgroundTasks (fallback)
        try:
            from app.workers.tasks import execute_pipeline_task

            celery_result = execute_pipeline_task.delay(
                job_id=job_id,
                project_id=request.project_id,
                input_context=sanitized_context,
                user_id=user.id,
            )
            job_store.update_job(
                job_id,
                result={"_celery_task_id": celery_result.id},
            )
        except Exception as celery_err:
            logger.warning(
                f"Celery dispatch failed ({celery_err}), "
                "falling back to BackgroundTasks"
            )
            if background_tasks:
                background_tasks.add_task(
                    execute_pipeline_background,
                    job_id=job_id,
                    project_id=request.project_id,
                    input_context=sanitized_context,
                )

        return AgentResponse(
            job_id=job_id,
            status=JobStatusType.QUEUED,
            estimated_time="10-15 minutes",
        )

    except Exception as e:
        logger.error(f"Error creating pipeline job: {str(e)}")
        raise


async def execute_pipeline_background(
    job_id: str, project_id: str, input_context: dict
):
    """Execute the full builder pipeline in background."""
    try:
        logger.info(f"Starting builder pipeline for job {job_id}")
        job_store.update_job(job_id, status=JobStatusType.RUNNING, progress=5)
        await _sync_job_to_db(job_id, status="running", progress=5)

        from app.agents.orchestrator import run_builder_pipeline

        result = await run_builder_pipeline(
            job_id=job_id,
            project_id=project_id,
            input_context=input_context,
        )

        job_store.update_job(
            job_id,
            status=JobStatusType.COMPLETED,
            progress=100,
            result=result,
        )
        await _sync_job_to_db(job_id, status="completed", progress=100, result=result)
        logger.info(f"Completed builder pipeline job {job_id}")

    except Exception as e:
        logger.error(f"Builder pipeline failed: {job_id} - {str(e)}")
        job_store.update_job(job_id, error=str(e), progress=0)
        await _sync_job_to_db(job_id, status="failed", error=str(e))


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

    # Authorization: verify the requesting user owns this job
    if job.user_id and job.user_id != user.id:
        from app.core.exceptions import PermissionError

        raise PermissionError("You do not have access to this job")

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
    page: int = 1,
    page_size: int = 20,
    user: CurrentUser = Depends(get_current_user),
):
    """
    List all jobs for a project with pagination.

    Query parameters:
    - page: Page number (default 1)
    - page_size: Items per page (default 20, max 100)

    Returns: Paginated list of jobs sorted by creation date (newest first)
    """
    if page_size > 100:
        raise ValidationError("page_size", "Maximum page_size is 100")
    if page < 1:
        raise ValidationError("page", "Page must be >= 1")

    InputValidator.validate_uuid(project_id)

    # Verify user owns this project
    from app.services.database import DatabaseOperations

    await DatabaseOperations.get_project(project_id, user_id=user.id)

    offset = (page - 1) * page_size
    result = job_store.get_project_jobs(project_id, limit=page_size, offset=offset)

    return {
        "project_id": project_id,
        "page": page,
        "page_size": page_size,
        "total": result["total"],
        "has_more": result["has_more"],
        "jobs": [job.to_dict() for job in result["items"]],
    }


async def _sync_job_to_db(
    job_id: str,
    status: Optional[str] = None,
    progress: Optional[float] = None,
    result: Optional[dict] = None,
    error: Optional[str] = None,
) -> None:
    """
    Best-effort sync of job status to the persistent agent_jobs table.
    This triggers Supabase Realtime notifications to connected frontends.
    Failures are logged but never propagated — the in-memory/Redis store
    remains the primary source during execution.
    """
    try:
        await DatabaseOperations.update_agent_job(
            job_id, status=status, progress=progress, result=result, error=error
        )
    except Exception as e:
        logger.warning(f"Could not sync job {job_id} to DB: {e}")


async def execute_agent_background(job_id: str, request: AgentRequest):
    """
    Execute agent in background
    Updates job status as it progresses.

    For research agents: runs the clarification phase first.
    The clarification questions are stored in the job result with is_complete=False.
    The user then calls POST /v1/agents/jobs/{job_id}/respond with answers,
    which triggers the final spec generation.
    """
    try:
        logger.info(f"Starting background execution for job {job_id}")

        # Update status to running — both in-memory store and persistent DB
        job_store.update_job(job_id, status=JobStatusType.RUNNING, progress=10)
        await _sync_job_to_db(job_id, status="running", progress=10)

        # Research agent: check if we should run clarification first
        if request.agent_type == "research":
            # Check if clarifications were already provided (respond flow)
            clarifications = request.input_context.get("_clarifications")
            if clarifications:
                # Phase 2: Generate final spec with clarification answers
                from app.agents.research_agent import run_research_with_context

                result_obj = await run_research_with_context(
                    user_idea=request.input_context.get("user_idea", ""),
                    target_audience=request.input_context.get("target_audience", ""),
                    clarifications=clarifications,
                )
                result = result_obj.model_dump()

                # Persist to database
                from app.services.database import DatabaseOperations

                await DatabaseOperations.update_project(
                    request.project_id,
                    {"status": "in-progress", "requirements_spec": result},
                )

                job_store.update_job(
                    job_id,
                    status=JobStatusType.COMPLETED,
                    progress=100,
                    result=result,
                )
                await _sync_job_to_db(
                    job_id, status="completed", progress=100, result=result
                )
                logger.info(f"Completed research job {job_id} (with clarifications)")
                return

            # Phase 1: Run clarification phase
            skip_clarification = request.input_context.get("skip_clarification", False)
            if not skip_clarification:
                try:
                    from app.agents.research_agent import run_research_clarification

                    job_store.update_job(job_id, progress=30)

                    clarify_result = await run_research_clarification(
                        user_idea=request.input_context.get("user_idea", ""),
                        target_audience=request.input_context.get(
                            "target_audience", ""
                        ),
                    )

                    # Store clarification data and mark as needing response
                    job = job_store.get_job(job_id)
                    if job:
                        job.clarification_data = {
                            "original_context": request.input_context,
                            "project_id": request.project_id,
                        }

                    job_store.update_job(
                        job_id,
                        status=JobStatusType.WAITING_FOR_INPUT,
                        progress=50,
                        result={
                            "is_complete": False,
                            "questions": clarify_result.model_dump()["questions"],
                            "message": "Please answer the clarifying questions and "
                            "submit via POST /v1/agents/jobs/{job_id}/respond",
                        },
                    )
                    await _sync_job_to_db(
                        job_id,
                        status="waiting_for_input",
                        progress=50,
                        result={
                            "is_complete": False,
                            "questions": clarify_result.model_dump()["questions"],
                        },
                    )
                    logger.info(
                        f"Clarification phase complete for job {job_id}: "
                        f"{len(clarify_result.questions)} questions"
                    )
                    return
                except Exception as clarify_err:
                    # If clarification fails, fall through to direct generation
                    logger.warning(
                        f"Clarification failed, falling back to direct: {clarify_err}"
                    )

        # Standard agent execution (non-research or skip_clarification)
        from app.agents.orchestrator import run_agent_workflow

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
        await _sync_job_to_db(job_id, status="completed", progress=100, result=result)

        logger.info(f"Completed job {job_id}")

    except Exception as e:
        logger.error(f"Agent job failed: {job_id} - {str(e)}")
        job_store.update_job(job_id, error=str(e), progress=0)
        await _sync_job_to_db(job_id, status="failed", error=str(e))


@router.post("/jobs/{job_id}/respond")
async def respond_to_clarification(
    job_id: str,
    body: ClarificationAnswer,
    user: CurrentUser = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
):
    """
    Submit answers to the Research Agent's clarifying questions.

    After triggering a research agent job, the job result may contain
    clarifying questions (is_complete=False). Use this endpoint to submit
    answers, which triggers the full requirements spec generation.

    Body:
    - answers: List of {question: answer} pairs

    Returns: New job tracking the final spec generation

    Security:
    - Auth required
    - Job existence validated
    - Original project ownership re-verified
    """
    InputValidator.validate_uuid(job_id)

    job = job_store.get_job(job_id)
    if not job:
        raise ResourceNotFoundError("Job", job_id)

    # Verify job has clarification data
    if (
        not job.result
        or job.result.get("is_complete") is not False
        or job.status != JobStatusType.WAITING_FOR_INPUT
    ):
        raise ValidationError(
            "job_id",
            "This job does not have pending clarification questions",
        )

    # Get original context
    clarification_data = job.clarification_data or {}
    original_context = clarification_data.get("original_context", {})
    project_id = clarification_data.get("project_id") or job.project_id

    # Verify the user owns the project
    from app.services.database import DatabaseOperations

    await DatabaseOperations.get_project(project_id, user_id=user.id)

    # Create a new job for the final generation
    from uuid import uuid4

    new_job_id = str(uuid4())

    # Build enriched context
    enriched_context = dict(original_context)
    enriched_context["_clarifications"] = body.answers
    enriched_context["skip_clarification"] = True

    new_request = AgentRequest(
        project_id=project_id,
        agent_type=AgentType.RESEARCH,
        input_context=enriched_context,
    )

    job_store.create_job(
        job_id=new_job_id,
        project_id=project_id,
        agent_type="research",
        input_context=enriched_context,
        user_id=user.id,
    )

    if background_tasks:
        background_tasks.add_task(
            execute_agent_background,
            job_id=new_job_id,
            request=new_request,
        )

    logger.info(
        f"Created follow-up research job {new_job_id} with "
        f"{len(body.answers)} clarification answers"
    )

    return AgentResponse(
        job_id=new_job_id,
        status=JobStatusType.QUEUED,
        estimated_time="2-3 minutes",
    )


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Cancel a running or queued agent job.

    If the job is running via Celery, sends a revoke signal to terminate
    the worker task. Updates job status to 'cancelled'.

    Security:
    - Auth required
    - Job ownership verified
    - Only non-terminal jobs can be cancelled
    """
    InputValidator.validate_uuid(job_id)

    job = job_store.get_job(job_id)
    if not job:
        raise ResourceNotFoundError("Job", job_id)

    # Authorization: verify the requesting user owns this job
    if job.user_id and job.user_id != user.id:
        from app.core.exceptions import PermissionError

        raise PermissionError("You do not have access to this job")

    # Can only cancel non-terminal jobs
    if job.is_complete:
        raise ValidationError(
            "job_id",
            f"Cannot cancel job in '{job.status.value}' state",
        )

    # Attempt Celery revocation if a celery_task_id is stored
    celery_task_id = (job.result or {}).get("_celery_task_id")
    if celery_task_id:
        try:
            from app.workers.celery_app import celery_app

            celery_app.control.revoke(celery_task_id, terminate=True, signal="SIGTERM")
            logger.info(f"Revoked Celery task {celery_task_id} for job {job_id}")
        except Exception as e:
            logger.warning(f"Could not revoke Celery task: {e}")

    # Update job status
    job_store.update_job(
        job_id,
        status=JobStatusType.CANCELLED,
        progress=job.progress,
    )

    logger.info(f"Cancelled job {job_id}")

    return {"job_id": job_id, "status": "cancelled", "message": "Job cancelled"}


# ──────────────────────────────────────────────────────────────
# SSE Streaming — real-time job progress
# ──────────────────────────────────────────────────────────────


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(
    job_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Stream agent job progress as Server-Sent Events (SSE).

    The endpoint polls the job store every second and emits SSE events
    with progress updates. Closes automatically when the job completes,
    fails, or the stream timeout is reached.

    Event format:
        event: progress
        data: {"job_id": "...", "status": "running", "progress": 40.0}

        event: complete
        data: {"job_id": "...", "status": "completed", "progress": 100.0, "result": {...}}

        event: error
        data: {"job_id": "...", "status": "failed", "error": "..."}

    Security:
    - Auth required
    - Job existence validated
    - Stream timeout prevents resource exhaustion
    """
    InputValidator.validate_uuid(job_id)

    # Verify the job exists before starting the stream
    job = job_store.get_job(job_id)
    if not job:
        raise ResourceNotFoundError("Job", job_id)

    # Authorization: verify the requesting user owns this job
    if job.user_id and job.user_id != user.id:
        from app.core.exceptions import PermissionError

        raise PermissionError("You do not have access to this job")

    # Stream timeout: agent timeout + 60s buffer
    stream_timeout = settings.AGENT_TIMEOUT + 60

    async def _event_generator():
        """Generate SSE events by polling job status."""
        elapsed = 0.0
        poll_interval = 1.0  # seconds
        last_progress = -1.0

        while elapsed < stream_timeout:
            current_job = job_store.get_job(job_id)
            if current_job is None:
                # Job was cleaned up
                yield _sse_event(
                    "error",
                    {
                        "job_id": job_id,
                        "status": "failed",
                        "error": "Job no longer exists",
                    },
                )
                return

            progress = current_job.progress

            if current_job.status == JobStatusType.COMPLETED:
                yield _sse_event(
                    "complete",
                    {
                        "job_id": job_id,
                        "status": "completed",
                        "progress": 100.0,
                        "result": current_job.result,
                    },
                )
                return

            if current_job.status == JobStatusType.FAILED:
                yield _sse_event(
                    "error",
                    {
                        "job_id": job_id,
                        "status": "failed",
                        "error": current_job.error or "Unknown error",
                    },
                )
                return

            if current_job.status == JobStatusType.CANCELLED:
                yield _sse_event(
                    "cancelled",
                    {
                        "job_id": job_id,
                        "status": "cancelled",
                        "progress": current_job.progress,
                    },
                )
                return

            if current_job.status == JobStatusType.WAITING_FOR_INPUT:
                yield _sse_event(
                    "waiting",
                    {
                        "job_id": job_id,
                        "status": "waiting_for_input",
                        "progress": current_job.progress,
                        "result": current_job.result,
                    },
                )
                # Don't return — keep streaming, user may respond
                if progress != last_progress:
                    last_progress = progress
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                continue

            # Only emit if progress changed (avoid duplicate events)
            if progress != last_progress:
                yield _sse_event(
                    "progress",
                    {
                        "job_id": job_id,
                        "status": current_job.status.value,
                        "progress": progress,
                    },
                )
                last_progress = progress

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        # Timeout reached
        yield _sse_event(
            "error",
            {
                "job_id": job_id,
                "status": "timeout",
                "error": f"Stream timeout after {stream_timeout}s",
            },
        )

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
