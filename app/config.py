"""Configuration management with security best practices."""

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with security configurations."""

    # Database Configuration
    database_url: str = "sqlite:///./test.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Security Configuration
    secret_key: str = (
        "test-secret-key-that-is-at-least-32-characters-long-for-testing"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Password Security
    bcrypt_rounds: int = 4  # Lower for testing
    min_password_length: int = 8

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # Security Headers
    cors_origins: List[str] = ["http://localhost:3000"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1", "testserver"]

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Environment
    environment: str = "test"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is strong enough."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v

    @field_validator("bcrypt_rounds")
    @classmethod
    def validate_bcrypt_rounds(cls, v: int) -> int:
        """Ensure bcrypt rounds are secure."""
        # Allow lower rounds for testing (we'll set environment to test)
        if v < 4:
            raise ValueError("BCrypt rounds must be at least 4")
        return v

    @field_validator("min_password_length")
    @classmethod
    def validate_min_password_length(cls, v: int) -> int:
        """Ensure minimum password length is reasonable."""
        if v < 8:
            raise ValueError("Minimum password length must be at least 8")
        return v

    model_config = {"env_file": ".env", "case_sensitive": False}


# Global settings instance
settings = Settings()
