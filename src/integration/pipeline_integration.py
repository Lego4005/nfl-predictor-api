"""
Real-time Data Pipeline Integration

Complete integration script that initializes and coordinates all components
of the real-time NFL data pipeline including WebSocket connections, caching,
validation, rate limiting, and error handling.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# Pipeline components
from ..pipeline.real_time_pipeline import real_time_pipeline
from ..cache.enhanced_cache_strategy import EnhancedCacheManager, CacheConfiguration
from ..validation.data_validator import data_validator
from ..middleware.rate_limiting import rate_limiter, RateLimitMiddleware
from ..error_handling.resilient_connection import connection_manager, RetryConfig, CircuitBreakerConfig
from ..websocket.websocket_manager import websocket_manager

# API endpoints
from ..api.realtime_endpoints import router as realtime_router

logger = logging.getLogger(__name__)


class PipelineIntegration:
    """
    Main integration class for the real-time data pipeline

    Coordinates initialization, shutdown, and management of all pipeline components
    including caching, validation, rate limiting, error handling, and WebSocket support.
    """

    def __init__(self):
        """Initialize pipeline integration"""
        self.app: Optional[FastAPI] = None
        self.cache_manager: Optional[EnhancedCacheManager] = None
        self.initialized = False

    async def initialize_all_components(self):
        """Initialize all pipeline components in the correct order"""
        try:
            logger.info("Initializing real-time data pipeline components...")

            # 1. Initialize cache manager
            await self._initialize_cache_manager()

            # 2. Initialize rate limiter
            await self._initialize_rate_limiter()

            # 3. Initialize connection manager
            await self._initialize_connection_manager()

            # 4. Initialize real-time pipeline with enhanced components
            await self._initialize_real_time_pipeline()

            # 5. Initialize WebSocket manager
            await self._initialize_websocket_manager()

            self.initialized = True
            logger.info("All pipeline components initialized successfully")

            # Send startup notification
            await websocket_manager.send_system_notification(
                "Real-time NFL data pipeline initialized and ready",
                level="info"
            )

        except Exception as e:
            logger.error(f"Failed to initialize pipeline components: {e}")
            await self.shutdown_all_components()
            raise

    async def shutdown_all_components(self):
        """Shutdown all pipeline components gracefully"""
        try:
            logger.info("Shutting down real-time data pipeline components...")

            # Send shutdown notification
            if self.initialized:
                try:
                    await websocket_manager.send_system_notification(
                        "Real-time NFL data pipeline shutting down",
                        level="warning"
                    )
                except:
                    pass  # May fail if WebSocket manager already shut down

            # Shutdown in reverse order
            if real_time_pipeline.status.value != "stopped":
                await real_time_pipeline.stop()

            await websocket_manager.stop_background_tasks()

            if self.cache_manager:
                await self.cache_manager.shutdown()

            await connection_manager.shutdown()

            self.initialized = False
            logger.info("All pipeline components shut down successfully")

        except Exception as e:
            logger.error(f"Error during pipeline shutdown: {e}")

    async def _initialize_cache_manager(self):
        """Initialize enhanced cache manager"""
        try:
            # Configure cache with optimal settings for real-time data
            cache_config = CacheConfiguration(
                redis_url="redis://localhost:6379",
                default_ttl=30,
                live_data_ttl=2,
                game_state_ttl=5,
                odds_ttl=3,
                player_stats_ttl=10,
                max_memory_cache_size=2000,
                refresh_threshold=0.75,
                enable_metrics=True
            )

            self.cache_manager = EnhancedCacheManager(cache_config)
            await self.cache_manager.initialize()

            # Replace pipeline cache manager
            real_time_pipeline.cache_manager = self.cache_manager

            logger.info("Enhanced cache manager initialized")

        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            raise

    async def _initialize_rate_limiter(self):
        """Initialize rate limiter"""
        try:
            await rate_limiter.initialize()
            logger.info("Rate limiter initialized")

        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {e}")
            raise

    async def _initialize_connection_manager(self):
        """Initialize connection manager with resilient connections"""
        try:
            await connection_manager.initialize()

            # Add ESPN API connection
            espn_retry_config = RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=30.0
            )

            espn_circuit_config = CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60,
                name="espn_api"
            )

            connection_manager.add_connection(
                name="espn_api",
                base_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl",
                retry_config=espn_retry_config,
                circuit_config=espn_circuit_config,
                timeout_seconds=30
            )

            # Add other API connections as needed
            # SportsData.io connection
            if True:  # Check if API key is configured
                sportsdata_retry_config = RetryConfig(
                    max_attempts=2,  # More conservative for paid API
                    base_delay=2.0,
                    max_delay=60.0
                )

                sportsdata_circuit_config = CircuitBreakerConfig(
                    failure_threshold=3,
                    recovery_timeout=120,
                    name="sportsdata_io"
                )

                connection_manager.add_connection(
                    name="sportsdata_io",
                    base_url="https://api.sportsdata.io/v3/nfl",
                    retry_config=sportsdata_retry_config,
                    circuit_config=sportsdata_circuit_config,
                    timeout_seconds=45
                )

            # Initialize all connections
            await connection_manager.initialize_all_connections()

            logger.info("Connection manager initialized with resilient connections")

        except Exception as e:
            logger.error(f"Failed to initialize connection manager: {e}")
            raise

    async def _initialize_real_time_pipeline(self):
        """Initialize real-time pipeline with enhanced components"""
        try:
            # Inject enhanced cache manager into pipeline
            if self.cache_manager:
                real_time_pipeline.cache_manager = self.cache_manager

            # Start the real-time pipeline
            await real_time_pipeline.start()

            # Set up data validation handlers
            real_time_pipeline.add_data_handler(self._validate_game_data)
            real_time_pipeline.add_error_handler(self._handle_pipeline_error)

            logger.info("Real-time pipeline initialized with enhanced components")

        except Exception as e:
            logger.error(f"Failed to initialize real-time pipeline: {e}")
            raise

    async def _initialize_websocket_manager(self):
        """Initialize WebSocket manager"""
        try:
            await websocket_manager.start_background_tasks()
            logger.info("WebSocket manager initialized")

        except Exception as e:
            logger.error(f"Failed to initialize WebSocket manager: {e}")
            raise

    async def _validate_game_data(self, data: Dict[str, Any]):
        """Data validation handler for pipeline"""
        try:
            if 'games' in data:
                for game in data['games']:
                    validation_result = data_validator.validate_game_data(game)
                    if not validation_result.is_valid:
                        logger.warning(f"Game data validation failed: {validation_result.issues}")
                    elif validation_result.sanitized_data:
                        # Use sanitized data
                        game.update(validation_result.sanitized_data)

        except Exception as e:
            logger.error(f"Error in data validation handler: {e}")

    async def _handle_pipeline_error(self, error: Exception, context: str):
        """Error handler for pipeline"""
        try:
            logger.error(f"Pipeline error in {context}: {error}")

            # Send error notification via WebSocket
            await websocket_manager.send_system_notification(
                f"Pipeline error in {context}: {str(error)}",
                level="error"
            )

        except Exception as e:
            logger.error(f"Error in pipeline error handler: {e}")

    def create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application with all components integrated"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """FastAPI lifespan manager"""
            # Startup
            await self.initialize_all_components()
            yield
            # Shutdown
            await self.shutdown_all_components()

        # Create FastAPI app
        app = FastAPI(
            title="NFL Predictor Real-time API",
            description="Real-time NFL data pipeline with WebSocket support",
            version="1.0.0",
            lifespan=lifespan
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add rate limiting middleware
        rate_limit_middleware = RateLimitMiddleware(rate_limiter)
        app.middleware("http")(rate_limit_middleware)

        # Include API routers
        app.include_router(realtime_router)

        # Add health check endpoint
        @app.get("/health")
        async def health_check():
            """Comprehensive health check endpoint"""
            try:
                health_status = {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "components": {
                        "pipeline": real_time_pipeline.get_pipeline_status(),
                        "cache": self.cache_manager.get_health_status() if self.cache_manager else {"status": "not_initialized"},
                        "rate_limiter": rate_limiter.get_metrics(),
                        "connections": connection_manager.get_overall_status(),
                        "websocket": websocket_manager.get_stats()
                    }
                }

                # Determine overall health
                is_healthy = (
                    real_time_pipeline.status.value == "running" and
                    (not self.cache_manager or self.cache_manager.get_health_status()["status"] in ["healthy", "degraded"]) and
                    connection_manager.get_overall_status()["health_percentage"] > 50
                )

                health_status["status"] = "healthy" if is_healthy else "degraded"

                return health_status

            except Exception as e:
                logger.error(f"Health check error: {e}")
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }

        # Add metrics endpoint
        @app.get("/metrics")
        async def metrics():
            """Comprehensive metrics endpoint"""
            try:
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "pipeline": real_time_pipeline.get_pipeline_status(),
                    "cache": self.cache_manager.get_metrics() if self.cache_manager else {},
                    "rate_limiter": rate_limiter.get_metrics(),
                    "connections": connection_manager.get_overall_status(),
                    "websocket": websocket_manager.get_stats(),
                    "validation": data_validator.get_validation_summary([])  # Would need to collect validation reports
                }

            except Exception as e:
                logger.error(f"Metrics error: {e}")
                return {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }

        # Store app reference
        self.app = app
        return app

    def get_integration_status(self) -> Dict[str, Any]:
        """Get overall integration status"""
        return {
            "initialized": self.initialized,
            "components": {
                "cache_manager": bool(self.cache_manager),
                "rate_limiter": True,
                "connection_manager": True,
                "real_time_pipeline": True,
                "websocket_manager": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global integration instance
pipeline_integration = PipelineIntegration()


# Convenience function for creating the app
def create_app() -> FastAPI:
    """Create and return configured FastAPI application"""
    return pipeline_integration.create_fastapi_app()


# Development server runner
async def run_development_server():
    """Run development server with all components"""
    try:
        import uvicorn

        app = create_app()

        # Configure uvicorn
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False  # Disable reload for proper async lifecycle management
        )

        server = uvicorn.Server(config)
        await server.serve()

    except Exception as e:
        logger.error(f"Failed to run development server: {e}")
        raise


if __name__ == "__main__":
    # Run development server
    asyncio.run(run_development_server())