#!/usr/bin/env python3
"""Debug the /users/me endpoint."""

import os
import traceback

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import SecurityEvent, User
from app.security import create_access_token, get_password_hash

# Set testing environment variable
os.environ["TESTING"] = "true"

# Test database - use file-based database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///debug_users_me.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing."""
    try:
        db = TestingSessionLocal()
        # Create tables for this session
        Base.metadata.create_all(bind=engine)
        yield db
    finally:
        db.close()


# Create all tables
Base.metadata.create_all(bind=engine)
print("Tables created:", Base.metadata.tables.keys())

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

# Create a test user
print("Creating test user...")
db_gen = override_get_db()
db = next(db_gen)
try:
    test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        is_active=True,
        is_verified=True,
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    print(f"✓ Test user created: {test_user.username} (ID: {test_user.id})")

    # Create access token
    token = create_access_token({"sub": test_user.username, "user_id": test_user.id})
    print(f"✓ Access token created")

    # Test the /users/me endpoint
    print("Testing /users/me endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("✓ /users/me endpoint working!")
    else:
        print("✗ /users/me endpoint failed")

finally:
    next(db_gen)

# Clean up
Base.metadata.drop_all(bind=engine)
app.dependency_overrides.clear()

# Remove the test database file
if os.path.exists("debug_users_me.db"):
    os.remove("debug_users_me.db")
