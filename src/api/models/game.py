"""
Pydantic models for Game-related responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Weather(BaseModel):
    temperature: int
    wind_speed: int
    conditions: str


class VegasLines(BaseModel):
    spread: float
    moneyline_home: int
    moneyline_away: int
    total: float


class CouncilGameConsensus(BaseModel):
    spread: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ExpertCount(BaseModel):
    predictions: int
    bets_placed: int


class Game(BaseModel):
    game_id: str
    home_team: str
    away_team: str
    game_time: datetime
    venue: str
    weather: Optional[Weather] = None
    vegas_lines: VegasLines
    council_consensus: Optional[CouncilGameConsensus] = None
    expert_count: ExpertCount


class WeekGamesResponse(BaseModel):
    week: int
    games: List[Game]


class BattleExpert(BaseModel):
    expert_id: str
    prediction: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bet_amount: Optional[float] = None
    reasoning: str


class HeadToHeadRecord(BaseModel):
    expert_a_wins: int
    expert_b_wins: int
    last_5: str


class UserVotes(BaseModel):
    expert_a: int
    expert_b: int


class Battle(BaseModel):
    battle_id: str
    game_id: str
    category: str
    expert_a: BattleExpert
    expert_b: BattleExpert
    head_to_head_record: HeadToHeadRecord
    user_votes: UserVotes


class BattlesResponse(BaseModel):
    battles: List[Battle]