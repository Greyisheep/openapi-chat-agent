from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
	API_HOST: str = "0.0.0.0"
	API_PORT: int = 8000
	DEBUG: bool = False

	SECRET_KEY: str = "dev-secret-key"
	ALGORITHM: str = "HS256"

	ADK_MODEL_PROVIDER: str = "gemini"
	ADK_MODEL_NAME: str = "gemini-2.5-flash"
	ADK_API_KEY: Optional[str] = None

	REDIS_URL: Optional[str] = None
	LOG_LEVEL: str = "INFO"

	class Config:
		env_file = ".env"


settings = Settings()




