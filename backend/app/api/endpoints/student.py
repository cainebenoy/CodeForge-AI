"""
Student Mode API endpoints
Handles learning roadmaps, daily sessions, and progress tracking
"""

import json
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends

from app.core.auth import CurrentUser, get_current_user
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.logging import logger
from app.schemas.protocol import (
    RoadmapCreate,
    RoadmapProgressUpdate,
    SessionCreate,
    StudentProgress,
)
from app.services.database import DatabaseOperations
from app.services.validation import InputValidator

router = APIRouter(tags=["student"])


async def _verify_project_ownership(project_id: str, user: CurrentUser) -> None:
    """
    Verify the user owns the project and it's in student mode.
    Raises appropriate errors if not.

    Security: Enforces object-level authorization.
    """
    InputValidator.validate_uuid(project_id)
    project = await DatabaseOperations.get_project(project_id, user_id=user.id)
    if project.get("mode") != "student":
        raise ValidationError(
            "mode", "This endpoint is only available for student-mode projects"
        )


# ──────────────────────────────────────────────────────────────
# Roadmap endpoints
# ──────────────────────────────────────────────────────────────


@router.post("/{project_id}/roadmap")
async def create_roadmap(
    project_id: str,
    body: RoadmapCreate,
    user: CurrentUser = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
):
    """
    Generate a learning roadmap for a student-mode project.

    Triggers the Roadmap Agent to create a personalized curriculum
    based on the project's requirements spec and the student's skill level.

    Requires:
    - Project must be in 'student' mode
    - Project should have a requirements_spec (run research agent first)

    Body:
    - skill_level: 'beginner', 'intermediate', or 'advanced'
    - focus_areas: Optional list of topics to focus on

    Security:
    - Auth required
    - Ownership check
    - Mode validation (student only)
    """
    await _verify_project_ownership(project_id, user)

    # Get project to access requirements_spec
    project = await DatabaseOperations.get_project(project_id, user_id=user.id)
    requirements = project.get("requirements_spec")

    if not requirements:
        raise ValidationError(
            "requirements_spec",
            "Project has no requirements spec. Run the research agent first.",
        )

    # Convert requirements to string for the agent
    if isinstance(requirements, dict):
        requirements_str = json.dumps(requirements, indent=2)
    else:
        requirements_str = str(requirements)

    focus_str = ", ".join(body.focus_areas) if body.focus_areas else ""

    # Generate roadmap via agent
    from app.agents.roadmap_agent import run_roadmap_agent

    roadmap_result = await run_roadmap_agent(
        requirements_spec=requirements_str,
        skill_level=body.skill_level,
        focus_areas=focus_str,
    )

    # Store in database
    roadmap_dict = roadmap_result.model_dump()
    roadmap = await DatabaseOperations.create_roadmap(
        project_id=project_id,
        modules=roadmap_dict["modules"],
        skill_level=body.skill_level,
    )

    logger.info(f"Created roadmap for project {project_id}")
    return {
        "roadmap": roadmap,
        "total_modules": len(roadmap_dict["modules"]),
        "total_estimated_hours": roadmap_dict["total_estimated_hours"],
    }


@router.get("/{project_id}/roadmap")
async def get_roadmap(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get the current learning roadmap for a project.

    Returns the roadmap with modules and current progress step.
    """
    await _verify_project_ownership(project_id, user)

    roadmap = await DatabaseOperations.get_roadmap(project_id)
    if not roadmap:
        raise ResourceNotFoundError("Roadmap", project_id)

    return roadmap


@router.put("/{project_id}/roadmap/progress")
async def update_roadmap_progress(
    project_id: str,
    body: RoadmapProgressUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Update the student's progress in the roadmap.

    Body:
    - step_index: The new current step index (0-based)

    Validates that step_index is within the range of modules.
    """
    await _verify_project_ownership(project_id, user)

    # Get roadmap to validate step_index
    roadmap = await DatabaseOperations.get_roadmap(project_id)
    if not roadmap:
        raise ResourceNotFoundError("Roadmap", project_id)

    modules = roadmap.get("modules", [])
    if body.step_index >= len(modules):
        raise ValidationError(
            "step_index",
            f"Step index {body.step_index} is out of range (max: {len(modules) - 1})",
        )

    updated = await DatabaseOperations.update_roadmap_progress(
        roadmap_id=roadmap["id"],
        step_index=body.step_index,
    )

    logger.info(
        f"Updated roadmap progress for project {project_id}: step={body.step_index}"
    )
    return updated


# ──────────────────────────────────────────────────────────────
# Session endpoints
# ──────────────────────────────────────────────────────────────


@router.post("/{project_id}/sessions")
async def create_session(
    project_id: str,
    body: SessionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Record a daily learning session.

    Body:
    - transcript: List of conversation messages
    - concepts_covered: List of concept strings learned
    - duration_minutes: How long the session lasted

    Security:
    - Auth required
    - Ownership check
    - Student mode only
    """
    await _verify_project_ownership(project_id, user)

    session = await DatabaseOperations.create_session(
        project_id=project_id,
        transcript=body.transcript,
        concepts_covered=body.concepts_covered,
        duration_minutes=body.duration_minutes,
    )

    logger.info(f"Created session for project {project_id}")
    return session


@router.get("/{project_id}/sessions")
async def list_sessions(
    project_id: str,
    limit: int = 50,
    user: CurrentUser = Depends(get_current_user),
):
    """
    List daily sessions for a project.

    Query params:
    - limit: Max sessions to return (default 50, max 100)
    """
    await _verify_project_ownership(project_id, user)

    if limit > 100:
        raise ValidationError("limit", "Maximum limit is 100")

    sessions = await DatabaseOperations.list_sessions(project_id, limit=limit)

    return {
        "project_id": project_id,
        "count": len(sessions),
        "sessions": sessions,
    }


# ──────────────────────────────────────────────────────────────
# Progress endpoint
# ──────────────────────────────────────────────────────────────


@router.get("/{project_id}/progress", response_model=StudentProgress)
async def get_progress(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get a computed progress summary for the student.

    Combines roadmap progress and session history into a single summary.
    """
    await _verify_project_ownership(project_id, user)

    # Get roadmap
    roadmap = await DatabaseOperations.get_roadmap(project_id)
    if not roadmap:
        raise ResourceNotFoundError("Roadmap", project_id)

    modules = roadmap.get("modules", [])
    current_index = roadmap.get("current_step_index", 0)
    total_modules = len(modules)

    # Get sessions for total count and time
    sessions = await DatabaseOperations.list_sessions(project_id, limit=1000)
    total_sessions = len(sessions)
    total_time = sum(s.get("duration_minutes", 0) for s in sessions)

    # Compute progress
    current_module = None
    if modules and current_index < total_modules:
        current_module = modules[current_index].get("title", "Unknown")

    percent = (current_index / total_modules * 100.0) if total_modules > 0 else 0.0

    return StudentProgress(
        roadmap_id=roadmap["id"],
        project_id=project_id,
        completed_modules=current_index,
        total_modules=total_modules,
        current_module=current_module,
        percent_complete=round(percent, 1),
        total_sessions=total_sessions,
        total_time_minutes=total_time,
    )
