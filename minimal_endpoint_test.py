#!/usr/bin/env python3
"""Test endpoint with minimal setup."""

import os

os.environ["TESTING"] = "true"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import SecurityEvent, User

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
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created:", Base.metadata.tables.keys())

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

# Test registration endpoint with different data
test_cases = [
    {
        "username": "testuser1",
        "email": "test1@example.com",
        "password": "StrongPass123!"
    },
    {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "AnotherPass123!"
    }
]

for i, test_data in enumerate(test_cases):
    print(f"Testing case {i+1}: {test_data['username']}")
    response = client.post("/auth/register", json=test_data)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text}")
    if response.status_code == 201:
        print("  ✓ Success!")
    else:
        print("  ✗ Failed!")

# Clean up
Base.metadata.drop_all(bind=engine)
app.dependency_overrides.clear()
