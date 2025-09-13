"""Database configuration with security best practices."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.config import settings

# Create database engine with security configurations
connect_args = {}

# Add database-specific connection arguments
if "postgresql" in settings.database_url:
    connect_args.update({
        "sslmode": "require",  # Force SSL connections
        "application_name": "secure_python_web_api",
    })
elif "sqlite" in settings.database_url:
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
    echo=False,  # Set to True for SQL debugging
    connect_args=connect_args
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Security event listeners
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set security parameters for PostgreSQL connections."""
    if "postgresql" in settings.database_url:
        with dbapi_connection.cursor() as cursor:
            # Set secure connection parameters
            cursor.execute("SET statement_timeout = '30s'")
            cursor.execute("SET lock_timeout = '10s'")
            cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
            cursor.execute("SET row_security = on")
            cursor.execute("SET default_transaction_isolation = 'read committed'")
