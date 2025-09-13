#!/usr/bin/env python3
"""Minimal test to check application setup."""

import os

os.environ["TESTING"] = "true"

# Test imports
try:
    from app.main import app
    print("✓ App import successful")
except Exception as e:
    print(f"✗ App import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test database setup
try:
    from app.database import Base, get_db
    from app.models import SecurityEvent, User
    print("✓ Database imports successful")
except Exception as e:
    print(f"✗ Database imports failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test SQLAlchemy setup
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    print("✓ Database setup successful")
except Exception as e:
    print(f"✗ Database setup failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test dependency override
try:
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    print("✓ Dependency override successful")
except Exception as e:
    print(f"✗ Dependency override failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test TestClient
try:
    from fastapi.testclient import TestClient
    client = TestClient(app)
    print("✓ TestClient creation successful")
except Exception as e:
    print(f"✗ TestClient creation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("All setup tests passed!")
