"""Pydantic models for authentication and user management."""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Union
from datetime import datetime
import re


class UserRegister(BaseModel):
    """User registration data."""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase, lowercase, digit, and special character
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v


class UserLogin(BaseModel):
    """User login data."""
    
    email_or_username: str = Field(..., description="Email address or username")
    password: str = Field(..., description="Password")


class Token(BaseModel):
    """Authentication token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token payload data."""
    
    user_id: Optional[str] = None
    username: Optional[str] = None
    scopes: list[str] = Field(default_factory=list)


class UserResponse(BaseModel):
    """User information response."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="Email address")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(..., description="Account active status")
    is_verified: bool = Field(..., description="Email verification status")
    created_at: datetime = Field(..., description="Account creation date")
    last_login: Optional[datetime] = Field(None, description="Last login date")
    
    class Config:
        from_attributes = True


class UpdateProfile(BaseModel):
    """User profile update data."""
    
    email: Optional[EmailStr] = Field(None, description="New email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="New username")
    full_name: Optional[str] = Field(None, max_length=255, description="New full name")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username format."""
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v


class ChangePassword(BaseModel):
    """Password change data."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase, lowercase, digit, and special character
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v


class ApiKeyRequest(BaseModel):
    """Request to set user's Gemini API key."""
    
    gemini_api_key: str = Field(..., description="User's Gemini API key")
    
    @field_validator('gemini_api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        v = v.strip()
        if not v:
            raise ValueError('API key cannot be empty')
        
        # Basic validation - Google API keys usually start with specific patterns
        if not (v.startswith('AIza') or v.startswith('Google')):
            raise ValueError('Invalid Gemini API key format')
        
        return v


class ApiKeyResponse(BaseModel):
    """API key configuration response."""
    
    has_gemini_api_key: bool = Field(..., description="Whether user has configured their Gemini API key")
    platform_api_key: Optional[str] = Field(None, description="Platform-generated API key for external use")
    created_at: Optional[datetime] = Field(None, description="When the API key was set")
    
    class Config:
        from_attributes = True
