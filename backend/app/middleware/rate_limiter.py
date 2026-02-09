"""
Rate limiting middleware
Implements token bucket algorithm with Redis backend
"""
import time
from typing import Optional
from fastapi import Request, HTTPException
from app.core.config import settings
from app.core.logging import logger

# In-memory rate limit store (replace with Redis in production)
# Format: {key: {tokens: float, last_update: float}}
_rate_limit_store: dict = {}


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key from request
    Uses IP address + user_id if authenticated
    """
    client_ip = request.client.host if request.client else "unknown"

    # Try to get user_id from headers
    user_id = request.headers.get("X-User-ID", "")

    if user_id:
        return f"user:{user_id}"
    return f"ip:{client_ip}"


async def check_rate_limit(request: Request) -> bool:
    """
    Check if request is within rate limit
    Returns: True if allowed, False if rate limited
    """
    key = get_rate_limit_key(request)
    current_time = time.time()
    rate_limit_per_minute = settings.RATE_LIMIT_PER_MINUTE

    if key not in _rate_limit_store:
        _rate_limit_store[key] = {"tokens": float(rate_limit_per_minute), "last_update": current_time}
        return True

    record = _rate_limit_store[key]
    time_elapsed = current_time - record["last_update"]

    # Refill tokens based on time elapsed
    refill_rate = rate_limit_per_minute / 60.0  # tokens per second
    tokens = record["tokens"] + (time_elapsed * refill_rate)
    tokens = min(tokens, float(rate_limit_per_minute))  # Cap at max

    if tokens >= 1:
        # Allow request
        _rate_limit_store[key] = {"tokens": tokens - 1, "last_update": current_time}
        logger.debug(f"Rate limit OK for {key}: {tokens - 1:.2f} tokens remaining")
        return True
    else:
        # Rate limited
        logger.warning(f"Rate limit exceeded for {key}")
        return False


async def rate_limit_middleware(request: Request):
    """
    Middleware to enforce rate limiting
    Raises: HTTPException with 429 status if rate limited
    """
    # Skip rate limiting for health checks and non-mutating requests
    if request.url.path == "/health":
        return

    allowed = await check_rate_limit(request)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 60 requests per minute.",
            headers={"Retry-After": "60"},
        )
