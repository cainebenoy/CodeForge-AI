"""
CodeForge AI Backend - FastAPI Application Entry Point
Handles app initialization, error handling, middleware setup, and event lifecycle
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import CodeForgeException
from app.core.logging import logger
from app.middleware.csrf import csrf_middleware
from app.middleware.rate_limiter import rate_limit_middleware
from app.middleware.request_tracking import logging_middleware, request_id_middleware

# ---------------------------------------------------------------------------
# Background housekeeping task
# ---------------------------------------------------------------------------

_cleanup_task: asyncio.Task | None = None

JOB_CLEANUP_INTERVAL_SECONDS = 3600  # 1 hour
JOB_CLEANUP_MAX_AGE_HOURS = 24


async def _periodic_job_cleanup() -> None:
    """
    Background coroutine that cleans up completed jobs older than
    JOB_CLEANUP_MAX_AGE_HOURS every JOB_CLEANUP_INTERVAL_SECONDS.
    Runs until cancelled on shutdown.
    """
    from app.services.job_queue import get_job_store

    while True:
        try:
            await asyncio.sleep(JOB_CLEANUP_INTERVAL_SECONDS)
            store = get_job_store()
            removed = store.cleanup_old_jobs(hours=JOB_CLEANUP_MAX_AGE_HOURS)
            if removed:
                logger.info(f"Periodic cleanup removed {removed} old jobs")
        except asyncio.CancelledError:
            logger.info("Job cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Job cleanup error: {e}")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with proper logging and background tasks"""
    global _cleanup_task

    # Startup
    logger.info(f"Starting CodeForge AI Backend ({settings.ENVIRONMENT})")
    logger.info(f"Log level: {settings.LOG_LEVEL}")

    # Launch periodic job cleanup
    _cleanup_task = asyncio.create_task(_periodic_job_cleanup())

    yield

    # Shutdown — cancel background tasks gracefully
    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass

    logger.info("Shutting down CodeForge AI Backend")


# FastAPI application factory
app = FastAPI(
    title="CodeForge AI Backend",
    description="AI Agent Engine for code generation and learning",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Middleware stack (order matters — last registered runs first)
# 1. Request tracking (must be outermost to capture all requests)
app.middleware("http")(request_id_middleware)
app.middleware("http")(logging_middleware)


# 2. Rate limiting — enforces per-IP and per-user request limits
@app.middleware("http")
async def _rate_limit_middleware(request: Request, call_next):
    """Rate limit middleware wrapper that calls next handler"""
    await rate_limit_middleware(request)
    return await call_next(request)


# 3. CSRF protection — double-submit cookie for state-changing requests
app.middleware("http")(csrf_middleware)


# 4. CORS middleware - HTTPS only in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# Include API routes
app.include_router(api_router, prefix="/v1")


@app.get("/health")
async def health_check():
    """
    Health check endpoint with dependency status.
    Returns overall status + individual dependency checks (Supabase, Redis).
    Always returns 200 so load balancers keep the instance in rotation —
    degraded dependencies are reported in the response body.
    """
    deps: dict = {}
    overall = "healthy"

    # --- Supabase ---
    try:
        from app.services.supabase import supabase_client

        # Lightweight query — RPC or table list to verify connectivity
        supabase_client.table("projects").select("id").limit(1).execute()
        deps["supabase"] = "ok"
    except Exception as e:
        deps["supabase"] = "degraded"
        overall = "degraded"

    # --- Redis (optional) ---
    try:
        from app.services.job_queue import RedisJobStore, get_job_store

        store = get_job_store()
        if isinstance(store, RedisJobStore):
            store._redis.ping()
            deps["redis"] = "ok"
        else:
            deps["redis"] = "not configured (in-memory fallback)"
    except Exception as e:
        deps["redis"] = "degraded"
        overall = "degraded"

    return {
        "status": overall,
        "service": "codeforge-backend",
        "version": "0.1.0",
        "dependencies": deps,
    }


# Error handlers
@app.exception_handler(CodeForgeException)
async def codeforge_exception_handler(request: Request, exc: CodeForgeException):
    """Handle CodeForge custom exceptions"""
    # Log internal details for debugging (especially for ExternalServiceError)
    internal_msg = getattr(exc, "_internal_message", None)
    if internal_msg:
        logger.error(
            f"CodeForge exception: {exc.error_code} - {exc.message} "
            f"(internal: {internal_msg})"
        )
    else:
        logger.error(f"CodeForge exception: {exc.error_code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    logger.warning(f"Validation error: {exc}")
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(x) for x in error["loc"][1:]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": errors},
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {type(exc).__name__} - {str(exc)}")

    # Don't expose internal errors in production
    if settings.ENVIRONMENT == "production":
        message = "Internal server error"
    else:
        message = str(exc)

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": message,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
