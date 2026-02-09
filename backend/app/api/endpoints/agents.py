"""
Agent API endpoints
POST /run-agent - Trigger an agent job
GET /jobs/{job_id} - Get job status
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from uuid import uuid4
from typing import Dict, Any

from app.schemas.protocol import AgentRequest, AgentResponse, JobStatus
from app.agents.orchestrator import run_agent_workflow

router = APIRouter()

# In-memory job storage (replace with Redis in production)
jobs: Dict[str, JobStatus] = {}


@router.post("/run-agent", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    background_tasks: BackgroundTasks,
) -> AgentResponse:
    """
    Trigger an AI agent to run asynchronously
    Returns job_id immediately for status polling
    
    Security: Input validated via Pydantic schema
    Rate limiting: Applied at middleware level
    """
    job_id = str(uuid4())
    
    # Initialize job status
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="queued",
        agent_type=request.agent_type,
        project_id=request.project_id,
    )
    
    # Run agent in background (non-blocking)
    background_tasks.add_task(
        run_agent_workflow,
        job_id=job_id,
        request=request,
        job_store=jobs,
    )
    
    return AgentResponse(
        job_id=job_id,
        status="queued",
        estimated_time="30-60s",
    )


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    """
    Get the status of an agent job
    
    Returns:
    - queued: Job is waiting
    - running: Agent is working
    - completed: Finished successfully
    - failed: Error occurred
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]
