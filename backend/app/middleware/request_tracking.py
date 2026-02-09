"""
Request ID middleware
Adds unique request identifier for tracing
"""
import uuid
from fastapi import Request
from app.core.logging import logger


async def request_id_middleware(request: Request):
    """
    Add request ID to each request for tracing
    Stored in request.state for access in handlers
    """
    request.state.request_id = str(uuid.uuid4())
    request.state.start_time = 0


async def logging_middleware(request: Request, call_next):
    """
    Log all requests and responses
    Includes timing and status code
    """
    import time

    request_id = getattr(request.state, "request_id", "unknown")
    method = request.method
    path = request.url.path

    start_time = time.time()

    logger.info(
        f"Request: {method} {path}",
        extra={"request_id": request_id},
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"Response: {response.status_code} ({process_time:.2f}s)",
            extra={"request_id": request_id},
        )

        return response
    except Exception as e:
        logger.error(
            f"Request error: {str(e)}",
            extra={"request_id": request_id},
        )
        raise
