#!/usr/bin/env python3
"""Test registration logic step by step."""

import os

os.environ["TESTING"] = "true"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User
from app.schemas import UserCreate
from app.security import get_password_hash

# Test database - use in-memory database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created:", Base.metadata.tables.keys())

# Test registration logic step by step
print("Testing registration logic...")

try:
    # Step 1: Create user data
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="StrongPass123!"
    )
    print("✓ User data creation successful")
    
    # Step 2: Check if username exists
    db = TestingSessionLocal()
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    print(f"✓ Username check successful: {existing_user is None}")
    
    # Step 3: Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    print(f"✓ Email check successful: {existing_email is None}")
    
    # Step 4: Hash password
    hashed_password = get_password_hash(user_data.password)
    print(f"✓ Password hashing successful: {hashed_password[:20]}...")
    
    # Step 5: Create user object
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    print("✓ User object creation successful")
    
    # Step 6: Add to database
    db.add(db_user)
    print("✓ User add to database successful")
    
    # Step 7: Commit
    db.commit()
    print("✓ Database commit successful")
    
    # Step 8: Refresh
    db.refresh(db_user)
    print(f"✓ Database refresh successful: user ID {db_user.id}")
    
    db.close()
    print("✓ All registration steps successful!")
    
except Exception as e:
    print(f"✗ Registration logic failed: {e}")
    import traceback
    traceback.print_exc()
    if 'db' in locals():
        db.close()

# Clean up
Base.metadata.drop_all(bind=engine)
