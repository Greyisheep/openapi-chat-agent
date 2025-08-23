"""Authentication routes for user registration, login, and token management."""

from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    store_token,
    revoke_token,
    AuthError,
    oauth2_scheme,
)
from app.utils.security import encrypt_api_key, decrypt_api_key
from app.core.config import settings
from app.database.config import get_db
from app.database.models.user import User
from app.models.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    ChangePassword,
    UpdateProfile,
    ApiKeyRequest,
    ApiKeyResponse,
)


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Register a new user."""
    
    # Check if user already exists
    existing_user = await db.execute(
        select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
    )
    
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Authenticate user and return access token."""
    
    # Authenticate user (form_data.username can be email or username)
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    # Store token in database (optional - for revocation)
    await store_token(db, str(user.id), access_token, "access")
    await store_token(
        db, 
        str(user.id), 
        refresh_token, 
        "refresh",
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=Token)
async def login_user(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Alternative login endpoint with JSON body."""
    
    user = await authenticate_user(db, user_data.email_or_username, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password"
        )
    
    # Create tokens (same logic as token endpoint)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    # Store tokens
    await store_token(db, str(user.id), access_token, "access")
    await store_token(
        db, 
        str(user.id), 
        refresh_token, 
        "refresh",
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout_user(
    token: str = Depends(lambda: oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Logout user by revoking their token."""
    
    # Revoke the current token
    await revoke_token(db, token)
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user information."""
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_data: UpdateProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Update current user profile."""
    
    # Check if new email/username already exists (if changed)
    if user_data.email and user_data.email != current_user.email:
        existing_user = await db.execute(
            select(User).where(User.email == user_data.email, User.id != current_user.id)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_data.email
    
    if user_data.username and user_data.username != current_user.username:
        existing_user = await db.execute(
            select(User).where(User.username == user_data.username, User.id != current_user.id)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_data.username
    
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Change user password."""
    
    # Verify current password
    from app.core.auth import verify_password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/api-keys/gemini")
async def set_gemini_api_key(
    api_key_data: ApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Set user's Gemini API key."""
    
    # Encrypt and store the API key
    encrypted_key = encrypt_api_key(api_key_data.gemini_api_key)
    current_user.gemini_api_key_encrypted = encrypted_key
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Gemini API key set successfully"}


@router.get("/api-keys", response_model=ApiKeyResponse)
async def get_api_key_status(
    current_user: User = Depends(get_current_user)
) -> ApiKeyResponse:
    """Get user's API key configuration status."""
    
    return ApiKeyResponse(
        has_gemini_api_key=bool(current_user.gemini_api_key_encrypted),
        platform_api_key=current_user.platform_api_key,
        created_at=current_user.created_at
    )


@router.delete("/api-keys/gemini")
async def remove_gemini_api_key(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Remove user's Gemini API key."""
    
    current_user.gemini_api_key_encrypted = None
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Gemini API key removed successfully"}


@router.post("/api-keys/platform/generate")
async def generate_platform_api_key(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Generate a platform API key for external use."""
    
    import secrets
    import string
    
    # Generate a secure random API key
    alphabet = string.ascii_letters + string.digits
    platform_key = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    current_user.platform_api_key = f"oak_{platform_key}"  # oak = OpenAPI Chat Agent
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "platform_api_key": current_user.platform_api_key,
        "message": "Platform API key generated successfully"
    }
