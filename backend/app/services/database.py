"""
Database operations layer
Handles all Supabase operations with proper error handling
"""

from typing import Any, Dict, List, Optional

from app.core.exceptions import (
    ExternalServiceError,
    PermissionError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.logging import logger
from app.services.supabase import supabase_client


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
            response = (
                supabase_client.table("projects")
                .select("*")
                .eq("id", project_id)
                .single()
                .execute()
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
            response = (
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
            response = (
                supabase_client.table("projects")
                .update(filtered_data)
                .eq("id", project_id)
                .execute()
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
            response = (
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
            response = (
                supabase_client.table("project_files")
                .select("*")
                .eq("project_id", project_id)
                .order("path", desc=False)
                .execute()
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
            response = (
                supabase_client.table("projects")
                .update({"status": "archived"})
                .eq("id", project_id)
                .execute()
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

            response = (
                query.order("created_at", desc=True)
                .range(offset, offset + page_size - 1)
                .execute()
            )

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
            response = (
                supabase_client.table("project_files")
                .select("*")
                .eq("project_id", project_id)
                .eq("path", file_path)
                .single()
                .execute()
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
        Raises ResourceNotFoundError if the file doesn't exist.
        """
        try:
            update_data: Dict[str, Any] = {"content": content}
            if language:
                update_data["language"] = language

            response = (
                supabase_client.table("project_files")
                .update(update_data)
                .eq("project_id", project_id)
                .eq("path", file_path)
                .execute()
            )

            if response.data:
                logger.info(f"Updated file: {file_path} (project {project_id})")
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

            supabase_client.table("project_files").delete().eq(
                "project_id", project_id
            ).eq("path", file_path).execute()

            logger.info(f"Deleted file: {file_path} (project {project_id})")
            return True
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))
