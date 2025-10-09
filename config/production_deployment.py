"""
Enhanced Production Deployment Configuration for NFL Expert Prediction Syste
Handles database connections, vector search optimization, API key management,
rate limiting, monitoring, and logging for production troubleshooting.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import redis
import asyncpg
from contextlib import asynccontextmanager


class DeploymentEnvironment(Enum):
    """Deployment environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DatabaseConfig:
    """Database connection and optimization configuration"""
    url: str
    min_pool_size: int = 10
    max_pool_size: int = 50
    query_timeout: int = 60
    slow_query_threshold: float = 2.0
    enable_query_logging: bool = True
    max_queries: int = 100000
    max_inactive_lifetime: int = 600
    statement_cache_size: int = 2048
    prepared_cache_size: int = 200

    def get_connection_params(self) -> Dict[str, Any]:
        """Get database connection parameters"""
        return {
            "dsn": self.url,
            "min_size": self.min_pool_size,
            "max_size": self.max_pool_size,
            "command_timeout": self.query_timeout,
            "max_queries": self.max_queries,
            "max_inactive_connection_lifetime": self.max_inactive_lifetime,
            "statement_cache_size": self.statement_cache_size,
            "prepared_statement_cache_size": self.prepared_cache_size
        }


@dataclass
class VectorSearchConfig:
    """Vector search optimization configuration"""
    embedding_model: str = "text-embedding-3-small"
    similarity_threshold: float = 0.7
    max_results: int = 50
    enable_indexing: bool = True
    index_type: str = "ivfflat"
    index_lists: int = 100
    probes: int = 10
    maintenance_interval: int = 3600  # seconds

    def get_pgvector_params(self) -> Dict[str, Any]:
        """Get pgvector optimization parameters"""
        return {
            "similarity_threshold": self.similarity_threshold,
            "max_results": self.max_results,
            "index_type": self.index_type,
            "lists": self.index_lists,
            "probes": self.probes
        }


