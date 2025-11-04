"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Project
    PROJECT_NAME: str = "Personal Finance AI Platform"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/personalfinance"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Plaid
    PLAID_CLIENT_ID: str = os.getenv("PLAID_CLIENT_ID", "")
    PLAID_SECRET: str = os.getenv("PLAID_SECRET", "")
    PLAID_ENV: str = os.getenv("PLAID_ENV", "sandbox")
    
    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")
    
    # Alpha Vantage
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY", None)
    
    # CORS
    _cors_origins_env = os.getenv("BACKEND_CORS_ORIGINS", "")
    if _cors_origins_env:
        # Parse from environment variable if provided
        BACKEND_CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_origins_env.split(",")]
    else:
        # Default origins
        BACKEND_CORS_ORIGINS: List[str] = [
            "http://localhost:3000",
            "http://localhost:3001",  # Docker frontend port
            "http://localhost:8080",
            "http://localhost:5173",
        ]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Model paths
    MODEL_CHECKPOINT_DIR: str = "/app/models/checkpoints"
    MODEL_ARTIFACT_DIR: str = "/app/models/artifacts"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

