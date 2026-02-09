"""
Application configuration using Pydantic Settings
Loads from environment variables with validation
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Application settings with secure defaults
    All secrets loaded from environment variables
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str  # Service role key - never expose to client

    # LLM API Keys - loaded from env, never hard-coded
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    ANTHROPIC_API_KEY: str

    # Redis (Optional)
    REDIS_URL: str = "redis://localhost:6379"

    # CORS - HTTPS only in production
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Dev frontend
        "https://codeforge.ai",  # Production frontend
    ]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Agent timeouts (seconds)
    AGENT_TIMEOUT: int = 300  # 5 minutes max

    # LangGraph recursion limits
    MAX_AGENT_ITERATIONS: int = 5


settings = Settings()
