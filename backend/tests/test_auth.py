"""
Tests for JWT authentication module.

Covers: valid tokens, expired tokens, missing tokens, malformed tokens,
wrong audience, missing claims, and the optional-user variant.
"""

import time
from unittest.mock import patch

import jwt
import pytest

from app.core.auth import (
    CurrentUser,
    _decode_token,
    get_current_user,
    get_optional_user,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Must match the value set in conftest.py
TEST_JWT_SECRET = "test-jwt-secret-super-secret-at-least-32-chars-long"


def _make_token(
    sub: str = "user-uuid-1234",
    email: str = "test@example.com",
    role: str = "authenticated",
    aud: str = "authenticated",
    exp_offset: int = 3600,
    **extra_claims,
) -> str:
    """Create a signed JWT for testing."""
    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "aud": aud,
        "exp": int(time.time()) + exp_offset,
        "iat": int(time.time()),
        **extra_claims,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


def _make_credentials(token: str):
    """Build a mock HTTPAuthorizationCredentials."""
    from fastapi.security import HTTPAuthorizationCredentials

    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


# ---------------------------------------------------------------------------
# _decode_token tests
# ---------------------------------------------------------------------------


class TestDecodeToken:
    """Tests for raw JWT decoding / validation."""

    def test_valid_token(self):
        token = _make_token()
        payload = _decode_token(token)
        assert payload["sub"] == "user-uuid-1234"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "authenticated"

    def test_expired_token(self):
        token = _make_token(exp_offset=-100)  # expired 100s ago
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="expired"):
            _decode_token(token)

    def test_invalid_audience(self):
        token = _make_token(aud="wrong-audience")
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="audience"):
            _decode_token(token)

    def test_invalid_signature(self):
        token = jwt.encode(
            {"sub": "x", "exp": int(time.time()) + 3600, "aud": "authenticated"},
            "wrong-secret",
            algorithm="HS256",
        )
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="Invalid token"):
            _decode_token(token)

    def test_malformed_token(self):
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError):
            _decode_token("this.is.not.a.valid.jwt")

    def test_completely_garbage_token(self):
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError):
            _decode_token("garbage")

    def test_missing_sub_claim(self):
        """Token without 'sub' should still decode but get_current_user will reject it."""
        payload = {
            "email": "test@example.com",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="validation failed"):
            _decode_token(token)

    def test_missing_exp_claim(self):
        """Token without 'exp' should be rejected."""
        payload = {
            "sub": "user-1",
            "aud": "authenticated",
        }
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError):
            _decode_token(token)


# ---------------------------------------------------------------------------
# get_current_user tests
# ---------------------------------------------------------------------------


class TestGetCurrentUser:
    """Tests for the FastAPI auth dependency."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        token = _make_token(sub="abc-123", email="alice@test.com")
        creds = _make_credentials(token)

        user = await get_current_user(credentials=creds)

        assert isinstance(user, CurrentUser)
        assert user.id == "abc-123"
        assert user.email == "alice@test.com"
        assert user.role == "authenticated"

    @pytest.mark.asyncio
    async def test_missing_credentials_raises_401(self):
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="Authorization header required"):
            await get_current_user(credentials=None)

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self):
        token = _make_token(exp_offset=-100)
        creds = _make_credentials(token)

        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="expired"):
            await get_current_user(credentials=creds)

    @pytest.mark.asyncio
    async def test_default_role(self):
        """If role is missing from token, defaults to 'authenticated'."""
        payload = {
            "sub": "user-1",
            "email": "bob@test.com",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        creds = _make_credentials(token)

        user = await get_current_user(credentials=creds)
        assert user.role == "authenticated"


# ---------------------------------------------------------------------------
# get_optional_user tests
# ---------------------------------------------------------------------------


class TestGetOptionalUser:
    """Tests for the optional auth dependency."""

    @pytest.mark.asyncio
    async def test_no_credentials_returns_none(self):
        user = await get_optional_user(credentials=None)
        assert user is None

    @pytest.mark.asyncio
    async def test_valid_credentials_returns_user(self):
        token = _make_token(sub="opt-user")
        creds = _make_credentials(token)

        user = await get_optional_user(credentials=creds)
        assert isinstance(user, CurrentUser)
        assert user.id == "opt-user"

    @pytest.mark.asyncio
    async def test_invalid_token_still_raises(self):
        """If a token IS provided it must be valid, even for optional auth."""
        creds = _make_credentials("bad-token")

        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError):
            await get_optional_user(credentials=creds)
