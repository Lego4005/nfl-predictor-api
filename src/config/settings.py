"""Settings configuration for NFL Predictor API"""

import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables"""

    # Expert Council Betting System Configuration
    RUN_ID: str = os.getenv("RUN_ID", "run_2025_pilot4")
    EXPERT_COUNCIL_ENABLED: bool = os.getenv("EXPERT_COUNCIL_ENABLED", "true").lower() == "true"

    # Memory Retrieval Configuration
    MEMORY_RETRIEVAL_TIMEOUT_MS: int = int(os.getenv("MEMORY_RETRIEVAL_TIMEOUT_MS", "5000"))
    DEFAULT_MEMORY_K: int = int(os.getenv("DEFAULT_MEMORY_K", "15"))
    MIN_MEMORY_K: int = int(os.getenv("MIN_MEMORY_K", "10"))
    MAX_MEMORY_K: int = int(os.getenv("MAX_MEMORY_K", "20"))

    # Database Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")

    # LLM Provider Configuration
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Performance Configuration
    MAX_PARALLEL_EXPERTS: int = int(os.getenv("MAX_PARALLEL_EXPERTS", "8"))
    EXPERT_TIMEOUT_MS: int = int(os.getenv("EXPERT_TIMEOUT_MS", "30000"))

    # Feature Flags
    ENABLE_SHADOW_RUNS: bool = os.getenv("ENABLE_SHADOW_RUNS", "false").lower() == "true"
    ENABLE_POST_GAME_REFLECTION: bool = os.getenv("ENABLE_POST_GAME_REFLECTION", "false").lower() == "true"

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info").upper()

    @classmethod
    def get_run_id(cls) -> str:
        """Get the current run ID for experimental isolation"""
        return cls.RUN_ID

    @classmethod
    def is_expert_council_enabled(cls) -> bool:
        """Check if expert council system is enabled"""
        return cls.EXPERT_COUNCIL_ENABLED

    @classmethod
    def get_memory_config(cls) -> dict:
        """Get memory retrieval configuration"""
        return {
            "timeout_ms": cls.MEMORY_RETRIEVAL_TIMEOUT_MS,
            "default_k": cls.DEFAULT_MEMORY_K,
            "min_k": cls.MIN_MEMORY_K,
            "max_k": cls.MAX_MEMORY_K
        }


# Global settings instance
settings = Settings()
