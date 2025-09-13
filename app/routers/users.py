"""User management endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import get_current_superuser, get_current_user
from app.database import get_db
from app.models import User
from app.schemas import UserResponse, UserUpdate
from app.security import log_security_event

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    request: Request,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update current user information."""
    user = db.query(User).filter(User.id == current_user["id"]).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if username is being changed and if it's already taken
    if user_update.username and user_update.username != user.username:
        existing_user = (
            db.query(User).filter(
                User.username == user_update.username
            ).first()
        )
        if existing_user:
            log_security_event(
                db=db,
                event_type="username_change_attempt_existing",
                user_id=current_user["id"],
                event_data=f"new_username={user_update.username}",
                severity="WARNING",
                request=request,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        user.username = user_update.username

    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != user.email:
        existing_user = db.query(User).filter(
            User.email == user_update.email
        ).first()
        if existing_user:
            log_security_event(
                db=db,
                event_type="email_change_attempt_existing",
                user_id=current_user["id"],
                event_data=f"new_email={user_update.email}",
                severity="WARNING",
                request=request,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken",
            )
        user.email = user_update.email

    # Update other fields
    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    db.commit()
    db.refresh(user)

    log_security_event(
        db=db,
        event_type="user_profile_updated",
        user_id=current_user["id"],
        severity="INFO",
        request=request,
    )

    return user


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_superuser),
):
    """Get all users (superuser only)."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_superuser),
):
    """Get user by ID (superuser only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_superuser),
):
    """Delete user (superuser only)."""
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    db.delete(user)
    db.commit()

    log_security_event(
        db=db,
        event_type="user_deleted",
        user_id=user_id,
        event_data=f"deleted_by={current_user['id']}",
        severity="WARNING",
        request=request,
    )

    return {"message": "User deleted successfully"}


@router.post("/{user_id}/lock")
async def lock_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_superuser),
):
    """Lock user account (superuser only)."""
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot lock your own account",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    from app.security import lock_user_account

    lock_user_account(db, user)

    log_security_event(
        db=db,
        event_type="user_locked",
        user_id=user_id,
        event_data=f"locked_by={current_user['id']}",
        severity="WARNING",
        request=request,
    )

    return {"message": "User account locked successfully"}


@router.post("/{user_id}/unlock")
async def unlock_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_superuser),
):
    """Unlock user account (superuser only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.locked_until = None
    user.failed_login_attempts = 0
    db.commit()

    log_security_event(
        db=db,
        event_type="user_unlocked",
        user_id=user_id,
        event_data=f"unlocked_by={current_user['id']}",
        severity="INFO",
        request=request,
    )

    return {"message": "User account unlocked successfully"}
