"""
Tests for input validation service
"""
import pytest
from app.services.validation import InputValidator
from app.core.exceptions import ValidationError


def test_sanitize_string_valid():
    """Test valid string sanitization"""
    result = InputValidator.sanitize_string("hello world")
    assert result == "hello world"


def test_sanitize_string_exceeds_max_length():
    """Test string exceeding max length"""
    with pytest.raises(ValidationError) as exc_info:
        InputValidator.sanitize_string("x" * 1001, max_length=1000)
    assert "exceeds max length" in str(exc_info.value)


def test_validate_uuid_valid():
    """Test valid UUID validation"""
    valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
    result = InputValidator.validate_uuid(valid_uuid)
    assert result == valid_uuid


def test_validate_uuid_invalid():
    """Test invalid UUID"""
    with pytest.raises(ValidationError):
        InputValidator.validate_uuid("not-a-uuid")


def test_validate_file_path_traversal():
    """Test file path traversal prevention"""
    with pytest.raises(ValidationError):
        InputValidator.validate_file_path("../../../etc/passwd")


def test_validate_file_path_valid():
    """Test valid file path"""
    path = "src/components/Button.tsx"
    result = InputValidator.validate_file_path(path)
    assert result == path


def test_validate_email_valid():
    """Test valid email"""
    result = InputValidator.validate_email("test@example.com")
    assert result == "test@example.com"


def test_validate_email_invalid():
    """Test invalid email"""
    with pytest.raises(ValidationError):
        InputValidator.validate_email("not-an-email")


def test_sanitize_dict_depth_limit():
    """Test dict nesting depth limit"""
    deep_dict = {"a": {"b": {"c": {"d": {"e": {"f": "value"}}}}}}
    with pytest.raises(ValidationError):
        InputValidator.sanitize_dict(deep_dict, max_depth=3)
