"""
CSRF protection middleware (defense-in-depth).

Even though the API uses JWT Bearer tokens (not vulnerable to CSRF),
this middleware adds double-submit token verification for state-changing
requests as an extra layer of protection.

How it works:
- On any request, if no CSRF cookie exists, set one with a random token.
- On state-changing requests (POST, PUT, DELETE), compare the
  X-CSRF-Token header value against the csrf_token cookie value.
- GET, HEAD, OPTIONS are exempt (safe methods).
- The /health endpoint is exempt.
- Requests without a cookie (e.g., first request) are exempt — the
  client JS reads the cookie and sends it in subsequent requests.

The frontend must:
1. Read the `csrf_token` cookie
2. Send it as `X-CSRF-Token` header on POST/PUT/DELETE requests
"""

import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logging import logger

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


async def csrf_middleware(request: Request, call_next):
    """
    CSRF double-submit cookie middleware.

    For state-changing methods, verifies that the X-CSRF-Token header
    matches the csrf_token cookie. Sets the cookie on every response
    if not already present.
    """
    # Skip safe methods and exempt paths
    if request.method in SAFE_METHODS or request.url.path in EXEMPT_PATHS:
        response = await call_next(request)
        _ensure_csrf_cookie(request, response)
        return response

    # For state-changing methods, validate the CSRF token
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)

    # If no cookie exists yet, this is likely the first request — skip validation
    # The response will set the cookie for subsequent requests
    if cookie_token is not None:
        if not header_token or not secrets.compare_digest(cookie_token, header_token):
            logger.warning(
                f"CSRF validation failed: path={request.url.path}, "
                f"cookie_present={bool(cookie_token)}, header_present={bool(header_token)}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF_VALIDATION_FAILED",
                    "message": "CSRF token validation failed. "
                    "Include the csrf_token cookie value in the X-CSRF-Token header.",
                },
            )

    response = await call_next(request)
    _ensure_csrf_cookie(request, response)
    return response


def _ensure_csrf_cookie(request: Request, response) -> None:
    """Set the CSRF cookie if it doesn't already exist."""
    if CSRF_COOKIE_NAME not in request.cookies:
        token = secrets.token_urlsafe(32)
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=token,
            httponly=False,  # JS needs to read this cookie
            secure=True,
            samesite="strict",
            max_age=3600 * 24,  # 24 hours
        )
