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
        """Rate limiter should extract user ID from JWT (not X-User-ID header)."""
        import jwt as pyjwt

        from app.middleware.rate_limiter import get_rate_limit_key

        token = pyjwt.encode(
            {"sub": "user-123", "aud": "authenticated", "exp": 99999999999},
            "test-jwt-secret-super-secret-at-least-32-chars-long",
            algorithm="HS256",
        )
        req = _make_request()
        req.headers = {"Authorization": f"Bearer {token}"}
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
        """Reset the global rate limiter between tests."""
        from app.middleware import rate_limiter as rl_mod
        from app.middleware.rate_limiter import InMemoryRateLimiter

        # Force a fresh in-memory limiter for each test
        rl_mod._limiter = InMemoryRateLimiter()
        yield
        rl_mod._limiter = None

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
        from app.middleware.rate_limiter import check_rate_limit, get_rate_limiter

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
        from app.middleware.rate_limiter import check_rate_limit, get_rate_limiter

        req = _make_request(client_host="11.11.11.11")
        # Exhaust tokens (61 calls to fully drain)
        for _ in range(61):
            await check_rate_limit(req)
        assert await check_rate_limit(req) is False

        # Simulate time passing (2 seconds → refills ~2 tokens)
        limiter = get_rate_limiter()
        key = "ip:11.11.11.11"
        limiter._store[key]["last_update"] -= 2
        assert await check_rate_limit(req) is True


class TestRateLimitMiddleware:
    """Tests for the middleware entrypoint."""

    @pytest.fixture(autouse=True)
    def _clear_store(self):
        from app.middleware import rate_limiter as rl_mod
        from app.middleware.rate_limiter import InMemoryRateLimiter

        rl_mod._limiter = InMemoryRateLimiter()
        yield
        rl_mod._limiter = None

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


# ---------------------------------------------------------------------------
# JWT-based rate limit key extraction
# ---------------------------------------------------------------------------


class TestJWTRateLimitKey:
    """Tests for JWT-based rate limit key generation."""

    def test_key_from_jwt_bearer(self):
        """Rate limiter should extract user ID from a valid JWT token."""
        import jwt as pyjwt

        from app.middleware.rate_limiter import get_rate_limit_key

        token = pyjwt.encode(
            {"sub": "test-user-id", "aud": "authenticated", "exp": 99999999999},
            "test-jwt-secret-super-secret-at-least-32-chars-long",
            algorithm="HS256",
        )
        request = _make_request()
        request.headers = {"Authorization": f"Bearer {token}"}

        key = get_rate_limit_key(request)
        assert key == "user:test-user-id"

    def test_key_falls_back_to_ip_on_invalid_jwt(self):
        """Rate limiter should fall back to IP when JWT is invalid."""
        from app.middleware.rate_limiter import get_rate_limit_key

        request = _make_request(client_host="10.0.0.42")
        request.headers = {"Authorization": "Bearer this-is-not-a-valid-jwt"}

        key = get_rate_limit_key(request)
        assert key == "ip:10.0.0.42"


# ---------------------------------------------------------------------------
# CSRF middleware tests
# ---------------------------------------------------------------------------


class TestCSRFMiddleware:
    """Tests for CSRF middleware using the FastAPI TestClient."""

    def test_get_request_passes_without_csrf(self, client):
        """GET requests should pass without any CSRF tokens."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_post_without_cookie_passes(self, client):
        """POST without a csrf cookie should pass (first request scenario)."""
        response = client.post(
            "/v1/agents/run-agent",
            json={
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_type": "research",
                "input_context": {"user_idea": "test"},
            },
        )
        # Should not be 403 from CSRF — will be 401 from auth instead
        assert response.status_code != 403

    def test_post_with_cookie_but_no_header_fails(self, client):
        """POST with csrf cookie but missing header should be rejected."""
        client.cookies.set("csrf_token", "test-csrf-token-value")
        response = client.post(
            "/v1/agents/run-agent",
            json={
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_type": "research",
                "input_context": {"user_idea": "test"},
            },
        )
        assert response.status_code == 403

    def test_post_with_matching_tokens_passes(self, client):
        """POST with matching CSRF cookie and header should pass through CSRF."""
        csrf_value = "matching-csrf-token"
        client.cookies.set("csrf_token", csrf_value)
        response = client.post(
            "/v1/agents/run-agent",
            json={
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_type": "research",
                "input_context": {"user_idea": "test"},
            },
            headers={"X-CSRF-Token": csrf_value},
        )
        # Should not be 403 — CSRF passes, may get 401 from auth
        assert response.status_code != 403

    def test_post_with_mismatched_tokens_fails(self, client):
        """POST with different CSRF cookie vs header should be rejected."""
        client.cookies.set("csrf_token", "cookie-value")
        response = client.post(
            "/v1/agents/run-agent",
            json={
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_type": "research",
                "input_context": {"user_idea": "test"},
            },
            headers={"X-CSRF-Token": "different-header-value"},
        )
        assert response.status_code == 403

    def test_health_endpoint_exempt(self, client):
        """Health endpoint should be exempt from CSRF checks."""
        client.cookies.set("csrf_token", "some-token")
        # POST to /health with cookie but no header — should still pass
        response = client.post("/health")
        # /health may not support POST (405) but should NOT be 403
        assert response.status_code != 403

    def test_response_sets_csrf_cookie(self, client):
        """GET request response should set a csrf_token cookie."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "csrf_token" in response.cookies
