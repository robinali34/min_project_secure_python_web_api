"""OAuth2 web interface for token management."""

import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    OAuth2TokenCreate, OAuth2TokenUpdate, OAuth2TokenResponse,
    OAuth2ServiceConfig, PasswordEntry
)
from app.models import OAuth2Token, User
from app.auth import get_current_user
from app.oauth2_service import (
    OAuth2TokenManager, get_oauth2_service_config, get_available_scopes,
    validate_scope
)
from app.security import log_security_event

router = APIRouter(prefix="/oauth", tags=["oauth2-web"])

# Initialize templates
templates = Jinja2Templates(directory="app/templates")

# Initialize token manager
token_manager = OAuth2TokenManager()


@router.get("/", response_class=HTMLResponse)
async def oauth2_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """OAuth2 token management dashboard."""
    # Get user's tokens
    user_tokens = token_manager.get_user_tokens(db, current_user["id"])
    
    # Get available services and scopes
    available_services = list(get_oauth2_service_config("github").keys()) if get_oauth2_service_config("github") else []
    available_scopes = get_available_scopes()
    
    return templates.TemplateResponse("oauth2_dashboard.html", {
        "request": request,
        "user": current_user,
        "tokens": user_tokens,
        "services": available_services,
        "scopes": available_scopes
    })


