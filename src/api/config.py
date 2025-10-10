"""
API Gateway Configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "NFL Predictor API Gateway"
    version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database (Supabase)
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_ttl_experts: int = 60
    redis_ttl_bets: int = 10
    redis_ttl_predictions: int = 120
    redis_ttl_council: int = 3600
    redis_ttl_games: int = 300

    # Rate Limiting
    rate_limit_experts: str = "100/minute"
    rate_limit_predictions: str = "150/minute"
    rate_limit_bets: str = "300/minute"
    rate_limit_council: str = "200/minute"
    rate_limit_games: str = "200/minute"

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_reconnect_max_delay: int = 16

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Run ID for experimental isolation
    run_id: str = "run_2025_pilot4"

    def get_run_id(self) -> str:
        """Get the current run ID for experimental isolation"""
        return self.run_id

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
