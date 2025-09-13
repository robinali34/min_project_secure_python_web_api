"""Database models with security considerations."""

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """User model with security best practices."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Security fields
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Indexes for security queries
    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
        Index("idx_users_username_active", "username", "is_active"),
        Index("idx_users_locked_until", "locked_until"),
    )


class RefreshToken(Base):
    """Refresh token model for secure token management."""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)

    # Security fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible

    # Indexes for cleanup and security
    __table_args__ = (
        Index("idx_refresh_tokens_user_expires", "user_id", "expires_at"),
        Index("idx_refresh_tokens_expires_revoked", "expires_at", "is_revoked"),
    )


class SecurityEvent(Base):
    """Security event logging model."""

    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Nullable for system events
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(Text, nullable=True)  # JSON data
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    severity = Column(String(20), default="INFO", nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )

    # Indexes for security monitoring
    __table_args__ = (
        Index("idx_security_events_type_created", "event_type", "created_at"),
        Index("idx_security_events_user_created", "user_id", "created_at"),
        Index("idx_security_events_severity_created", "severity", "created_at"),
    )


class OAuth2Token(Base):
    """OAuth2 token model for caching external service tokens."""

    __tablename__ = "oauth2_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    service_name = Column(
        String(50), nullable=False, index=True
    )  # e.g., 'github', 'google'
    access_token = Column(Text, nullable=False)  # Encrypted token
    refresh_token = Column(Text, nullable=True)  # Encrypted refresh token
    token_type = Column(String(20), default="Bearer", nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    scope = Column(String(255), nullable=False, index=True)  # Space-separated scopes

    # Additional OAuth2 fields
    client_id = Column(String(255), nullable=True)
    client_secret_hash = Column(String(255), nullable=True)  # Hashed for security

    # Security and audit fields
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_oauth2_tokens_user_service", "user_id", "service_name"),
        Index("idx_oauth2_tokens_service_scope", "service_name", "scope"),
        Index("idx_oauth2_tokens_expires_active", "expires_at", "is_active"),
        Index("idx_oauth2_tokens_user_active", "user_id", "is_active"),
    )
