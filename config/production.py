"""
Production configuration for NFL Predictor API.
Handles environment variables, API keys, and production settings.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class APIKeyConfig:
    """Configuration for API keys and authentication"""
    odds_api_key: Optional[str]
    sportsdata_io_key: Optional[str]
    rapid_api_key: Optional[str]
    api_secret_key: Optional[str]
    
    def validate_primary_keys(self) -> bool:
        """Validate that primary API keys are present"""
        return bool(self.odds_api_key and self.sportsdata_io_key)
    
    def get_missing_keys(self) -> list[str]:
        """Get list of missing required API keys"""
        missing = []
        if not self.odds_api_key:
            missing.append("ODDS_API_KEY")
        if not self.sportsdata_io_key:
            missing.append("SPORTSDATA_IO_KEY")
        return missing


@dataclass
class CacheConfig:
    """Configuration for Redis caching"""
    redis_url: str
    redis_password: Optional[str]
    redis_db: int
    ttl_minutes: int
    max_memory: str
    
    def get_redis_connection_params(self) -> Dict[str, Any]:
        """Get Redis connection parameters"""
        params = {
            "url": self.redis_url,
            "db": self.redis_db,
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "retry_on_timeout": True,
            "health_check_interval": 30
        }
        
        if self.redis_password:
            params["password"] = self.redis_password
            
        return params


@dataclass
class RateLimitConfig:
    """Configuration for API rate limiting"""
    odds_api_limit: int
    sportsdata_io_limit: int
    espn_api_limit: int
    nfl_api_limit: int
    rapid_api_limit: int
    
    def get_limits_dict(self) -> Dict[str, int]:
        """Get rate limits as dictionary"""
        return {
            "odds_api": self.odds_api_limit,
            "sportsdata_io": self.sportsdata_io_limit,
            "espn_api": self.espn_api_limit,
            "nfl_api": self.nfl_api_limit,
            "rapid_api": self.rapid_api_limit
        }


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and health checks"""
    health_check_interval: int
    monitoring_enabled: bool
    log_level: str
    
    def get_log_level_int(self) -> int:
        """Convert log level string to integer"""
        levels = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50
        }
        return levels.get(self.log_level.upper(), 20)


