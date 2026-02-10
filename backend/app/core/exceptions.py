"""
Custom exceptions for the application
Provides comprehensive error handling with proper HTTP status codes
"""

from typing import Any, Dict, Optional


class CodeForgeException(Exception):
    """Base exception for all CodeForge exceptions"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to response format"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ResourceNotFoundError(CodeForgeException):
    """Resource not found (404)"""

    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "id": resource_id},
        )


class ValidationError(CodeForgeException):
    """Input validation error (400)"""

    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Validation error in {field}",
            status_code=400,
            error_code="VALIDATION_ERROR",
            details={"field": field, "reason": reason},
        )


class AuthenticationError(CodeForgeException):
    """Authentication error (401)"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
        )


class PermissionError(CodeForgeException):
    """Permission denied error (403)"""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="PERMISSION_DENIED",
        )


class RateLimitExceededError(CodeForgeException):
    """Rate limit exceeded (429)"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
        )


class ExternalServiceError(CodeForgeException):
    """External service error (502/503)

    Security: The raw error message is logged server-side but only the
    service name is exposed to the client to prevent information leakage.
    """

    def __init__(self, service: str, message: str):
        # Log full error detail server-side; expose only service name to client
        super().__init__(
            message=f"{service} service error",
            status_code=503,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
        )
        # Store raw message for server-side logging (not in to_dict output)
        self._internal_message = message


class AgentExecutionError(CodeForgeException):
    """Agent execution error"""

    def __init__(self, agent_type: str, message: str):
        super().__init__(
            message=f"Agent execution failed: {message}",
            status_code=500,
            error_code="AGENT_EXECUTION_ERROR",
            details={"agent": agent_type},
        )
