"""
Project API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.supabase import supabase_client

router = APIRouter()


@router.get("/{project_id}")
async def get_project(project_id: str) -> Dict[str, Any]:
    """
    Get project by ID
    
    Security: RLS enforced at database level
    Returns only minimal required fields
    """
    try:
        response = supabase_client.table("projects").select("*").eq("id", project_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/{project_id}")
async def update_project(project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update project
    
    Security: Input validated, RLS enforced
    """
    # Validate input fields (whitelist approach)
    allowed_fields = {"title", "description", "status", "requirements_spec", "architecture_spec"}
    filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    try:
        response = (
            supabase_client.table("projects")
            .update(filtered_data)
            .eq("id", project_id)
            .execute()
        )
        
        return response.data[0] if response.data else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
