"""
Database operations layer
Handles all Supabase operations with proper error handling
"""
from typing import Any, Dict, List, Optional
from app.services.supabase import supabase_client
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    ExternalServiceError,
)
from app.core.logging import logger


class DatabaseOperations:
    """Abstraction layer for database operations"""

    @staticmethod
    async def get_project(project_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a project by ID
        Raises: ResourceNotFoundError if not found
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

            logger.info(f"Retrieved project: {project_id}")
            return response.data
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
                .insert({
                    "user_id": user_id,
                    "title": title,
                    "description": description,
                    "mode": mode,
                    "tech_stack": tech_stack,
                    "status": "planning",
                })
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
        project_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a project
        Only allows specific fields (whitelist approach)
        """
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
                .upsert({
                    "project_id": project_id,
                    "path": path,
                    "content": content,
                    "language": language,
                })
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

            logger.info(f"Retrieved {len(response.data)} files for project: {project_id}")
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise ExternalServiceError("Supabase", str(e))
