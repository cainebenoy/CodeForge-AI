"""
Pydantic schemas for API request/response contracts
Enforces strict validation on all inputs/outputs
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class AgentRequest(BaseModel):
    """
    Request to run an AI agent
    All fields validated and sanitized
    """
    project_id: str = Field(..., min_length=36, max_length=36, description="UUID of the project")
    agent_type: str = Field(..., pattern="^(research|wireframe|code|qa|pedagogy)$")
    input_context: Dict[str, Any] = Field(..., description="Agent-specific context")


class AgentResponse(BaseModel):
    """Response from agent trigger"""
    job_id: str
    status: str
    estimated_time: str


class JobStatus(BaseModel):
    """Agent job status"""
    job_id: str
    status: str  # queued, running, completed, failed
    agent_type: str
    project_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


# Agent output schemas (Pydantic enforced)

class UserPersona(BaseModel):
    """User persona for requirements"""
    role: str
    goal: str
    pain_point: str


class Feature(BaseModel):
    """Feature specification"""
    name: str
    description: str
    priority: str = Field(..., pattern="^(Must Have|Should Have|Nice to Have)$")


class RequirementsDoc(BaseModel):
    """
    Research Agent output schema
    Forces LLM to output valid structured data
    """
    app_name: str
    elevator_pitch: str
    target_audience: List[UserPersona]
    core_features: List[Feature]
    recommended_stack: List[str]
    technical_constraints: Optional[str] = None


class Component(BaseModel):
    """React component specification"""
    name: str
    props: List[str]
    children: List[str]


class PageRoute(BaseModel):
    """Page route specification"""
    path: str
    description: str
    components: List[Component]


class WireframeSpec(BaseModel):
    """
    Wireframe Agent output schema
    """
    site_map: List[PageRoute]
    global_state_needs: List[str]
    theme_colors: List[str]
