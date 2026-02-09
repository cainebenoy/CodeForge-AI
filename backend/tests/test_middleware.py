"""
Tests for rate limiter and request tracking middleware
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(client_host: str = "127.0.0.1", user_id: str = "") -> MagicMock:
    """Build a minimal mock FastAPI Request."""
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = client_host
    request.headers = {"X-User-ID": user_id} if user_id else {}
    request.url = MagicMock()
    request.url.path = "/v1/agents/run-agent"
    request.method = "POST"
    request.state = MagicMock()
    return request


# ---------------------------------------------------------------------------
# Rate limiter tests
# ---------------------------------------------------------------------------


class TestGetRateLimitKey:
    """Tests for rate limit key generation."""

    def test_key_from_ip(self):
        from app.middleware.rate_limiter import get_rate_limit_key

        req = _make_request(client_host="10.0.0.1")
        key = get_rate_limit_key(req)
        assert key == "ip:10.0.0.1"

    def test_key_from_user_id(self):
        from app.middleware.rate_limiter import get_rate_limit_key

        req = _make_request(user_id="user-123")
        key = get_rate_limit_key(req)
        assert key == "user:user-123"

    def test_key_when_no_client(self):
        from app.middleware.rate_limiter import get_rate_limit_key

        req = _make_request()
        req.client = None
        key = get_rate_limit_key(req)
        assert key == "ip:unknown"


class TestCheckRateLimit:
    """Tests for the token-bucket rate limiter."""

    @pytest.fixture(autouse=True)
    def _clear_store(self):
        """Reset the in-memory rate limit store between tests."""
        from app.middleware import rate_limiter

        rate_limiter._rate_limit_store.clear()
        yield
        rate_limiter._rate_limit_store.clear()

    @pytest.mark.asyncio
    async def test_first_request_allowed(self):
        from app.middleware.rate_limiter import check_rate_limit

        req = _make_request(client_host="1.2.3.4")
        assert await check_rate_limit(req) is True

    @pytest.mark.asyncio
    async def test_burst_within_limit(self):
        from app.middleware.rate_limiter import check_rate_limit

        req = _make_request(client_host="5.6.7.8")
        for _ in range(10):
            assert await check_rate_limit(req) is True

    @pytest.mark.asyncio
    async def test_exceeding_limit(self):
        from app.middleware.rate_limiter import _rate_limit_store, check_rate_limit

        req = _make_request(client_host="9.9.9.9")
        # First call creates with full bucket (60 tokens) without decrement.
        # Subsequent calls decrement by 1 each. So it takes 61 successes
        # (1 initial + 60 decrements) before the 62nd is denied.
        for _ in range(61):
            result = await check_rate_limit(req)
            assert result is True
        # 62nd request should be denied (0 tokens remaining)
        assert await check_rate_limit(req) is False

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self):
        from app.middleware.rate_limiter import _rate_limit_store, check_rate_limit

        req = _make_request(client_host="11.11.11.11")
        # Exhaust tokens (61 calls to fully drain)
        for _ in range(61):
            await check_rate_limit(req)
        assert await check_rate_limit(req) is False

        # Simulate time passing (2 seconds → refills ~2 tokens)
        key = "ip:11.11.11.11"
        _rate_limit_store[key]["last_update"] -= 2
        assert await check_rate_limit(req) is True


class TestRateLimitMiddleware:
    """Tests for the middleware entrypoint."""

    @pytest.fixture(autouse=True)
    def _clear_store(self):
        from app.middleware import rate_limiter

        rate_limiter._rate_limit_store.clear()
        yield
        rate_limiter._rate_limit_store.clear()

    @pytest.mark.asyncio
    async def test_health_check_skips_rate_limit(self):
        from app.middleware.rate_limiter import rate_limit_middleware

        req = _make_request()
        req.url.path = "/health"
        # Should not raise even if we spam it
        for _ in range(100):
            await rate_limit_middleware(req)

    @pytest.mark.asyncio
    async def test_raises_429_when_exceeded(self):
        from app.middleware.rate_limiter import rate_limit_middleware

        req = _make_request(client_host="99.99.99.99")
        # Drain all 61 allowed requests (1 creates bucket + 60 decrements)
        for _ in range(61):
            await rate_limit_middleware(req)
        with pytest.raises(HTTPException) as exc_info:
            await rate_limit_middleware(req)
        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers


# ---------------------------------------------------------------------------
# Request tracking tests
# ---------------------------------------------------------------------------


class TestRequestIdMiddleware:
    """Tests for request ID assignment."""

    @pytest.mark.asyncio
    async def test_assigns_request_id(self):
        from app.middleware.request_tracking import request_id_middleware

        req = _make_request()
        req.state = MagicMock()
        response = MagicMock()
        call_next = AsyncMock(return_value=response)

        result = await request_id_middleware(req, call_next)

        # Should have set request_id
        assert hasattr(req.state, "request_id")
        # request_id should be a UUID string
        import uuid

        uuid.UUID(req.state.request_id)  # Raises ValueError if invalid
        call_next.assert_awaited_once_with(req)
        assert result is response

    @pytest.mark.asyncio
    async def test_assigns_start_time(self):
        from app.middleware.request_tracking import request_id_middleware

        req = _make_request()
        req.state = MagicMock()
        call_next = AsyncMock(return_value=MagicMock())

        before = time.time()
        await request_id_middleware(req, call_next)
        after = time.time()

        assert before <= req.state.start_time <= after


class TestLoggingMiddleware:
    """Tests for the logging middleware."""

    @pytest.mark.asyncio
    async def test_logs_and_returns_response(self):
        from app.middleware.request_tracking import logging_middleware

        req = _make_request()
        req.state.request_id = "test-req-id"
        response = MagicMock()
        response.status_code = 200
        call_next = AsyncMock(return_value=response)

        result = await logging_middleware(req, call_next)

        call_next.assert_awaited_once_with(req)
        assert result is response

    @pytest.mark.asyncio
    async def test_logs_and_reraises_on_error(self):
        from app.middleware.request_tracking import logging_middleware

        req = _make_request()
        req.state.request_id = "test-req-id"
        call_next = AsyncMock(side_effect=RuntimeError("boom"))

        with pytest.raises(RuntimeError, match="boom"):
            await logging_middleware(req, call_next)
