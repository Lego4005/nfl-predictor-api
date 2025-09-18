"""
WebSocket Manager for real-time NFL predictions and updates
"""

import json
import asyncio
import logging
from typing import Dict, Set, List, Optional, Any
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .websocket_events import (
    WebSocketEventType, WebSocketMessage, ConnectionMessage,
    HeartbeatMessage, SystemMessage
)


logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Individual WebSocket connection wrapper"""

    def __init__(self, websocket: WebSocket, connection_id: str, user_id: Optional[str] = None):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.subscriptions: Set[str] = set()
        self.is_active = True

    async def send_message(self, message: WebSocketMessage) -> bool:
        """Send message to WebSocket client"""
        try:
            await self.websocket.send_text(message.json())
            return True
        except Exception as e:
            logger.error(f"Error sending message to {self.connection_id}: {e}")
            self.is_active = False
            return False

    async def send_json(self, data: Dict[str, Any]) -> bool:
        """Send raw JSON data to WebSocket client"""
        try:
            await self.websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"Error sending JSON to {self.connection_id}: {e}")
            self.is_active = False
            return False

    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()

    def is_expired(self, timeout_seconds: int = 60) -> bool:
        """Check if connection has expired based on heartbeat"""
        return (datetime.utcnow() - self.last_heartbeat).seconds > timeout_seconds

    def subscribe_to_channel(self, channel: str):
        """Subscribe to a specific channel/topic"""
        self.subscriptions.add(channel)
        logger.info(f"Connection {self.connection_id} subscribed to {channel}")

    def unsubscribe_from_channel(self, channel: str):
        """Unsubscribe from a specific channel/topic"""
        self.subscriptions.discard(channel)
        logger.info(f"Connection {self.connection_id} unsubscribed from {channel}")


class ConnectionManager:
    """Manages all WebSocket connections and broadcasting"""

    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.channels: Dict[str, Set[str]] = {}  # channel -> connection_ids
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self._cleanup_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> str:
        """Accept new WebSocket connection"""
        await websocket.accept()

        connection_id = str(uuid4())
        connection = WebSocketConnection(websocket, connection_id, user_id)
        self.connections[connection_id] = connection

        # Track user connections
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)

        # Send connection acknowledgment
        ack_message = WebSocketMessage(
            event_type=WebSocketEventType.CONNECTION_ACK,
            data=ConnectionMessage(
                connection_id=connection_id,
                server_time=datetime.utcnow(),
                supported_events=list(WebSocketEventType),
                heartbeat_interval=30
            ).dict()
        )

        await connection.send_message(ack_message)

        logger.info(f"New WebSocket connection: {connection_id} (user: {user_id})")
        return connection_id

    async def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]

            # Remove from user connections
            if connection.user_id and connection.user_id in self.user_connections:
                self.user_connections[connection.user_id].discard(connection_id)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]

            # Remove from channels
            for channel in connection.subscriptions:
                if channel in self.channels:
                    self.channels[channel].discard(connection_id)
                    if not self.channels[channel]:
                        del self.channels[channel]

            del self.connections[connection_id]
            logger.info(f"WebSocket connection disconnected: {connection_id}")

    async def send_to_connection(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Send message to specific connection"""
        if connection_id in self.connections:
            return await self.connections[connection_id].send_message(message)
        return False

    async def send_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """Send message to all connections of a specific user"""
        sent_count = 0
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        return sent_count

    async def send_to_channel(self, channel: str, message: WebSocketMessage) -> int:
        """Send message to all connections subscribed to a channel"""
        sent_count = 0
        if channel in self.channels:
            for connection_id in self.channels[channel].copy():
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        return sent_count

    async def broadcast(self, message: WebSocketMessage) -> int:
        """Broadcast message to all active connections"""
        sent_count = 0
        for connection_id in list(self.connections.keys()):
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        return sent_count

    def subscribe_to_channel(self, connection_id: str, channel: str):
        """Subscribe connection to a channel"""
        if connection_id in self.connections:
            self.connections[connection_id].subscribe_to_channel(channel)

            if channel not in self.channels:
                self.channels[channel] = set()
            self.channels[channel].add(connection_id)

    def unsubscribe_from_channel(self, connection_id: str, channel: str):
        """Unsubscribe connection from a channel"""
        if connection_id in self.connections:
            self.connections[connection_id].unsubscribe_from_channel(channel)

            if channel in self.channels:
                self.channels[channel].discard(connection_id)
                if not self.channels[channel]:
                    del self.channels[channel]

    async def handle_heartbeat(self, connection_id: str, heartbeat_data: Dict[str, Any]):
        """Handle heartbeat from client"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.update_heartbeat()

            # Send heartbeat response
            response = WebSocketMessage(
                event_type=WebSocketEventType.HEARTBEAT,
                data=HeartbeatMessage(
                    timestamp=datetime.utcnow(),
                    connection_id=connection_id,
                    client_time=heartbeat_data.get('client_time')
                ).dict()
            )

            await connection.send_message(response)

    async def cleanup_expired_connections(self):
        """Remove expired connections based on heartbeat timeout"""
        expired_connections = []

        for connection_id, connection in self.connections.items():
            if connection.is_expired():
                expired_connections.append(connection_id)

        for connection_id in expired_connections:
            await self.disconnect(connection_id)
            logger.warning(f"Removed expired connection: {connection_id}")

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections"""
        return {
            "total_connections": len(self.connections),
            "total_users": len(self.user_connections),
            "total_channels": len(self.channels),
            "channels": {
                channel: len(connections)
                for channel, connections in self.channels.items()
            }
        }


