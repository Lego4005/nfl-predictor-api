"""
Expert Endpoints Router
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.api.models.expert import (
    ExpertsResponse, BankrollDetailResponse, MemoriesResponse
)
from src.api.models.prediction import PredictionsResponse
from src.api.services.database import db_service
from src.api.services.cache import cache_response
from src.api.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/experts", tags=["experts"])


@router.get("", response_model=ExpertsResponse)
@cache_response(ttl=settings.redis_ttl_experts, key_prefix="experts")
async def get_experts():
    """
    Get all 15 AI experts with current stats.

    - **Caching**: 60 seconds
    - **Rate Limit**: 100 requests/minute
    """
    try:
        experts_data = await db_service.get_experts()

        # Transform database data to response model
        experts = []
        for expert_data in experts_data:
            expert = {
                "expert_id": expert_data.get("expert_id"),
                "name": expert_data.get("name"),
                "emoji": expert_data.get("emoji"),
                "archetype": expert_data.get("archetype"),
                "bankroll": {
                    "current": expert_data.get("current_bankroll", 10000.0),
                    "starting": expert_data.get("starting_bankroll", 10000.0),
                    "change_percent": expert_data.get("bankroll_change_percent", 0.0),
                    "status": expert_data.get("bankroll_status", "safe")
                },
                "performance": {
                    "accuracy": expert_data.get("accuracy", 0.5),
                    "win_rate": expert_data.get("win_rate", 0.5),
                    "total_bets": expert_data.get("total_bets", 0),
                    "roi": expert_data.get("roi", 0.0)
                },
                "specialization": {
                    "category": expert_data.get("specialization_category", "general"),
                    "weight": expert_data.get("specialization_weight", 0.5)
                }
            }
            experts.append(expert)

        return ExpertsResponse(experts=experts)

    except Exception as e:
        logger.error(f"Error fetching experts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch experts")


@router.get("/{expert_id}/bankroll", response_model=BankrollDetailResponse)
@cache_response(ttl=30, key_prefix="expert_bankroll")
async def get_expert_bankroll(
    expert_id: str,
    timeframe: str = Query(default="week", regex="^(week|month|season)$"),
    include_bets: bool = Query(default=False)
):
    """
    Get detailed bankroll history for specific expert.

    - **expert_id**: Expert identifier (e.g., "the-analyst")
    - **timeframe**: "week" | "month" | "season" (default: "week")
    - **include_bets**: Include bet details (default: false)

    - **Caching**: 30 seconds
    - **Rate Limit**: 200 requests/minute
    """
    try:
        # Verify expert exists
        expert = await db_service.get_expert_by_id(expert_id)
        if not expert:
            raise HTTPException(status_code=404, detail=f"Expert {expert_id} not found")

        # Get bankroll history
        history_data = await db_service.get_expert_bankroll_history(expert_id, timeframe)

        response = {
            "expert_id": expert_id,
            "current_balance": expert.get("current_bankroll", 10000.0),
            "starting_balance": expert.get("starting_bankroll", 10000.0),
            "peak_balance": expert.get("peak_bankroll", 10000.0),
            "lowest_balance": expert.get("lowest_bankroll", 10000.0),
            "total_wagered": expert.get("total_wagered", 0.0),
            "total_won": expert.get("total_won", 0.0),
            "total_lost": expert.get("total_lost", 0.0),
            "history": history_data.get("history", []),
            "risk_metrics": {
                "volatility": expert.get("volatility", 0.0),
                "sharpe_ratio": expert.get("sharpe_ratio", 0.0),
                "max_drawdown": expert.get("max_drawdown", 0.0)
            }
        }

        return BankrollDetailResponse(**response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bankroll for {expert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bankroll data")


@router.get("/{expert_id}/predictions", response_model=PredictionsResponse)
@cache_response(ttl=settings.redis_ttl_predictions, key_prefix="expert_predictions")
async def get_expert_predictions(
    expert_id: str,
    week: Optional[int] = Query(default=None, ge=1, le=18),
    status: Optional[str] = Query(default="all", regex="^(pending|completed|all)$"),
    min_confidence: Optional[float] = Query(default=None, ge=0.0, le=1.0)
):
    """
    Get expert's predictions with confidence levels.

    - **expert_id**: Expert identifier
    - **week**: Week number (default: current week)
    - **status**: "pending" | "completed" | "all" (default: "all")
    - **min_confidence**: 0.0 - 1.0 (filter by minimum confidence)

    - **Caching**: 120 seconds
    - **Rate Limit**: 150 requests/minute
    """
    try:
        # Verify expert exists
        expert = await db_service.get_expert_by_id(expert_id)
        if not expert:
            raise HTTPException(status_code=404, detail=f"Expert {expert_id} not found")

        # Get predictions
        predictions_data = await db_service.get_expert_predictions(
            expert_id=expert_id,
            week=week,
            status=status if status != "all" else None,
            min_confidence=min_confidence
        )

        return PredictionsResponse(
            expert_id=expert_id,
            week=week or 5,  # Default to current week
            predictions=predictions_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching predictions for {expert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch predictions")


@router.get("/{expert_id}/memories", response_model=MemoriesResponse)
@cache_response(ttl=300, key_prefix="expert_memories")
async def get_expert_memories(
    expert_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    importance_min: Optional[float] = Query(default=None, ge=0.0, le=1.0)
):
    """
    Get episodic memories for Memory Lane feature.

    - **expert_id**: Expert identifier
    - **limit**: Number of memories (default: 20, max: 100)
    - **offset**: Pagination offset
    - **importance_min**: Filter by importance score (0.0 - 1.0)

    - **Caching**: 300 seconds (memories don't change often)
    - **Rate Limit**: 100 requests/minute
    """
    try:
        # Verify expert exists
        expert = await db_service.get_expert_by_id(expert_id)
        if not expert:
            raise HTTPException(status_code=404, detail=f"Expert {expert_id} not found")

        # Get memories
        memories_data = await db_service.get_expert_memories(
            expert_id=expert_id,
            limit=limit,
            offset=offset,
            importance_min=importance_min
        )

        return MemoriesResponse(
            expert_id=expert_id,
            memories=memories_data.get("memories", []),
            total_count=memories_data.get("total_count", 0),
            pagination={
                "offset": offset,
                "limit": limit,
                "has_more": (offset + limit) < memories_data.get("total_count", 0)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching memories for {expert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch memories")