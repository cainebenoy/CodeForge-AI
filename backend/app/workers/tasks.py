"""
Celery tasks for agent execution

These tasks wrap the existing orchestrator functions to run as
persistent background tasks via Celery workers. Jobs persist across
server restarts and can be cancelled via Celery's revoke mechanism.

Each task:
1. Updates the job store on entry (RUNNING)
2. Invokes the orchestrator function (which uses LangGraph)
3. Persists results to Supabase AND the agent_jobs table
4. Updates the job store on completion/failure
5. Checks for cancellation at key boundaries
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.workers.celery_app import celery_app

logger = logging.getLogger("codeforge.workers")


def _get_event_loop() -> asyncio.AbstractEventLoop:
    """Get or create an event loop for running async code in Celery workers."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def _run_async(coro):
    """Run an async coroutine synchronously in the Celery worker."""
    loop = _get_event_loop()
    return loop.run_until_complete(coro)


class AgentTask(Task):
    """
    Base task class with common error handling and job store integration.
    Provides automatic status updates on failure and retry.
    """

    autoretry_for = ()  # Don't auto-retry agent tasks — LLM calls are non-idempotent
    max_retries = 0

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Update job store when a task fails."""
        job_id = kwargs.get("job_id") or (args[0] if args else None)
        if job_id:
            try:
                from app.schemas.protocol import JobStatusType
                from app.services.job_queue import get_job_store

                store = get_job_store()
                store.update_job(job_id, error=str(exc))
                logger.error(f"Celery task failed for job {job_id}: {exc}")
            except Exception as e:
                logger.error(f"Could not update job store on failure: {e}")

    def on_success(self, retval, task_id, args, kwargs):
        """Log successful task completion."""
        job_id = kwargs.get("job_id") or (args[0] if args else None)
        logger.info(f"Celery task succeeded for job {job_id}")


def _check_cancelled(job_id: str) -> bool:
    """
    Check if a job has been cancelled.
    Called at key boundaries between agent steps to allow early termination.
    Returns True if the job should stop.
    """
    from app.schemas.protocol import JobStatusType
    from app.services.job_queue import get_job_store

    store = get_job_store()
    job = store.get_job(job_id)
    if job and job.status == JobStatusType.CANCELLED:
        logger.info(f"Job {job_id} was cancelled, stopping execution")
        return True
    return False


@celery_app.task(base=AgentTask, bind=True, name="agents.execute_single")
def execute_single_agent_task(
    self: Task,
    job_id: str,
    project_id: str,
    agent_type: str,
    input_context: Dict[str, Any],
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Execute a single agent via Celery.

    This wraps the existing execute_agent_background logic from agents.py
    to run as a persistent Celery task.

    Args:
        job_id: Unique job identifier
        project_id: UUID of the project
        agent_type: Agent type string
        input_context: Agent-specific context dict
        user_id: UUID of the requesting user
    """
    from app.schemas.protocol import AgentRequest, AgentType, JobStatusType
    from app.services.job_queue import get_job_store

    store = get_job_store()

    # Store the Celery task ID for cancellation lookups
    store.update_job(
        job_id,
        status=JobStatusType.RUNNING,
        progress=5,
        result={"_celery_task_id": self.request.id},
    )

    try:
        if _check_cancelled(job_id):
            return None

        # Build the AgentRequest
        request = AgentRequest(
            project_id=project_id,
            agent_type=AgentType(agent_type),
            input_context=input_context,
        )

        # Delegate to the existing background execution logic
        async def _run():
            from app.api.endpoints.agents import execute_agent_background

            await execute_agent_background(job_id=job_id, request=request)

        _run_async(_run())

        return store.get_job(job_id).to_dict() if store.get_job(job_id) else None

    except SoftTimeLimitExceeded:
        logger.error(f"Celery soft time limit exceeded for job {job_id}")
        store.update_job(job_id, error="Agent execution timed out")
        return None

    except Exception as e:
        logger.error(f"Celery task error for job {job_id}: {e}")
        store.update_job(job_id, error=str(e))
        raise


@celery_app.task(base=AgentTask, bind=True, name="agents.execute_pipeline")
def execute_pipeline_task(
    self: Task,
    job_id: str,
    project_id: str,
    input_context: Dict[str, Any],
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Execute the full builder pipeline via Celery.

    Runs: research → wireframe → code → qa (with retry loop).
    Checks for cancellation between major steps.

    Args:
        job_id: Unique job identifier
        project_id: UUID of the project
        input_context: Must contain 'user_idea' at minimum
        user_id: UUID of the requesting user
    """
    from app.schemas.protocol import JobStatusType
    from app.services.job_queue import get_job_store

    store = get_job_store()

    # Store Celery task ID and mark running
    store.update_job(
        job_id,
        status=JobStatusType.RUNNING,
        progress=5,
        result={"_celery_task_id": self.request.id},
    )

    try:
        if _check_cancelled(job_id):
            return None

        async def _run():
            from app.agents.orchestrator import run_builder_pipeline

            # Progress callback that also checks cancellation
            async def _progress_callback(progress: float, node_name: str):
                if _check_cancelled(job_id):
                    raise asyncio.CancelledError(f"Job {job_id} cancelled")
                store.update_job(job_id, progress=progress)

            result = await run_builder_pipeline(
                job_id=job_id,
                project_id=project_id,
                input_context=input_context,
                progress_callback=_progress_callback,
            )

            store.update_job(
                job_id,
                status=JobStatusType.COMPLETED,
                progress=100,
                result=result,
            )

        _run_async(_run())

        return store.get_job(job_id).to_dict() if store.get_job(job_id) else None

    except SoftTimeLimitExceeded:
        logger.error(f"Pipeline soft time limit exceeded for job {job_id}")
        store.update_job(job_id, error="Builder pipeline timed out")
        return None

    except asyncio.CancelledError:
        logger.info(f"Pipeline cancelled for job {job_id}")
        return None

    except Exception as e:
        logger.error(f"Pipeline task error for job {job_id}: {e}")
        store.update_job(job_id, error=str(e))
        raise
