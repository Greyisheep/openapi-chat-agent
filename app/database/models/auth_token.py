"""Authentication token model for JWT token management."""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database.config import Base


class AuthToken(Base):
    """Authentication token model for managing JWT tokens."""
    
    __tablename__ = "auth_tokens"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Token data
    token_hash = Column(String(255), unique=True, nullable=False, index=True)  # Hashed token for security
    token_type = Column(String(50), default="bearer", nullable=False)  # bearer, refresh, etc.
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Token metadata
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional token data (for refresh tokens, etc.)
    scope = Column(String(255), nullable=True)  # Token permissions/scope
    user_agent = Column(Text, nullable=True)  # Browser/client info
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 address
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="auth_tokens")
    
    def __repr__(self) -> str:
        return f"<AuthToken(id={self.id}, user_id={self.user_id}, token_type={self.token_type}, is_revoked={self.is_revoked})>"
