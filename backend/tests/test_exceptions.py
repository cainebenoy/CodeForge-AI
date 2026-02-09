"""
Tests for exceptions
"""
import pytest
from app.core.exceptions import (
    CodeForgeException,
    ResourceNotFoundError,
    ValidationError,
    AuthenticationError,
    RateLimitExceededError,
)


def test_codeforge_exception():
    """Test base exception"""
    exc = CodeForgeException("test error", status_code=400, error_code="TEST_ERROR")
    assert exc.status_code == 400
    assert exc.error_code == "TEST_ERROR"


def test_resource_not_found_error():
    """Test resource not found exception"""
    exc = ResourceNotFoundError("User", "user-123")
    assert exc.status_code == 404
    assert exc.error_code == "RESOURCE_NOT_FOUND"


def test_validation_error():
    """Test validation exception"""
    exc = ValidationError("email", "Invalid email format")
    assert exc.status_code == 400
    assert exc.error_code == "VALIDATION_ERROR"


def test_authentication_error():
    """Test authentication exception"""
    exc = AuthenticationError("Invalid credentials")
    assert exc.status_code == 401
    assert exc.error_code == "AUTHENTICATION_ERROR"


def test_rate_limit_error():
    """Test rate limit exception"""
    exc = RateLimitExceededError(retry_after=60)
    assert exc.status_code == 429
    assert exc.details["retry_after"] == 60


def test_exception_to_dict():
    """Test exception serialization"""
    exc = ValidationError("name", "Name too short")
    exc_dict = exc.to_dict()
    
    assert exc_dict["error"] == "VALIDATION_ERROR"
    assert "message" in exc_dict
    assert "details" in exc_dict