@dataclass
class APIKeyManager:
    """Secure API key management with rotation support"""
    primary_keys: Dict[str, str] = field(default_factory=dict)
    backup_keys: Dict[str, str] = field(default_factory=dict)
    rotation_schedule: Dict[str, int] = field(default_factory=dict)  # days
    last_rotation: Dict[str, datetime] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize API keys from environment"""
        self.primary_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY"),
            "odds_api": os.getenv("ODDS_API_KEY"),
            "sportsdata_io": os.getenv("SPORTSDATA_IO_KEY"),
            "rapid_api": os.getenv("RAPID_API_KEY")
        }

        self.backup_keys = {
            "openai": os.getenv("OPENAI_API_KEY_BACKUP"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY_BACKUP"),
            "google": os.getenv("GOOGLE_API_KEY_BACKUP")
        }

        # Default rotation schedule (days)
        self.rotation_schedule = {
            "openai": 90,
            "anthropic": 90,
            "google": 90,
            "odds_api": 180,
            "sportsdata_io": 180,
            "rapid_api": 180
        }

    def get_active_key(self, service: str) -> Optional[str]:
        """Get active API key for service"""
        return self.primary_keys.get(service)

    def needs_rotation(self, service: str) -> bool:
        """Check if API key needs rotation"""
        if service not in self.last_rotation:
            return False

        days_since_rotation = (datetime.now() - self.last_rotation[service]).days
        return days_since_rotation >= self.rotation_schedule.get(service, 90)

    def rotate_key(self, service: str) -> bool:
        """Rotate API key to backup if available"""
        if service in self.backup_keys and self.backup_keys[service]:
            self.primary_keys[service] = self.backup_keys[service]
            self.last_rotation[service] = datetime.now()
            return True
        return False

    def validate_keys(self) -> Dict[str, bool]:
        """Validate all API keys are present"""
        return {
            service: bool(key)
            for service, key in self.primary_keys.items()
        }


@dataclass
class RateLimitConfig:
    """Advanced rate limiting configuration"""
    limits: Dict[str, int] = field(default_factory=dict)
    burst_limits: Dict[str, int] = field(default_factory=dict)
    window_size: int = 60  # seconds
    enable_adaptive: bool = True
    backoff_multiplier: float = 2.0
    max_backoff: int = 300  # seconds

    def __post_init__(self):
        """Initialize rate limits from environment"""
        self.limits = {
            "openai": int(os.getenv("OPENAI_RATE_LIMIT", "3000")),
            "anthropic": int(os.getenv("ANTHROPIC_RATE_LIMIT", "1000")),
            "google": int(os.getenv("GOOGLE_RATE_LIMIT", "1000")),
            "odds_api": int(os.getenv("ODDS_API_RATE_LIMIT", "500")),
            "sportsdata_io": int(os.getenv("SPORTSDATA_IO_RATE_LIMIT", "1000")),
            "espn_api": int(os.getenv("ESPN_API_RATE_LIMIT", "1000"))
        }

        self.burst_limits = {
            service: limit * 2 for service, limit in self.limits.items()
        }

    def get_limit(self, service: str) -> int:
        """Get rate limit for service"""
        return self.limits.get(service, 100)

    def get_burst_limit(self, service: str) -> int:
        """Get burst limit for service"""
        return self.burst_limits.get(service, 200)


@dataclass
class MonitoringConfig:
    """Comprehensive monitoring and alerting configuration"""
    enable_metrics: bool = True
    enable_health_checks: bool = True
    health_check_interval: int = 300  # seconds
    metrics_port: int = 9090
    log_level: LogLevel = LogLevel.INFO
    enable_performance_tracking: bool = True
    enable_error_tracking: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize monitoring configuration"""
        self.alert_thresholds = {
            "error_rate": float(os.getenv("ALERT_ERROR_RATE", "0.05")),
            "response_time_p95": float(os.getenv("ALERT_RESPONSE_TIME", "2.0")),
            "memory_usage": float(os.getenv("ALERT_MEMORY_USAGE", "0.85")),
            "cpu_usage": float(os.getenv("ALERT_CPU_USAGE", "0.80")),
            "database_connections": float(os.getenv("ALERT_DB_CONNECTIONS", "0.90")),
            "expert_failure_rate": float(os.getenv("ALERT_EXPERT_FAILURE_RATE", "0.10"))
        }


