#!/usr/bin/env python3
"""
API Endpoints for AI Game Narrator
Provides real-time insights, predictions, and intelligent commentary
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis
from contextlib import asynccontextmanager

from ..ml.ai_game_narrator import AIGameNarrator, GameState, NarratorInsight
from ..ml.live_game_processor import LiveGameProcessor, GameStateUpdate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router for narrator endpoints
router = APIRouter(prefix="/narrator", tags=["AI Game Narrator"])

# Global processor instance
live_processor: Optional[LiveGameProcessor] = None
redis_client: Optional[redis.Redis] = None


# Pydantic models for API
class GameStateRequest(BaseModel):
    quarter: int = Field(..., ge=1, le=5, description="Game quarter (1-4, 5 for OT)")
    time_remaining: str = Field(..., pattern=r"^\d{1,2}:\d{2}$", description="Time remaining (MM:SS)")
    down: int = Field(..., ge=1, le=4, description="Current down")
    yards_to_go: int = Field(..., ge=1, le=99, description="Yards to first down")
    yard_line: int = Field(..., ge=0, le=100, description="Field position (0-100)")
    home_score: int = Field(..., ge=0, description="Home team score")
    away_score: int = Field(..., ge=0, description="Away team score")
    possession: str = Field(..., regex="^(home|away)$", description="Team with possession")
    game_id: str = Field(..., description="Unique game identifier")
    week: int = Field(1, ge=1, le=18, description="NFL week")
    season: int = Field(2024, ge=2020, le=2030, description="NFL season")


class ContextRequest(BaseModel):
    weather_data: Optional[Dict[str, Any]] = Field(None, description="Weather conditions")
    team_stats: Optional[Dict[str, Any]] = Field(None, description="Team statistics")
    recent_scoring: Optional[List[Dict[str, Any]]] = Field(None, description="Recent scoring events")
    injury_reports: Optional[Dict[str, Any]] = Field(None, description="Injury reports")


class InsightRequest(BaseModel):
    game_state: GameStateRequest
    context: Optional[ContextRequest] = None


class LiveGameSubscription(BaseModel):
    game_ids: List[str] = Field(..., description="List of game IDs to monitor")
    insight_types: Optional[List[str]] = Field(None, description="Types of insights to receive")
    minimum_significance: float = Field(0.5, ge=0, le=1, description="Minimum significance for updates")


class PredictionResponse(BaseModel):
    timestamp: datetime
    game_id: str
    predictions: Dict[str, Any]
    insights: List[Dict[str, Any]]
    momentum: Dict[str, Any]
    confidence: Dict[str, Any]


class WebSocketConnection:
    """Manage WebSocket connections for live updates"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, LiveGameSubscription] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
        logger.info(f"WebSocket client {client_id} disconnected")

    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast_update(self, game_update: GameStateUpdate):
        """Broadcast game update to subscribed clients"""
        message = {
            "type": "game_update",
            "timestamp": game_update.timestamp.isoformat(),
            "game_id": game_update.game_id,
            "significance": game_update.significance_score,
            "insight": None
        }

        if game_update.narrator_insight:
            narrator = AIGameNarrator()
            message["insight"] = narrator.get_insight_summary(game_update.narrator_insight)

        # Send to subscribed clients
        for client_id, subscription in self.subscriptions.items():
            if (game_update.game_id in subscription.game_ids and
                game_update.significance_score >= subscription.minimum_significance):
                await self.send_to_client(client_id, message)


# Global WebSocket manager
websocket_manager = WebSocketConnection()


