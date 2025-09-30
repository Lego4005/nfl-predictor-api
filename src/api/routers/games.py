"""
Game Endpoints Router
"""
from fastapi import APIRouter, HTTPException, Query, Path
from src.api.models.game import WeekGamesResponse, BattlesResponse
from src.api.services.database import db_service
from src.api.services.cache import cache_response
from src.api.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/games", tags=["games"])


@router.get("/week/{week_number}", response_model=WeekGamesResponse)
@cache_response(ttl=settings.redis_ttl_games, key_prefix="games_week")
async def get_week_games(
    week_number: int = Path(..., ge=1, le=18),
    include_predictions: bool = Query(default=True),
    include_odds: bool = Query(default=True)
):
    """
    Get all games for specific week with predictions.

    - **week_number**: NFL week number (1-18)
    - **include_predictions**: Include expert predictions (default: true)
    - **include_odds**: Include Vegas odds (default: true)

    Returns:
    - Game schedule with times and venues
    - Weather conditions
    - Vegas lines (spread, moneyline, total)
    - Council consensus predictions
    - Expert participation counts

    - **Caching**: 300 seconds
    - **Rate Limit**: 200 requests/minute
    """
    try:
        games_data = await db_service.get_week_games(
            week_number=week_number,
            include_predictions=include_predictions,
            include_odds=include_odds
        )

        return WeekGamesResponse(
            week=week_number,
            games=games_data
        )

    except Exception as e:
        logger.error(f"Error fetching games for week {week_number}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch games")


@router.get("/battles/active", response_model=BattlesResponse)
@cache_response(ttl=60, key_prefix="battles_active")
async def get_active_battles(
    week: Optional[int] = Query(default=None, ge=1, le=18),
    min_difference: float = Query(default=3.0, ge=0.0, le=20.0)
):
    """
    Get active prediction battles where experts disagree.

    - **week**: Week number (default: current)
    - **min_difference**: Minimum prediction difference to qualify as battle (default: 3.0)

    A "battle" occurs when two high-profile experts make significantly
    different predictions on the same game. Shows:
    - Opposing predictions with confidence levels
    - Bet amounts (if placed)
    - Head-to-head historical record
    - User voting/sentiment

    Perfect for the "Expert Battles" feature where fans can follow
    dramatic disagreements and see who was right.

    - **Caching**: 60 seconds
    - **Rate Limit**: 150 requests/minute
    """
    try:
        battles_data = await db_service.get_active_battles(
            week=week,
            min_difference=min_difference
        )

        return BattlesResponse(battles=battles_data)

    except Exception as e:
        logger.error(f"Error fetching battles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch battles")