#!/usr/bin/env python3
"""Test endpoint directly."""

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
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created:", Base.metadata.tables.keys())

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

# Test a simple endpoint first
print("Testing health endpoint...")
response = client.get("/health")
print(f"Health status: {response.status_code}")
print(f"Health response: {response.text}")

# Test registration endpoint
print("Testing registration endpoint...")
response = client.post(
    "/auth/register",
    json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123!",
    },
)

print(f"Registration status: {response.status_code}")
print(f"Registration response: {response.text}")

# Clean up
Base.metadata.drop_all(bind=engine)
app.dependency_overrides.clear()
