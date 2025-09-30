"""
Pydantic models for Expert-related responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BankrollStatus(str, Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGER = "danger"
    ELIMINATED = "eliminated"


class Archetype(str, Enum):
    DATA_DRIVEN = "data_driven"
    GUT_FEELING = "gut_feeling"
    STATISTICAL = "statistical"
    MOMENTUM = "momentum"
    CONTRARIAN = "contrarian"
    SHARP = "sharp"


class BankrollInfo(BaseModel):
    current: float = Field(..., description="Current bankroll amount")
    starting: float = Field(default=10000.0, description="Starting bankroll")
    change_percent: float = Field(..., description="Change percentage from start")
    status: BankrollStatus


class PerformanceMetrics(BaseModel):
    accuracy: float = Field(..., ge=0.0, le=1.0)
    win_rate: float = Field(..., ge=0.0, le=1.0)
    total_bets: int = Field(..., ge=0)
    roi: float


class Specialization(BaseModel):
    category: str
    weight: float = Field(..., ge=0.0, le=1.0)


class Expert(BaseModel):
    expert_id: str
    name: str
    emoji: str
    archetype: Archetype
    bankroll: BankrollInfo
    performance: PerformanceMetrics
    specialization: Specialization


class ExpertsResponse(BaseModel):
    experts: List[Expert]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BankrollHistoryEntry(BaseModel):
    timestamp: datetime
    balance: float
    change: float
    reason: str


class RiskMetrics(BaseModel):
    volatility: float
    sharpe_ratio: float
    max_drawdown: float


class BankrollDetailResponse(BaseModel):
    expert_id: str
    current_balance: float
    starting_balance: float
    peak_balance: float
    lowest_balance: float
    total_wagered: float
    total_won: float
    total_lost: float
    history: List[BankrollHistoryEntry]
    risk_metrics: RiskMetrics


class MemoryType(str, Enum):
    LESSON_LEARNED = "lesson_learned"
    SUCCESS = "success"
    FAILURE = "failure"
    PATTERN = "pattern"


class Memory(BaseModel):
    memory_id: str
    game_id: str
    memory_type: MemoryType
    content: str
    emotional_valence: float = Field(..., ge=-1.0, le=1.0)
    importance_score: float = Field(..., ge=0.0, le=1.0)
    recalled_count: int = Field(default=0)
    created_at: datetime


class MemoriesResponse(BaseModel):
    expert_id: str
    memories: List[Memory]
    total_count: int
    pagination: dict