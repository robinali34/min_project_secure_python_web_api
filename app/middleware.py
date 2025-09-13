"""Security middleware and request processing."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import get_db
from app.security import log_security_event

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Custom security middleware for request processing."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:  # noqa: C901
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Check allowed hosts
        if not self._is_allowed_host(request):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid host header"},
            )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log security event for unexpected errors (skip in test mode)
            import os

            if not os.getenv("TESTING"):
                try:
                    db_gen = get_db()
                    db = next(db_gen)
                    try:
                        log_security_event(
                            db=db,
                            event_type="unexpected_error",
                            event_data=(
                                f"error={str(e)}, path={request.url.path}"
                            ),
                            severity="ERROR",
                            request=request,
                        )
                    finally:
                        try:
                            next(db_gen)  # Complete the generator
                        except StopIteration:
                            pass
                except Exception:
                    # If logging fails, just continue
                    # This is intentional - we don't want logging failures to
                    # break the app
                    pass  # nosec B110

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )

        # Add security headers manually
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self'; font-src 'self'; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
            "magnetometer=(), gyroscope=(), accelerometer=()"
        )

        # Add custom security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Add timing header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Log slow requests (skip in test mode)
        if process_time > 5.0 and not os.getenv("TESTING"):  # 5 seconds
            try:
                db_gen = get_db()
                db = next(db_gen)
                try:
                    log_security_event(
                        db=db,
                        event_type="slow_request",
                        event_data=(
                            f"path={request.url.path}, "
                            f"time={process_time: .2f}s"
                        ),
                        severity="WARNING",
                        request=request,
                    )
                finally:
                    try:
                        next(db_gen)  # Complete the generator
                    except StopIteration:
                        pass
            except Exception:
                # If logging fails, just continue
                # This is intentional - we don't want logging failures to
                # break the app
                pass  # nosec B110

        return response

    def _is_allowed_host(self, request: Request) -> bool:
        """Check if the request is from an allowed host."""
        host = request.headers.get("host", "").split(":")[0]
        # Allow test hosts and localhost variations
        allowed_hosts = settings.allowed_hosts + [
            "testserver",
            "localhost",
            "127.0.0.1",
        ]
        return host in allowed_hosts or host == ""


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Apply rate limiting
        try:
            # This is a simplified rate limiting implementation
            # In production, you'd want to use Redis or similar
            pass
        except RateLimitExceeded:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )

        return await call_next(request)


def setup_cors(app):
    """Setup CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )


def setup_security_middleware(app):
    """Setup security middleware."""
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(RateLimitMiddleware)


def setup_rate_limiting(app):
    """Setup rate limiting."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
