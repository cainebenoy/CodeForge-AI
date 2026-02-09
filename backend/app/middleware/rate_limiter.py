"""
Rate limiting middleware
Implements token bucket algorithm with pluggable backend.

Backends:
- InMemoryRateLimiter  (development, single-process)
- RedisRateLimiter     (production, multi-instance safe)

The factory ``get_rate_limiter()`` picks the right backend automatically
based on ``settings.REDIS_URL`` availability.
"""

import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from fastapi import HTTPException, Request

from app.core.config import settings
from app.core.logging import logger

# ---------------------------------------------------------------------------
# Rate limit key generation
# ---------------------------------------------------------------------------


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key from request.
    Uses authenticated user ID when available, otherwise falls back to IP.
    """
    client_ip = request.client.host if request.client else "unknown"

    # Try to get user_id from headers
    user_id = request.headers.get("X-User-ID", "")

    if user_id:
        return f"user:{user_id}"
    return f"ip:{client_ip}"


# ---------------------------------------------------------------------------
# Abstract backend
# ---------------------------------------------------------------------------


class BaseRateLimiter(ABC):
    """Abstract rate limiter interface."""

    @abstractmethod
    async def is_allowed(self, key: str) -> Tuple[bool, float]:
        """
        Check whether ``key`` is allowed through.

        Returns:
            (allowed, remaining_tokens)
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Clear all stored state (useful for testing)."""
        ...


# ---------------------------------------------------------------------------
# In-memory backend (development / single-process)
# ---------------------------------------------------------------------------


class InMemoryRateLimiter(BaseRateLimiter):
    """Token-bucket rate limiter backed by a plain dict."""

    def __init__(self, rate_per_minute: int | None = None):
        self._rate = rate_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self._store: dict = {}

    async def is_allowed(self, key: str) -> Tuple[bool, float]:
        now = time.time()

        if key not in self._store:
            self._store[key] = {"tokens": float(self._rate), "last_update": now}
            return True, float(self._rate)

        record = self._store[key]
        elapsed = now - record["last_update"]

        # Refill tokens
        refill_rate = self._rate / 60.0
        tokens = min(record["tokens"] + elapsed * refill_rate, float(self._rate))

        if tokens >= 1:
            self._store[key] = {"tokens": tokens - 1, "last_update": now}
            return True, tokens - 1
        else:
            self._store[key]["last_update"] = now
            return False, 0.0

    def reset(self) -> None:
        self._store.clear()


# ---------------------------------------------------------------------------
# Redis backend (production / multi-instance)
# ---------------------------------------------------------------------------


class RedisRateLimiter(BaseRateLimiter):
    """
    Sliding-window counter rate limiter backed by Redis.

    Uses a single key per (identity, minute-window) with INCR + EXPIRE.
    No Lua scripts needed — simple, atomic, and race-condition safe.
    """

    def __init__(self, redis_url: str, rate_per_minute: int | None = None):
        import redis as redis_lib

        self._rate = rate_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self._redis = redis_lib.Redis.from_url(redis_url, decode_responses=True)
        # Verify connectivity eagerly
        self._redis.ping()
        logger.info("[Redis] Rate limiter connected")

    async def is_allowed(self, key: str) -> Tuple[bool, float]:
        """
        Sliding-window counter:
        - Key = ``rl:{key}:{window}`` where window = current minute
        - INCR the key; if count <= rate, allow; else deny
        - Key auto-expires after 60 s so old windows self-clean
        """
        window = int(time.time()) // 60
        redis_key = f"rl:{key}:{window}"

        # INCR is atomic — safe under concurrent requests
        count = self._redis.incr(redis_key)
        if count == 1:
            # First request in this window — set TTL
            self._redis.expire(redis_key, 60)

        remaining = max(0.0, float(self._rate - count))
        allowed = count <= self._rate

        if not allowed:
            logger.warning(f"Rate limit exceeded for {key} (count={count})")

        return allowed, remaining

    def reset(self) -> None:
        """Flush all rate-limit keys (testing only)."""
        cursor = 0
        while True:
            cursor, keys = self._redis.scan(cursor, match="rl:*", count=200)
            if keys:
                self._redis.delete(*keys)
            if cursor == 0:
                break


# ---------------------------------------------------------------------------
# Factory + singleton
# ---------------------------------------------------------------------------

_limiter: Optional[BaseRateLimiter] = None


def get_rate_limiter() -> BaseRateLimiter:
    """Get or create the global rate limiter instance."""
    global _limiter
    if _limiter is None:
        _limiter = _create_rate_limiter()
    return _limiter


def _create_rate_limiter() -> BaseRateLimiter:
    """Pick Redis if available, otherwise fall back to in-memory."""
    if settings.REDIS_URL:
        try:
            limiter = RedisRateLimiter(settings.REDIS_URL)
            return limiter
        except Exception as e:
            logger.warning(
                f"Redis rate limiter unavailable ({e}), falling back to in-memory"
            )

    logger.info("Using in-memory rate limiter")
    return InMemoryRateLimiter()


# ---------------------------------------------------------------------------
# Legacy compatibility — module-level functions used by middleware
# ---------------------------------------------------------------------------


async def check_rate_limit(request: Request) -> bool:
    """
    Check if request is within rate limit.
    Returns: True if allowed, False if rate limited.
    """
    key = get_rate_limit_key(request)
    allowed, remaining = await get_rate_limiter().is_allowed(key)

    if allowed:
        logger.debug(f"Rate limit OK for {key}: {remaining:.0f} remaining")
    else:
        logger.warning(f"Rate limit exceeded for {key}")

    return allowed


async def rate_limit_middleware(request: Request):
    """
    Middleware to enforce rate limiting.
    Raises: HTTPException with 429 status if rate limited.
    """
    # Skip rate limiting for health checks
    if request.url.path == "/health":
        return

    allowed = await check_rate_limit(request)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 60 requests per minute.",
            headers={"Retry-After": "60"},
        )
