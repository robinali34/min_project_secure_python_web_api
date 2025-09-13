"""Logging configuration for security monitoring."""

import logging
from typing import Any, Dict, List

import structlog

from app.config import settings


def configure_logging() -> None:
    """Configure structured logging for security monitoring."""

    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Configure structlog
    processors: List[Any] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class SecurityLogger:
    """Security-specific logger with structured logging."""

    def __init__(self) -> None:
        self.logger = structlog.get_logger("security")

    def log_authentication_attempt(
        self, username: str, success: bool, ip_address: str, user_agent: str = None
    ) -> None:
        """Log authentication attempts."""
        self.logger.info(
            "Authentication attempt",
            username=username,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            event_type="authentication_attempt",
        )

    def log_authorization_failure(
        self, user_id: int, resource: str, action: str, ip_address: str
    ) -> None:
        """Log authorization failures."""
        self.logger.warning(
            "Authorization failure",
            user_id=user_id,
            resource=resource,
            action=action,
            ip_address=ip_address,
            event_type="authorization_failure",
        )

    def log_security_event(self, event_type: str, severity: str, **kwargs: Any) -> None:
        """Log general security events."""
        log_level = getattr(logging, severity.upper(), logging.INFO)
        self.logger.log(
            log_level,
            "Security event",
            event_type=event_type,
            severity=severity,
            **kwargs,
        )

    def log_data_access(
        self, user_id: int, resource_type: str, resource_id: str, action: str
    ) -> None:
        """Log data access events."""
        self.logger.info(
            "Data access",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            event_type="data_access",
        )

    def log_configuration_change(
        self, user_id: int, config_key: str, old_value: Any, new_value: Any
    ) -> None:
        """Log configuration changes."""
        self.logger.warning(
            "Configuration change",
            user_id=user_id,
            config_key=config_key,
            old_value=str(old_value),
            new_value=str(new_value),
            event_type="configuration_change",
        )


# Global security logger instance
security_logger = SecurityLogger()
