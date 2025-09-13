#!/usr/bin/env python3
"""Simple test to check database session."""

import os

os.environ["TESTING"] = "true"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User

# Test database - use in-memory database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created:", Base.metadata.tables.keys())

# Test database session
print("Testing database session...")
db = TestingSessionLocal()

try:
    # Test query
    users = db.query(User).all()
    print(f"Found {len(users)} users")
    
    # Test insert
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="test_hash",
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    print("User created successfully")
    
    # Test query again
    users = db.query(User).all()
    print(f"Found {len(users)} users after insert")
    
except Exception as e:
    print(f"Database error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

# Clean up
Base.metadata.drop_all(bind=engine)
