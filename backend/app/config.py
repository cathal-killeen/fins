"""
Application configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Fins"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fins"
    DUCKDB_PATH: str = "./analytics.duckdb"

    # Security
    SECRET_KEY: str = "change-this-to-a-random-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ADMIN_USERNAME: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI / LLM Configuration
    LLM_PROVIDER: str = "anthropic"  # anthropic, openai, azure, bedrock, etc.
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    LLM_API_KEY: str = ""  # Provider-specific API key
    LLM_API_BASE: Optional[str] = None  # For custom endpoints
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    # Legacy support
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Prefect
    PREFECT_API_URL: Optional[str] = None
    PREFECT_API_KEY: Optional[str] = None

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    TEMP_UPLOAD_DIR: str = "/tmp/fins-uploads"
    SUPPORTED_FILE_TYPES: list[str] = ["csv", "pdf"]
    PROCESSING_TIMEOUT: int = 300  # 5 minutes

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
