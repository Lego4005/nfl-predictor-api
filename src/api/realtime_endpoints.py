"""
Real-time API Endpoints

FastAPI endpoints for real-time data pipeline management and WebSocket connections.
Provides REST API for pipeline control and WebSocket endpoints for live data streams.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..pipeline.real_time_pipeline import real_time_pipeline, PipelineStatus
from ..websocket.websocket_manager import websocket_manager
from ..auth.middleware import get_current_user  # Assuming auth exists

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/realtime", tags=["Real-time Data"])


# Pydantic models for API responses
class PipelineStatusResponse(BaseModel):
    """Pipeline status response model"""
    status: str
    active_games_count: int
    total_subscribers: int
    metrics: Dict[str, Any]
    rate_limits: Dict[str, int]
    cache_status: Dict[str, Any]
    recent_errors: List[Dict[str, Any]]


class GameStateResponse(BaseModel):
    """Game state response model"""
    game_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    quarter: str
    time_remaining: str
    possession: Optional[str]
    down: Optional[int]
    distance: Optional[int]
    field_position: Optional[str]
    last_update: str
    update_count: int


class SubscriptionRequest(BaseModel):
    """WebSocket subscription request model"""
    action: str = Field(..., description="subscribe or unsubscribe")
    game_id: Optional[str] = Field(None, description="Game ID for game-specific subscriptions")
    channels: Optional[List[str]] = Field(None, description="List of channels to subscribe to")


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str
    data: Dict[str, Any]
    timestamp: str
    source: str = "realtime_api"


# Pipeline Management Endpoints

@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status():
    """
    Get real-time pipeline status and metrics

    Returns comprehensive status including:
    - Pipeline operational status
    - Active games count
    - Performance metrics
    - Rate limiting status
    - Cache health
    - Recent errors
    """
    try:
        status = real_time_pipeline.get_pipeline_status()
        return PipelineStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_pipeline(current_user: Optional[Dict] = Depends(get_current_user)):
    """
    Start the real-time data pipeline

    Requires authentication. Starts background tasks for:
    - Live data fetching
    - WebSocket broadcasting
    - Cache management
    - Health monitoring
    """
    try:
        if real_time_pipeline.status == PipelineStatus.RUNNING:
            return {"message": "Pipeline is already running", "status": "running"}

        await real_time_pipeline.start()

        return {
            "message": "Real-time pipeline started successfully",
            "status": real_time_pipeline.status.value,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")


@router.post("/stop")
async def stop_pipeline(current_user: Optional[Dict] = Depends(get_current_user)):
    """
    Stop the real-time data pipeline

    Requires authentication. Stops all background tasks and cleans up resources.
    """
    try:
        await real_time_pipeline.stop()

        return {
            "message": "Real-time pipeline stopped successfully",
            "status": real_time_pipeline.status.value,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop pipeline: {str(e)}")


@router.post("/restart")
async def restart_pipeline(current_user: Optional[Dict] = Depends(get_current_user)):
    """
    Restart the real-time data pipeline

    Requires authentication. Performs graceful restart of the pipeline.
    """
    try:
        await real_time_pipeline.stop()
        await real_time_pipeline.start()

        return {
            "message": "Real-time pipeline restarted successfully",
            "status": real_time_pipeline.status.value,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error restarting pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart pipeline: {str(e)}")


# Game Data Endpoints

@router.get("/games", response_model=List[GameStateResponse])
async def get_active_games():
    """
    Get all currently active games

    Returns list of games currently being tracked by the pipeline
    with their latest state information.
    """
    try:
        games = real_time_pipeline.get_active_games()
        return [GameStateResponse(**game) for game in games]
    except Exception as e:
        logger.error(f"Error getting active games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/games/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """
    Get specific game state

    Args:
        game_id: Unique game identifier

    Returns:
        Current state of the specified game
    """
    try:
        games = real_time_pipeline.get_active_games()
        game = next((g for g in games if g['game_id'] == game_id), None)

        if not game:
            raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

        return GameStateResponse(**game)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/games/{game_id}/subscribers")
async def get_game_subscribers(game_id: str):
    """
    Get subscriber count for a specific game

    Args:
        game_id: Unique game identifier

    Returns:
        Number of active subscribers for the game
    """
    try:
        if game_id in real_time_pipeline.game_states:
            game_state = real_time_pipeline.game_states[game_id]
            return {
                "game_id": game_id,
                "subscriber_count": len(game_state.subscribers),
                "last_update": game_state.last_update.isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game subscribers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Cache Management Endpoints

@router.get("/cache/status")
async def get_cache_status():
    """
    Get cache health status and metrics

    Returns cache performance metrics and health information.
    """
    try:
        status = real_time_pipeline.cache_manager.get_health_status()
        return status
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Pattern to match for selective clearing"),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Clear cache entries

    Args:
        pattern: Optional pattern to match for selective clearing

    Requires authentication. Clears cache entries matching the pattern.
    """
    try:
        if pattern:
            count = real_time_pipeline.cache_manager.invalidate_pattern(pattern)
            return {
                "message": f"Cleared {count} cache entries matching pattern '{pattern}'",
                "count": count
            }
        else:
            # Clear all pipeline-related cache
            count = real_time_pipeline.cache_manager.invalidate_pattern("nfl_predictor:*")
            return {
                "message": f"Cleared {count} cache entries",
                "count": count
            }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoints

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time data

    Provides real-time updates for:
    - Live game scores and stats
    - Field position and possession changes
    - Odds updates
    - System notifications

    Protocol:
    - Send subscription messages to receive specific data types
    - Receive real-time updates as JSON messages
    - Heartbeat messages maintain connection
    """
    connection_id = None
    try:
        # Accept WebSocket connection
        connection_id = await websocket_manager.handle_websocket(websocket)

        logger.info(f"WebSocket connection established: {connection_id}")

    except WebSocketDisconnect:
        if connection_id:
            logger.info(f"WebSocket client {connection_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if connection_id:
            await websocket_manager.connection_manager.disconnect(connection_id)


@router.websocket("/ws/game/{game_id}")
async def game_websocket_endpoint(websocket: WebSocket, game_id: str):
    """
    Game-specific WebSocket endpoint

    Args:
        game_id: Unique game identifier

    Provides real-time updates for a specific game including:
    - Score changes
    - Field position updates
    - Down and distance changes
    - Possession changes
    """
    connection_id = None
    try:
        # Accept WebSocket connection
        connection_id = await websocket_manager.handle_websocket(websocket)

        # Subscribe to game-specific updates
        await real_time_pipeline.subscribe_to_game(connection_id, game_id)

        logger.info(f"WebSocket connection established for game {game_id}: {connection_id}")

        # Keep connection alive - the websocket_manager handles the rest
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        if connection_id:
            await real_time_pipeline.unsubscribe_from_game(connection_id, game_id)
            logger.info(f"WebSocket client {connection_id} disconnected from game {game_id}")
    except Exception as e:
        logger.error(f"Game WebSocket error for {game_id}: {e}")
        if connection_id:
            await real_time_pipeline.unsubscribe_from_game(connection_id, game_id)
            await websocket_manager.connection_manager.disconnect(connection_id)


@router.websocket("/ws/live")
async def live_websocket_endpoint(websocket: WebSocket):
    """
    Live updates WebSocket endpoint

    Optimized for high-frequency live game updates. Provides:
    - Real-time score updates
    - Critical game state changes
    - Minimal latency notifications
    """
    connection_id = None
    try:
        # Accept WebSocket connection
        connection_id = await websocket_manager.handle_websocket(websocket)

        # Subscribe to live updates channel
        websocket_manager.connection_manager.subscribe_to_channel(
            connection_id, "live_games"
        )

        logger.info(f"Live WebSocket connection established: {connection_id}")

        # Keep connection alive
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        if connection_id:
            logger.info(f"Live WebSocket client {connection_id} disconnected")
    except Exception as e:
        logger.error(f"Live WebSocket error: {e}")
        if connection_id:
            await websocket_manager.connection_manager.disconnect(connection_id)


# Health Check Endpoints

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the real-time pipeline

    Returns:
        Health status of all pipeline components
    """
    try:
        pipeline_status = real_time_pipeline.get_pipeline_status()
        websocket_stats = websocket_manager.get_stats()

        health_status = {
            "status": "healthy" if real_time_pipeline.status == PipelineStatus.RUNNING else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "pipeline": {
                "status": pipeline_status["status"],
                "active_games": pipeline_status["active_games_count"],
                "success_rate": pipeline_status["metrics"]["success_rate"]
            },
            "websocket": {
                "total_connections": websocket_stats["total_connections"],
                "total_channels": websocket_stats["total_channels"]
            },
            "cache": pipeline_status["cache_status"]["overall_status"]
        }

        # Determine overall health
        is_healthy = (
            real_time_pipeline.status == PipelineStatus.RUNNING and
            pipeline_status["metrics"]["success_rate"] > 80 and
            pipeline_status["cache_status"]["overall_status"] in ["healthy", "degraded"]
        )

        status_code = 200 if is_healthy else 503
        health_status["status"] = "healthy" if is_healthy else "unhealthy"

        return JSONResponse(content=health_status, status_code=status_code)

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )


