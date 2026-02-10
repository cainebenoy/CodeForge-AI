"""
Database operations layer
Handles all Supabase operations with proper error handling.

All synchronous supabase-py calls are wrapped with ``asyncio.to_thread``
so they never block the FastAPI event loop.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, TypeVar

from app.core.exceptions import (
    ExternalServiceError,
    PermissionError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.logging import logger
from app.services.supabase import supabase_client

T = TypeVar("T")


async def _db_execute(fn: Callable[[], T]) -> T:
    """
    Run a **synchronous** supabase-py call in a background thread so the
    event loop is never blocked.  Every database method below uses this.
    """
    return await asyncio.to_thread(fn)


class DatabaseOperations:
    """Abstraction layer for database operations"""

    @staticmethod
    async def get_project(
        project_id: str, user_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a project by ID.
        If user_id is provided, enforces ownership check (returns 403 on mismatch).
        Raises: ResourceNotFoundError if not found, PermissionError if not owner.
        """
        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("projects")
                    .select("*")
                    .eq("id", project_id)
                    .single()
                    .execute()
                )
            )

            if not response.data:
                raise ResourceNotFoundError("Project", project_id)

            # Authorization: verify the requesting user owns this project
            if user_id and response.data.get("user_id") != user_id:
                raise PermissionError("You do not have access to this project")

            logger.info(f"Retrieved project: {project_id}")
            return response.data
        except (ResourceNotFoundError, PermissionError):
            raise
        except Exception as e:
            logger.error(f"Database error fetching project: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def create_project(
        user_id: str,
        title: str,
        description: str,
        mode: str,
        tech_stack: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new project
        Validates input before creation
        """
        if not title or len(title) < 3:
            raise ValidationError("title", "Title must be at least 3 characters")

        if mode not in ["builder", "student"]:
            raise ValidationError("mode", "Mode must be 'builder' or 'student'")

        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("projects")
                    .insert(
                        {
                            "user_id": user_id,
                            "title": title,
                            "description": description,
                            "mode": mode,
                            "tech_stack": tech_stack,
                            "status": "planning",
                        }
                    )
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Created project: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise ExternalServiceError("Supabase", "Failed to create project")
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def update_project(
        project_id: str, data: Dict[str, Any], user_id: str = None
    ) -> Dict[str, Any]:
        """
        Update a project
        Only allows specific fields (whitelist approach).
        If user_id is provided, enforces ownership.
        """
        # Verify ownership if user_id supplied
        if user_id:
            await DatabaseOperations.get_project(project_id, user_id=user_id)

        # Whitelist allowed fields for security
        allowed_fields = {
            "title",
            "description",
            "status",
            "requirements_spec",
            "architecture_spec",
            "tech_stack",
        }
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not filtered_data:
            raise ValidationError("data", "No valid fields to update")

        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("projects")
                    .update(filtered_data)
                    .eq("id", project_id)
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Updated project: {project_id}")
                return response.data[0]
            else:
                raise ResourceNotFoundError("Project", project_id)
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def create_file(
        project_id: str, path: str, content: str, language: str = "typescript"
    ) -> Dict[str, Any]:
        """
        Create or update a file in the virtual file system
        Validates path format
        """
        if not path or not path.startswith("src/"):
            raise ValidationError("path", "Path must start with 'src/'")

        try:
            # Try to update first (upsert pattern)
            response = await _db_execute(
                lambda: (
                    supabase_client.table("project_files")
                    .upsert(
                        {
                            "project_id": project_id,
                            "path": path,
                            "content": content,
                            "language": language,
                        }
                    )
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Created/updated file: {path}")
                return response.data[0]
            else:
                raise ExternalServiceError("Supabase", "Failed to create file")
        except Exception as e:
            logger.error(f"Error creating file: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def list_project_files(project_id: str) -> List[Dict[str, Any]]:
        """
        List all files in a project
        Returns: List of file records
        """
        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("project_files")
                    .select("*")
                    .eq("project_id", project_id)
                    .order("path", desc=False)
                    .execute()
                )
            )

            logger.info(
                f"Retrieved {len(response.data)} files for project: {project_id}"
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    # ──────────────────────────────────────────────────────────
    # Additional Project operations
    # ──────────────────────────────────────────────────────────

    @staticmethod
    async def delete_project(project_id: str, user_id: str) -> Dict[str, Any]:
        """
        Soft-delete a project by setting status to 'archived'.
        Preserves data for potential recovery.
        Raises PermissionError if the requesting user is not the owner.
        """
        # Verify ownership
        await DatabaseOperations.get_project(project_id, user_id=user_id)

        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("projects")
                    .update({"status": "archived"})
                    .eq("id", project_id)
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Archived project: {project_id}")
                return response.data[0]
            else:
                raise ResourceNotFoundError("Project", project_id)
        except (ResourceNotFoundError, PermissionError):
            raise
        except Exception as e:
            logger.error(f"Error archiving project: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def list_user_projects(
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        mode: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List projects belonging to a user with pagination.
        Excludes archived projects by default unless status='archived' is requested.
        Returns dict with 'items', 'total', 'page', 'page_size', 'has_more'.
        """
        page_size = min(page_size, 50)  # Cap at 50
        offset = (page - 1) * page_size

        try:

            def _query():
                query = (
                    supabase_client.table("projects")
                    .select("*", count="exact")
                    .eq("user_id", user_id)
                )

                # Filter by mode if specified
                if mode:
                    query = query.eq("mode", mode)

                # Filter by status; default excludes archived
                if status:
                    query = query.eq("status", status)
                else:
                    query = query.neq("status", "archived")

                return (
                    query.order("created_at", desc=True)
                    .range(offset, offset + page_size - 1)
                    .execute()
                )

            response = await _db_execute(_query)

            total = response.count if response.count is not None else 0
            items = response.data or []

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": (offset + page_size) < total,
            }
        except Exception as e:
            logger.error(f"Error listing projects for user {user_id}: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    # ──────────────────────────────────────────────────────────
    # File operations (get, update, delete)
    # ──────────────────────────────────────────────────────────

    @staticmethod
    async def get_file(project_id: str, file_path: str) -> Dict[str, Any]:
        """
        Get a single file by project_id and path.
        Raises ResourceNotFoundError if not found.
        """
        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("project_files")
                    .select("*")
                    .eq("project_id", project_id)
                    .eq("path", file_path)
                    .single()
                    .execute()
                )
            )

            if not response.data:
                raise ResourceNotFoundError("File", file_path)

            logger.info(f"Retrieved file: {file_path} (project {project_id})")
            return response.data
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching file {file_path}: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def update_file(
        project_id: str, file_path: str, content: str, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing file's content (and optionally language).
        Increments the version counter on each update.
        Raises ResourceNotFoundError if the file doesn't exist.
        """
        try:
            # First get current version
            current = await DatabaseOperations.get_file(project_id, file_path)
            current_version = current.get("version", 1)

            update_data: Dict[str, Any] = {
                "content": content,
                "version": current_version + 1,
            }
            if language:
                update_data["language"] = language

            response = await _db_execute(
                lambda: (
                    supabase_client.table("project_files")
                    .update(update_data)
                    .eq("project_id", project_id)
                    .eq("path", file_path)
                    .execute()
                )
            )

            if response.data:
                logger.info(
                    f"Updated file: {file_path} (project {project_id}, "
                    f"v{current_version} → v{current_version + 1})"
                )
                return response.data[0]
            else:
                raise ResourceNotFoundError("File", file_path)
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating file {file_path}: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def delete_file(project_id: str, file_path: str) -> bool:
        """
        Delete a file from the project.
        Returns True on success.
        Raises ResourceNotFoundError if the file doesn't exist.
        """
        try:
            # Verify file exists first
            await DatabaseOperations.get_file(project_id, file_path)

            await _db_execute(
                lambda: (
                    supabase_client.table("project_files")
                    .delete()
                    .eq("project_id", project_id)
                    .eq("path", file_path)
                    .execute()
                )
            )

            logger.info(f"Deleted file: {file_path} (project {project_id})")
            return True
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    # ──────────────────────────────────────────────────────────
    # Learning Roadmap operations (Student Mode)
    # ──────────────────────────────────────────────────────────

    @staticmethod
    async def create_roadmap(
        project_id: str,
        modules: list,
        skill_level: str = "beginner",
    ) -> Dict[str, Any]:
        """
        Create a learning roadmap for a project.
        Replaces any existing roadmap for the project (one roadmap per project).
        """
        try:
            # Delete existing roadmap for this project first
            await _db_execute(
                lambda: (
                    supabase_client.table("learning_roadmaps")
                    .delete()
                    .eq("project_id", project_id)
                    .execute()
                )
            )

            response = await _db_execute(
                lambda: (
                    supabase_client.table("learning_roadmaps")
                    .insert(
                        {
                            "project_id": project_id,
                            "modules": modules,
                            "current_step_index": 0,
                        }
                    )
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Created roadmap for project: {project_id}")
                return response.data[0]
            else:
                raise ExternalServiceError("Supabase", "Failed to create roadmap")
        except Exception as e:
            logger.error(f"Error creating roadmap: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def get_roadmap(project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the learning roadmap for a project.
        Returns None if no roadmap exists.
        """
        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("learning_roadmaps")
                    .select("*")
                    .eq("project_id", project_id)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Retrieved roadmap for project: {project_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching roadmap: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def update_roadmap_progress(
        roadmap_id: str, step_index: int
    ) -> Dict[str, Any]:
        """
        Update the current step index of a roadmap.
        Raises ResourceNotFoundError if roadmap doesn't exist.
        """
        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("learning_roadmaps")
                    .update({"current_step_index": step_index})
                    .eq("id", roadmap_id)
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Updated roadmap {roadmap_id}: step_index={step_index}")
                return response.data[0]
            else:
                raise ResourceNotFoundError("Roadmap", roadmap_id)
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating roadmap progress: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def update_roadmap_modules(roadmap_id: str, modules: list) -> Dict[str, Any]:
        """
        Update the modules JSONB of a roadmap.
        Used by the Choice Framework to persist student selections.
        Raises ResourceNotFoundError if roadmap doesn't exist.
        """
        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("learning_roadmaps")
                    .update({"modules": modules})
                    .eq("id", roadmap_id)
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Updated roadmap modules for {roadmap_id}")
                return response.data[0]
            else:
                raise ResourceNotFoundError("Roadmap", roadmap_id)
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating roadmap modules: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    # ──────────────────────────────────────────────────────────
    # Daily Session operations (Student Mode)
    # ──────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────
    # Profile operations
    # ──────────────────────────────────────────────────────────

    @staticmethod
    async def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user's profile by ID.
        Returns None if no profile exists.
        """
        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("profiles")
                    .select("*")
                    .eq("id", user_id)
                    .single()
                    .execute()
                )
            )

            if not response.data:
                return None

            logger.info(f"Retrieved profile for user: {user_id}")
            return response.data
        except Exception as e:
            # single() raises on no rows - treat as not found
            if "No rows" in str(e) or "0 rows" in str(e) or "JSON" in str(e):
                return None
            logger.error(f"Error fetching profile: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def create_profile(
        user_id: str,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        skill_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a profile for a user.
        Uses upsert so it's idempotent (Supabase Auth trigger may have created it).
        """
        try:
            data: Dict[str, Any] = {"id": user_id}
            if username is not None:
                data["username"] = username
            if full_name is not None:
                data["full_name"] = full_name
            if avatar_url is not None:
                data["avatar_url"] = avatar_url
            if skill_level is not None:
                data["skill_level"] = skill_level

            response = await _db_execute(
                lambda: (
                    supabase_client.table("profiles")
                    .upsert(data)
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Created/updated profile for user: {user_id}")
                return response.data[0]
            else:
                raise ExternalServiceError("Supabase", "Failed to create profile")
        except Exception as e:
            logger.error(f"Error creating profile: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def update_profile(
        user_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a user's profile. Only allows known fields.
        Raises ResourceNotFoundError if profile doesn't exist.
        """
        allowed_fields = {"username", "full_name", "avatar_url", "skill_level"}
        filtered = {k: v for k, v in data.items() if k in allowed_fields}

        if not filtered:
            raise ValidationError("data", "No valid fields to update")

        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("profiles")
                    .update(filtered)
                    .eq("id", user_id)
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Updated profile for user: {user_id}")
                return response.data[0]
            else:
                raise ResourceNotFoundError("Profile", user_id)
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def create_session(
        project_id: str,
        transcript: list,
        concepts_covered: list,
        duration_minutes: int = 0,
    ) -> Dict[str, Any]:
        """
        Record a daily learning session.
        """
        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("daily_sessions")
                    .insert(
                        {
                            "project_id": project_id,
                            "transcript": transcript,
                            "concepts_covered": concepts_covered,
                            "duration_minutes": duration_minutes,
                        }
                    )
                    .execute()
                )
            )

            if response.data:
                logger.info(f"Created session for project: {project_id}")
                return response.data[0]
            else:
                raise ExternalServiceError("Supabase", "Failed to create session")
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))

    @staticmethod
    async def list_sessions(project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List daily sessions for a project, ordered by most recent first.
        """
        limit = min(limit, 100)  # Cap at 100
        try:
            response = await _db_execute(
                lambda: (
                    supabase_client.table("daily_sessions")
                    .select("*")
                    .eq("project_id", project_id)
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
                )
            )

            logger.info(
                f"Retrieved {len(response.data or [])} sessions for project: {project_id}"
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))
