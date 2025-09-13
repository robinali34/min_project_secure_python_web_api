"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""

    username: Optional[str] = Field(
        None, min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$"
    )
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user responses."""

    id: int
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class Token(BaseModel):
    """Schema for access token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Schema for token data."""

    username: Optional[str] = None
    user_id: Optional[int] = None


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class SecurityEventCreate(BaseModel):
    """Schema for security event creation."""

    event_type: str = Field(..., min_length=1, max_length=50)
    event_data: Optional[str] = None
    severity: str = Field(
        default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )


class SecurityEventResponse(BaseModel):
    """Schema for security event response."""

    id: int
    user_id: Optional[int]
    event_type: str
    event_data: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    severity: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OAuth2TokenCreate(BaseModel):
    """Schema for OAuth2 token creation."""

    service_name: str = Field(..., min_length=1, max_length=50)
    access_token: str = Field(..., min_length=1)
    refresh_token: Optional[str] = None
    token_type: str = Field(default="Bearer", max_length=20)
    expires_in: Optional[int] = None  # Seconds until expiration
    scope: str = Field(..., min_length=1, max_length=255)
    client_id: Optional[str] = None


class OAuth2TokenUpdate(BaseModel):
    """Schema for OAuth2 token updates."""

    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    is_active: Optional[bool] = None


class OAuth2TokenResponse(BaseModel):
    """Schema for OAuth2 token response."""

    id: int
    user_id: int
    service_name: str
    token_type: str
    expires_at: Optional[datetime]
    scope: str
    client_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]

    model_config = {"from_attributes": True}


class OAuth2ServiceConfig(BaseModel):
    """Schema for OAuth2 service configuration."""

    service_name: str = Field(..., min_length=1, max_length=50)
    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)
    authorization_url: str = Field(..., min_length=1)
    token_url: str = Field(..., min_length=1)
    scope: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1)


class PasswordEntry(BaseModel):
    """Schema for password entry in web interface."""

    password: str = Field(..., min_length=1, max_length=128)
    service_name: str = Field(..., min_length=1, max_length=50)
    remember_me: bool = Field(default=False)
