"""
FastAPI Application for NFL Predictor Authentication
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Import our modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import run_migrations
from narrator_endpoints import router as narrator_router
from performance_endpoints import router as performance_router
from clean_predictions_endpoints import router as predictions_router

# Import performance optimization services
from performance.optimized_prediction_service import get_optimized_service
from performance.database_optimizer import get_database_optimizer
from performance.performance_monitor import get_performance_monitor

# Import real data endpoints (with fallback handling)
try:
    from real_data_endpoints import router as real_data_router
    REAL_DATA_ENDPOINTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Real data endpoints not available: {e}")
    REAL_DATA_ENDPOINTS_AVAILABLE = False
    real_data_router = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting NFL Predictor API with Performance Optimizations...")

    # Run database migrations
    try:
        run_migrations()
        logger.info("✅ Database migrations completed")
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        # Don't fail startup for database issues in development

    # Initialize performance optimization services
    try:
        # Initialize optimized prediction service
        prediction_service = await get_optimized_service()
        logger.info("✅ Optimized prediction service initialized")

        # Initialize database optimizer
        db_optimizer = await get_database_optimizer()
        logger.info("✅ Database optimizer initialized")

        # Initialize performance monitor
        monitor = await get_performance_monitor()
        await monitor.start_monitoring()
        logger.info("✅ Performance monitoring started")

        logger.info("🎯 All performance optimizations active")

    except Exception as e:
        logger.warning(f"⚠️ Performance optimization initialization warning: {e}")
        # Continue startup even if optimization fails

    yield

    # Shutdown
    logger.info("🛑 Shutting down NFL Predictor API...")

    # Cleanup performance services
    try:
        prediction_service = await get_optimized_service()
        await prediction_service.shutdown()

        db_optimizer = await get_database_optimizer()
        await db_optimizer.shutdown()

        monitor = await get_performance_monitor()
        await monitor.stop_monitoring()

        logger.info("✅ Performance services shutdown complete")

    except Exception as e:
        logger.error(f"Error during performance services shutdown: {e}")

# Create FastAPI app
app = FastAPI(
    title="NFL Predictor API - High Performance Edition",
    description="""Real-time AI Game Narrator and NFL Prediction System with advanced performance optimizations.

    Features:
    - Sub-second response times for 375+ predictions per game
    - Redis caching with intelligent invalidation
    - Parallel processing with asyncio.gather()
    - Database connection pooling and optimization
    - Real-time performance monitoring and alerting
    - Response compression for large datasets
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Add performance middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(narrator_router)
app.include_router(performance_router)  # High-performance prediction endpoints
app.include_router(predictions_router)  # Clean predictions endpoints

# Include real data router if available
if REAL_DATA_ENDPOINTS_AVAILABLE and real_data_router:
    app.include_router(real_data_router)
    logger.info("✅ Real data endpoints included")
else:
    logger.warning("⚠️ Real data endpoints not included - check dependencies")

# Enhanced health check endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check with performance metrics"""
    try:
        # Get performance monitor status
        monitor = await get_performance_monitor()
        monitor_status = monitor.get_current_status()

        # Get database optimizer health
        db_optimizer = await get_database_optimizer()
        db_health = await db_optimizer.health_check()

        # Get prediction service health
        prediction_service = await get_optimized_service()
        perf_stats = await prediction_service.get_performance_stats()

        return {
            "status": "healthy",
            "service": "nfl-predictor-api",
            "version": "2.0.0",
            "performance_optimizations": {
                "redis_caching": prediction_service.cache_manager is not None,
                "database_pooling": db_health.get('healthy', False),
                "monitoring_active": monitor_status.get('monitoring_active', False),
                "parallel_processing": True
            },
            "system_health": monitor_status.get('system_health', 'unknown'),
            "cache_hit_rate": perf_stats.get('cache_metrics', {}).get('current', {}).get('hit_rate', 0),
            "database_connections": db_health.get('connection_pool', {}).get('size', 0)
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "degraded",
            "service": "nfl-predictor-api",
            "version": "2.0.0",
            "error": str(e)
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with performance features"""
    return {
        "message": "NFL Predictor API - High Performance Edition",
        "version": "2.0.0",
        "performance_features": [
            "Sub-second response times",
            "375+ predictions per game",
            "Redis caching with 5-minute TTL",
            "Parallel expert processing",
            "Database connection pooling",
            "Real-time performance monitoring",
            "Response compression"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "performance_predictions": "/api/v2/performance/predictions/batch",
            "performance_stats": "/api/v2/performance/performance/stats",
            "benchmark": "/api/v2/performance/performance/benchmark"
        }
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Run the application
    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )