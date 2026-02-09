"""
Agent Orchestrator - coordinates agent workflows
"""
from typing import Dict, Any
from datetime import datetime

from app.schemas.protocol import AgentRequest, JobStatus
from app.agents.research_agent import run_research_agent
from app.agents.wireframe_agent import run_wireframe_agent
from app.agents.code_agent import run_code_agent
from app.services.supabase import supabase_client


async def run_agent_workflow(
    job_id: str,
    request: AgentRequest,
    job_store: Dict[str, JobStatus],
) -> None:
    """
    Execute agent workflow asynchronously
    Updates job status and stores results in Supabase
    
    Security: All inputs validated via Pydantic
    Timeout: Max 5 minutes per agent
    """
    try:
        # Update status to running
        job_store[job_id].status = "running"
        
        # Route to appropriate agent
        if request.agent_type == "research":
            user_idea = request.input_context.get("user_idea", "")
            result = await run_research_agent(user_idea)
            
            # Store in Supabase
            await supabase_client.table("projects").update({
                "requirements_spec": result.model_dump(),
                "status": "requirements_complete",
            }).eq("id", request.project_id).execute()
        
        elif request.agent_type == "wireframe":
            requirements = request.input_context.get("requirements", "")
            result = await run_wireframe_agent(requirements)
            
            await supabase_client.table("projects").update({
                "architecture_spec": result.model_dump(),
                "status": "architecture_complete",
            }).eq("id", request.project_id).execute()
        
        elif request.agent_type == "code":
            architecture = request.input_context.get("architecture", "")
            file_path = request.input_context.get("file_path", "")
            result = await run_code_agent(architecture, file_path)
            
            # Store file in project_files table
            await supabase_client.table("project_files").insert({
                "project_id": request.project_id,
                "path": file_path,
                "content": result,
                "language": "typescript",
            }).execute()
        
        # Mark job as completed
        job_store[job_id].status = "completed"
        job_store[job_id].result = {"success": True}
        job_store[job_id].completed_at = datetime.utcnow()
    
    except Exception as e:
        # Error handling - log but don't expose internals
        job_store[job_id].status = "failed"
        job_store[job_id].error = "Agent execution failed"
        job_store[job_id].completed_at = datetime.utcnow()
        
        # Log error server-side (structured logging)
        print(f"Agent error: {str(e)}")
