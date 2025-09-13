"""Test configuration and fixtures."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import User, SecurityEvent, OAuth2Token

# Set testing environment variable
os.environ["TESTING"] = "true"

# Test database - use unique file-based database for each test
import uuid
import tempfile
import os

# Create a temporary directory for test databases
temp_dir = tempfile.mkdtemp()

# Create a new database file for each test run
def create_test_database():
    test_db_name = f"test_{uuid.uuid4().hex[:8]}.db"
    test_db_path = os.path.join(temp_dir, test_db_name)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{test_db_path}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, TestingSessionLocal, test_db_path

# Initialize with first database
engine, TestingSessionLocal, test_db_path = create_test_database()


def override_get_db():
    """Override the database dependency for testing."""
    try:
        db = TestingSessionLocal()
        # Create tables for this session
        Base.metadata.create_all(bind=engine)
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """Set up the test database for each test."""
    global engine, TestingSessionLocal, test_db_path
    
    # Create a new database for each test
    engine, TestingSessionLocal, test_db_path = create_test_database()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    # Clean up after each test
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()
    
    # Remove the test database file
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from app.security import get_password_hash
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    from app.security import create_access_token
    token = create_access_token({"sub": test_user.username, "user_id": test_user.id})
    return {"Authorization": f"Bearer {token}"}
