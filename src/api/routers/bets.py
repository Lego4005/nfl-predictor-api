"""
Betting Endpoints Router
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.api.models.bet import LiveBetsResponse, BetHistoryResponse
from src.api.services.database import db_service
from src.api.services.cache import cache_response
from src.api.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bets", tags=["bets"])


@router.get("/live", response_model=LiveBetsResponse)
@cache_response(ttl=settings.redis_ttl_bets, key_prefix="bets_live")
async def get_live_bets(
    game_id: Optional[str] = Query(default=None),
    expert_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    status: str = Query(default="pending", regex="^(pending|won|lost|push)$")
):
    """
    Get real-time betting feed showing recent expert bets.

    - **game_id**: Filter by specific game (optional)
    - **expert_id**: Filter by specific expert (optional)
    - **limit**: Number of bets (default: 50, max: 200)
    - **status**: "pending" | "won" | "lost" | "push" (default: "pending")

    Shows:
    - Recent bets with full details
    - Expert confidence and risk levels
    - Potential payouts
    - Bankroll percentages
    - Real-time updates

    - **Caching**: 10 seconds (near real-time)
    - **Rate Limit**: 300 requests/minute
    """
    try:
        bets_data = await db_service.get_live_bets(
            game_id=game_id,
            expert_id=expert_id,
            limit=limit,
            status=status
        )

        # Calculate summary
        total_at_risk = sum(bet.get("bet_amount", 0.0) for bet in bets_data)
        potential_payout = sum(bet.get("potential_payout", 0.0) for bet in bets_data)
        avg_confidence = (
            sum(bet.get("confidence", 0.0) for bet in bets_data) / len(bets_data)
            if bets_data else 0.0
        )

        return LiveBetsResponse(
            bets=bets_data,
            summary={
                "total_at_risk": total_at_risk,
                "potential_payout": potential_payout,
                "avg_confidence": avg_confidence
            }
        )

    except Exception as e:
        logger.error(f"Error fetching live bets: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch live bets")


@router.get("/expert/{expert_id}/history", response_model=BetHistoryResponse)
@cache_response(ttl=60, key_prefix="bet_history")
async def get_bet_history(
    expert_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    result: str = Query(default="all", regex="^(won|lost|push|all)$")
):
    """
    Get bet history for specific expert.

    - **expert_id**: Expert identifier
    - **limit**: Number of bets (default: 50)
    - **offset**: Pagination offset
    - **result**: "won" | "lost" | "push" | "all" (default: "all")

    Returns complete betting history with:
    - Settled bets with outcomes
    - Profit/loss calculations
    - Performance statistics
    - Win rate and ROI metrics

    - **Caching**: 60 seconds
    - **Rate Limit**: 150 requests/minute
    """
    try:
        # Verify expert exists
        expert = await db_service.get_expert_by_id(expert_id)
        if not expert:
            raise HTTPException(status_code=404, detail=f"Expert {expert_id} not found")

        # Get bet history
        history_data = await db_service.get_bet_history(
            expert_id=expert_id,
            limit=limit,
            offset=offset,
            result=result
        )

        bets = history_data.get("bets", [])

        # Calculate statistics
        total_bets = len(bets)
        wins = sum(1 for bet in bets if bet.get("result") == "won")
        losses = sum(1 for bet in bets if bet.get("result") == "lost")
        pushes = sum(1 for bet in bets if bet.get("result") == "push")

        total_wagered = sum(bet.get("bet_amount", 0.0) for bet in bets)
        total_profit = sum(bet.get("profit", 0.0) for bet in bets)

        win_rate = wins / total_bets if total_bets > 0 else 0.0
        roi = total_profit / total_wagered if total_wagered > 0 else 0.0
        avg_bet_size = total_wagered / total_bets if total_bets > 0 else 0.0

        return BetHistoryResponse(
            expert_id=expert_id,
            bet_history=bets,
            statistics={
                "total_bets": total_bets,
                "wins": wins,
                "losses": losses,
                "pushes": pushes,
                "win_rate": win_rate,
                "roi": roi,
                "avg_bet_size": avg_bet_size
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bet history for {expert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bet history")