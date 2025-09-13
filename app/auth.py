"""Authentication dependencies and utilities."""

from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TokenData
from app.security import (
    get_user_by_id,
    get_user_by_username,
    is_user_locked,
    log_security_event,
    verify_token,
)

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(credentials.credentials)
    if token_data is None:
        log_security_event(
            db=db, event_type="invalid_token", severity="WARNING", request=request
        )
        raise credentials_exception

    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        log_security_event(
            db=db,
            event_type="user_not_found",
            user_id=token_data.user_id,
            severity="WARNING",
            request=request,
        )
        raise credentials_exception

    if not user.is_active:
        log_security_event(
            db=db,
            event_type="inactive_user_access_attempt",
            user_id=user.id,
            severity="WARNING",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    if is_user_locked(user):
        log_security_event(
            db=db,
            event_type="locked_user_access_attempt",
            user_id=user.id,
            severity="WARNING",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Account is temporarily locked"
        )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login": user.last_login,
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get current active user."""
    if not current_user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """Get current verified user."""
    if not current_user["is_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified"
        )
    return current_user


async def get_current_superuser(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """Get current superuser."""
    if not current_user["is_superuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


def require_permissions(required_permissions: list):
    """Decorator to require specific permissions."""

    def permission_checker(current_user: dict = Depends(get_current_active_user)):
        # This is a simplified permission system
        # In a real application, you'd have a more complex permission system
        if not current_user["is_superuser"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return current_user

    return permission_checker
