"""Security monitoring and management endpoints."""

from typing import List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.schemas import SecurityEventResponse
from app.models import SecurityEvent, RefreshToken, User
from app.auth import get_current_superuser, get_current_user
from app.security import log_security_event, cleanup_expired_tokens

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_type: str = Query(None),
    severity: str = Query(None),
    user_id: int = Query(None),
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_superuser)
):
    """Get security events (superuser only)."""
    query = db.query(SecurityEvent)
    
    # Filter by time range
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = query.filter(SecurityEvent.created_at >= since)
    
    # Apply filters
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if severity:
        query = query.filter(SecurityEvent.severity == severity)
    if user_id:
        query = query.filter(SecurityEvent.user_id == user_id)
    
    # Order by most recent first
    events = query.order_by(desc(SecurityEvent.created_at)).offset(skip).limit(limit).all()
    
    return events


@router.get("/events/stats")
async def get_security_stats(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_superuser)
):
    """Get security event statistics (superuser only)."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Count events by type
    event_types = db.query(
        SecurityEvent.event_type,
        db.func.count(SecurityEvent.id).label('count')
    ).filter(
        SecurityEvent.created_at >= since
    ).group_by(SecurityEvent.event_type).all()
    
    # Count events by severity
    severities = db.query(
        SecurityEvent.severity,
        db.func.count(SecurityEvent.id).label('count')
    ).filter(
        SecurityEvent.created_at >= since
    ).group_by(SecurityEvent.severity).all()
    
    # Count total events
    total_events = db.query(SecurityEvent).filter(
        SecurityEvent.created_at >= since
    ).count()
    
    return {
        "total_events": total_events,
        "event_types": {event_type: count for event_type, count in event_types},
        "severities": {severity: count for severity, count in severities},
        "time_range_hours": hours
    }


@router.post("/events")
async def create_security_event(
    request: Request,
    event_type: str,
    event_data: str = None,
    severity: str = "INFO",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a security event (for testing purposes)."""
    log_security_event(
        db=db,
        event_type=event_type,
        user_id=current_user["id"],
        event_data=event_data,
        severity=severity,
        request=request
    )
    
    return {"message": "Security event created"}


@router.get("/tokens/active")
async def get_active_tokens(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_superuser)
):
    """Get active refresh tokens (superuser only)."""
    now = datetime.now(timezone.utc)
    active_tokens = db.query(RefreshToken).filter(
        RefreshToken.expires_at > now,
        RefreshToken.is_revoked == False
    ).all()
    
    return {
        "active_tokens": len(active_tokens),
        "tokens": [
            {
                "id": token.id,
                "user_id": token.user_id,
                "created_at": token.created_at,
                "expires_at": token.expires_at,
                "last_used_at": token.last_used_at,
                "ip_address": token.ip_address
            }
            for token in active_tokens
        ]
    }


@router.post("/tokens/cleanup")
async def cleanup_tokens(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_superuser)
):
    """Clean up expired tokens (superuser only)."""
    cleaned_count = cleanup_expired_tokens(db)
    
    log_security_event(
        db=db,
        event_type="token_cleanup",
        user_id=current_user["id"],
        event_data=f"cleaned_tokens={cleaned_count}",
        severity="INFO",
        request=request
    )
    
    return {"message": f"Cleaned up {cleaned_count} expired tokens"}


@router.get("/health")
async def security_health_check(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Security health check endpoint."""
    # Check for recent security events
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_events = db.query(SecurityEvent).filter(
        SecurityEvent.created_at >= since,
        SecurityEvent.severity.in_(["ERROR", "CRITICAL"])
    ).count()
    
    # Check for locked users
    locked_users = db.query(User).filter(
        User.locked_until > datetime.now(timezone.utc)
    ).count()
    
    # Check for failed login attempts in the last hour
    failed_logins = db.query(SecurityEvent).filter(
        SecurityEvent.event_type == "failed_login",
        SecurityEvent.created_at >= since
    ).count()
    
    health_status = "healthy"
    if recent_events > 10 or failed_logins > 50:
        health_status = "warning"
    if recent_events > 50 or failed_logins > 100:
        health_status = "critical"
    
    return {
        "status": health_status,
        "recent_critical_events": recent_events,
        "locked_users": locked_users,
        "failed_logins_last_hour": failed_logins,
        "timestamp": datetime.now(timezone.utc)
    }


