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
    ROADMAP = "roadmap"


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
    status: Optional[str] = Field(
        None, pattern="^(planning|in-progress|completed|archived)$"
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


class ChoiceFrameworkRequest(BaseModel):
    """Request to generate a choice framework for a decision point"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    decision_context: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="What architectural decision needs to be made",
    )
    module_index: int = Field(
        ..., ge=0, description="Index of the roadmap module this decision relates to"
    )


class ChoiceSelection(BaseModel):
    """Request to record a student's choice from the framework"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    module_index: int = Field(..., ge=0, description="Index of the roadmap module")
    option_id: str = Field(
        ..., min_length=1, max_length=50, description="ID of the chosen option"
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


# --- Student Mode / Learning Roadmap schemas ---


class LearningModule(BaseModel):
    """A single module in a learning roadmap"""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=1000)
    concepts: List[str] = Field(..., min_length=1, max_length=20)
    exercises: List[str] = Field(default_factory=list, max_length=10)
    estimated_hours: float = Field(..., ge=0.5, le=40.0)


class LearningRoadmap(BaseModel):
    """
    Learning roadmap output schema (used by Roadmap Agent)
    Structured curriculum generated from project requirements + student skill level
    """

    model_config = ConfigDict(extra="forbid")

    modules: List[LearningModule] = Field(
        ..., min_length=1, max_length=20, description="Ordered learning modules"
    )
    total_estimated_hours: float = Field(
        ..., ge=1.0, le=500.0, description="Total estimated hours"
    )
    prerequisites: List[str] = Field(
        default_factory=list, max_length=10, description="Prerequisite knowledge"
    )
    learning_objectives: List[str] = Field(
        ..., min_length=1, max_length=10, description="High-level learning goals"
    )


class RoadmapCreate(BaseModel):
    """Request to create/generate a learning roadmap"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    skill_level: Literal["beginner", "intermediate", "advanced"] = Field(
        ..., description="Student's current skill level"
    )
    focus_areas: Optional[List[str]] = Field(
        None, max_length=5, description="Specific topics to focus on"
    )


class RoadmapProgressUpdate(BaseModel):
    """Request to update roadmap progress"""

    model_config = ConfigDict(extra="forbid")

    step_index: int = Field(..., ge=0, description="New current step index")


class SessionCreate(BaseModel):
    """Request to create a daily learning session"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    transcript: List[Dict[str, Any]] = Field(
        default_factory=list,
        max_length=100,
        description="Session conversation transcript",
    )
    concepts_covered: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Concepts covered in this session",
    )
    duration_minutes: int = Field(
        default=0, ge=0, le=480, description="Session duration in minutes"
    )


class GitHubExportRequest(BaseModel):
    """Request to export project to GitHub"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    repo_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern="^[a-zA-Z0-9][a-zA-Z0-9._-]*$",
        description="GitHub repository name",
    )
    description: str = Field(
        default="",
        max_length=350,
        description="Repository description",
    )
    private: bool = Field(
        default=True,
        description="Whether the repository should be private",
    )
    github_token: str = Field(
        ...,
        min_length=1,
        max_length=500,
        repr=False,
        description="GitHub personal access token (never stored)",
    )


class StudentProgress(BaseModel):
    """Computed student progress summary"""

    model_config = ConfigDict(extra="forbid")

    roadmap_id: str = Field(..., description="UUID of the roadmap")
    project_id: str = Field(..., description="UUID of the project")
    completed_modules: int = Field(..., ge=0)
    total_modules: int = Field(..., ge=0)
    current_module: Optional[str] = Field(
        None, description="Title of the current module"
    )
    percent_complete: float = Field(..., ge=0.0, le=100.0)
    total_sessions: int = Field(..., ge=0)
    total_time_minutes: int = Field(..., ge=0)


# --- Research Agent Clarification schemas ---


class ClarificationQuestion(BaseModel):
    """A single clarifying question from the Research Agent"""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        ..., min_length=10, max_length=500, description="The clarifying question"
    )
    why: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Why this clarification matters",
    )
    options: Optional[List[str]] = Field(
        None, max_length=6, description="Suggested answer options"
    )


class ClarificationResponse(BaseModel):
    """Research Agent clarification output — questions to ask the user"""

    model_config = ConfigDict(extra="forbid")

    questions: List[ClarificationQuestion] = Field(
        ..., min_length=1, max_length=5, description="Clarifying questions"
    )
    is_complete: bool = Field(
        default=False, description="Whether the spec can be generated without answers"
    )


class ClarificationAnswer(BaseModel):
    """User's answers to clarification questions"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    answers: List[Dict[str, str]] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="List of {question: answer} pairs",
    )


# --- Refactor schemas ---


class RefactorRequest(BaseModel):
    """Request to refactor a code segment"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    selected_code: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="The highlighted code segment to refactor",
    )
    instruction: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="What to do with the code (e.g. 'Make this more accessible')",
    )


class RefactorResult(BaseModel):
    """Refactor Agent output"""

    model_config = ConfigDict(extra="forbid")

    original_code: str = Field(
        ..., min_length=1, description="The original selected code"
    )
    refactored_code: str = Field(
        ..., min_length=1, description="The refactored code segment"
    )
    explanation: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="What was changed and why",
    )
    full_file_content: str = Field(
        ...,
        min_length=1,
        description="Complete file content with refactored segment applied",
    )


# --- Profile schemas ---


class ProfileRead(BaseModel):
    """Profile data returned from the API"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="User UUID (matches auth.users id)")
    username: Optional[str] = Field(None, max_length=50)
    full_name: Optional[str] = Field(None, max_length=200)
    avatar_url: Optional[str] = Field(None, max_length=500)
    skill_level: Optional[str] = Field(
        None, pattern="^(beginner|intermediate|advanced)$"
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProfileCreate(BaseModel):
    """Create profile request (used if auto-creation via trigger is not available)"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    username: Optional[str] = Field(None, min_length=2, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    avatar_url: Optional[str] = Field(None, max_length=500)
    skill_level: Optional[str] = Field(
        None, pattern="^(beginner|intermediate|advanced)$"
    )


class ProfileUpdate(BaseModel):
    """Update profile request"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    username: Optional[str] = Field(None, min_length=2, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    avatar_url: Optional[str] = Field(None, max_length=500)
    skill_level: Optional[str] = Field(
        None, pattern="^(beginner|intermediate|advanced)$"
    )
