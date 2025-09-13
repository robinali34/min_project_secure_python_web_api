#!/usr/bin/env python3
"""Detailed debug of the registration endpoint."""

import os
import traceback

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import SecurityEvent, User

# Set testing environment variable
os.environ["TESTING"] = "true"

# Test database - use in-memory database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing."""
    try:
        db = TestingSessionLocal()
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

# Test the registration endpoint with detailed error handling
print("Testing registration endpoint...")
try:
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123!"
    })
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 500:
        print("500 error - checking response details...")
        try:
            response_json = response.json()
            print(f"Error response: {response_json}")
        except:
            print("Could not parse response as JSON")
            
except Exception as e:
    print(f"Exception occurred: {e}")
    traceback.print_exc()

# Test a simple endpoint first
print("\nTesting health endpoint...")
try:
    response = client.get("/health")
    print(f"Health status code: {response.status_code}")
    print(f"Health response: {response.text}")
except Exception as e:
    print(f"Health endpoint exception: {e}")
    traceback.print_exc()

# Test database operations directly
print("\nTesting database operations directly...")
try:
    db_gen = override_get_db()
    db = next(db_gen)
    
    # Test if we can query the database
    user_count = db.query(User).count()
    print(f"User count: {user_count}")
    
    # Test if we can add a user
    from app.security import get_password_hash
    test_user = User(
        username="directtest",
        email="direct@example.com",
        hashed_password=get_password_hash("TestPass123!")
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    print(f"Direct user creation successful: {test_user.username}")
    
    # Clean up
    next(db_gen)
    
except Exception as e:
    print(f"Database operation exception: {e}")
    traceback.print_exc()

# Clean up
Base.metadata.drop_all(bind=engine)
app.dependency_overrides.clear()
