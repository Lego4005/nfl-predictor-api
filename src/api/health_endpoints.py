"""
Health Check API Endpoints for NFL Expert Prediction System.
ovides comprehensive health monitoring endpoints for production deployment.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from config.production_deployment import get_deployment_manager
from src.admin.system_administration import (
    get_health_monitor,
    get_training_monitor,
    get_memory_maintenance,
    get_performance_analyzer
)

# Create router
router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger("health_api")


@router.get("/")
async def basic_health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "nfl-expert-prediction-system",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with all system components"""
    try:
        health_monitor = await get_health_monitor()
        health_status = await health_monitor.get_comprehensive_health_status()

        # Convert to dict for JSON response
        health_dict = {
            "timestamp": health_status.timestamp.isoformat(),
            "overall_status": health_status.overall_status,
            "database_health": health_status.database_health,
            "memory_system_health": health_status.memory_system_health,
            "expert_system_health": health_status.expert_system_health,
            "api_health": health_status.api_health,
            "performance_metrics": health_status.performance_metrics,
            "alerts": health_status.alerts
        }

        # Set HTTP status based on health
        status_code = 200
        if health_status.overall_status == "critical":
            status_code = 503  # Service Unavailable
        elif health_status.overall_status == "warning":
            status_code = 200  # OK but with warnings

        return JSONResponse(content=health_dict, status_code=status_code)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/database")
async def database_health():
    """Database-specific health check"""
    try:
        deployment_manager = await get_deployment_manager()

        async with deployment_manager.get_db_connection() as conn:
            # Test basic connectivity
            await conn.execute("SELECT 1")

            # Get database statistics
            stats = await conn.fetchrow("""
                SELECT
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections,
                    (SELECT count(*) FROM expert_episodic_memories) as total_memories,
                    (SELECT count(*) FROM games WHERE season = 2025) as current_season_games
            """)

            connection_usage = stats["active_connections"] / stats["max_connections"]

            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_connections": stats["active_connections"],
                "max_connections": stats["max_connections"],
                "connection_usage_percent": round(connection_usage * 100, 2),
                "total_memories": stats["total_memories"],
                "current_season_games": stats["current_season_games"]
            }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/memory-system")
async def memory_system_health():
    """Memory system health check"""
    try:
        memory_maintenance = await get_memory_maintenance()
        memory_stats = await memory_maintenance.get_memory_statistics()

        overall = memory_stats.get("overall", {})
        storage = memory_stats.get("storage", {})

        # Calculate health metrics
        total_memories = overall.get("total_memories", 0)
        active_experts = overall.get("active_experts", 0)
        avg_strength = overall.get("avg_strength", 0)

        status = "healthy"
        if total_memories < 100:
            status = "warning"
        elif active_experts < 10:
            status = "warning"

        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "total_memories": total_memories,
            "active_experts": active_experts,
            "average_memory_strength": round(avg_strength, 3) if avg_strength else 0,
            "table_size": storage.get("table_size", "unknown"),
            "index_size": storage.get("index_size", "unknown")
        }

    except Exception as e:
        logger.error(f"Memory system health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/expert-system")
