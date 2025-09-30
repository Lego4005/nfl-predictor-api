"""
WebSocket Event Handlers
"""
from typing import Dict, Any
from datetime import datetime
from src.api.websocket.manager import connection_manager
import logging

logger = logging.getLogger(__name__)


async def handle_bet_placed(bet_data: Dict[str, Any]):
    """Handle bet_placed event"""
    message = {
        "type": "bet_placed",
        "bet_id": bet_data.get("bet_id"),
        "expert_id": bet_data.get("expert_id"),
        "expert_name": bet_data.get("expert_name"),
        "game_id": bet_data.get("game_id"),
        "bet_amount": bet_data.get("bet_amount"),
        "prediction": bet_data.get("prediction"),
        "confidence": bet_data.get("confidence"),
        "timestamp": datetime.utcnow().isoformat()
    }

    await connection_manager.broadcast("bets", message)
    logger.info(f"Broadcast bet_placed for {bet_data.get('expert_id')}")


async def handle_line_movement(line_data: Dict[str, Any]):
    """Handle line_movement event"""
    message = {
        "type": "line_movement",
        "game_id": line_data.get("game_id"),
        "line_type": line_data.get("line_type"),
        "old_value": line_data.get("old_value"),
        "new_value": line_data.get("new_value"),
        "movement": line_data.get("movement"),
        "timestamp": datetime.utcnow().isoformat()
    }

    await connection_manager.broadcast("lines", message)
    logger.info(f"Broadcast line_movement for {line_data.get('game_id')}")


async def handle_expert_eliminated(elimination_data: Dict[str, Any]):
    """Handle expert_eliminated event"""
    message = {
        "type": "expert_eliminated",
        "expert_id": elimination_data.get("expert_id"),
        "expert_name": elimination_data.get("expert_name"),
        "final_bankroll": elimination_data.get("final_bankroll"),
        "elimination_reason": elimination_data.get("elimination_reason"),
        "final_bet": elimination_data.get("final_bet"),
        "season_stats": elimination_data.get("season_stats"),
        "timestamp": datetime.utcnow().isoformat()
    }

    await connection_manager.broadcast("eliminations", message)
    logger.info(f"Broadcast expert_eliminated for {elimination_data.get('expert_id')}")


async def handle_bankroll_updated(bankroll_data: Dict[str, Any]):
    """Handle bankroll_updated event"""
    message = {
        "type": "bankroll_updated",
        "expert_id": bankroll_data.get("expert_id"),
        "old_balance": bankroll_data.get("old_balance"),
        "new_balance": bankroll_data.get("new_balance"),
        "change": bankroll_data.get("change"),
        "reason": bankroll_data.get("reason"),
        "bet_id": bankroll_data.get("bet_id"),
        "timestamp": datetime.utcnow().isoformat()
    }

    await connection_manager.broadcast("bankroll", message)
    logger.info(f"Broadcast bankroll_updated for {bankroll_data.get('expert_id')}")


async def handle_client_message(client_id: str, message: Dict[str, Any]):
    """Handle incoming messages from clients"""
    message_type = message.get("type")

    if message_type == "subscribe":
        channels = message.get("channels", [])
        filters = message.get("filters", {})
        connection_manager.subscribe(client_id, channels, filters)

        # Send confirmation
        await connection_manager.send_personal_message(client_id, {
            "type": "subscribed",
            "channels": channels,
            "timestamp": datetime.utcnow().isoformat()
        })

    elif message_type == "unsubscribe":
        channels = message.get("channels", [])
        connection_manager.unsubscribe(client_id, channels)

        # Send confirmation
        await connection_manager.send_personal_message(client_id, {
            "type": "unsubscribed",
            "channels": channels,
            "timestamp": datetime.utcnow().isoformat()
        })

    elif message_type == "ping":
        await connection_manager.send_personal_message(client_id, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })

    else:
        logger.warning(f"Unknown message type: {message_type} from {client_id}")