"""
Pydantic schemas for API request/response contracts
Enforces strict validation on all inputs/outputs
Uses Pydantic v2 with strict mode for maximum type safety
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
        ..., min_length=36, max_length=36, description="UUID of the project (36 chars)"
    )
    agent_type: AgentType = Field(..., description="Type of agent to run")
    input_context: Dict[str, Any] = Field(
        default_factory=dict,
        max_length=10,  # Limit fields
        description="Agent-specific context (max 10 fields)",
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
    estimated_time: str = Field(
        ..., description="Estimated completion time (e.g., '5-10 minutes')"
    )


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
        default=0.0, ge=0.0, le=100.0, description="Completion percentage"
    )
    created_at: datetime
    completed_at: Optional[datetime] = None


class ProjectCreate(BaseModel):
    """Create project request"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(..., min_length=3, max_length=200, description="Project title")
    description: str = Field(
        default="", max_length=1000, description="Project description"
    )
    mode: Literal["builder", "student"] = Field(
        default="builder", description="Learning mode - builder or student"
    )
    tech_stack: Optional[List[str]] = Field(
        default=None, max_length=10, description="Recommended technologies (up to 10)"
    )


class ProjectUpdate(BaseModel):
    """Update project request"""

    model_config = ConfigDict(
        str_strip_whitespace=True, extra="forbid", use_attribute_docstrings=True
    )

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern="^(planning|in-progress|completed)$")


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
        None, max_length=1000, description="Any technical limitations or considerations"
    )


class Component(BaseModel):
    """React component specification"""

    name: str = Field(..., min_length=1, max_length=100, pattern="^[A-Z][a-zA-Z0-9]*$")
    props: List[str] = Field(default_factory=list, max_length=20)
    children: List[str] = Field(default_factory=list, max_length=20)


class PageRoute(BaseModel):
    """Page route specification"""

    path: str = Field(..., min_length=1, max_length=200, pattern="^/[a-z0-9-/]*$")
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
                raise ValueError(
                    f"Invalid color format: {color}. Expected hex color like #FF5733"
                )
        return v


# --- Code Agent output schemas ---


class GeneratedFile(BaseModel):
    """A single generated code file"""

    file_path: str = Field(
        ..., min_length=1, max_length=500, description="Path relative to src/"
    )
    content: str = Field(..., min_length=1, description="Complete file content")
    language: str = Field(default="typescript", description="Programming language")
    explanation: str = Field(
        default="", max_length=1000, description="Why this file was generated"
    )


class CodeGenerationResult(BaseModel):
    """
    Code Agent output schema
    Enforces structured code generation output
    """

    model_config = ConfigDict(extra="forbid")

    files: List[GeneratedFile] = Field(
        ..., min_length=1, max_length=50, description="Generated files"
    )
    summary: str = Field(
        ..., min_length=10, max_length=2000, description="Overview of generated code"
    )
    dependencies: List[str] = Field(
        default_factory=list, max_length=30, description="npm packages needed"
    )


# --- QA Agent output schemas ---


class QAIssueSeverity(str, Enum):
    """QA issue severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QAIssue(BaseModel):
    """A single QA issue found in code"""

    severity: QAIssueSeverity = Field(..., description="Issue severity level")
    category: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="e.g. 'security', 'type-safety', 'performance'",
    )
    file_path: str = Field(..., min_length=1, max_length=500)
    line_hint: Optional[str] = Field(
        None, max_length=200, description="Approximate location hint"
    )
    description: str = Field(..., min_length=5, max_length=1000)
    suggestion: str = Field(
        ..., min_length=5, max_length=1000, description="How to fix it"
    )


class QAResult(BaseModel):
    """
    QA Agent output schema
    Structured code review results with actionable issues
    """

    model_config = ConfigDict(extra="forbid")

    passed: bool = Field(..., description="Whether the code passes quality checks")
    issues: List[QAIssue] = Field(default_factory=list, max_length=100)
    summary: str = Field(
        ..., min_length=5, max_length=2000, description="Overall review summary"
    )
    score: float = Field(..., ge=0.0, le=100.0, description="Quality score out of 100")


# --- Pedagogy Agent output schemas ---


class LearningStep(BaseModel):
    """A guided learning step"""

    step_number: int = Field(..., ge=1)
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Socratic question to ask the student",
    )
    hint: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Hint without giving away the answer",
    )
    concept: str = Field(
        ..., min_length=1, max_length=200, description="Concept being taught"
    )


class PedagogyResponse(BaseModel):
    """
    Pedagogy Agent output schema
    Guided Socratic learning response
    """

    model_config = ConfigDict(extra="forbid")

    encouragement: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Positive framing for the student",
    )
    steps: List[LearningStep] = Field(
        ..., min_length=1, max_length=10, description="Guided learning steps"
    )
    key_concept: str = Field(
        ..., min_length=5, max_length=500, description="Core concept being explored"
    )
    further_exploration: List[str] = Field(
        default_factory=list, max_length=5, description="Topics to explore next"
    )


# --- Student Mode / Choice Framework schemas ---


class ImplementationOption(BaseModel):
    """An implementation option for the student to choose from"""

    id: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=3, max_length=200)
    pros: List[str] = Field(..., min_length=1, max_length=10)
    cons: List[str] = Field(default_factory=list, max_length=10)
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(...)
    educational_value: str = Field(..., min_length=5, max_length=500)


class ChoiceFramework(BaseModel):
    """
    Choice Framework for Student Mode
    Presents implementation options for the student to reason about
    """

    model_config = ConfigDict(extra="forbid")

    context: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="What decision needs to be made",
    )
    options: List[ImplementationOption] = Field(..., min_length=2, max_length=5)
    recommendation: Optional[str] = Field(
        None, max_length=500, description="Mentor's recommended option and reasoning"
    )


class CodeFileCreate(BaseModel):
    """Create a code file in project"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    path: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="File path (must start with 'src/')",
    )
    content: str = Field(..., max_length=100000, description="File content (max 100KB)")
    language: str = Field(
        default="typescript", pattern="^(typescript|javascript|jsx|tsx|css|html)$"
    )

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate file path"""
        if not v.startswith("src/"):
            raise ValueError("File path must start with 'src/'")
        if ".." in v or v.startswith("/"):
            raise ValueError(
                "Invalid path: cannot traverse directories or start with /"
            )
        return v


class CodeFileUpdate(BaseModel):
    """Update an existing code file"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    content: str = Field(..., max_length=100000, description="File content (max 100KB)")
    language: Optional[str] = Field(
        None, pattern="^(typescript|javascript|jsx|tsx|css|html|json|markdown)$"
    )


class PaginatedResponse(BaseModel):
    """Generic paginated response envelope"""

    items: List[Dict[str, Any]] = Field(default_factory=list)
    total: int = Field(..., ge=0, description="Total number of records")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=50, description="Items per page (max 50)")
    has_more: bool = Field(..., description="Whether more pages exist")
