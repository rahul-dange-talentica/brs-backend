import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)
from app.config import settings


class TestPasswordHashing:
    """Test password hashing and verification functions."""
    
    def test_hash_password(self):
        """Test password hashing function."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        
    def test_hash_password_different_results(self):
        """Test that same password produces different hashes (salt)."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
        
    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password("", hashed) is False
        



class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data=data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode token to verify content
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload
        
    def test_create_access_token_with_expiry(self):
        """Test access token creation with custom expiry."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data=data, expires_delta=expires_delta)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # Check that expiry is approximately 30 minutes from now
        exp_timestamp = payload["exp"]
        expected_exp = datetime.utcnow() + expires_delta
        actual_exp = datetime.utcfromtimestamp(exp_timestamp)  # Use utcfromtimestamp
        
        # Allow 5 second tolerance
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert time_diff < 5
        
    def test_create_access_token_default_expiry(self):
        """Test access token creation with default expiry."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data=data)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # Check that expiry is approximately 15 minutes from now (default)
        exp_timestamp = payload["exp"]
        expected_exp = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        actual_exp = datetime.utcfromtimestamp(exp_timestamp)  # Use utcfromtimestamp
        
        # Allow 5 second tolerance
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert time_diff < 5
        
    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data=data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        
        assert payload is None
        
    def test_verify_token_expired(self):
        """Test token verification with expired token."""
        data = {"sub": "test@example.com"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data=data, expires_delta=expires_delta)
        
        payload = verify_token(token)
        
        assert payload is None
        
    def test_verify_token_malformed(self):
        """Test token verification with malformed token."""
        malformed_tokens = [
            "",
            "not.a.jwt",
            "header.payload",  # Missing signature
            "too.many.parts.here.invalid"
        ]
        
        for token in malformed_tokens:
            payload = verify_token(token)
            assert payload is None
            
    def test_verify_token_wrong_algorithm(self):
        """Test token verification with wrong algorithm."""
        data = {"sub": "test@example.com"}
        
        # Create token with different algorithm
        token = jwt.encode(data, settings.secret_key, algorithm="HS512")
        
        payload = verify_token(token)
        
        assert payload is None
        
    def test_verify_token_wrong_secret(self):
        """Test token verification with wrong secret."""
        data = {"sub": "test@example.com"}
        
        # Create token with different secret
        token = jwt.encode(data, "wrong_secret", algorithm=settings.algorithm)
        
        payload = verify_token(token)
        
        assert payload is None


class TestTokenEdgeCases:
    """Test edge cases and security scenarios."""
    
    def test_token_with_additional_claims(self):
        """Test token with additional claims."""
        data = {
            "sub": "test@example.com",
            "role": "admin",
            "permissions": ["read", "write"]
        }
        token = create_access_token(data=data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]
        
    def test_token_with_unicode_data(self):
        """Test token with unicode characters."""
        data = {"sub": "tëst@éxämplé.com"}
        token = create_access_token(data=data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "tëst@éxämplé.com"
        
    def test_empty_token_data(self):
        """Test token creation with empty data."""
        data = {}
        token = create_access_token(data=data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert "exp" in payload  # Should still have expiration
        
    def test_none_token_verification(self):
        """Test token verification with None."""
        # verify_token expects a string, not None
        # This should be handled gracefully
        try:
            payload = verify_token(None)
            assert payload is None
        except AttributeError:
            # This is expected since None doesn't have string methods
            assert True
