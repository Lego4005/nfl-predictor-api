"""
Configuration settings for the NFL prediction system
"""

import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables"""

    # Database settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # Expert system settings
    MAX_STAKE_UNITS_PER_BET: float = float(os.getenv("MAX_STAKE_UNITS_PER_BET", "10.0"))
    MAX_TOTAL_STAKE_PER_GAME: float = float(os.getenv("MAX_TOTAL_STAKE_PER_GAME", "100.0"))

    # Memory retrieval settings
    DEFAULT_MEMORY_K: int = int(os.getenv("DEFAULT_MEMORY_K", "15"))
    MAX_MEMORY_K: int = int(os.getenv("MAX_MEMORY_K", "20"))
    MIN_MEMORY_K: int = int(os.getenv("MIN_MEMORY_K", "10"))

    # LLM settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # Agentuity settings
    AGENTUITY_API_KEY: Optional[str] = os.getenv("AGENTUITY_API_KEY")
    AGENTUITY_BASE_URL: str = os.getenv("AGENTUITY_BASE_URL", "https://api.agentuity.com")

    # Validation settings
    SCHEMA_VALIDATION_ENABLED: bool = os.getenv("SCHEMA_VALIDATION_ENABLED", "true").lower() == "true"
    STRICT_CATEGORY_VALIDATION: bool = os.getenv("STRICT_CATEGORY_VALIDATION", "true").lower() == "true"

    # Performance settings
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    MEMORY_RETRIEVAL_TIMEOUT_SECONDS: int = int(os.getenv("MEMORY_RETRIEVAL_TIMEOUT_SECONDS", "5"))

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"


# Global settings instance
settings = Settings()
