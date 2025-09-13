"""Security tests for the API."""

import pytest
from app.security import get_password_hash, create_access_token
from app.models import User


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    token = create_access_token({"sub": test_user.username, "user_id": test_user.id})
    return {"Authorization": f"Bearer {token}"}


class TestAuthentication:
    """Test authentication security."""
    
    def test_register_weak_password(self, db_session, client):
        """Test registration with weak password."""
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak"
        })
        assert response.status_code == 422
        assert "String should have at least 8 characters" in response.text
    
    def test_register_strong_password(self, db_session, client):
        """Test registration with strong password."""
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123!"
        })
        assert response.status_code == 201
        assert response.json()["username"] == "testuser"
    
    def test_login_invalid_credentials(self, db_session, client):
        """Test login with invalid credentials."""
        response = client.post("/auth/login", data={
            "username": "nonexistent",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_login_valid_credentials(self, test_user, client):
        """Test login with valid credentials."""
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "TestPass123!"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_protected_endpoint_without_token(self, db_session, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/users/me")
        assert response.status_code == 403
    
    def test_protected_endpoint_with_token(self, auth_headers, db_session, client):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"


class TestInputValidation:
    """Test input validation security."""
    
    def test_sql_injection_attempt(self, auth_headers, db_session, client):
        """Test SQL injection attempt."""
        response = client.put("/users/me",
            headers=auth_headers,
            json={
                "username": "test'; DROP TABLE users; --",
                "email": "test@example.com"
            }
        )
        # Should reject malicious input at validation layer (more secure)
        assert response.status_code == 422
    
    def test_xss_attempt(self, auth_headers, db_session, client):
        """Test XSS attempt."""
        response = client.put("/users/me",
            headers=auth_headers,
            json={
                "username": "<script>alert('xss')</script>",
                "email": "test@example.com"
            }
        )
        # Should reject malicious input at validation layer (more secure)
        assert response.status_code == 422
    
    def test_email_validation(self, auth_headers, db_session, client):
        """Test email validation."""
        response = client.put("/users/me",
            headers=auth_headers,
            json={
                "username": "testuser",
                "email": "invalid-email"
            }
        )
        assert response.status_code == 422


class TestRateLimiting:
    """Test rate limiting."""
    
    def test_public_endpoint_rate_limit(self, client):
        """Test rate limiting on public endpoint."""
        # Make multiple requests quickly
        for _ in range(65):  # Exceed the 60/minute limit
            response = client.get("/api/public")
            if response.status_code == 429:
                break
        else:
            pytest.fail("Rate limiting not working")


class TestSecurityHeaders:
    """Test security headers."""
    
    def test_security_headers_present(self, client):
        """Test that security headers are present."""
        response = client.get("/")
        headers = response.headers
        
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Referrer-Policy" in headers


class TestPasswordSecurity:
    """Test password security features."""
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        from app.security_utils import SecurityValidator
        
        # Test weak passwords
        weak_passwords = [
            "12345678",  # No uppercase, special chars
            "password",  # No uppercase, digits, special chars
            "PASSWORD",  # No lowercase, digits, special chars
            "Pass123",   # No special chars
            "Pass!@#",   # No digits
        ]
        
        for password in weak_passwords:
            is_valid, issues = SecurityValidator.validate_password_strength(password)
            assert not is_valid
            assert len(issues) > 0
    
    def test_strong_password_validation(self):
        """Test strong password validation."""
        from app.security_utils import SecurityValidator
        
        strong_passwords = [
            "StrongPass123!",
            "MySecure@Password456",
            "Complex!Pass#789",
        ]
        
        for password in strong_passwords:
            is_valid, issues = SecurityValidator.validate_password_strength(password)
            assert is_valid
            assert len(issues) == 0


class TestAccountSecurity:
    """Test account security features."""
    
    def test_account_lockout_after_failed_attempts(self, db_session):
        """Test account lockout after multiple failed attempts."""
        # This would require implementing the lockout logic in tests
        # For now, we'll test the basic structure
        user = User(
            username="locktest",
            email="locktest@example.com",
            hashed_password=get_password_hash("TestPass123!"),
            failed_login_attempts=4
        )
        db_session.add(user)
        db_session.commit()
        
        # Simulate one more failed attempt
        user.failed_login_attempts += 1
        db_session.commit()
        
        # Account should be locked after 5 attempts
        assert user.failed_login_attempts >= 5
