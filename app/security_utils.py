"""Additional security utilities and validators."""

import ipaddress
import re
from typing import List, Union
from urllib.parse import urlparse

from fastapi import HTTPException, status


class SecurityValidator:
    """Security validation utilities."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format with security considerations."""
        if not email or len(email) > 254:
            return False

        # Basic email regex (RFC 5322 compliant)
        email_regex = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        return bool(email_regex.match(email))

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username with security considerations."""
        if not username or len(username) < 3 or len(username) > 50:
            return False

        # Only allow alphanumeric characters and underscores
        username_regex = re.compile(r"^[a-zA-Z0-9_]+$")
        return bool(username_regex.match(username))

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, List[str]]:
        """Validate password strength and return issues."""
        issues = []

        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")

        if len(password) > 128:
            issues.append("Password must be no more than 128 characters long")

        if not any(c.isupper() for c in password):
            issues.append(
                "Password must contain at least one uppercase letter"
            )

        if not any(c.islower() for c in password):
            issues.append(
                "Password must contain at least one lowercase letter"
            )

        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append(
                "Password must contain at least one special character"
            )

        # Check for common weak patterns (exact matches only)
        weak_patterns = [
            r"^password$",
            r"^123456$",
            r"^qwerty$",
            r"^admin$",
            r"^user$",
            r"^login$",
        ]

        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                issues.append("Password contains common weak patterns")
                break

        return len(issues) == 0, issues

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 1000) -> str:
        """Sanitize user input."""
        if not input_string:
            return ""

        # Truncate to max length
        sanitized = input_string[:max_length]

        # Remove null bytes and control characters
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", sanitized)

        # Remove potential SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",  # noqa: E501
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+\w+\s*=\s*\w+)",
            r"(\b(OR|AND)\s+\w+\s*LIKE\s+\w+)",
            r"(\b(OR|AND)\s+\w+\s*IN\s*\([^)]+\))",
        ]

        for pattern in sql_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        return sanitized.strip()


class SecurityHeaders:
    """Security headers management."""

    @staticmethod
    def get_security_headers() -> dict:
        """Get comprehensive security headers."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), "
                "gyroscope=(), accelerometer=()"
            ),
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self'; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
        }


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self.requests = {}

    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit."""
        import time

        now = time.time()
        window_start = now - window

        # Clean old entries
        if key in self.requests:
            self.requests[key] = [
                req_time
                for req_time in self.requests[key]
                if req_time > window_start
            ]
        else:
            self.requests[key] = []

        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(now)
            return True

        return False


class InputValidator:
    """Input validation utilities."""

    @staticmethod
    def validate_json_input(data: dict, required_fields: List[str]) -> None:
        """Validate JSON input data."""
        for field in required_fields:
            if field not in data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

    @staticmethod
    def validate_string_length(
        value: str, min_length: int = 0, max_length: int = 1000
    ) -> None:
        """Validate string length."""
        if len(value) < min_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"String too short (minimum {min_length} characters)",
            )

        if len(value) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"String too long (maximum {max_length} characters)",
            )

    @staticmethod
    def validate_numeric_range(
        value: Union[int, float],
        min_value: float = None,
        max_value: float = None,
    ) -> None:
        """Validate numeric range."""
        if min_value is not None and value < min_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Value too small (minimum {min_value})",
            )

        if max_value is not None and value > max_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Value too large (maximum {max_value})",
            )
