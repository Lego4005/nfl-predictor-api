"""
Pydantic models for Prediction-related responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PredictionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PredictionCategory(str, Enum):
    SPREAD = "spread"
    MONEYLINE = "moneyline"
    TOTAL = "total"
    PROP = "prop"


class Prediction(BaseModel):
    prediction_id: str
    game_id: str
    category: PredictionCategory
    prediction: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    bet_placed: bool
    bet_amount: Optional[float] = None
    status: PredictionStatus
    created_at: datetime


class PredictionsResponse(BaseModel):
    expert_id: str
    week: int
    predictions: List[Prediction]