@dataclass
class SecurityConfig:
    """Configuration for security settings"""
    cors_origins: list[str]
    allowed_hosts: list[str]
    api_base_url: str
    
    def get_cors_origins_list(self) -> list[str]:
        """Get CORS origins as list"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins
    
    def get_allowed_hosts_list(self) -> list[str]:
        """Get allowed hosts as list"""
        if isinstance(self.allowed_hosts, str):
            return [host.strip() for host in self.allowed_hosts.split(",")]
        return self.allowed_hosts


class ProductionConfig:
    """
    Main production configuration class.
    Loads and validates all configuration from environment variables.
    """
    
    def __init__(self):
        self.environment = Environment(os.getenv("ENVIRONMENT", "development"))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Load all configuration sections
        self.api_keys = self._load_api_keys()
        self.cache = self._load_cache_config()
        self.rate_limits = self._load_rate_limit_config()
        self.monitoring = self._load_monitoring_config()
        self.security = self._load_security_config()
        
        # Validate configuration
        self._validate_config()
    
    def _load_api_keys(self) -> APIKeyConfig:
        """Load API key configuration from environment"""
        return APIKeyConfig(
            odds_api_key=os.getenv("ODDS_API_KEY"),
            sportsdata_io_key=os.getenv("SPORTSDATA_IO_KEY"),
            rapid_api_key=os.getenv("RAPID_API_KEY"),
            api_secret_key=os.getenv("API_SECRET_KEY")
        )
    
    def _load_cache_config(self) -> CacheConfig:
        """Load cache configuration from environment"""
        return CacheConfig(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            redis_password=os.getenv("REDIS_PASSWORD"),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            ttl_minutes=int(os.getenv("CACHE_TTL_MINUTES", "30")),
            max_memory=os.getenv("CACHE_MAX_MEMORY", "256mb")
        )
    
    def _load_rate_limit_config(self) -> RateLimitConfig:
        """Load rate limit configuration from environment"""
        return RateLimitConfig(
            odds_api_limit=int(os.getenv("ODDS_API_RATE_LIMIT", "500")),
            sportsdata_io_limit=int(os.getenv("SPORTSDATA_IO_RATE_LIMIT", "1000")),
            espn_api_limit=int(os.getenv("ESPN_API_RATE_LIMIT", "1000")),
            nfl_api_limit=int(os.getenv("NFL_API_RATE_LIMIT", "500")),
            rapid_api_limit=int(os.getenv("RAPID_API_RATE_LIMIT", "100"))
        )
    
    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration from environment"""
        return MonitoringConfig(
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "300")),
            monitoring_enabled=os.getenv("MONITORING_ENABLED", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration from environment"""
        cors_origins = os.getenv("CORS_ORIGINS", "*")
        allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost")
        
        return SecurityConfig(
            cors_origins=cors_origins.split(",") if cors_origins != "*" else ["*"],
            allowed_hosts=allowed_hosts.split(","),
            api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000")
        )
    
    def _validate_config(self):
        """Validate configuration and raise errors for missing required values"""
        errors = []
        
        # Validate API keys in production
        if self.environment == Environment.PRODUCTION:
            missing_keys = self.api_keys.get_missing_keys()
            if missing_keys:
                errors.append(f"Missing required API keys: {', '.join(missing_keys)}")
        
        # Validate Redis URL format
        if not self.cache.redis_url.startswith(("redis://", "rediss://")):
            errors.append("REDIS_URL must start with redis:// or rediss://")
        
        # Validate security settings in production
        if self.environment == Environment.PRODUCTION:
            if "*" in self.security.cors_origins:
                errors.append("CORS_ORIGINS should not include '*' in production")
            
            if not self.security.api_base_url.startswith("https://"):
                errors.append("API_BASE_URL should use HTTPS in production")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT
    
    def get_api_config_dict(self) -> Dict[str, Any]:
        """Get API configuration as dictionary for client manager"""
        return {
            "primary_sources": {
                "odds_api": {
                    "base_url": "https://api.the-odds-api.com/v4",
                    "api_key": self.api_keys.odds_api_key,
                    "rate_limit": self.rate_limits.odds_api_limit,
                    "timeout": 30
                },
                "sportsdata_io": {
                    "base_url": "https://api.sportsdata.io/v3/nfl",
                    "api_key": self.api_keys.sportsdata_io_key,
                    "rate_limit": self.rate_limits.sportsdata_io_limit,
                    "timeout": 30
                }
            },
            "fallback_sources": {
                "espn_api": {
                    "base_url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl",
                    "rate_limit": self.rate_limits.espn_api_limit,
                    "timeout": 20
                },
                "nfl_api": {
                    "base_url": "https://api.nfl.com/v1",
                    "rate_limit": self.rate_limits.nfl_api_limit,
                    "timeout": 20
                },
                "rapid_api": {
                    "base_url": "https://api-american-football.p.rapidapi.com",
                    "api_key": self.api_keys.rapid_api_key,
                    "rate_limit": self.rate_limits.rapid_api_limit,
                    "timeout": 25
                }
            },
            "cache_config": {
                "ttl_minutes": self.cache.ttl_minutes,
                "max_retries": 3,
                "backoff_factor": 2.0
            }
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging/debugging"""
        return {
            "environment": self.environment.value,
            "debug": self.debug,
            "api_keys_configured": {
                "odds_api": bool(self.api_keys.odds_api_key),
                "sportsdata_io": bool(self.api_keys.sportsdata_io_key),
                "rapid_api": bool(self.api_keys.rapid_api_key)
            },
            "cache": {
                "redis_url": self.cache.redis_url,
                "ttl_minutes": self.cache.ttl_minutes,
                "max_memory": self.cache.max_memory
            },
            "rate_limits": self.rate_limits.get_limits_dict(),
            "monitoring": {
                "enabled": self.monitoring.monitoring_enabled,
                "log_level": self.monitoring.log_level,
                "health_check_interval": self.monitoring.health_check_interval
            },
            "security": {
                "cors_origins": self.security.cors_origins,
                "api_base_url": self.security.api_base_url
            }
        }


# Global configuration instance
config = ProductionConfig()


def get_config() -> ProductionConfig:
    """Get the global configuration instance"""
    return config


def reload_config() -> ProductionConfig:
    """Reload configuration from environment variables"""
    global config
    config = ProductionConfig()
    return config