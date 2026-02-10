"""
Project API endpoints
Handles project CRUD operations with proper security and validation
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.auth import CurrentUser, get_current_user
from app.core.exceptions import ExternalServiceError
from app.core.exceptions import ValidationError as CFValidationError
from app.core.logging import logger
from app.schemas.protocol import (
    CodeFileCreate,
    CodeFileUpdate,
    GitHubExportRequest,
    PaginatedResponse,
    ProjectCreate,
    ProjectUpdate,
    RefactorRequest,
)
from app.services.database import DatabaseOperations
from app.services.validation import InputValidator

router = APIRouter(tags=["projects"])


async def validate_project_id(project_id: str) -> str:
    """Validate project ID is a valid UUID"""
    InputValidator.validate_uuid(project_id)
    return project_id


@router.post("/", response_model=dict)
async def create_project(
    request: ProjectCreate,
    user: CurrentUser = Depends(get_current_user),
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
        logger.info(f"Creating project: {request.title} for user {user.id}")

        project = await DatabaseOperations.create_project(
            user_id=user.id,
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
    project_id: str = Depends(validate_project_id),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Get project by ID

    Returns: Project details

    Security:
    - UUID validation enforced
    - Ownership check: user can only access their own projects
    - Only necessary fields returned
    """
    logger.info(f"Fetching project: {project_id}")
    return await DatabaseOperations.get_project(project_id, user_id=user.id)


