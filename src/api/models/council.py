"""
Pydantic models for Council-related responses
"""
from pydantic import BaseModel, Field
from typing import List, Dict


class CouncilMember(BaseModel):
    expert_id: str
    rank: int
    selection_score: float = Field(..., ge=0.0, le=1.0)
    vote_weight: float = Field(..., ge=0.0, le=1.0)
    reason_selected: str


class SelectionCriteria(BaseModel):
    accuracy_weight: float
    recent_performance_weight: float
    consistency_weight: float
    calibration_weight: float
    specialization_weight: float


class CurrentCouncilResponse(BaseModel):
    week: int
    council_members: List[CouncilMember]
    selection_criteria: SelectionCriteria


class VoteBreakdown(BaseModel):
    pass  # Dynamic structure based on predictions


class ConsensusCategory(BaseModel):
    prediction: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    agreement_level: float = Field(..., ge=0.0, le=1.0)
    vote_breakdown: Dict[str, float]


class ExpertVote(BaseModel):
    expert_id: str
    vote_weight: float
    prediction: str
    confidence: float


class Disagreement(BaseModel):
    expert_a: str
    expert_b: str
    category: str
    difference: str


class CouncilConsensus(BaseModel):
    spread: ConsensusCategory
    winner: ConsensusCategory


class ConsensusResponse(BaseModel):
    game_id: str
    consensus: CouncilConsensus
    expert_votes: List[ExpertVote]
    disagreements: List[Disagreement]