"""
Profile API endpoints
Handles user profile CRUD operations

Profiles are auto-created by the Supabase Auth trigger on signup.
These endpoints allow reading and updating profile data.
"""

from fastapi import APIRouter, Depends

from app.core.auth import CurrentUser, get_current_user
from app.core.exceptions import ResourceNotFoundError
from app.core.logging import logger
from app.schemas.protocol import ProfileCreate, ProfileRead, ProfileUpdate
from app.services.database import DatabaseOperations

router = APIRouter(tags=["profiles"])


@router.get("/me", response_model=ProfileRead)
async def get_my_profile(
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Get the authenticated user's profile.

    Returns the current user's profile data.
    If no profile exists yet (edge case), creates one automatically.

    Security:
    - Auth required
    - Users can only access their own profile
    """
    profile = await DatabaseOperations.get_profile(user.id)

    if not profile:
        # Auto-create profile if it doesn't exist yet
        # (Supabase Auth trigger normally handles this, but handle edge cases)
        logger.info(f"Auto-creating profile for user {user.id}")
        profile = await DatabaseOperations.create_profile(user_id=user.id)

    return profile


@router.post("/", response_model=ProfileRead)
async def create_profile(
    body: ProfileCreate,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Create or update the authenticated user's profile.

    Uses upsert — safe to call even if profile already exists.

    Body:
    - username: Optional unique username (2-50 chars)
    - full_name: Optional display name
    - avatar_url: Optional avatar URL
    - skill_level: Optional skill level ('beginner', 'intermediate', 'advanced')

    Security:
    - Auth required
    - Users can only create/update their own profile
    """
    logger.info(f"Creating/updating profile for user {user.id}")

    profile = await DatabaseOperations.create_profile(
        user_id=user.id,
        username=body.username,
        full_name=body.full_name,
        avatar_url=body.avatar_url,
        skill_level=body.skill_level,
    )

    return profile


@router.put("/me", response_model=ProfileRead)
async def update_my_profile(
    body: ProfileUpdate,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Update the authenticated user's profile.

    Only provided fields are updated; others are left unchanged.

    Body:
    - username: Optional unique username
    - full_name: Optional display name
    - avatar_url: Optional avatar URL
    - skill_level: Optional skill level

    Security:
    - Auth required
    - Users can only update their own profile
    - Field whitelist enforced in DatabaseOperations
    """
    update_data = body.model_dump(exclude_none=True)

    if not update_data:
        from app.core.exceptions import ValidationError

        raise ValidationError("data", "At least one field must be provided for update")

    logger.info(f"Updating profile for user {user.id}")
    profile = await DatabaseOperations.update_profile(user.id, update_data)

    return profile
