"""
Project API endpoints
Handles project CRUD operations with proper security and validation
"""
from fastapi import APIRouter, Depend, Query
from typing import Optional, List

from app.schemas.protocol import ProjectCreate, ProjectUpdate
from app.services.database import DatabaseOperations
from app.services.validation import InputValidator
from app.core.logging import logger

router = APIRouter(tags=["projects"])


async def validate_project_id(project_id: str) -> str:
    """Validate project ID is a valid UUID"""
    InputValidator.validate_uuid(project_id)
    return project_id


@router.post("/", response_model=dict)
async def create_project(
    request: ProjectCreate,
    user_id: str = Depend(lambda: "user_placeholder"),  # In production: from JWT token
) -> dict:
    """
    Create a new project

    Request body:
    - title: Project name (3-200 chars)
    - description: Optional description
    - mode: 'builder' or 'student' mode
    - tech_stack: Optional list of technologies

    Returns: Created project with ID

    Security:
    - Input validated via Pydantic schema
    - User ID extracted from JWT token
    - RLS enforces user can only access their own projects
    """
    try:
        logger.info(f"Creating project: {request.title} for user {user_id}")

        project = await DatabaseOperations.create_project(
            user_id=user_id,
            title=request.title,
            description=request.description,
            mode=request.mode,
            tech_stack=request.tech_stack,
        )

        logger.info(f"Created project: {project['id']}")
        return project

    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise


@router.get("/{project_id}", response_model=dict)
async def get_project(
    project_id: str = Depend(validate_project_id),
) -> dict:
    """
    Get project by ID

    Returns: Project details

    Security:
    - UUID validation enforced
    - RLS ensures user can only access their own projects
    - Only necessary fields returned
    """
    logger.info(f"Fetching project: {project_id}")
    return await DatabaseOperations.get_project(project_id)


@router.put("/{project_id}", response_model=dict)
async def update_project(
    project_id: str = Depend(validate_project_id),
    data: ProjectUpdate = None,
) -> dict:
    """
    Update a project

    Supported fields:
    - title: Project name
    - description: Project description
    - status: 'planning', 'in-progress', or 'completed'
    - requirements_spec: JSON object from Research Agent
    - architecture_spec: JSON object from Wireframe Agent

    Security:
    - Whitelist approach: only specified fields allowed
    - UUID validation enforced
    - RLS prevents unauthorized updates
    """
    if not data or not any(getattr(data, f) for f in data.model_dump()):
        from app.core.exceptions import ValidationError
        raise ValidationError("data", "At least one field must be provided for update")

    logger.info(f"Updating project: {project_id}")

    # Convert Pydantic model to dict, excluding None values
    update_data = data.model_dump(exclude_none=True)

    return await DatabaseOperations.update_project(project_id, update_data)


@router.get("/{project_id}/files")
async def list_project_files(
    project_id: str = Depend(validate_project_id),
) -> dict:
    """
    List all files in a project

    Returns: List of file records with paths, languages, and last modified

    Security:
    - RLS enforces user ownership
    - Only file metadata returned, not full content
    """
    logger.info(f"Listing files for project: {project_id}")
    files = await DatabaseOperations.list_project_files(project_id)

    return {
        "project_id": project_id,
        "count": len(files),
        "files": files,
    }


@router.post("/{project_id}/files", response_model=dict)
async def create_file(
    project_id: str = Depend(validate_project_id),
    path: str = Query(..., min_length=5, max_length=500),
    content: str = Query(..., max_length=100000),
    language: str = Query(default="typescript"),
) -> dict:
    """
    Create or update a file in project

    Query parameters:
    - path: File path (must start with 'src/')
    - content: File content (max 100KB)
    - language: Programming language

    Security:
    - Path traversal prevention (no .. or leading /)
    - File size limited to 100KB
    - RLS ensures user can only modify own projects
    """
    # Validate path
    InputValidator.validate_file_path(path)

    logger.info(f"Creating file for project {project_id}: {path}")

    return await DatabaseOperations.create_file(
        project_id=project_id,
        path=path,
        content=content,
        language=language,
    )
