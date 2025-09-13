"""OAuth2 service utilities for token management and caching."""

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.config import settings
from app.models import OAuth2Token, User
from app.schemas import OAuth2TokenCreate, OAuth2TokenUpdate
from app.security import log_security_event


class OAuth2TokenManager:
    """Manager for OAuth2 token operations."""

    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize the token manager with encryption."""
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate a key from the secret key
            key = Fernet.generate_key()
            self.cipher = Fernet(key)

    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token for storage."""
        return self.cipher.encrypt(token.encode()).decode()

    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token from storage."""
        return self.cipher.decrypt(encrypted_token.encode()).decode()

    def store_token(
        self, db: Session, user_id: int, token_data: OAuth2TokenCreate, request=None
    ) -> OAuth2Token:
        """Store an OAuth2 token for a user."""
        # Check if token already exists for this user and service
        existing_token = (
            db.query(OAuth2Token)
            .filter(
                and_(
                    OAuth2Token.user_id == user_id,
                    OAuth2Token.service_name == token_data.service_name,
                    OAuth2Token.is_active.is_(True),
                )
            )
            .first()
        )

        # Calculate expiration time
        expires_at = None
        if token_data.expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_data.expires_in
            )

        if existing_token:
            # Update existing token
            existing_token.access_token = self._encrypt_token(token_data.access_token)
            if token_data.refresh_token:
                existing_token.refresh_token = self._encrypt_token(
                    token_data.refresh_token
                )
            existing_token.token_type = token_data.token_type
            existing_token.expires_at = expires_at
            existing_token.scope = token_data.scope
            existing_token.client_id = token_data.client_id
            existing_token.updated_at = datetime.now(timezone.utc)
            existing_token.last_used_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(existing_token)

            log_security_event(
                db=db,
                event_type="oauth2_token_updated",
                user_id=user_id,
                event_data=f"service={token_data.service_name}, scope={token_data.scope}",
                severity="INFO",
                request=request,
            )

            return existing_token
        else:
            # Create new token
            new_token = OAuth2Token(
                user_id=user_id,
                service_name=token_data.service_name,
                access_token=self._encrypt_token(token_data.access_token),
                refresh_token=self._encrypt_token(token_data.refresh_token)
                if token_data.refresh_token
                else None,
                token_type=token_data.token_type,
                expires_at=expires_at,
                scope=token_data.scope,
                client_id=token_data.client_id,
                last_used_at=datetime.now(timezone.utc),
            )

            db.add(new_token)
            db.commit()
            db.refresh(new_token)

            log_security_event(
                db=db,
                event_type="oauth2_token_created",
                user_id=user_id,
                event_data=f"service={token_data.service_name}, scope={token_data.scope}",
                severity="INFO",
                request=request,
            )

            return new_token

    def get_token(
        self, db: Session, user_id: int, service_name: str, scope: Optional[str] = None
    ) -> Optional[OAuth2Token]:
        """Get an active OAuth2 token for a user and service."""
        query = db.query(OAuth2Token).filter(
            and_(
                OAuth2Token.user_id == user_id,
                OAuth2Token.service_name == service_name,
                OAuth2Token.is_active.is_(True),
            )
        )

        if scope:
            query = query.filter(OAuth2Token.scope.contains(scope))

        token = query.first()

        if token:
            # Check if token is expired
            if token.expires_at and token.expires_at.replace(
                tzinfo=timezone.utc
            ) < datetime.now(timezone.utc):
                # Mark token as inactive
                token.is_active = False
                db.commit()
                return None

            # Update last used timestamp
            token.last_used_at = datetime.now(timezone.utc)
            db.commit()

            return token

        return None

    def get_decrypted_token(
        self, db: Session, user_id: int, service_name: str, scope: Optional[str] = None
    ) -> Optional[str]:
        """Get a decrypted access token."""
        token = self.get_token(db, user_id, service_name, scope)
        if token:
            return self._decrypt_token(token.access_token)
        return None

    def revoke_token(
        self, db: Session, user_id: int, service_name: str, request=None
    ) -> bool:
        """Revoke an OAuth2 token."""
        token = (
            db.query(OAuth2Token)
            .filter(
                and_(
                    OAuth2Token.user_id == user_id,
                    OAuth2Token.service_name == service_name,
                    OAuth2Token.is_active.is_(True),
                )
            )
            .first()
        )

        if token:
            token.is_active = False
            token.updated_at = datetime.now(timezone.utc)
            db.commit()

            log_security_event(
                db=db,
                event_type="oauth2_token_revoked",
                user_id=user_id,
                event_data=f"service={service_name}",
                severity="INFO",
                request=request,
            )

            return True

        return False

    def get_user_tokens(
        self, db: Session, user_id: int, active_only: bool = True
    ) -> List[OAuth2Token]:
        """Get all tokens for a user."""
        query = db.query(OAuth2Token).filter(OAuth2Token.user_id == user_id)

        if active_only:
            query = query.filter(OAuth2Token.is_active.is_(True))

        return query.all()

    def cleanup_expired_tokens(self, db: Session) -> int:
        """Clean up expired tokens."""
        now = datetime.now(timezone.utc)
        expired_tokens = (
            db.query(OAuth2Token)
            .filter(and_(OAuth2Token.expires_at < now, OAuth2Token.is_active.is_(True)))
            .all()
        )

        count = len(expired_tokens)
        for token in expired_tokens:
            token.is_active = False
            token.updated_at = now

        db.commit()

        if count > 0:
            log_security_event(
                db=db,
                event_type="oauth2_tokens_cleanup",
                event_data=f"cleaned_up={count}",
                severity="INFO",
            )

        return count


# Predefined OAuth2 service configurations
OAUTH2_SERVICES = {
    "github": {
        "client_id": "",
        "client_secret": "",
        "authorization_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "scope": "read:user user:email",
        "redirect_uri": "http://localhost:8000/oauth/callback/github",
    },
    "google": {
        "client_id": "",
        "client_secret": "",
        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scope": "openid profile email",
        "redirect_uri": "http://localhost:8000/oauth/callback/google",
    },
    "microsoft": {
        "client_id": "",
        "client_secret": "",
        "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "scope": "openid profile email",
        "redirect_uri": "http://localhost:8000/oauth/callback/microsoft",
    },
}

# Scope definitions
OAUTH2_SCOPES = {
    "read-only": {
        "description": "Read-only access to user data",
        "permissions": ["read:user", "read:profile", "read:email"],
    },
    "profile": {
        "description": "Access to user profile information",
        "permissions": ["read:user", "read:profile", "read:email", "read:avatar"],
    },
    "full": {
        "description": "Full access to user account",
        "permissions": [
            "read:user",
            "read:profile",
            "read:email",
            "write:user",
            "write:profile",
        ],
    },
}


def get_oauth2_service_config(service_name: str) -> Optional[Dict[str, str]]:
    """Get OAuth2 service configuration."""
    return OAUTH2_SERVICES.get(service_name)


def get_available_scopes() -> Dict[str, Dict[str, Any]]:
    """Get available OAuth2 scopes."""
    return OAUTH2_SCOPES


def validate_scope(scope: str, service_name: str) -> bool:
    """Validate if a scope is valid for a service."""
    service_config = get_oauth2_service_config(service_name)
    if not service_config:
        return False

    # Check if scope is in the predefined scopes
    if scope in OAUTH2_SCOPES:
        return True

    # For now, accept any scope (in production, you'd validate against service-specific scopes)
    return True
