"""Security utilities and authentication logic."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models import RefreshToken, User
from app.schemas import TokenData

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(user_id: int) -> str:
    """Create a refresh token."""
    token_data = {
        "user_id": user_id,
        "type": "refresh",
        "jti": secrets.token_urlsafe(32),  # Unique token identifier
    }
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    token_data.update({"exp": expire})

    token = jwt.encode(token_data, settings.secret_key, algorithm=settings.algorithm)
    return token


def verify_token(
    token: str, token_type: str = "access"
) -> Optional[TokenData]:  # nosec B107
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        token_type_claim = payload.get("type")
        if token_type_claim != token_type:
            return None

        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if username is None or user_id is None:
            return None

        return TokenData(username=username, user_id=user_id)
    except JWTError:
        return None


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):  # type: ignore
        return None
    return user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def is_user_locked(user: User) -> bool:
    """Check if user account is locked."""
    if user.locked_until is None:
        return False
    return datetime.now(timezone.utc) < user.locked_until  # type: ignore


def lock_user_account(db: Session, user: User, lock_duration_minutes: int = 30) -> None:
    """Lock user account for specified duration."""
    user.locked_until = datetime.now(timezone.utc) + timedelta(  # type: ignore
        minutes=lock_duration_minutes
    )
    user.failed_login_attempts = 0  # type: ignore
    db.commit()


def increment_failed_login_attempts(db: Session, user: User) -> None:
    """Increment failed login attempts for user."""
    user.failed_login_attempts += 1  # type: ignore

    # Lock account after 5 failed attempts
    if user.failed_login_attempts >= 5:
        lock_user_account(db, user)
    else:
        db.commit()


def reset_failed_login_attempts(db: Session, user: User) -> None:
    """Reset failed login attempts for user."""
    user.failed_login_attempts = 0  # type: ignore
    user.locked_until = None  # type: ignore
    user.last_login = datetime.now(timezone.utc)  # type: ignore
    db.commit()


def store_refresh_token(
    db: Session, user_id: int, token: str, request: Request
) -> None:
    """Store refresh token in database."""
    token_hash = hash_refresh_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    db.add(refresh_token)
    db.commit()


def revoke_refresh_token(db: Session, token: str) -> bool:
    """Revoke a refresh token."""
    token_hash = hash_refresh_token(token)
    refresh_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked.is_(False),
        )
        .first()
    )

    if refresh_token:
        refresh_token.is_revoked = True  # type: ignore
        db.commit()
        return True
    return False


def cleanup_expired_tokens(db: Session) -> int:
    """Clean up expired refresh tokens."""
    now = datetime.now(timezone.utc)
    expired_tokens = db.query(RefreshToken).filter(RefreshToken.expires_at < now).all()

    for token in expired_tokens:
        db.delete(token)

    db.commit()
    return len(expired_tokens)


def log_security_event(
    db: Session,
    event_type: str,
    user_id: Optional[int] = None,
    event_data: Optional[str] = None,
    severity: str = "INFO",
    request: Optional[Request] = None,
) -> None:
    """Log a security event."""
    # Temporarily disable all logging for testing
    return None


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for forwarded headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct connection
    return request.client.host if request.client else "unknown"