class WebSocketManager:
    """Main WebSocket manager integrating with FastAPI"""

    def __init__(self):
        self.connection_manager = ConnectionManager()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 60  # seconds

    async def start_background_tasks(self):
        """Start background tasks for connection management"""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("WebSocket background tasks started")

    async def stop_background_tasks(self):
        """Stop background tasks"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("WebSocket background tasks stopped")

    async def _periodic_cleanup(self):
        """Periodic cleanup of expired connections"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self.connection_manager.cleanup_expired_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    async def handle_websocket(self, websocket: WebSocket, user_id: Optional[str] = None):
        """Handle WebSocket connection lifecycle"""
        connection_id = await self.connection_manager.connect(websocket, user_id)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()

                try:
                    message_data = json.loads(data)
                    await self._handle_client_message(connection_id, message_data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {connection_id}: {data}")
                except ValidationError as e:
                    logger.error(f"Invalid message format from {connection_id}: {e}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket client {connection_id} disconnected")
        except Exception as e:
            logger.error(f"Unexpected error with connection {connection_id}: {e}")
        finally:
            await self.connection_manager.disconnect(connection_id)

    async def _handle_client_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle incoming message from WebSocket client"""
        event_type = message_data.get('event_type')
        data = message_data.get('data', {})

        if event_type == WebSocketEventType.HEARTBEAT:
            await self.connection_manager.handle_heartbeat(connection_id, data)

        elif event_type == WebSocketEventType.USER_SUBSCRIPTION:
            channel = data.get('channel')
            if channel:
                self.connection_manager.subscribe_to_channel(connection_id, channel)

        elif event_type == WebSocketEventType.USER_UNSUBSCRIPTION:
            channel = data.get('channel')
            if channel:
                self.connection_manager.unsubscribe_from_channel(connection_id, channel)

        else:
            logger.warning(f"Unknown event type from {connection_id}: {event_type}")

    # Public API methods for sending updates
    async def send_game_update(self, game_data: Dict[str, Any]):
        """Send game update to subscribers"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.GAME_UPDATE,
            data=game_data,
            channel=f"game_{game_data.get('game_id')}"
        )

        # Send to game-specific channel and general games channel
        await self.connection_manager.send_to_channel(f"game_{game_data.get('game_id')}", message)
        await self.connection_manager.send_to_channel("games", message)

    async def send_odds_update(self, odds_data: Dict[str, Any]):
        """Send odds update to subscribers"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.ODDS_UPDATE,
            data=odds_data,
            channel=f"odds_{odds_data.get('game_id')}"
        )

        await self.connection_manager.send_to_channel(f"odds_{odds_data.get('game_id')}", message)
        await self.connection_manager.send_to_channel("odds", message)

    async def send_prediction_update(self, prediction_data: Dict[str, Any]):
        """Send prediction update to subscribers"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.PREDICTION_UPDATE,
            data=prediction_data,
            channel=f"predictions_{prediction_data.get('game_id')}"
        )

        await self.connection_manager.send_to_channel(f"predictions_{prediction_data.get('game_id')}", message)
        await self.connection_manager.send_to_channel("predictions", message)

    async def send_system_notification(self, notification: str, level: str = "info"):
        """Send system-wide notification"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.NOTIFICATION,
            data=SystemMessage(
                message=notification,
                level=level,
                title="System Notification"
            ).dict()
        )

        await self.connection_manager.broadcast(message)

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return self.connection_manager.get_connection_stats()


# Global WebSocket manager instance
websocket_manager = WebSocketManager()