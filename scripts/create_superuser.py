#!/usr/bin/env python3
"""Script to create a superuser account."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import User, Base
from app.security import get_password_hash
from app.config import settings

def create_superuser():
    """Create a superuser account."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if superuser already exists
        existing_superuser = db.query(User).filter(User.is_superuser == True).first()
        if existing_superuser:
            print(f"Superuser already exists: {existing_superuser.username}")
            return
        
        # Get user input
        username = input("Enter username: ").strip()
        email = input("Enter email: ").strip()
        password = input("Enter password: ").strip()
        
        if not username or not email or not password:
            print("❌ All fields are required")
            return
        
        # Validate password strength
        from app.security_utils import SecurityValidator
        is_valid, issues = SecurityValidator.validate_password_strength(password)
        if not is_valid:
            print("❌ Password does not meet security requirements:")
            for issue in issues:
                print(f"  - {issue}")
            return
        
        # Create superuser
        hashed_password = get_password_hash(password)
        superuser = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            is_superuser=True
        )
        
        db.add(superuser)
        db.commit()
        db.refresh(superuser)
        
        print(f"✅ Superuser created successfully: {username}")
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔐 Creating superuser account...")
    create_superuser()
