"""Authentication endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import PasswordChange, Token, UserCreate, UserResponse
from app.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    log_security_event,
    reset_failed_login_attempts,
    revoke_refresh_token,
    store_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: Request, user_data: UserCreate, db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        log_security_event(
            db=db,
            event_type="registration_attempt_existing_username",
            event_data=f"username={user_data.username}",
            severity="WARNING",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        log_security_event(
            db=db,
            event_type="registration_attempt_existing_email",
            event_data=f"email={user_data.email}",
            severity="WARNING",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    log_security_event(
        db=db,
        event_type="user_registered",
        user_id=db_user.id,
        event_data=f"username={user_data.username}, email={user_data.email}",
        severity="INFO",
        request=request,
    )

    return db_user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login user and return access token."""
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        # Log failed login attempt
        log_security_event(
            db=db,
            event_type="failed_login",
            event_data=f"username={form_data.username}",
            severity="WARNING",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        log_security_event(
            db=db,
            event_type="inactive_user_login_attempt",
            user_id=user.id,
            severity="WARNING",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    # Check if account is locked
    from app.security import is_user_locked

    if is_user_locked(user):
        log_security_event(
            db=db,
            event_type="locked_user_login_attempt",
            user_id=user.id,
            severity="WARNING",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts",
        )

    # Reset failed login attempts on successful login
    reset_failed_login_attempts(db, user)

    # Create tokens
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires,
    )

    refresh_token = create_refresh_token(user.id)
    store_refresh_token(db, user.id, refresh_token, request)

    log_security_event(
        db=db,
        event_type="successful_login",
        user_id=user.id,
        severity="INFO",
        request=request,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request, refresh_token: str, db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    from app.security import get_user_by_id, verify_token

    token_data = verify_token(refresh_token, "refresh")
    if not token_data:
        log_security_event(
            db=db,
            event_type="invalid_refresh_token",
            severity="WARNING",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user = get_user_by_id(db, token_data.user_id)
    if not user or not user.is_active:
        log_security_event(
            db=db,
            event_type="refresh_token_inactive_user",
            user_id=token_data.user_id,
            severity="WARNING",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires,
    )

    log_security_event(
        db=db,
        event_type="token_refreshed",
        user_id=user.id,
        severity="INFO",
        request=request,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post("/logout")
async def logout(request: Request, refresh_token: str, db: Session = Depends(get_db)):
    """Logout user by revoking refresh token."""
    success = revoke_refresh_token(db, refresh_token)

    if success:
        log_security_event(
            db=db, event_type="user_logout", severity="INFO", request=request
        )
        return {"message": "Successfully logged out"}
    else:
        return {"message": "Token not found or already revoked"}


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Change user password."""
    from app.security import get_password_hash, verify_password

    # Verify current password
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not verify_password(password_data.current_password, user.hashed_password):
        log_security_event(
            db=db,
            event_type="password_change_wrong_current",
            user_id=current_user["id"],
            severity="WARNING",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    db.commit()

    log_security_event(
        db=db,
        event_type="password_changed",
        user_id=current_user["id"],
        severity="INFO",
        request=request,
    )

    return {"message": "Password changed successfully"}
