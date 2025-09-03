import pytest
import uuid
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import get_current_user, get_current_active_user, get_optional_current_user
from app.core.security import create_access_token


class TestGetCurrentUser:
    """Test get_current_user authentication function."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, db_session, test_user):
        """Test getting current user with valid token."""
        # Create valid token
        token = create_access_token(data={"sub": str(test_user.id)})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        user = await get_current_user(credentials, db_session)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session):
        """Test getting current user with invalid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
        
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, db_session, test_user):
        """Test getting current user with expired token."""
        from datetime import timedelta
        
        # Create expired token
        token = create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1)
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
        
    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, db_session):
        """Test getting current user with token for non-existent user."""
        fake_user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": fake_user_id})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
        
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_user_id_format(self, db_session):
        """Test getting current user with invalid user ID format."""
        token = create_access_token(data={"sub": "not_a_uuid"})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
        
    @pytest.mark.asyncio
    async def test_get_current_user_no_sub_claim(self, db_session):
        """Test getting current user with token missing sub claim."""
        token = create_access_token(data={"user": "test@example.com"})  # Wrong claim
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401


class TestGetCurrentActiveUser:
    """Test get_current_active_user function."""
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_active(self, test_user):
        """Test getting current active user with active user."""
        user = await get_current_active_user(test_user)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.is_active is True
        
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self, inactive_user):
        """Test getting current active user with inactive user."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(inactive_user)
        
        assert exc_info.value.status_code == 400
        assert "Inactive user account" in exc_info.value.detail


class TestGetOptionalCurrentUser:
    """Test get_optional_current_user function."""
    
    def test_get_optional_current_user_valid_token(self, db_session, test_user):
        """Test getting optional current user with valid token."""
        token = create_access_token(data={"sub": str(test_user.id)})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        user = get_optional_current_user(credentials, db_session)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        
    def test_get_optional_current_user_no_credentials(self, db_session):
        """Test getting optional current user with no credentials."""
        user = get_optional_current_user(None, db_session)
        
        assert user is None
        
    def test_get_optional_current_user_invalid_token(self, db_session):
        """Test getting optional current user with invalid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )
        
        user = get_optional_current_user(credentials, db_session)
        
        assert user is None
        
    def test_get_optional_current_user_nonexistent_user(self, db_session):
        """Test getting optional current user with token for non-existent user."""
        fake_user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": fake_user_id})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        user = get_optional_current_user(credentials, db_session)
        
        assert user is None
        
    def test_get_optional_current_user_inactive_user(self, db_session, inactive_user):
        """Test getting optional current user with inactive user."""
        token = create_access_token(data={"sub": str(inactive_user.id)})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        user = get_optional_current_user(credentials, db_session)
        
        assert user is None  # Should return None for inactive users
        
    def test_get_optional_current_user_invalid_uuid(self, db_session):
        """Test getting optional current user with invalid UUID."""
        token = create_access_token(data={"sub": "not_a_uuid"})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        user = get_optional_current_user(credentials, db_session)
        
        assert user is None
        
    def test_get_optional_current_user_no_sub_claim(self, db_session):
        """Test getting optional current user with token missing sub claim."""
        token = create_access_token(data={"user": "test@example.com"})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        user = get_optional_current_user(credentials, db_session)
        
        assert user is None
