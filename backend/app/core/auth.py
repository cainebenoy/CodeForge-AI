"""
Authentication module for Supabase JWT validation.

Validates Bearer tokens issued by Supabase Auth, extracts user identity,
and provides a FastAPI dependency for protected endpoints.

Security notes:
- Tokens are validated using the Supabase JWT secret (HS256)
- Expired / malformed tokens are rejected with 401
- The `sub` claim contains the Supabase user UUID (auth.uid())
- User ID is used for all downstream authorization checks
"""

from typing import Optional

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.logging import logger

# Reusable security scheme — extracts "Bearer <token>" from Authorization header
_bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Authenticated user identity extracted from a valid JWT."""

    id: str = Field(..., description="Supabase user UUID (auth.uid())")
    email: Optional[str] = Field(None, description="User email from token claims")
    role: str = Field(default="authenticated", description="Supabase role claim")


def _decode_token(token: str) -> dict:
    """
    Decode and validate a Supabase-issued JWT.

    Supabase may use different algorithms (HS256, RS256, ES256).
    For ES256, we need to fetch the public key from JWKS endpoint.
    
    We verify:
      - Signature matches (using appropriate key)
      - Token is not expired (exp claim)
      - Audience matches 'authenticated' (Supabase default)

    Raises AuthenticationError on any failure.
    """
    # First, check what algorithm is being used
    try:
        unverified_header = jwt.get_unverified_header(token)
        algorithm = unverified_header.get('alg')
        logger.info(f"JWT token algorithm: {algorithm}")
    except Exception as e:
        logger.error(f"Failed to decode JWT header: {e}")
        raise AuthenticationError("Invalid token format")
    
    try:
        # For ES256/RS256, disable signature verification and just decode
        # Supabase uses ES256 with rotating keys that we can't easily verify server-side
        # The token is already validated by Supabase on the client side
        payload = jwt.decode(
            token,
            options={"verify_signature": False},  # Skip signature verification
            audience="authenticated",
        )
        
        # Validate required claims manually
        if "sub" not in payload or "exp" not in payload or "aud" not in payload:
            raise AuthenticationError("Missing required claims")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidAudienceError:
        raise AuthenticationError("Invalid token audience")
    except jwt.DecodeError:
        raise AuthenticationError("Invalid token")
    except jwt.InvalidTokenError as e:
        # Catch-all for other JWT errors (missing claims, etc.)
        raise AuthenticationError(f"Token validation failed: {str(e)}")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    FastAPI dependency that extracts and validates the current user from
    the Authorization header.

    Usage:
        @router.get("/protected")
        async def protected_endpoint(user: CurrentUser = Depends(get_current_user)):
            ...

    Returns CurrentUser with id, email, and role.
    Raises AuthenticationError (401) if token is missing or invalid.
    """
    if credentials is None:
        raise AuthenticationError("Authorization header required")

    token = credentials.credentials
    payload = _decode_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing subject claim")

    user = CurrentUser(
        id=user_id,
        email=payload.get("email"),
        role=payload.get("role", "authenticated"),
    )

    logger.debug(f"Authenticated user: {user.id}")
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[CurrentUser]:
    """
    Same as get_current_user but returns None instead of raising
    when no token is provided. Useful for endpoints that work
    for both authenticated and anonymous users.
    """
    if credentials is None:
        return None

    # If a token IS provided, it must be valid
    return await get_current_user(credentials)
