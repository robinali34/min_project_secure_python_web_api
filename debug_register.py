#!/usr/bin/env python3
"""Debug the registration endpoint."""

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

# Test database - use file-based database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///debug_test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
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

# Test the registration endpoint
print("Testing registration endpoint...")
try:
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123!",
        },
    )
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

# Clean up
Base.metadata.drop_all(bind=engine)
app.dependency_overrides.clear()

# Remove the test database file
import os

if os.path.exists("debug_test.db"):
    os.remove("debug_test.db")
