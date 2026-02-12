"""
Application configuration using Pydantic Settings
Loads from environment variables with validation
"""

import logging
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_startup_logger = logging.getLogger("codeforge.config")


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
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""  # Service role key - never expose to client
    SUPABASE_JWT_SECRET: str = ""  # JWT secret for verifying user tokens

    # LLM API Keys - loaded from env, never hard-coded
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Redis (Optional — set to empty string to disable)
    REDIS_URL: Optional[str] = "redis://localhost:6379"

    # Celery (Optional - uses Redis as broker by default)
    CELERY_BROKER_URL: Optional[str] = None  # Defaults to REDIS_URL if not set
    CELERY_RESULT_BACKEND: Optional[str] = None  # Defaults to REDIS_URL if not set

    # CORS - HTTPS only in production
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Dev frontend
        "http://127.0.0.1:3000",  # Dev frontend (IP)
        "https://codeforge.ai",  # Production frontend
    ]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Agent timeouts (seconds)
    AGENT_TIMEOUT: int = 300  # 5 minutes max

    # LangGraph recursion limits
    MAX_AGENT_ITERATIONS: int = 5

    @model_validator(mode="after")
    def _validate_startup(self) -> "Settings":
        """
        Fail-fast validation on startup.
        In production, missing required keys raise immediately.
        In dev/test, log warnings so local runs still work.
        """
        # Celery broker defaults to Redis URL when not explicitly set
        if not self.CELERY_BROKER_URL and self.REDIS_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND and self.REDIS_URL:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL

        if self.ENVIRONMENT == "test":
            return self

        # Critical infrastructure keys
        critical = {
            "SUPABASE_URL": self.SUPABASE_URL,
            "SUPABASE_SERVICE_KEY": self.SUPABASE_SERVICE_KEY,
            "SUPABASE_JWT_SECRET": self.SUPABASE_JWT_SECRET,
        }
        # LLM API keys
        llm_keys = {
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "GOOGLE_API_KEY": self.GOOGLE_API_KEY,
            "ANTHROPIC_API_KEY": self.ANTHROPIC_API_KEY,
        }

        missing_critical = [k for k, v in critical.items() if not v]
        missing_llm = [k for k, v in llm_keys.items() if not v]

        if self.ENVIRONMENT == "production":
            if missing_critical:
                raise ValueError(
                    f"Missing required secrets for production: {', '.join(missing_critical)}"
                )
            if missing_llm:
                raise ValueError(
                    f"Missing LLM API keys for production: {', '.join(missing_llm)}"
                )
        else:
            # Development — warn but don't block
            for k in missing_critical:
                _startup_logger.warning(f"⚠ {k} is not set — some features will fail")
            for k in missing_llm:
                _startup_logger.warning(
                    f"⚠ {k} is not set — {k.replace('_API_KEY', '').lower()} agents will fail"
                )

        return self


settings = Settings()
