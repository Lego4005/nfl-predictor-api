"""
WebSocket Event Types and Message Structures
"""

from enum import Enum
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel
from datetime import datetime


class WebSocketEventType(str, Enum):
    """WebSocket event types for different update categories"""

    # Game Events
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    GAME_UPDATE = "game_update"
    SCORE_UPDATE = "score_update"
    QUARTER_CHANGE = "quarter_change"

    # Prediction Events
    PREDICTION_UPDATE = "prediction_update"
    PREDICTION_REFRESH = "prediction_refresh"
    MODEL_UPDATE = "model_update"

    # Odds Events
    ODDS_UPDATE = "odds_update"
    LINE_MOVEMENT = "line_movement"

    # System Events
    CONNECTION_ACK = "connection_ack"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    NOTIFICATION = "notification"

    # User Events
    USER_SUBSCRIPTION = "user_subscription"
    USER_UNSUBSCRIPTION = "user_unsubscription"


class WebSocketMessage(BaseModel):
    """Standard WebSocket message structure"""

    event_type: WebSocketEventType
    data: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()
    message_id: Optional[str] = None
    user_id: Optional[str] = None
    channel: Optional[str] = None

    class Config:
        use_enum_values = True


class GameUpdateMessage(BaseModel):
    """Game update specific message"""

    game_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    quarter: int
    time_remaining: str
    game_status: str
    updated_at: datetime


class PredictionUpdateMessage(BaseModel):
    """Prediction update specific message"""

    game_id: str
    home_team: str
    away_team: str
    home_win_probability: float
    away_win_probability: float
    predicted_spread: float
    confidence_level: float
    model_version: str
    updated_at: datetime


class OddsUpdateMessage(BaseModel):
    """Odds update specific message"""

    game_id: str
    sportsbook: str
    home_team: str
    away_team: str
    spread: float
    moneyline_home: int
    moneyline_away: int
    over_under: float
    updated_at: datetime


class SystemMessage(BaseModel):
    """System notification message"""

    message: str
    level: str = "info"  # info, warning, error
    title: Optional[str] = None
    action_required: bool = False


class ConnectionMessage(BaseModel):
    """Connection acknowledgment message"""

    connection_id: str
    server_time: datetime
    supported_events: list[WebSocketEventType]
    heartbeat_interval: int = 30  # seconds


class HeartbeatMessage(BaseModel):
    """Heartbeat message for connection monitoring"""

    timestamp: datetime
    connection_id: str
    client_time: Optional[datetime] = None