@router.put("/{project_id}", response_model=dict)
async def update_project(
    project_id: str = Depends(validate_project_id),
    data: ProjectUpdate = None,
    user: CurrentUser = Depends(get_current_user),
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

    return await DatabaseOperations.update_project(
        project_id, update_data, user_id=user.id
    )


@router.get("/{project_id}/files")
async def list_project_files(
    project_id: str = Depends(validate_project_id),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    List all files in a project

    Returns: List of file records with paths, languages, and last modified

    Security:
    - Ownership check enforces user access
    - Only file metadata returned, not full content
    """
    logger.info(f"Listing files for project: {project_id}")
    # Verify ownership first
    await DatabaseOperations.get_project(project_id, user_id=user.id)
    files = await DatabaseOperations.list_project_files(project_id)

    return {
        "project_id": project_id,
        "count": len(files),
        "files": files,
    }


@router.post("/{project_id}/files", response_model=dict)
async def create_file(
    file_data: CodeFileCreate,
    project_id: str = Depends(validate_project_id),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Create or update a file in project

    Request body (JSON):
    - path: File path (must start with 'src/')
    - content: File content (max 100KB)
    - language: Programming language

    Security:
    - Path traversal prevention (validated by CodeFileCreate schema)
    - File size limited to 100KB
    - RLS ensures user can only modify own projects
    """
    # Additional path validation
    InputValidator.validate_file_path(file_data.path)

    # Verify ownership
    await DatabaseOperations.get_project(project_id, user_id=user.id)

    logger.info(f"Creating file for project {project_id}: {file_data.path}")

    return await DatabaseOperations.create_file(
        project_id=project_id,
        path=file_data.path,
        content=file_data.content,
        language=file_data.language,
    )


# ──────────────────────────────────────────────────────────────
# List user projects (paginated)
# ──────────────────────────────────────────────────────────────


@router.get("/", response_model=PaginatedResponse)
async def list_projects(
    user: CurrentUser = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=50, description="Items per page (max 50)"),
    mode: Optional[str] = Query(None, pattern="^(builder|student)$"),
    status: Optional[str] = Query(
        None, pattern="^(planning|in-progress|completed|archived)$"
    ),
) -> dict:
    """
    List all projects belonging to the authenticated user.

    Query parameters:
    - page: Page number (default 1)
    - page_size: Items per page (max 50, default 20)
    - mode: Filter by 'builder' or 'student'
    - status: Filter by status (archived projects hidden by default)

    Security:
    - Only returns projects owned by the authenticated user
    """
    logger.info(f"Listing projects for user {user.id} (page={page})")
    return await DatabaseOperations.list_user_projects(
        user_id=user.id,
        page=page,
        page_size=page_size,
        mode=mode,
        status=status,
    )


# ──────────────────────────────────────────────────────────────
# Delete (archive) project
# ──────────────────────────────────────────────────────────────


@router.delete("/{project_id}", response_model=dict)
async def delete_project(
    project_id: str = Depends(validate_project_id),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Soft-delete a project (sets status to 'archived').

    The project and its files are preserved for potential recovery.
    Archived projects are excluded from listings by default.

    Security:
    - Ownership check: only the project owner can delete
    - UUID validation enforced
    """
    logger.info(f"Archiving project: {project_id} (user {user.id})")
    project = await DatabaseOperations.delete_project(project_id, user_id=user.id)
    return {"message": "Project archived", "project_id": project["id"]}


# ──────────────────────────────────────────────────────────────
# Single file CRUD
# ──────────────────────────────────────────────────────────────


@router.get("/{project_id}/files/{file_path:path}", response_model=dict)
async def get_file(
    file_path: str,
    project_id: str = Depends(validate_project_id),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Get a single file's content by path.

    Security:
    - Ownership check on the parent project
    - Path traversal validation
    """
    InputValidator.validate_file_path(file_path)
    await DatabaseOperations.get_project(project_id, user_id=user.id)

    logger.info(f"Fetching file {file_path} from project {project_id}")
    return await DatabaseOperations.get_file(project_id, file_path)


@router.put("/{project_id}/files/{file_path:path}", response_model=dict)
async def update_file(
    file_path: str,
    file_data: CodeFileUpdate,
    project_id: str = Depends(validate_project_id),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Update an existing file's content.

    Request body:
    - content: New file content (max 100KB)
    - language: Optional new language tag

    Security:
    - Ownership check on the parent project
    - Path traversal validation
    - Content size limited to 100KB
    """
    InputValidator.validate_file_path(file_path)
    await DatabaseOperations.get_project(project_id, user_id=user.id)

    logger.info(f"Updating file {file_path} in project {project_id}")
    return await DatabaseOperations.update_file(
        project_id=project_id,
        file_path=file_path,
        content=file_data.content,
        language=file_data.language,
    )


@router.delete("/{project_id}/files/{file_path:path}")
async def delete_file(
    file_path: str,
    project_id: str = Depends(validate_project_id),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Delete a file from the project.

    Security:
    - Ownership check on the parent project
    - Path traversal validation
    """
    InputValidator.validate_file_path(file_path)
    await DatabaseOperations.get_project(project_id, user_id=user.id)

    logger.info(f"Deleting file {file_path} from project {project_id}")
    await DatabaseOperations.delete_file(project_id, file_path)
    return {"message": "File deleted", "path": file_path}


# ──────────────────────────────────────────────────────────────
# Refactor with AI
# ──────────────────────────────────────────────────────────────


@router.post("/{project_id}/files/{file_path:path}/refactor", response_model=dict)
async def refactor_file(
    file_path: str,
    body: RefactorRequest,
    project_id: str = Depends(validate_project_id),
    user: CurrentUser = Depends(get_current_user),
    apply: bool = False,
) -> dict:
    """
    Refactor a code segment in a file using AI.

    Select code → "Refactor with AI" → returns refactored code with explanation.

    Body:
    - selected_code: The highlighted code segment (max 50KB)
    - instruction: What to do (e.g. "Make this more accessible")

    Query params:
    - apply: If true, auto-apply the refactored code to the file

    Returns: RefactorResult with original, refactored code, explanation, and full file

    Security:
    - Auth required
    - Ownership check on the parent project
    - Path traversal validation
    - Content size limited by Pydantic schema
    """
    InputValidator.validate_file_path(file_path)
    await DatabaseOperations.get_project(project_id, user_id=user.id)

    # Fetch the full file content for context
    file_record = await DatabaseOperations.get_file(project_id, file_path)
    full_content = file_record.get("content", "")

    logger.info(
        f"Refactoring {file_path} in project {project_id}: '{body.instruction[:60]}...'"
    )

    from app.agents.code_agent import run_refactor_agent

    result = await run_refactor_agent(
        file_path=file_path,
        selected_code=body.selected_code,
        instruction=body.instruction,
        full_file_content=full_content,
    )

    # Optionally auto-apply the refactored code
    if apply:
        await DatabaseOperations.update_file(
            project_id=project_id,
            file_path=file_path,
            content=result.full_file_content,
        )
        logger.info(f"Auto-applied refactor to {file_path}")

    return result.model_dump()


# ──────────────────────────────────────────────────────────────
# GitHub Export
# ──────────────────────────────────────────────────────────────


@router.post("/{project_id}/export/github", response_model=dict)
async def export_to_github(
    body: GitHubExportRequest,
    project_id: str = Depends(validate_project_id),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Export project files to a new GitHub repository.

    Creates a repo under the user's GitHub account and pushes
    all project files as an initial commit.

    Body:
    - repo_name: Desired repository name
    - description: Optional repo description
    - private: Whether the repo is private (default true)
    - github_token: User's GitHub PAT (never stored)

    Security:
    - GitHub token passed per-request, never persisted
    - Ownership check on project
    - All file paths sanitised before upload
    """
    # Verify ownership
    await DatabaseOperations.get_project(project_id, user_id=user.id)

    logger.info(f"Exporting project {project_id} to GitHub repo '{body.repo_name}'")

    try:
        from app.services.github import export_project

        result = await export_project(
            token=body.github_token,
            project_id=project_id,
            repo_name=body.repo_name,
            description=body.description,
            private=body.private,
        )
        return result
    except ValueError as e:
        raise CFValidationError("export", str(e))
    except Exception as e:
        logger.error(f"GitHub export failed: {str(e)}")
        raise ExternalServiceError("GitHub", str(e))