@router.get("/metrics")
async def get_metrics():
    """
    Get detailed pipeline metrics

    Returns:
        Comprehensive metrics for monitoring and analytics
    """
    try:
        pipeline_status = real_time_pipeline.get_pipeline_status()
        websocket_stats = websocket_manager.get_stats()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "pipeline_metrics": pipeline_status["metrics"],
            "rate_limits": pipeline_status["rate_limits"],
            "websocket_metrics": websocket_stats,
            "cache_metrics": pipeline_status["cache_status"],
            "error_summary": {
                "recent_error_count": len(pipeline_status["recent_errors"]),
                "unique_errors": len(set(
                    error["message"] for error in pipeline_status["recent_errors"]
                ))
            }
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin Endpoints (require authentication)

@router.post("/admin/force-update")
async def force_update(current_user: Optional[Dict] = Depends(get_current_user)):
    """
    Force immediate data update (admin only)

    Triggers immediate fetch of live game data, bypassing normal intervals.
    """
    try:
        # Trigger immediate update by calling the fetch method directly
        await real_time_pipeline._fetch_live_games()

        return {
            "message": "Force update completed",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in force update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/broadcast")
async def admin_broadcast(
    message: str,
    level: str = "info",
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Send system-wide broadcast message (admin only)

    Args:
        message: Message to broadcast
        level: Message level (info, warning, error)
    """
    try:
        await websocket_manager.send_system_notification(message, level)

        return {
            "message": "Broadcast sent successfully",
            "broadcast_message": message,
            "level": level,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error sending broadcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))