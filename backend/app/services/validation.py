"""
Input validation and sanitization service
Sanitizes user inputs and prevents common attacks
"""
import re
from typing import Any, Dict
from app.core.exceptions import ValidationError


class InputValidator:
    """Comprehensive input validation"""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input
        Removes dangerous characters and enforces length limits
        """
        if not isinstance(value, str):
            raise ValidationError("field", "Must be a string")

        if len(value) > max_length:
            raise ValidationError("field", f"String exceeds max length of {max_length}")

        # Remove control characters
        value = "".join(char for char in value if ord(char) >= 32 or char in "\n\t")

        return value.strip()

    @staticmethod
    def validate_uuid(value: str) -> str:
        """
        Validate UUID format
        """
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )

        if not uuid_pattern.match(value):
            raise ValidationError("id", "Invalid UUID format")

        return value

    @staticmethod
    def validate_file_path(path: str) -> str:
        """
        Validate file path
        Prevents directory traversal attacks
        """
        if not isinstance(path, str):
            raise ValidationError("path", "Path must be a string")

        # Prevent directory traversal
        if ".." in path or path.startswith("/") or path.startswith("\\"):
            raise ValidationError("path", "Invalid path: cannot traverse directories")

        # Only allow alphanumeric, dots, slashes, hyphens, underscores
        if not re.match(r"^[a-zA-Z0-9/_\-\.]+$", path):
            raise ValidationError("path", "Path contains invalid characters")

        return path

    @staticmethod
    def validate_email(email: str) -> str:
        """Basic email validation"""
        email_pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )

        if not email_pattern.match(email):
            raise ValidationError("email", "Invalid email format")

        return email.lower()

    @staticmethod
    def validate_url(url: str) -> str:
        """Validate URL format"""
        url_pattern = re.compile(
            r"^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=]+$"
        )

        if not url_pattern.match(url):
            raise ValidationError("url", "Invalid URL format")

        return url

    @staticmethod
    def sanitize_dict(data: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary
        Limits nesting depth to prevent resource exhaustion
        """
        if max_depth <= 0:
            raise ValidationError("data", "Object nesting too deep")

        sanitized = {}

        for key, value in data.items():
            if not isinstance(key, str):
                continue  # Skip non-string keys

            # Sanitize key
            sanitized_key = InputValidator.sanitize_string(key, max_length=100)

            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[sanitized_key] = InputValidator.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[sanitized_key] = InputValidator.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[sanitized_key] = [
                    InputValidator.sanitize_dict(item, max_depth - 1)
                    if isinstance(item, dict)
                    else item
                    for item in value[:100]  # Limit list length
                ]
            elif isinstance(value, (int, float, bool)):
                sanitized[sanitized_key] = value
            else:
                # Skip unsupported types
                pass

        return sanitized
