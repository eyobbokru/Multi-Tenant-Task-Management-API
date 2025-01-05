import pytest
from datetime import datetime, timedelta
from jose import jwt
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_token_data,
    verify_password,
    get_password_hash,
    is_token_expired,
    SecurityUtils
)
from app.core.config import settings

class TestSecurity:
    def test_password_hash(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Test that hashed password is different from original
        assert hashed != password
        
        # Test that we can verify the password
        assert verify_password(password, hashed) is True
        
        # Test that wrong password fails verification
        assert verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self):
        user_id = "test_user_id"
        token = create_access_token(user_id)
        
        # Decode and verify token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_create_access_token_with_expiry(self):
        user_id = "test_user_id"
        expires_delta = timedelta(minutes=30)
        token = create_access_token(user_id, expires_delta)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        expiry = datetime.fromtimestamp(payload["exp"])
        expected_expiry = datetime.utcnow() + expires_delta
        
        # Allow 1 second tolerance for test execution time
        assert abs((expiry - expected_expiry).total_seconds()) < 1

    def test_create_refresh_token(self):
        user_id = "test_user_id"
        token = create_refresh_token(user_id)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_verify_token(self):
        user_id = "test_user_id"
        token = create_access_token(user_id)
        
        # Test valid token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        
        # Test invalid token
        invalid_payload = verify_token("invalid_token")
        assert invalid_payload is None

    def test_get_token_data(self):
        user_id = "test_user_id"
        token = create_access_token(user_id)
        
        # Test valid token
        subject = get_token_data(token)
        assert subject == user_id
        
        # Test invalid token
        invalid_subject = get_token_data("invalid_token")
        assert invalid_subject is None

    def test_is_token_expired(self):
        user_id = "test_user_id"
        
        # Test non-expired token
        valid_token = create_access_token(
            user_id,
            expires_delta=timedelta(minutes=30)
        )
        assert is_token_expired(valid_token) is False
        
        # Test expired token
        expired_token = create_access_token(
            user_id,
            expires_delta=timedelta(minutes=-1)
        )
        assert is_token_expired(expired_token) is True
        
        # Test invalid token
        assert is_token_expired("invalid_token") is True

class TestSecurityUtils:
    def test_create_token_response(self):
        user_id = "test_user_id"
        response = SecurityUtils.create_token_response(user_id)
        
        assert "access_token" in response
        assert "refresh_token" in response
        assert "token_type" in response
        assert response["token_type"] == "bearer"
        
        # Verify both tokens
        access_payload = verify_token(response["access_token"])
        refresh_payload = verify_token(response["refresh_token"])
        
        assert access_payload["sub"] == user_id
        assert refresh_payload["sub"] == user_id
        assert refresh_payload["type"] == "refresh"

    def test_refresh_access_token(self):
        user_id = "test_user_id"
        refresh_token = create_refresh_token(user_id)
        
        # Test valid refresh token
        new_access_token = SecurityUtils.refresh_access_token(refresh_token)
        assert new_access_token is not None
        
        payload = verify_token(new_access_token)
        assert payload["sub"] == user_id
        
        # Test invalid refresh token
        invalid_token = create_access_token(user_id)  # Using access token instead of refresh
        new_token = SecurityUtils.refresh_access_token(invalid_token)
        assert new_token is None
        
        # Test completely invalid token
        new_token = SecurityUtils.refresh_access_token("invalid_token")
        assert new_token is None