async def get_live_processor() -> LiveGameProcessor:
    """Get or create live game processor"""
    global live_processor

    if live_processor is None:
        live_processor = LiveGameProcessor(update_callback=websocket_manager.broadcast_update)
        # Start background processing
        asyncio.create_task(live_processor.start_live_processing())

    return live_processor


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client for caching"""
    global redis_client

    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_timeout=5
            )
            # Test connection
            redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            redis_client = None

    return redis_client


@router.post("/insight", response_model=PredictionResponse)
async def generate_insight(
    request: InsightRequest,
    background_tasks: BackgroundTasks
) -> PredictionResponse:
    """Generate AI narrator insight for current game state"""

    try:
        # Convert request to GameState
        game_state = GameState(
            quarter=request.game_state.quarter,
            time_remaining=request.game_state.time_remaining,
            down=request.game_state.down,
            yards_to_go=request.game_state.yards_to_go,
            yard_line=request.game_state.yard_line,
            home_score=request.game_state.home_score,
            away_score=request.game_state.away_score,
            possession=request.game_state.possession,
            last_play={},
            drive_info={},
            game_id=request.game_state.game_id,
            week=request.game_state.week,
            season=request.game_state.season
        )

        # Prepare context
        context = {}
        if request.context:
            if request.context.weather_data:
                context['weather_data'] = request.context.weather_data
            if request.context.team_stats:
                context['team_stats'] = request.context.team_stats
            if request.context.recent_scoring:
                context['recent_scoring'] = request.context.recent_scoring

        # Generate insight
        narrator = AIGameNarrator()
        insight = narrator.generate_comprehensive_insight(game_state, context)

        # Convert to response format
        summary = narrator.get_insight_summary(insight)

        # Cache result in Redis
        redis_client = await get_redis_client()
        if redis_client:
            cache_key = f"insight:{game_state.game_id}:{datetime.now().timestamp()}"
            background_tasks.add_task(cache_insight, redis_client, cache_key, summary)

        return PredictionResponse(
            timestamp=insight.timestamp,
            game_id=game_state.game_id,
            predictions=summary.get('predictions', {}),
            insights=summary.get('insights', []),
            momentum=summary.get('momentum', {}),
            confidence={
                'scoring': summary.get('predictions', {}).get('next_score', {}).get('confidence', 'medium'),
                'outcome': summary.get('predictions', {}).get('game_outcome', {}).get('confidence', 'medium')
            }
        )

    except Exception as e:
        logger.error(f"Error generating insight: {e}")
        raise HTTPException(status_code=500, detail="Error generating insight")


@router.get("/live-games")
async def get_live_games(processor: LiveGameProcessor = Depends(get_live_processor)) -> Dict[str, Any]:
    """Get list of currently active live games"""

    try:
        active_games = await processor.get_active_games()

        response = {
            "timestamp": datetime.now().isoformat(),
            "active_games_count": len(active_games),
            "games": []
        }

        for game_id, game_info in active_games.items():
            game_data = {
                "game_id": game_id,
                "last_update": game_info["last_update"].isoformat(),
                "current_state": {
                    "quarter": game_info["current_state"].quarter,
                    "time_remaining": game_info["current_state"].time_remaining,
                    "score": {
                        "home": game_info["current_state"].home_score,
                        "away": game_info["current_state"].away_score
                    },
                    "possession": game_info["current_state"].possession,
                    "down": game_info["current_state"].down,
                    "yards_to_go": game_info["current_state"].yards_to_go,
                    "field_position": game_info["current_state"].yard_line
                }
            }

            if "latest_insight" in game_info and game_info["latest_insight"]:
                narrator = AIGameNarrator()
                game_data["latest_insight"] = narrator.get_insight_summary(game_info["latest_insight"])

            response["games"].append(game_data)

        return response

    except Exception as e:
        logger.error(f"Error getting live games: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving live games")


@router.get("/game/{game_id}/insight")
async def get_game_insight(
    game_id: str,
    processor: LiveGameProcessor = Depends(get_live_processor)
) -> Dict[str, Any]:
    """Get latest insight for a specific game"""

    try:
        insight = await processor.get_game_insight(game_id)

        if not insight:
            raise HTTPException(status_code=404, detail="Game not found or no insight available")

        narrator = AIGameNarrator()
        summary = narrator.get_insight_summary(insight)

        return {
            "game_id": game_id,
            "timestamp": insight.timestamp.isoformat(),
            "insight": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game insight for {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving game insight")


@router.post("/game/{game_id}/force-update")
async def force_game_update(
    game_id: str,
    processor: LiveGameProcessor = Depends(get_live_processor)
) -> Dict[str, Any]:
    """Force an immediate update for a specific game"""

    try:
        state_update = await processor.force_update_game(game_id)

        if not state_update:
            raise HTTPException(status_code=404, detail="Game not found or no update available")

        response = {
            "game_id": game_id,
            "timestamp": state_update.timestamp.isoformat(),
            "significance": state_update.significance_score,
            "update_triggered": True
        }

        if state_update.narrator_insight:
            narrator = AIGameNarrator()
            response["insight"] = narrator.get_insight_summary(state_update.narrator_insight)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forcing update for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Error forcing game update")


@router.get("/game/{game_id}/predictions")
async def get_game_predictions(
    game_id: str,
    prediction_types: Optional[str] = None,
    processor: LiveGameProcessor = Depends(get_live_processor)
) -> Dict[str, Any]:
    """Get specific predictions for a game"""

    try:
        insight = await processor.get_game_insight(game_id)

        if not insight:
            raise HTTPException(status_code=404, detail="Game not found")

        narrator = AIGameNarrator()
        summary = narrator.get_insight_summary(insight)

        # Filter predictions if specific types requested
        if prediction_types:
            requested_types = [t.strip() for t in prediction_types.split(',')]
            filtered_predictions = {}

            for pred_type in requested_types:
                if pred_type in summary.get('predictions', {}):
                    filtered_predictions[pred_type] = summary['predictions'][pred_type]

            summary['predictions'] = filtered_predictions

        return {
            "game_id": game_id,
            "timestamp": insight.timestamp.isoformat(),
            "predictions": summary.get('predictions', {}),
            "confidence_levels": {
                "next_score": summary.get('predictions', {}).get('next_score', {}).get('confidence', 'unknown'),
                "game_outcome": summary.get('predictions', {}).get('game_outcome', {}).get('confidence', 'unknown')
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting predictions for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving predictions")


@router.get("/game/{game_id}/momentum")
async def get_game_momentum(
    game_id: str,
    processor: LiveGameProcessor = Depends(get_live_processor)
) -> Dict[str, Any]:
    """Get momentum analysis for a game"""

    try:
        insight = await processor.get_game_insight(game_id)

        if not insight:
            raise HTTPException(status_code=404, detail="Game not found")

        narrator = AIGameNarrator()
        summary = narrator.get_insight_summary(insight)

        return {
            "game_id": game_id,
            "timestamp": insight.timestamp.isoformat(),
            "momentum": summary.get('momentum', {}),
            "contextual_insights": [
                insight for insight in summary.get('insights', [])
                if 'momentum' in insight.get('type', '').lower()
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting momentum for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving momentum analysis")


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str
):
    """WebSocket endpoint for real-time game updates"""

    await websocket_manager.connect(websocket, client_id)

    try:
        while True:
            # Receive subscription data
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe":
                subscription = LiveGameSubscription(**message.get("data", {}))
                websocket_manager.subscriptions[client_id] = subscription

                await websocket_manager.send_to_client(client_id, {
                    "type": "subscription_confirmed",
                    "game_ids": subscription.game_ids,
                    "minimum_significance": subscription.minimum_significance
                })

            elif message.get("type") == "unsubscribe":
                if client_id in websocket_manager.subscriptions:
                    del websocket_manager.subscriptions[client_id]

                await websocket_manager.send_to_client(client_id, {
                    "type": "unsubscribed"
                })

            elif message.get("type") == "ping":
                await websocket_manager.send_to_client(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        websocket_manager.disconnect(client_id)


@router.get("/health")
async def narrator_health():
    """Health check for narrator service"""

    try:
        # Check if processor is running
        processor_status = "running" if live_processor and live_processor.is_running else "stopped"

        # Check Redis connection
        redis_status = "connected"
        try:
            redis_client = await get_redis_client()
            if redis_client:
                redis_client.ping()
            else:
                redis_status = "unavailable"
        except:
            redis_status = "disconnected"

        # Check active connections
        active_connections = len(websocket_manager.active_connections)
        active_subscriptions = len(websocket_manager.subscriptions)

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "live_processor": processor_status,
                "redis_cache": redis_status,
                "websocket_connections": active_connections,
                "active_subscriptions": active_subscriptions
            }
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


# Background task functions
async def cache_insight(redis_client: redis.Redis, cache_key: str, insight_data: Dict[str, Any]):
    """Cache insight data in Redis"""
    try:
        redis_client.setex(cache_key, 3600, json.dumps(insight_data))  # Cache for 1 hour
    except Exception as e:
        logger.error(f"Error caching insight: {e}")


# Startup event to initialize processor
@router.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global live_processor

    logger.info("Starting AI Game Narrator services...")

    # Initialize live processor
    live_processor = LiveGameProcessor(update_callback=websocket_manager.broadcast_update)

    # Start background processing task
    asyncio.create_task(live_processor.start_live_processing())

    logger.info("AI Game Narrator services started")


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global live_processor, redis_client

    logger.info("Shutting down AI Game Narrator services...")

    if live_processor:
        await live_processor.stop_live_processing()

    if redis_client:
        redis_client.close()

    logger.info("AI Game Narrator services shut down")


# Export router for main app
__all__ = ["router"]