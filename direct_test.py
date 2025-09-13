#!/usr/bin/env python3
"""Test endpoint directly without TestClient."""

import os

os.environ["TESTING"] = "true"

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import SecurityEvent, User
from app.routers.auth import register
from app.schemas import UserCreate

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

# Test the registration function directly
print("Testing registration function directly...")

async def test_registration():
    try:
        # Create user data
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!"
        )
        print("✓ User data creation successful")
        
        # Create mock request
        class MockRequest:
            def __init__(self):
                self.client = type('MockClient', (), {'host': 'testserver'})()
                self.headers = {}
        
        request = MockRequest()
        print("✓ Mock request creation successful")
        
        # Get database session
        db_gen = override_get_db()
        db = next(db_gen)
        print("✓ Database session creation successful")
        
        # Call registration function (async)
        result = await register(user_data, request, db)
        print(f"✓ Registration function successful: {result.username}")
        
        # Clean up
        try:
            next(db_gen)
        except StopIteration:
            pass
        
    except Exception as e:
        print(f"✗ Registration function failed: {e}")
        import traceback
        traceback.print_exc()
        if 'db_gen' in locals():
            try:
                next(db_gen)
            except StopIteration:
                pass

# Run the async test
import asyncio

asyncio.run(test_registration())

# Clean up
Base.metadata.drop_all(bind=engine)
