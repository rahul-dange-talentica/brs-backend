"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
import re


class UserRegister(BaseModel):
    """User registration request schema."""
    
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength according to security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields."""
        if not v or not v.strip():
            raise ValueError('Name fields cannot be empty')
        if len(v.strip()) > 100:
            raise ValueError('Name fields must be 100 characters or less')
        return v.strip()


class UserLogin(BaseModel):
    """User login request schema."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")


class Token(BaseModel):
    """Token response schema."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")


class TokenRefresh(BaseModel):
    """Token refresh request schema."""
    
    refresh_token: str = Field(..., description="JWT refresh token")


class TokenData(BaseModel):
    """Token payload data schema."""
    
    user_id: Optional[str] = Field(None, description="User ID from token")
    email: Optional[str] = Field(None, description="User email from token")


class UserResponse(BaseModel):
    """User response schema (without sensitive data)."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    is_active: bool = Field(..., description="User active status")
    created_at: str = Field(..., description="User creation timestamp")
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response schema with token and user data."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserResponse = Field(..., description="User information")


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password_strength(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
