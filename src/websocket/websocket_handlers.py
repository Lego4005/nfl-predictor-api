"""
WebSocket Request Handlers and Route Integration
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import logging

from .websocket_manager import websocket_manager
from .websocket_events import WebSocketEventType, WebSocketMessage


logger = logging.getLogger(__name__)

# Create WebSocket router
websocket_router = APIRouter()


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None)
):
    """
    Main WebSocket endpoint for real-time updates

    Query Parameters:
    - user_id: Optional user identifier for personalized updates
    - token: Optional authentication token for protected channels
    """
    # TODO: Add authentication validation if token is provided
    # if token:
    #     user_id = validate_token(token)

    await websocket_manager.handle_websocket(websocket, user_id)


@websocket_router.websocket("/ws/games")
async def games_websocket(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint specifically for game updates
    Automatically subscribes to 'games' channel
    """
    connection_id = await websocket_manager.connection_manager.connect(websocket, user_id)

    # Auto-subscribe to games channel
    websocket_manager.connection_manager.subscribe_to_channel(connection_id, "games")

    try:
        await websocket_manager.handle_websocket(websocket, user_id)
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.connection_manager.disconnect(connection_id)


@websocket_router.websocket("/ws/odds")
async def odds_websocket(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint specifically for odds updates
    Automatically subscribes to 'odds' channel
    """
    connection_id = await websocket_manager.connection_manager.connect(websocket, user_id)

    # Auto-subscribe to odds channel
    websocket_manager.connection_manager.subscribe_to_channel(connection_id, "odds")

    try:
        await websocket_manager.handle_websocket(websocket, user_id)
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.connection_manager.disconnect(connection_id)


@websocket_router.websocket("/ws/predictions")
async def predictions_websocket(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint specifically for prediction updates
    Automatically subscribes to 'predictions' channel
    """
    connection_id = await websocket_manager.connection_manager.connect(websocket, user_id)

    # Auto-subscribe to predictions channel
    websocket_manager.connection_manager.subscribe_to_channel(connection_id, "predictions")

    try:
        await websocket_manager.handle_websocket(websocket, user_id)
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.connection_manager.disconnect(connection_id)


@websocket_router.websocket("/ws/game/{game_id}")
async def game_specific_websocket(
    websocket: WebSocket,
    game_id: str,
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for specific game updates
    Automatically subscribes to game-specific channels
    """
    connection_id = await websocket_manager.connection_manager.connect(websocket, user_id)

    # Auto-subscribe to game-specific channels
    websocket_manager.connection_manager.subscribe_to_channel(connection_id, f"game_{game_id}")
    websocket_manager.connection_manager.subscribe_to_channel(connection_id, f"odds_{game_id}")
    websocket_manager.connection_manager.subscribe_to_channel(connection_id, f"predictions_{game_id}")

    try:
        await websocket_manager.handle_websocket(websocket, user_id)
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.connection_manager.disconnect(connection_id)


class WebSocketHandlers:
    """
    Helper class for handling WebSocket events from other parts of the application
    """

    def __init__(self, manager=None):
        self.manager = manager or websocket_manager

    async def handle_game_score_change(self, game_id: str, home_score: int, away_score: int, **kwargs):
        """Handle game score updates"""
        game_data = {
            "game_id": game_id,
            "home_score": home_score,
            "away_score": away_score,
            "event": "score_update",
            **kwargs
        }

        await self.manager.send_game_update(game_data)
        logger.info(f"Sent score update for game {game_id}: {home_score}-{away_score}")

    async def handle_game_status_change(self, game_id: str, status: str, **kwargs):
        """Handle game status changes (started, ended, etc.)"""
        game_data = {
            "game_id": game_id,
            "game_status": status,
            "event": "status_update",
            **kwargs
        }

        await self.manager.send_game_update(game_data)
        logger.info(f"Sent status update for game {game_id}: {status}")

    async def handle_odds_change(self, game_id: str, sportsbook: str, odds_data: dict):
        """Handle odds/line movements"""
        odds_update = {
            "game_id": game_id,
            "sportsbook": sportsbook,
            "event": "odds_change",
            **odds_data
        }

        await self.manager.send_odds_update(odds_update)
        logger.info(f"Sent odds update for game {game_id} from {sportsbook}")

    async def handle_prediction_refresh(self, game_id: str, prediction_data: dict):
        """Handle ML prediction updates"""
        prediction_update = {
            "game_id": game_id,
            "event": "prediction_refresh",
            **prediction_data
        }

        await self.manager.send_prediction_update(prediction_update)
        logger.info(f"Sent prediction update for game {game_id}")

    async def handle_system_alert(self, message: str, level: str = "info", channels: list = None):
        """Handle system-wide alerts and notifications"""
        if channels:
            # Send to specific channels
            for channel in channels:
                notification_data = {
                    "message": message,
                    "level": level,
                    "timestamp": str(websocket_manager.connection_manager.connections[list(websocket_manager.connection_manager.connections.keys())[0]].connected_at)
                }

                websocket_message = WebSocketMessage(
                    event_type=WebSocketEventType.NOTIFICATION,
                    data=notification_data,
                    channel=channel
                )

                await self.manager.connection_manager.send_to_channel(channel, websocket_message)
        else:
            # Broadcast to all connections
            await self.manager.send_system_notification(message, level)

        logger.info(f"Sent system notification: {message} (level: {level})")


# Global handlers instance
websocket_handlers = WebSocketHandlers()