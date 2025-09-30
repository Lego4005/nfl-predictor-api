"""
Council Endpoints Router
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.api.models.council import CurrentCouncilResponse, ConsensusResponse
from src.api.services.database import db_service
from src.api.services.cache import cache_response
from src.api.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/council", tags=["council"])


@router.get("/current", response_model=CurrentCouncilResponse)
@cache_response(ttl=settings.redis_ttl_council, key_prefix="council_current")
async def get_council_current(
    week: Optional[int] = Query(default=None, ge=1, le=18)
):
    """
    Get current week's top 5 council members.

    - **week**: Week number (default: current week)

    Council selection based on:
    - Accuracy (35%)
    - Recent performance (25%)
    - Consistency (20%)
    - Calibration (10%)
    - Specialization (10%)

    - **Caching**: 1 hour (council changes weekly)
    - **Rate Limit**: 200 requests/minute
    """
    try:
        council_data = await db_service.get_council_current(week)

        members = council_data.get("members", [])

        # Transform to response model
        council_members = []
        for member in members[:5]:  # Top 5 only
            council_members.append({
                "expert_id": member.get("expert_id"),
                "rank": member.get("rank"),
                "selection_score": member.get("selection_score", 0.0),
                "vote_weight": member.get("vote_weight", 0.2),
                "reason_selected": member.get("reason_selected", "")
            })

        return CurrentCouncilResponse(
            week=week or 5,  # Default to current week
            council_members=council_members,
            selection_criteria={
                "accuracy_weight": 0.35,
                "recent_performance_weight": 0.25,
                "consistency_weight": 0.20,
                "calibration_weight": 0.10,
                "specialization_weight": 0.10
            }
        )

    except Exception as e:
        logger.error(f"Error fetching council: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch council data")


@router.get("/consensus/{game_id}", response_model=ConsensusResponse)
@cache_response(ttl=60, key_prefix="council_consensus")
async def get_council_consensus(game_id: str):
    """
    Get weighted voting consensus for specific game.

    - **game_id**: Game identifier (e.g., "2025_05_KC_BUF")

    Returns weighted voting from top 5 council members, showing:
    - Consensus prediction with confidence
    - Agreement level (how aligned the council is)
    - Vote breakdown
    - Individual expert votes
    - Notable disagreements

    - **Caching**: 60 seconds
    - **Rate Limit**: 150 requests/minute
    """
    try:
        consensus_data = await db_service.get_consensus_for_game(game_id)

        if not consensus_data:
            raise HTTPException(status_code=404, detail=f"No consensus found for game {game_id}")

        # Transform to response model
        response = {
            "game_id": game_id,
            "consensus": {
                "spread": {
                    "prediction": consensus_data.get("spread_prediction", ""),
                    "confidence": consensus_data.get("spread_confidence", 0.0),
                    "agreement_level": consensus_data.get("spread_agreement", 0.0),
                    "vote_breakdown": consensus_data.get("spread_votes", {})
                },
                "winner": {
                    "prediction": consensus_data.get("winner_prediction", ""),
                    "confidence": consensus_data.get("winner_confidence", 0.0),
                    "agreement_level": consensus_data.get("winner_agreement", 0.0),
                    "vote_breakdown": consensus_data.get("winner_votes", {})
                }
            },
            "expert_votes": consensus_data.get("expert_votes", []),
            "disagreements": consensus_data.get("disagreements", [])
        }

        return ConsensusResponse(**response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching consensus for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch consensus data")