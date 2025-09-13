#!/usr/bin/env python3
"""Test with minimal FastAPI app."""

import os

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import SecurityEvent, User
from app.routers.auth import register
from app.schemas import UserCreate

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
        # Create tables for this session
        Base.metadata.create_all(bind=engine)
        yield db
    finally:
        db.close()


# Create minimal FastAPI app
app = FastAPI()

# Create all tables
Base.metadata.create_all(bind=engine)
print("Tables created:", Base.metadata.tables.keys())

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Add the registration endpoint directly
@app.post("/auth/register")
async def register_endpoint(
    user_data: UserCreate,
    db = Depends(get_db)
):
    """Register a new user."""
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    from app.security import get_password_hash
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# Create test client
client = TestClient(app)

# Test the registration endpoint
print("Testing minimal registration endpoint...")
try:
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123!"
    })
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        print("✓ Registration successful!")
    else:
        print("✗ Registration failed")
            
except Exception as e:
    print(f"Exception occurred: {e}")
    import traceback
    traceback.print_exc()

# Clean up
Base.metadata.drop_all(bind=engine)
app.dependency_overrides.clear()
