"""
WebSocket Connection Manager
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {
            "bets": set(),
            "lines": set(),
            "eliminations": set(),
            "bankroll": set()
        }
        self.client_filters: Dict[str, dict] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        """Connect a new client"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

        # Send welcome message
        await self.send_personal_message(client_id, {
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    def disconnect(self, client_id: str):
        """Disconnect a client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Remove from all subscriptions
        for channel in self.subscriptions.values():
            channel.discard(client_id)

        if client_id in self.client_filters:
            del self.client_filters[client_id]

        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, client_id: str, message: dict):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, channel: str, message: dict):
        """Broadcast message to all subscribers of a channel"""
        if channel not in self.subscriptions:
            return

        subscribers = list(self.subscriptions[channel])

        for client_id in subscribers:
            # Check filters
            if not self._should_send_to_client(client_id, message):
                continue

            await self.send_personal_message(client_id, message)

    def subscribe(self, client_id: str, channels: List[str], filters: dict = None):
        """Subscribe client to channels with optional filters"""
        for channel in channels:
            if channel in self.subscriptions:
                self.subscriptions[channel].add(client_id)

        if filters:
            self.client_filters[client_id] = filters

        logger.info(f"Client {client_id} subscribed to {channels}")

    def unsubscribe(self, client_id: str, channels: List[str]):
        """Unsubscribe client from channels"""
        for channel in channels:
            if channel in self.subscriptions:
                self.subscriptions[channel].discard(client_id)

        logger.info(f"Client {client_id} unsubscribed from {channels}")

    def _should_send_to_client(self, client_id: str, message: dict) -> bool:
        """Check if message should be sent to client based on filters"""
        if client_id not in self.client_filters:
            return True

        filters = self.client_filters[client_id]

        # Check expert_ids filter
        if "expert_ids" in filters and "expert_id" in message:
            if message["expert_id"] not in filters["expert_ids"]:
                return False

        # Check game_ids filter
        if "game_ids" in filters and "game_id" in message:
            if message["game_id"] not in filters["game_ids"]:
                return False

        return True

    async def heartbeat_loop(self):
        """Send periodic heartbeat to all connections"""
        while True:
            await asyncio.sleep(30)  # 30 second interval

            disconnected = []
            for client_id, websocket in list(self.active_connections.items()):
                try:
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Heartbeat failed for {client_id}: {e}")
                    disconnected.append(client_id)

            # Clean up disconnected clients
            for client_id in disconnected:
                self.disconnect(client_id)


# Singleton instance
connection_manager = ConnectionManager()