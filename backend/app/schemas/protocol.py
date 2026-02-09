"""
Pydantic schemas for API request/response contracts
Enforces strict validation on all inputs/outputs
Uses Pydantic v2 with strict mode for maximum type safety
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Valid agent types"""
    RESEARCH = "research"
    WIREFRAME = "wireframe"
    CODE = "code"
    QA = "qa"
    PEDAGOGY = "pedagogy"


class JobStatusType(str, Enum):
    """Valid job statuses"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PriorityLevel(str, Enum):
    """Feature priority levels"""
    MUST_HAVE = "must-have"
    SHOULD_HAVE = "should-have"
    NICE_TO_HAVE = "nice-to-have"


class AgentRequest(BaseModel):
    """
    Request to run an AI agent
    All fields validated and sanitized according to security requirements
    """
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    project_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
        description="UUID of the project (36 chars)"
    )
    agent_type: AgentType = Field(
        ...,
        description="Type of agent to run"
    )
    input_context: Dict[str, Any] = Field(
        default_factory=dict,
        max_length=10,  # Limit fields
        description="Agent-specific context (max 10 fields)"
    )
    
    @field_validator("input_context")
    @classmethod
    def validate_context(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input context doesn't exceed size limits"""
        import json
        context_size = len(json.dumps(v))
        if context_size > 50000:  # 50KB limit
            raise ValueError("Input context exceeds 50KB size limit")
        return v


class AgentResponse(BaseModel):
    """Response from agent trigger"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatusType = Field(..., description="Current job status")
    estimated_time: str = Field(..., description="Estimated completion time (e.g., '5-10 minutes')")


class JobStatus(BaseModel):
    """Agent job status for polling"""
    model_config = ConfigDict(extra="forbid")
    
    job_id: str
    status: JobStatusType
    agent_type: AgentType
    project_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Completion percentage"
    )
    created_at: datetime
    completed_at: Optional[datetime] = None


class ProjectCreate(BaseModel):
    """Create project request"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Project title"
    )
    description: str = Field(
        default="",
        max_length=1000,
        description="Project description"
    )
    mode: Literal["builder", "student"] = Field(
        default="builder",
        description="Learning mode - builder or student"
    )
    tech_stack: Optional[List[str]] = Field(
        default=None,
        max_length=10,
        description="Recommended technologies (up to 10)"
    )


class ProjectUpdate(BaseModel):
    """Update project request"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", use_attribute_docstrings=True)
    
    title: Optional[str] = Field(
        None,
        min_length=3,
        max_length=200
    )
    description: Optional[str] = Field(
        None,
        max_length=1000
    )
    status: Optional[str] = Field(
        None,
        pattern="^(planning|in-progress|completed)$"
    )


# Agent output schemas (Pydantic enforced - prevents hallucinated outputs)

class UserPersona(BaseModel):
    """User persona for requirements"""
    role: str = Field(..., min_length=1, max_length=100)
    goal: str = Field(..., min_length=1, max_length=500)
    pain_point: str = Field(..., min_length=1, max_length=500)


class Feature(BaseModel):
    """Feature specification with validation"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=500)
    priority: PriorityLevel


class RequirementsDoc(BaseModel):
    """
    Research Agent output schema
    Pydantic enforces this structure - prevents LLM hallucinations
    """
    model_config = ConfigDict(extra="forbid")
    
    app_name: str = Field(..., min_length=1, max_length=200)
    elevator_pitch: str = Field(..., min_length=20, max_length=500)
    target_audience: List[UserPersona] = Field(..., min_length=1, max_length=5)
    core_features: List[Feature] = Field(..., min_length=1, max_length=20)
    recommended_stack: List[str] = Field(..., min_length=1, max_length=10)
    technical_constraints: Optional[str] = Field(
        None,
        max_length=1000,
        description="Any technical limitations or considerations"
    )


class Component(BaseModel):
    """React component specification"""
    name: str = Field(..., min_length=1, max_length=100, pattern="^[A-Z][a-zA-Z0-9]*$")
    props: List[str] = Field(default_factory=list, max_length=20)
    children: List[str] = Field(default_factory=list, max_length=20)


class PageRoute(BaseModel):
    """Page route specification"""
    path: str = Field(..., min_length=1, max_length=200, pattern="^/[a-z0-9-]*$")
    description: str = Field(..., min_length=1, max_length=500)
    components: List[Component] = Field(..., min_length=1, max_length=50)


class WireframeSpec(BaseModel):
    """
    Wireframe Agent output schema
    Enforced structure prevents invalid architecture definitions
    """
    model_config = ConfigDict(extra="forbid")
    
    site_map: List[PageRoute] = Field(..., min_length=1, max_length=50)
    global_state_needs: List[str] = Field(default_factory=list, max_length=20)
    theme_colors: List[str] = Field(..., min_length=1, max_length=10)

    @field_validator("theme_colors")
    @classmethod
    def validate_colors(cls, v: List[str]) -> List[str]:
        """Validate CSS color formats"""
        import re
        hex_pattern = re.compile(r"^#[0-9a-fA-F]{6}$")
        for color in v:
            if not hex_pattern.match(color):
                raise ValueError(f"Invalid color format: {color}. Expected hex color like #FF5733")
        return v


class CodeFileCreate(BaseModel):
    """Create a code file in project"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    path: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="File path (must start with 'src/')"
    )
    content: str = Field(
        ...,
        max_length=100000,
        description="File content (max 100KB)"
    )
    language: str = Field(
        default="typescript",
        pattern="^(typescript|javascript|jsx|tsx|css|html)$"
    )
    
    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate file path"""
        if not v.startswith("src/"):
            raise ValueError("File path must start with 'src/'")
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid path: cannot traverse directories or start with /")
        return v