@dataclass
class LoggingConfig:
    """Advanced logging configuration for production troubleshooting"""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_file_logging: bool = True
    enable_json_logging: bool = True
    log_directory: str = "./logs"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    backup_count: int = 10
    enable_structured_logging: bool = True
    enable_correlation_ids: bool = True

    def setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Create logs directory
        os.makedirs(self.log_directory, exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, self.level.value),
            format=self.format,
            handlers=self._get_handlers()
        )

        # Configure specific loggers
        self._configure_expert_logger()
        self._configure_database_logger()
        self._configure_api_logger()
        self._configure_performance_logger()

    def _get_handlers(self) -> List[logging.Handler]:
        """Get logging handlers"""
        handlers = []

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(self.format))
        handlers.append(console_handler)

        if self.enable_file_logging:
            # File handler with rotation
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                f"{self.log_directory}/nfl_expert_system.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            file_handler.setFormatter(logging.Formatter(self.format))
            handlers.append(file_handler)

        return handlers

    def _configure_expert_logger(self):
        """Configure expert system specific logging"""
        expert_logger = logging.getLogger("expert_system")
        expert_logger.setLevel(logging.INFO)

        if self.enable_file_logging:
            from logging.handlers import RotatingFileHandler
            expert_handler = RotatingFileHandler(
                f"{self.log_directory}/expert_system.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            expert_handler.setFormatter(logging.Formatter(
                "%(asctime)s - EXPERT[%(expert_id)s] - %(levelname)s - %(message)s"
            ))
            expert_logger.addHandler(expert_handler)

    def _configure_database_logger(self):
        """Configure database specific logging"""
        db_logger = logging.getLogger("database")
        db_logger.setLevel(logging.WARNING)

        if self.enable_file_logging:
            from logging.handlers import RotatingFileHandler
            db_handler = RotatingFileHandler(
                f"{self.log_directory}/database.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            db_handler.setFormatter(logging.Formatter(
                "%(asctime)s - DB - %(levelname)s - %(message)s"
            ))
            db_logger.addHandler(db_handler)

    def _configure_api_logger(self):
        """Configure API specific logging"""
        api_logger = logging.getLogger("api")
        api_logger.setLevel(logging.INFO)

        if self.enable_file_logging:
            from logging.handlers import RotatingFileHandler
            api_handler = RotatingFileHandler(
                f"{self.log_directory}/api.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            api_handler.setFormatter(logging.Formatter(
                "%(asctime)s - API - %(levelname)s - %(message)s"
            ))
            api_logger.addHandler(api_handler)

    def _configure_performance_logger(self):
        """Configure performance specific logging"""
        perf_logger = logging.getLogger("performance")
        perf_logger.setLevel(logging.INFO)

        if self.enable_file_logging:
            from logging.handlers import RotatingFileHandler
            perf_handler = RotatingFileHandler(
                f"{self.log_directory}/performance.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            perf_handler.setFormatter(logging.Formatter(
                "%(asctime)s - PERF - %(levelname)s - %(message)s"
            ))
            perf_logger.addHandler(perf_handler)


