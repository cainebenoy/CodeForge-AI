"""
CodeForge AI Backend - FastAPI Application Entry Point
Handles app initialization, error handling, middleware setup, and event lifecycle
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import CodeForgeException
from app.core.logging import logger
from app.middleware.rate_limiter import rate_limit_middleware
from app.middleware.request_tracking import logging_middleware, request_id_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with proper logging"""
    # Startup
    logger.info(f"Starting CodeForge AI Backend ({settings.ENVIRONMENT})")
    logger.info(f"Log level: {settings.LOG_LEVEL}")

    yield

    # Shutdown
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


# 2. CORS middleware - HTTPS only in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-User-ID"],
    max_age=3600,
)

# Include API routes
app.include_router(api_router, prefix="/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint (skips logging)"""
    return {"status": "healthy", "service": "codeforge-backend", "version": "0.1.0"}


# Error handlers
@app.exception_handler(CodeForgeException)
async def codeforge_exception_handler(request: Request, exc: CodeForgeException):
    """Handle CodeForge custom exceptions"""
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
