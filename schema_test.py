#!/usr/bin/env python3
"""Test schema validation."""

import os

os.environ["TESTING"] = "true"

try:
    from app.schemas import UserCreate
    print("✓ Schema import successful")
    
    # Test schema validation
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123!"
    }
    
    user = UserCreate(**user_data)
    print(f"✓ Schema validation successful: {user.username}, {user.email}")
    
except Exception as e:
    print(f"✗ Schema validation failed: {e}")
    import traceback
    traceback.print_exc()