class ProductionDeploymentManager:
    """
    Main production deployment configuration manager.
    Handles all aspects of production deployment including database connections,
    vector search optimization, API key management, rate limiting, and monitoring.
    """

    def __init__(self):
        self.environment = DeploymentEnvironment(os.getenv("ENVIRONMENT", "development"))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

        # Initialize configuration components
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "postgresql://localhost:5432/nfl_predictor"),
            min_pool_size=int(os.getenv("DB_MIN_POOL_SIZE", "10")),
            max_pool_size=int(os.getenv("DB_MAX_POOL_SIZE", "50")),
            query_timeout=int(os.getenv("DB_QUERY_TIMEOUT", "60")),
            slow_query_threshold=float(os.getenv("DB_SLOW_QUERY_THRESHOLD", "2.0")),
            enable_query_logging=os.getenv("DB_ENABLE_QUERY_LOGGING", "true").lower() == "true"
        )

        self.vector_search = VectorSearchConfig(
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            similarity_threshold=float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", "0.7")),
            max_results=int(os.getenv("VECTOR_MAX_RESULTS", "50"))
        )

        self.api_keys = APIKeyManager()
        self.rate_limits = RateLimitConfig()
        self.monitoring = MonitoringConfig(
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "300")),
            log_level=LogLevel(os.getenv("LOG_LEVEL", "INFO"))
        )

        self.logging = LoggingConfig(
            level=LogLevel(os.getenv("LOG_LEVEL", "INFO")),
            log_directory=os.getenv("LOG_DIRECTORY", "./logs"),
            enable_json_logging=os.getenv("ENABLE_JSON_LOGGING", "true").lower() == "true"
        )

        # Connection pools
        self._db_pool = None
        self._redis_pool = None

        # Validate configuration
        self._validate_configuration()

    def _validate_configuration(self):
        """Validate production configuration"""
        errors = []

        # Validate API keys in production
        if self.environment == DeploymentEnvironment.PRODUCTION:
            key_validation = self.api_keys.validate_keys()
            missing_keys = [service for service, valid in key_validation.items() if not valid]
            if missing_keys:
                errors.append(f"Missing required API keys: {', '.join(missing_keys)}")

        # Validate database URL
        if not self.database.url.startswith("postgresql://"):
            errors.append("DATABASE_URL must be a valid PostgreSQL connection string")

        # Validate vector search configuration
        if self.vector_search.similarity_threshold < 0 or self.vector_search.similarity_threshold > 1:
            errors.append("Vector similarity threshold must be between 0 and 1")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

    async def initialize(self):
        """Initialize production deployment components"""
        logger = logging.getLogger(__name__)
        logger.info("Initializing production deployment...")

        # Setup logging
        self.logging.setup_logging()

        # Initialize database connection pool
        await self._initialize_database_pool()

        # Initialize Redis connection pool
        await self._initialize_redis_pool()

        # Setup vector search optimization
        await self._setup_vector_search_optimization()

        # Initialize monitoring
        await self._initialize_monitoring()

        logger.info("Production deployment initialization completed")

    async def _initialize_database_pool(self):
        """Initialize database connection pool with optimization"""
        logger = logging.getLogger("database")

        try:
            self._db_pool = await asyncpg.create_pool(
                **self.database.get_connection_params()
            )

            # Test connection
            async with self._db_pool.acquire() as conn:
                await conn.execute("SELECT 1")

            logger.info(f"Database pool initialized: {self.database.min_pool_size}-{self.database.max_pool_size} connections")

        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def _initialize_redis_pool(self):
        """Initialize Redis connection pool"""
        logger = logging.getLogger("database")

        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            redis_password = os.getenv("REDIS_PASSWORD")

            self._redis_pool = redis.ConnectionPool.from_url(
                redis_url,
                password=redis_password,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Test connection
            redis_client = redis.Redis(connection_pool=self._redis_pool)
            await redis_client.ping()

            logger.info("Redis pool initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            raise

    async def _setup_vector_search_optimization(self):
        """Setup vector search optimization"""
        logger = logging.getLogger("database")

        if not self.vector_search.enable_indexing:
            return

        try:
            async with self._db_pool.acquire() as conn:
                # Create vector index if not exists
                await conn.execute("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS expert_memories_embedding_idx
                    ON expert_episodic_memories
                    USING ivfflat (combined_embedding vector_cosine_ops)
                    WITH (lists = $1)
                """, self.vector_search.index_lists)

                # Set search parameters
                await conn.execute("SET ivfflat.probes = $1", self.vector_search.probes)

            logger.info("Vector search optimization configured")

        except Exception as e:
            logger.error(f"Failed to setup vector search optimization: {e}")
            # Don't raise - vector search can work without optimization

    async def _initialize_monitoring(self):
        """Initialize monitoring and health checks"""
        logger = logging.getLogger(__name__)

        if not self.monitoring.enable_metrics:
            return

        try:
            # Start health check loop
            asyncio.create_task(self._health_check_loop())

            # Start metrics collection
            asyncio.create_task(self._metrics_collection_loop())

            logger.info("Monitoring initialized")

        except Exception as e:
            logger.error(f"Failed to initialize monitoring: {e}")
            # Don't raise - monitoring is not critical for core functionality

    async def _health_check_loop(self):
        """Continuous health check loop"""
        logger = logging.getLogger("monitoring")

        while True:
            try:
                await asyncio.sleep(self.monitoring.health_check_interval)

                health_status = await self.get_health_status()

                if not health_status["healthy"]:
                    logger.warning(f"Health check failed: {health_status}")

            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _metrics_collection_loop(self):
        """Continuous metrics collection loop"""
        logger = logging.getLogger("monitoring")

        while True:
            try:
                await asyncio.sleep(60)  # Collect metrics every minute

                metrics = await self.collect_metrics()

                # Log metrics for external collection
                logger.info(f"Metrics: {json.dumps(metrics)}")

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health = {
            "healthy": True,
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }

        # Check database
        try:
            async with self._db_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            health["components"]["database"] = {"status": "healthy"}
        except Exception as e:
            health["components"]["database"] = {"status": "unhealthy", "error": str(e)}
            health["healthy"] = False

        # Check Redis
        try:
            redis_client = redis.Redis(connection_pool=self._redis_pool)
            await redis_client.ping()
            health["components"]["redis"] = {"status": "healthy"}
        except Exception as e:
            health["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health["healthy"] = False

        # Check API keys
        key_validation = self.api_keys.validate_keys()
        invalid_keys = [service for service, valid in key_validation.items() if not valid]
        if invalid_keys:
            health["components"]["api_keys"] = {"status": "degraded", "invalid_keys": invalid_keys}
        else:
            health["components"]["api_keys"] = {"status": "healthy"}

        return health

    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "database": {},
            "redis": {},
            "api_keys": {}
        }

        # Database metrics
        try:
            async with self._db_pool.acquire() as conn:
                # Connection pool metrics
                metrics["database"]["pool_size"] = self._db_pool.get_size()
                metrics["database"]["pool_free"] = self._db_pool.get_idle_size()

                # Query performance metrics
                result = await conn.fetchrow("""
                    SELECT
                        count(*) as active_connections,
                        avg(extract(epoch from now() - query_start)) as avg_query_time
                    FROM pg_stat_activity
                    WHERE state = 'active' AND query != '<IDLE>'
                """)

                if result:
                    metrics["database"]["active_connections"] = result["active_connections"]
                    metrics["database"]["avg_query_time"] = result["avg_query_time"]

        except Exception as e:
            metrics["database"]["error"] = str(e)

        # Redis metrics
        try:
            redis_client = redis.Redis(connection_pool=self._redis_pool)
            info = await redis_client.info()
            metrics["redis"]["used_memory"] = info.get("used_memory", 0)
            metrics["redis"]["connected_clients"] = info.get("connected_clients", 0)
            metrics["redis"]["keyspace_hits"] = info.get("keyspace_hits", 0)
            metrics["redis"]["keyspace_misses"] = info.get("keyspace_misses", 0)
        except Exception as e:
            metrics["redis"]["error"] = str(e)

        # API key rotation status
        for service in self.api_keys.primary_keys:
            metrics["api_keys"][service] = {
                "needs_rotation": self.api_keys.needs_rotation(service),
                "has_backup": bool(self.api_keys.backup_keys.get(service))
            }

        return metrics

    @asynccontextmanager
    async def get_db_connection(self):
        """Get database connection from pool"""
        async with self._db_pool.acquire() as conn:
            yield conn

    def get_redis_client(self):
        """Get Redis client"""
        return redis.Redis(connection_pool=self._redis_pool)

    async def shutdown(self):
        """Graceful shutdown"""
        logger = logging.getLogger(__name__)
        logger.info("Shutting down production deployment...")

        if self._db_pool:
            await self._db_pool.close()

        if self._redis_pool:
            self._redis_pool.disconnect()

        logger.info("Production deployment shutdown completed")

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging"""
        return {
            "environment": self.environment.value,
            "debug": self.debug,
            "database": {
                "pool_size": f"{self.database.min_pool_size}-{self.database.max_pool_size}",
                "query_timeout": self.database.query_timeout,
                "slow_query_threshold": self.database.slow_query_threshold
            },
            "vector_search": {
                "model": self.vector_search.embedding_model,
                "similarity_threshold": self.vector_search.similarity_threshold,
                "indexing_enabled": self.vector_search.enable_indexing
            },
            "rate_limits": self.rate_limits.limits,
            "monitoring": {
                "enabled": self.monitoring.enable_metrics,
                "health_check_interval": self.monitoring.health_check_interval,
                "log_level": self.monitoring.log_level.value
            }
        }


# Global deployment manager instance
deployment_manager = ProductionDeploymentManager()


async def get_deployment_manager() -> ProductionDeploymentManager:
    """Get the global deployment manager instance"""
    return deployment_manager


async def initialize_production_deployment():
    """Initialize production deployment"""
    await deployment_manager.initialize()


async def shutdown_production_deployment():
    """Shutdown production deployment"""
    await deployment_manager.shutdown()
