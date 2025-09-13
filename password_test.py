#!/usr/bin/env python3
"""Test password hashing."""

import os

os.environ["TESTING"] = "true"

try:
    from app.security import get_password_hash

    print("✓ Password hashing import successful")

    # Test password hashing
    password = "StrongPass123!"
    hashed = get_password_hash(password)
    print(f"✓ Password hashing successful: {hashed[:20]}...")

except Exception as e:
    print(f"✗ Password hashing failed: {e}")
    import traceback

    traceback.print_exc()
