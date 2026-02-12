"""
Waitlist API endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.logging import logger
from app.services.supabase import supabase_client

router = APIRouter()


class WaitlistRequest(BaseModel):
    email: EmailStr


@router.post("/", status_code=201)
async def join_waitlist(request: WaitlistRequest):
    """
    Join the waitlist.
    """
    try:
        # Check if email already exists
        # Note: We could use on_conflict='ignore' in the insert, but Supabase-py
        # explicit check is safer for custom logic if needed.
        # Actually, let's just try insert and catch unique violation or let it fail gracefully
        # if the policy allows.

        # Since we have RLS 'Allow public insert', we can just insert.
        # However, public cannot READ, so we can't check if it exists first as anon.
        # But here we are the service role (backend), so we CAN check.
        
        # Simple upsert or ignore
        data = {"email": request.email}
        
        # We use the upsert method to handle duplicates gracefully (idempotent)
        response = supabase_client.table("waitlist").upsert(data, on_conflict="email").execute()
        
        logger.info(f"Waitlist signup: {request.email}")
        return {"message": "Joined waitlist successfully"}

    except Exception as e:
        logger.error(f"Waitlist error: {str(e)}")
        # Don't leak internal errors
        raise HTTPException(status_code=500, detail="Failed to join waitlist")
