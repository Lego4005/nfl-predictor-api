"""
WebSocket API endpoints for triggering real-time updates
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import logging

from ..websocket.websocket_manager import websocket_manager
from ..websocket.websocket_handlers import websocket_handlers


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/websocket", tags=["WebSocket API"])


@router.post("/game-update")
async def trigger_game_update(
    game_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Trigger a game update broadcast via WebSocket

    Example payload:
    {
        "game_id": "2024_week1_KC_BUF",
        "home_team": "KC",
        "away_team": "BUF",
        "home_score": 21,
        "away_score": 14,
        "quarter": 2,
        "time_remaining": "5:32",
        "game_status": "live",
        "updated_at": "2024-09-14T20:30:00Z"
    }
    """
    try:
        required_fields = ["game_id", "home_team", "away_team", "home_score", "away_score", "game_status"]

        # Validate required fields
        for field in required_fields:
            if field not in game_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Send game update via WebSocket
        background_tasks.add_task(websocket_manager.send_game_update, game_data)

        logger.info(f"Game update triggered for {game_data['game_id']}")

        return {
            "success": True,
            "message": "Game update broadcast initiated",
            "game_id": game_data["game_id"]
        }

    except Exception as e:
        logger.error(f"Error triggering game update: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger game update")


@router.post("/odds-update")
async def trigger_odds_update(
    odds_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Trigger an odds update broadcast via WebSocket

    Example payload:
    {
        "game_id": "2024_week1_KC_BUF",
        "sportsbook": "DraftKings",
        "home_team": "KC",
        "away_team": "BUF",
        "spread": -3.5,
        "moneyline_home": -180,
        "moneyline_away": +150,
        "over_under": 54.5,
        "updated_at": "2024-09-14T20:30:00Z"
    }
    """
    try:
        required_fields = ["game_id", "sportsbook", "home_team", "away_team"]

        # Validate required fields
        for field in required_fields:
            if field not in odds_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Send odds update via WebSocket
        background_tasks.add_task(websocket_manager.send_odds_update, odds_data)

        logger.info(f"Odds update triggered for {odds_data['game_id']} from {odds_data['sportsbook']}")

        return {
            "success": True,
            "message": "Odds update broadcast initiated",
            "game_id": odds_data["game_id"],
            "sportsbook": odds_data["sportsbook"]
        }

    except Exception as e:
        logger.error(f"Error triggering odds update: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger odds update")


@router.post("/prediction-update")
async def trigger_prediction_update(
    prediction_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Trigger a prediction update broadcast via WebSocket

    Example payload:
    {
        "game_id": "2024_week1_KC_BUF",
        "home_team": "KC",
        "away_team": "BUF",
        "home_win_probability": 0.65,
        "away_win_probability": 0.35,
        "predicted_spread": -3.2,
        "confidence_level": 0.82,
        "model_version": "v1.2.0",
        "updated_at": "2024-09-14T20:30:00Z"
    }
    """
    try:
        required_fields = ["game_id", "home_team", "away_team", "home_win_probability", "away_win_probability"]

        # Validate required fields
        for field in required_fields:
            if field not in prediction_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Send prediction update via WebSocket
        background_tasks.add_task(websocket_manager.send_prediction_update, prediction_data)

        logger.info(f"Prediction update triggered for {prediction_data['game_id']}")

        return {
            "success": True,
            "message": "Prediction update broadcast initiated",
            "game_id": prediction_data["game_id"]
        }

    except Exception as e:
        logger.error(f"Error triggering prediction update: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger prediction update")


@router.post("/system-notification")
async def trigger_system_notification(
    notification_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Trigger a system-wide notification via WebSocket

    Example payload:
    {
        "message": "System maintenance scheduled for 2AM EST",
        "level": "warning",
        "channels": ["system", "notifications"]  // Optional: specific channels
    }
    """
    try:
        if "message" not in notification_data:
            raise HTTPException(status_code=400, detail="Missing required field: message")

        message = notification_data["message"]
        level = notification_data.get("level", "info")
        channels = notification_data.get("channels")

        # Send system notification via WebSocket
        if channels:
            background_tasks.add_task(websocket_handlers.handle_system_alert, message, level, channels)
        else:
            background_tasks.add_task(websocket_manager.send_system_notification, message, level)

        logger.info(f"System notification triggered: {message}")

        return {
            "success": True,
            "message": "System notification broadcast initiated",
            "level": level,
            "channels": channels
        }

    except Exception as e:
        logger.error(f"Error triggering system notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger system notification")


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics
    """
    try:
        stats = websocket_manager.get_stats()

        return {
            "success": True,
            "stats": stats,
            "timestamp": "2024-09-14T20:30:00Z"
        }

    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get WebSocket stats")


@router.post("/test-broadcast")
async def test_broadcast(
    test_data: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = None
):
    """
    Test WebSocket broadcasting functionality
    """
    try:
        if not test_data:
            test_data = {
                "game_id": "test_game_123",
                "home_team": "TEST_HOME",
                "away_team": "TEST_AWAY",
                "home_score": 21,
                "away_score": 14,
                "quarter": 3,
                "time_remaining": "8:42",
                "game_status": "live",
                "updated_at": "2024-09-14T20:30:00Z"
            }

        # Send test update
        background_tasks.add_task(websocket_manager.send_game_update, test_data)

        # Also send test notification
        background_tasks.add_task(
            websocket_manager.send_system_notification,
            "Test broadcast message - WebSocket is working correctly!",
            "info"
        )

        logger.info("Test broadcast initiated")

        return {
            "success": True,
            "message": "Test broadcast initiated",
            "test_data": test_data
        }

    except Exception as e:
        logger.error(f"Error in test broadcast: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute test broadcast")