import pytest
from fastapi import status
from jose import jwt

from app.config import settings
from app.core.security import verify_password


class TestUserRegistration:
    """Test user registration endpoint."""
    
    def test_register_user_success(self, client):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",  # Added special character
            "first_name": "John",
            "last_name": "Doe"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["first_name"] == "John"
        assert data["user"]["last_name"] == "Doe"
        assert data["user"]["is_active"] is True
        assert "id" in data["user"]
        assert "created_at" in data["user"]
        assert "updated_at" in data["user"]
        
        # Verify token is valid
        token = data["access_token"]
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == data["user"]["id"]
    
    def test_register_user_minimal_data(self, client):
        """Test registration with minimal required data."""
        user_data = {
            "email": "minimal@example.com",
            "password": "SecurePassword123!",
            "first_name": "Minimal",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["user"]["email"] == "minimal@example.com"
        assert data["user"]["first_name"] == "Minimal"
        assert data["user"]["last_name"] == "User"
    
    def test_register_user_duplicate_email(self, client, test_user):
        """Test registration with existing email."""
        user_data = {
            "email": test_user.email,
            "password": "SecurePassword123!",
            "first_name": "Duplicate",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "An account with this email address already exists" in response.json()["detail"]
    
    def test_register_user_invalid_email(self, client):
        """Test registration with invalid email."""
        user_data = {
            "email": "invalid_email",
            "password": "SecurePassword123!"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_weak_password(self, client):
        """Test registration with weak password."""
        user_data = {
            "email": "weakpass@example.com",
            "password": "weak"  # Too short
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_missing_email(self, client):
        """Test registration without email."""
        user_data = {
            "password": "SecurePassword123!",
            "first_name": "No",
            "last_name": "Email"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_missing_password(self, client):
        """Test registration without password."""
        user_data = {
            "email": "nopass@example.com",
            "first_name": "No",
            "last_name": "Password"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_long_names(self, client):
        """Test registration with names exceeding length limits."""
        user_data = {
            "email": "longname@example.com",
            "password": "SecurePassword123!",
            "first_name": "x" * 101,  # Exceeds 100 char limit
            "last_name": "Doe"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_case_insensitive_email(self, client, test_user):
        """Test that email uniqueness is case-insensitive."""
        user_data = {
            "email": test_user.email.upper(),  # Same email but uppercase
            "password": "SecurePassword123!",
            "first_name": "Case",
            "last_name": "Test"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        # Should fail due to duplicate email (case-insensitive)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_user_password_not_stored_plaintext(self, client, db_session):
        """Test that password is not stored in plaintext."""
        user_data = {
            "email": "passwordtest@example.com",
            "password": "PlaintextTest123!",
            "first_name": "Password",
            "last_name": "Test"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check database directly
        from app.models.user import User
        user_in_db = db_session.query(User).filter(User.email == user_data["email"]).first()
        
        assert user_in_db is not None
        assert user_in_db.password_hash != user_data["password"]
        assert verify_password(user_data["password"], user_in_db.password_hash)


class TestUserLogin:
    """Test user login endpoint."""
    
    def test_login_success(self, client, test_user):
        """Test successful user login."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword"  # From fixture
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user.email
        assert data["user"]["id"] == str(test_user.id)
        
        # Verify token is valid
        token = data["access_token"]
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == str(test_user.id)
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "somepassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_inactive_user(self, client, inactive_user):
        """Test login with inactive user account."""
        login_data = {
            "username": inactive_user.email,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Account has been deactivated" in response.json()["detail"]
    
    def test_login_missing_username(self, client):
        """Test login without username."""
        login_data = {
            "password": "somepassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_missing_password(self, client):
        """Test login without password."""
        login_data = {
            "username": "user@example.com"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_empty_credentials(self, client):
        """Test login with empty credentials."""
        login_data = {
            "username": "",
            "password": ""
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_case_insensitive_email(self, client, test_user):
        """Test login with different email case."""
        login_data = {
            "username": test_user.email.upper(),
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        # Should succeed (email lookup should be case-insensitive)
        assert response.status_code == status.HTTP_200_OK
    
    def test_login_with_json_body(self, client, test_user):
        """Test that login requires form data, not JSON."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword"
        }
        
        # Try sending as JSON (should fail)
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTokenValidation:
    """Test token validation in protected endpoints."""
    
    def test_protected_endpoint_with_valid_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/api/v1/users/profile", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "email" in data
        assert "id" in data
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/users/profile")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/users/profile", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_protected_endpoint_with_expired_token(self, client, test_user):
        """Test accessing protected endpoint with expired token."""
        from datetime import timedelta
        from app.core.security import create_access_token
        
        # Create expired token
        expired_token = create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/api/v1/users/profile", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_protected_endpoint_with_malformed_auth_header(self, client):
        """Test various malformed authorization headers."""
        malformed_headers = [
            {"Authorization": "invalid_format"},
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "Basic dGVzdA=="},  # Wrong scheme
            {"Authorization": ""},  # Empty value
        ]
        
        for headers in malformed_headers:
            response = client.get("/api/v1/users/profile", headers=headers)
            assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_protected_endpoint_with_inactive_user_token(self, client, inactive_user):
        """Test protected endpoint with token for inactive user."""
        from app.core.security import create_access_token
        
        token = create_access_token(data={"sub": str(inactive_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/users/profile", headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Inactive user account" in response.json()["detail"]
    
    def test_protected_endpoint_with_nonexistent_user_token(self, client):
        """Test protected endpoint with token for non-existent user."""
        import uuid
        from app.core.security import create_access_token
        
        fake_user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": fake_user_id})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/users/profile", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthenticationFlow:
    """Test complete authentication flows."""
    
    def test_register_then_login_flow(self, client):
        """Test complete flow: register -> login -> access protected endpoint."""
        # Step 1: Register
        user_data = {
            "email": "flowtest@example.com",
            "password": "FlowTestPassword123!",
            "first_name": "Flow",
            "last_name": "Test"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # Step 2: Login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        token = login_response.json()["access_token"]
        
        # Step 3: Access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = client.get("/api/v1/users/profile", headers=headers)
        
        assert profile_response.status_code == status.HTTP_200_OK
        profile_data = profile_response.json()
        assert profile_data["email"] == user_data["email"]
    
    def test_token_reuse(self, client, test_user):
        """Test that token can be reused for multiple requests."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make multiple requests with same token
        for _ in range(3):
            response = client.get("/api/v1/users/profile", headers=headers)
            assert response.status_code == status.HTTP_200_OK
    
    def test_concurrent_logins(self, client, test_user):
        """Test multiple concurrent login attempts."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword"
        }
        
        # Multiple login requests should all succeed
        responses = []
        for _ in range(3):
            response = client.post("/api/v1/auth/login", data=login_data)
            responses.append(response)
        
        # All should succeed and return valid tokens
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            token = response.json()["access_token"]
            
            # Each token should work
            headers = {"Authorization": f"Bearer {token}"}
            profile_response = client.get("/api/v1/users/profile", headers=headers)
            assert profile_response.status_code == status.HTTP_200_OK


class TestAuthenticationSecurity:
    """Test security aspects of authentication."""
    
    def test_password_not_returned_in_responses(self, client):
        """Test that password/hash is never returned in API responses."""
        user_data = {
            "email": "securitytest@example.com",
            "password": "SecurityTestPassword123!",
            "first_name": "Security",
            "last_name": "Test"
        }
        
        # Register user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        register_data = register_response.json()
        
        # Check registration response
        assert "password" not in register_data["user"]
        assert "password_hash" not in register_data["user"]
        
        # Login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        login_data_response = login_response.json()
        
        # Check login response
        assert "password" not in login_data_response["user"]
        assert "password_hash" not in login_data_response["user"]
        
        # Get profile
        token = login_data_response["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = client.get("/api/v1/users/profile", headers=headers)
        profile_data = profile_response.json()
        
        # Check profile response
        assert "password" not in profile_data
        assert "password_hash" not in profile_data
    
    def test_timing_attack_resistance(self, client, test_user):
        """Test that login timing doesn't reveal user existence."""
        import time
        
        # Time login with valid user, wrong password
        start = time.time()
        response1 = client.post("/api/v1/auth/login", data={
            "username": test_user.email,
            "password": "wrongpassword"
        })
        time1 = time.time() - start
        
        # Time login with non-existent user
        start = time.time()
        response2 = client.post("/api/v1/auth/login", data={
            "username": "nonexistent@example.com",
            "password": "somepassword"
        })
        time2 = time.time() - start
        
        # Both should return 401
        assert response1.status_code == status.HTTP_401_UNAUTHORIZED
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Times should be relatively similar (within reasonable bounds)
        # This is a basic check - in production you'd want more sophisticated timing analysis
        time_diff = abs(time1 - time2)
        assert time_diff < 1.0  # Should complete within similar timeframes
