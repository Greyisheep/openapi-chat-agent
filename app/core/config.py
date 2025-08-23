from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
	# API Configuration
	API_HOST: str = "0.0.0.0"
	API_PORT: int = 8000
	DEBUG: bool = False

	# Security Configuration
	SECRET_KEY: str = "dev-secret-key-change-in-production"
	ALGORITHM: str = "HS256"
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
	REFRESH_TOKEN_EXPIRE_DAYS: int = 7

	# Database Configuration
	DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/openapi_chat_agent"
	DATABASE_ECHO: bool = False

	# Google ADK Configuration
	ADK_MODEL_PROVIDER: str = "gemini"
	ADK_MODEL_NAME: str = "gemini-2.5-flash"
	ADK_API_KEY: Optional[str] = None  # Platform fallback key

	# External Services
	REDIS_URL: Optional[str] = None
	LOG_LEVEL: str = "INFO"

	# Authentication Configuration
	BCRYPT_ROUNDS: int = 12
	JWT_ISSUER: str = "openapi-chat-agent"
	JWT_AUDIENCE: str = "openapi-chat-agent-users"

	# Platform Configuration
	PLATFORM_NAME: str = "OpenAPI Chat Agent"
	PLATFORM_VERSION: str = "1.0.0"
	ADMIN_EMAIL: str = "admin@example.com"

	class Config:
		env_file = ".env"
		env_file_encoding = "utf-8"


settings = Settings()