@router.get("/add-token", response_class=HTMLResponse)
async def add_token_form(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Form to add a new OAuth2 token."""
    available_services = ["github", "google", "microsoft"]  # Predefined services
    available_scopes = get_available_scopes()
    
    return templates.TemplateResponse("add_token.html", {
        "request": request,
        "user": current_user,
        "services": available_services,
        "scopes": available_scopes
    })


@router.post("/add-token")
async def add_token(
    request: Request,
    service_name: str = Form(...),
    access_token: str = Form(...),
    refresh_token: str = Form(None),
    token_type: str = Form("Bearer"),
    expires_in: int = Form(None),
    scope: str = Form(...),
    client_id: str = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new OAuth2 token."""
    # Validate scope
    if not validate_scope(scope, service_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope '{scope}' for service '{service_name}'"
        )
    
    # Create token data
    token_data = OAuth2TokenCreate(
        service_name=service_name,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=token_type,
        expires_in=expires_in,
        scope=scope,
        client_id=client_id
    )
    
    # Store token
    try:
        token_manager.store_token(db, current_user["id"], token_data, request)
        return RedirectResponse(url="/oauth/", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store token: {str(e)}"
        )


@router.post("/tokens", response_model=OAuth2TokenResponse, status_code=status.HTTP_201_CREATED)
async def create_token(
    token_data: OAuth2TokenCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Create a new OAuth2 token."""
    # Validate scope
    if not validate_scope(token_data.scope, token_data.service_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope '{token_data.scope}' for service '{token_data.service_name}'"
        )
    
    # Store token
    try:
        stored_token = token_manager.store_token(db, current_user["id"], token_data, request)
        return stored_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store token: {str(e)}"
        )


@router.get("/tokens", response_model=List[OAuth2TokenResponse])
async def get_user_tokens(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    active_only: bool = True
):
    """Get all OAuth2 tokens for the current user."""
    tokens = token_manager.get_user_tokens(db, current_user["id"], active_only)
    return tokens


@router.get("/tokens/{service_name}", response_model=Optional[OAuth2TokenResponse])
async def get_token(
    service_name: str,
    scope: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific OAuth2 token."""
    token = token_manager.get_token(db, current_user["id"], service_name, scope)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active token found for service '{service_name}'"
        )
    return token


@router.get("/tokens/{service_name}/decrypted")
async def get_decrypted_token(
    service_name: str,
    scope: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a decrypted access token (for API use)."""
    token = token_manager.get_decrypted_token(db, current_user["id"], service_name, scope)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active token found for service '{service_name}'"
        )
    
    return {
        "access_token": token,
        "service_name": service_name,
        "scope": scope,
        "retrieved_at": datetime.now(timezone.utc).isoformat()
    }


@router.delete("/tokens/{service_name}")
async def revoke_token(
    service_name: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Revoke an OAuth2 token."""
    success = token_manager.revoke_token(db, current_user["id"], service_name, request)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active token found for service '{service_name}'"
        )
    
    return {"message": f"Token for service '{service_name}' has been revoked"}


@router.put("/tokens/{service_name}", response_model=OAuth2TokenResponse)
async def update_token(
    service_name: str,
    token_update: OAuth2TokenUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Update an OAuth2 token."""
    token = db.query(OAuth2Token).filter(
        OAuth2Token.user_id == current_user["id"],
        OAuth2Token.service_name == service_name,
        OAuth2Token.is_active == True
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active token found for service '{service_name}'"
        )
    
    # Update fields
    if token_update.access_token:
        token.access_token = token_manager._encrypt_token(token_update.access_token)
    if token_update.refresh_token:
        token.refresh_token = token_manager._encrypt_token(token_update.refresh_token)
    if token_update.expires_in:
        token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_update.expires_in)
    if token_update.scope:
        token.scope = token_update.scope
    if token_update.is_active is not None:
        token.is_active = token_update.is_active
    
    token.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(token)
    
    log_security_event(
        db=db,
        event_type="oauth2_token_updated",
        user_id=current_user["id"],
        event_data=f"service={service_name}",
        severity="INFO",
        request=request
    )
    
    return token


@router.get("/services", response_model=List[dict])
async def get_available_services():
    """Get available OAuth2 services."""
    from app.oauth2_service import OAUTH2_SERVICES
    services = []
    for service_name, config in OAUTH2_SERVICES.items():
        services.append({
            "name": service_name,
            "display_name": service_name.title(),
            "scopes": config.get("scope", ""),
            "authorization_url": config.get("authorization_url", ""),
            "token_url": config.get("token_url", "")
        })
    return services


@router.get("/scopes", response_model=dict)
async def get_available_scopes_endpoint():
    """Get available OAuth2 scopes."""
    return get_available_scopes()


@router.post("/cleanup")
async def cleanup_expired_tokens(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up expired tokens (admin only)."""
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can perform cleanup operations"
        )
    
    count = token_manager.cleanup_expired_tokens(db)
    return {"message": f"Cleaned up {count} expired tokens"}


@router.get("/password-entry", response_class=HTMLResponse)
async def password_entry_form(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Form for password entry to access OAuth2 tokens."""
    available_services = ["github", "google", "microsoft"]
    
    return templates.TemplateResponse("password_entry.html", {
        "request": request,
        "user": current_user,
        "services": available_services
    })


@router.post("/password-entry")
async def verify_password_and_get_tokens(
    request: Request,
    password: str = Form(...),
    service_name: str = Form(...),
    remember_me: bool = Form(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify password and return OAuth2 tokens."""
    # In a real implementation, you'd verify the password here
    # For now, we'll just check if it's not empty
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    # Get tokens for the service
    tokens = db.query(OAuth2Token).filter(
        OAuth2Token.user_id == current_user["id"],
        OAuth2Token.service_name == service_name,
        OAuth2Token.is_active == True
    ).all()
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No tokens found for service '{service_name}'"
        )
    
    # Log the access attempt
    log_security_event(
        db=db,
        event_type="oauth2_token_access",
        user_id=current_user["id"],
        event_data=f"service={service_name}, remember_me={remember_me}",
        severity="INFO",
        request=request
    )
    
    # Return token information (without the actual tokens for security)
    return {
        "service_name": service_name,
        "tokens_count": len(tokens),
        "scopes": [token.scope for token in tokens],
        "expires_at": [token.expires_at.isoformat() if token.expires_at else None for token in tokens],
        "remember_me": remember_me,
        "accessed_at": datetime.now(timezone.utc).isoformat()
    }
