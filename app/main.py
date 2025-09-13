"""Main FastAPI application with security configurations."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import Base, engine
from app.middleware import setup_cors, setup_rate_limiting, setup_security_middleware
from app.routers import auth, oauth2_web, security, users

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting up secure Python web API")

    # Create database tables (skip in testing environment)
    if not os.getenv("TESTING"):
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    else:
        logger.info("Skipping database table creation in testing environment")

    yield

    # Shutdown
    logger.info("Shutting down secure Python web API")


# Create FastAPI application
app = FastAPI(
    title="Secure Python Web API",
    description="A secure Python web API with PostgreSQL demonstrating security best practices",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    openapi_url="/openapi.json" if settings.environment == "development" else None,
    lifespan=lifespan,
)

# Setup middleware
setup_cors(app)
setup_security_middleware(app)
setup_rate_limiting(app)

# Add trusted host middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

# Add rate limiting exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
        client_ip=get_remote_address(request),
    )

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        client_ip=get_remote_address(request),
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0",
    }


# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Secure Python Web API",
        "version": "1.0.0",
        "docs": "/docs" if settings.environment == "development" else "disabled",
    }


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(security.router)
app.include_router(oauth2_web.router)


# Rate limited endpoints
@app.get("/api/public")
@limiter.limit("60/minute")
async def public_endpoint(request: Request) -> Dict[str, str]:
    """Public endpoint with rate limiting."""
    return {"message": "This is a public endpoint"}


@app.get("/api/status")
@limiter.limit("10/minute")
async def status_endpoint(request: Request) -> Dict[str, str]:
    """Status endpoint with rate limiting."""
    return {"status": "operational", "timestamp": "2024-01-01T00:00:00Z"}


if __name__ == "__main__":
    import uvicorn

    # Use localhost for development, 0.0.0.0 for production (containerized)
    if settings.environment == "development":
        host = "127.0.0.1"
    else:
        host = "0.0.0.0"  # nosec B104

    uvicorn.run(
        "app.main:app",
        host=host,
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
        access_log=True,
    )