async def expert_system_health():
    """Expert system health check"""
    try:
        deployment_manager = await get_deployment_manager()

        async with deployment_manager.get_db_connection() as conn:
            # Get expert activity statistics
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(DISTINCT expert_id) as active_experts,
                    COUNT(*) as total_predictions,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_predictions,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' THEN 1 END) as very_recent_predictions
                FROM expert_predictions
                WHERE created_at > NOW() - INTERVAL '7 days'
            """)

            # Get memory activity
            memory_stats = await conn.fetchrow("""
                SELECT
                    COUNT(DISTINCT expert_id) as experts_with_memories,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_memories
                FROM expert_episodic_memories
            """)

            active_experts = stats["active_experts"]
            experts_with_memories = memory_stats["experts_with_memories"]

            status = "healthy"
            if active_experts < 10:
                status = "warning"
            elif experts_with_memories < 10:
                status = "warning"

            return {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "active_experts_7d": active_experts,
                "experts_with_memories": experts_with_memories,
                "total_predictions_7d": stats["total_predictions"],
                "recent_predictions_24h": stats["recent_predictions"],
                "very_recent_predictions_1h": stats["very_recent_predictions"],
                "recent_memories_24h": memory_stats["recent_memories"]
            }

    except Exception as e:
        logger.error(f"Expert system health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/training-progress")
async def training_progress_health():
    """Training progress health check"""
    try:
        training_monitor = await get_training_monitor()
        progress_summary = training_monitor.get_progress_summary()

        total_experts = progress_summary.get("total_experts", 0)
        overall_progress = progress_summary.get("overall_progress", 0)
        total_memories = progress_summary.get("total_memories", 0)
        experts_by_phase = progress_summary.get("experts_by_phase", {})

        # Determine status based on progress
        status = "healthy"
        if overall_progress < 10:
            status = "warning"
        elif experts_by_phase.get("failed", 0) > 0:
            status = "warning"

        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "total_experts": total_experts,
            "overall_progress_percent": round(overall_progress, 2),
            "total_memories_created": total_memories,
            "experts_by_phase": experts_by_phase,
            "experts_in_progress": experts_by_phase.get("in_progress", 0),
            "experts_completed": experts_by_phase.get("completed", 0),
            "experts_failed": experts_by_phase.get("failed", 0)
        }

    except Exception as e:
        logger.error(f"Training progress health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/api-keys")
async def api_keys_health():
    """API keys health check"""
    try:
        deployment_manager = await get_deployment_manager()
        api_keys = deployment_manager.api_keys

        # Check key status
        key_validation = api_keys.validate_keys()
        configured_keys = sum(1 for valid in key_validation.values() if valid)
        total_keys = len(key_validation)

        # Check for keys needing rotation
        keys_needing_rotation = []
        for service in api_keys.primary_keys:
            if api_keys.needs_rotation(service):
                keys_needing_rotation.append(service)

        status = "healthy"
        if configured_keys < total_keys * 0.8:
            status = "warning"
        elif configured_keys < total_keys * 0.5:
            status = "critical"

        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "configured_keys": configured_keys,
            "total_keys": total_keys,
            "configuration_percentage": round((configured_keys / total_keys) * 100, 2),
            "keys_needing_rotation": keys_needing_rotation,
            "key_status": {
                service: {
                    "configured": valid,
                    "needs_rotation": api_keys.needs_rotation(service),
                    "has_backup": bool(api_keys.backup_keys.get(service))
                }
                for service, valid in key_validation.items()
            }
        }

    except Exception as e:
        logger.error(f"API keys health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/performance")
async def performance_metrics():
    """Performance metrics endpoint"""
    try:
        deployment_manager = await get_deployment_manager()
        metrics = await deployment_manager.collect_metrics()

        # Add response time measurement
        start_time = datetime.now()

        # Test database response time
        async with deployment_manager.get_db_connection() as conn:
            await conn.execute("SELECT 1")

        db_response_time = (datetime.now() - start_time).total_seconds()

        # Test Redis response time
        start_time = datetime.now()
        redis_client = deployment_manager.get_redis_client()
        redis_client.ping()
        redis_response_time = (datetime.now() - start_time).total_seconds()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database_response_time_seconds": round(db_response_time, 3),
            "redis_response_time_seconds": round(redis_response_time, 3),
            "database_metrics": metrics.get("database", {}),
            "redis_metrics": metrics.get("redis", {}),
            "api_key_metrics": metrics.get("api_keys", {})
        }

    except Exception as e:
        logger.error(f"Performance metrics failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/readiness")
async def readiness_check():
    """Kubernetes-style readiness check"""
    try:
        # Check if all critical components are ready
        deployment_manager = await get_deployment_manager()

        # Test database
        async with deployment_manager.get_db_connection() as conn:
            await conn.execute("SELECT 1")

        # Test Redis
        redis_client = deployment_manager.get_redis_client()
        redis_client.ping()

        # Check API keys
        api_keys = deployment_manager.api_keys
        key_validation = api_keys.validate_keys()
        configured_keys = sum(1 for valid in key_validation.values() if valid)

        if configured_keys < len(key_validation) * 0.5:
            raise Exception("Insufficient API keys configured")

        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "ready",
                "redis": "ready",
                "api_keys": "ready"
            }
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            content={
                "status": "not_ready",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/liveness")
async def liveness_check():
    """Kubernetes-style liveness check"""
    try:
        # Basic liveness check - just verify the service is running
        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": 0  # Would need to track actual uptime
        }

    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JSONResponse(
            content={
                "status": "dead",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    try:
        deployment_manager = await get_deployment_manager()
        metrics = await deployment_manager.collect_metrics()

        # Format metrics in Prometheus format
        prometheus_metrics = []

        # Database metrics
        db_metrics = metrics.get("database", {})
        if "pool_size" in db_metrics:
            prometheus_metrics.append(f"nfl_db_pool_size {db_metrics['pool_size']}")
        if "pool_free" in db_metrics:
            prometheus_metrics.append(f"nfl_db_pool_free {db_metrics['pool_free']}")
        if "active_connections" in db_metrics:
            prometheus_metrics.append(f"nfl_db_active_connections {db_metrics['active_connections']}")

        # Redis metrics
        redis_metrics = metrics.get("redis", {})
        if "used_memory" in redis_metrics:
            prometheus_metrics.append(f"nfl_redis_used_memory_bytes {redis_metrics['used_memory']}")
        if "connected_clients" in redis_metrics:
            prometheus_metrics.append(f"nfl_redis_connected_clients {redis_metrics['connected_clients']}")

        # API key metrics
        api_metrics = metrics.get("api_keys", {})
        for service, data in api_metrics.items():
            needs_rotation = 1 if data.get("needs_rotation", False) else 0
            prometheus_metrics.append(f"nfl_api_key_needs_rotation{{service=\"{service}\"}} {needs_rotation}")

        # Add timestamp
        timestamp = int(datetime.now().timestamp() * 1000)
        prometheus_metrics.append(f"nfl_metrics_timestamp {timestamp}")

        return "\n".join(prometheus_metrics)

    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))
