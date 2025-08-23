"""Authentication utilities for JWT tokens and password hashing."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.config import get_db
from app.database.models.user import User
from app.database.models.auth_token import AuthToken
from sqlalchemy import select


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
bearer_scheme = HTTPBearer(auto_error=False)


class AuthError(HTTPException):
    """Custom authentication error."""
    
    def __init__(self, detail: str = "Authentication failed", status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "type": "access"
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "type": "refresh"
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )
        return payload
    except JWTError as e:
        raise AuthError(f"Invalid token: {str(e)}")


def hash_token(token: str) -> str:
    """Create a hash of the token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email_or_username: str, password: str) -> Optional[User]:
    """Authenticate a user with email/username and password."""
    # Try to find user by email first, then username
    user = await get_user_by_email(db, email_or_username)
    if not user:
        user = await get_user_by_username(db, email_or_username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    return user


async def store_token(db: AsyncSession, user_id: str, token: str, token_type: str = "bearer", **kwargs) -> AuthToken:
    """Store a token hash in the database."""
    token_hash = hash_token(token)
    
    # Set default expires_at if not provided
    if 'expires_at' not in kwargs:
        kwargs['expires_at'] = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    auth_token = AuthToken(
        user_id=user_id,
        token_hash=token_hash,
        token_type=token_type,
        **kwargs
    )
    
    db.add(auth_token)
    await db.commit()
    await db.refresh(auth_token)
    
    return auth_token


async def revoke_token(db: AsyncSession, token: str) -> bool:
    """Revoke a token by marking it as revoked."""
    token_hash = hash_token(token)
    
    result = await db.execute(
        select(AuthToken).where(
            AuthToken.token_hash == token_hash,
            AuthToken.is_revoked == False
        )
    )
    
    auth_token = result.scalar_one_or_none()
    if not auth_token:
        return False
    
    auth_token.is_revoked = True
    await db.commit()
    return True


async def is_token_revoked(db: AsyncSession, token: str) -> bool:
    """Check if a token is revoked."""
    token_hash = hash_token(token)
    
    result = await db.execute(
        select(AuthToken).where(
            AuthToken.token_hash == token_hash
        )
    )
    
    auth_token = result.scalar_one_or_none()
    if not auth_token:
        return True  # Token not found = considered revoked
    
    return auth_token.is_revoked


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    
    # Check if token is revoked
    if await is_token_revoked(db, token):
        raise AuthError("Token has been revoked")
    
    # Decode token
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthError("Invalid token payload")
    except AuthError:
        raise
    except Exception as e:
        raise AuthError(f"Token decode error: {str(e)}")
    
    # Get user from database
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise AuthError("User not found")
    
    if not user.is_active:
        raise AuthError("User account is disabled")
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (additional check)."""
    if not current_user.is_active:
        raise AuthError("User account is disabled")
    return current_user
