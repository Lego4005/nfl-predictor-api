"""
Pydantic models for Bet-related responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class BetStatus(str, Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    PUSH = "push"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class BetType(str, Enum):
    SPREAD = "spread"
    MONEYLINE = "moneyline"
    TOTAL = "total"
    PROP = "prop"


class Bet(BaseModel):
    bet_id: str
    expert_id: str
    expert_name: str
    expert_emoji: str
    game_id: str
    bet_type: BetType
    prediction: str
    bet_amount: float
    bankroll_percentage: float = Field(..., ge=0.0, le=1.0)
    vegas_odds: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    reasoning: str
    potential_payout: float
    placed_at: datetime
    status: BetStatus
    settled_at: Optional[datetime] = None
    result_payout: Optional[float] = None


class BetSummary(BaseModel):
    total_at_risk: float
    potential_payout: float
    avg_confidence: float


class LiveBetsResponse(BaseModel):
    bets: List[Bet]
    summary: BetSummary


class BetHistoryEntry(BaseModel):
    bet_id: str
    game_id: str
    bet_amount: float
    result: BetStatus
    payout: Optional[float] = None
    profit: Optional[float] = None
    settled_at: Optional[datetime] = None


class BetStatistics(BaseModel):
    total_bets: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    roi: float
    avg_bet_size: float


class BetHistoryResponse(BaseModel):
    expert_id: str
    bet_history: List[BetHistoryEntry]
    statistics: BetStatistics