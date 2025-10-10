"""
Expert Context API - Provides memory context for expert predictions
Handles run_id isolation and memory retrieval
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from src.services.memory_retrieval_service import memory_retrieval_service
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Expert Context"])


@router.get("/context/{expert_id}/{game_id}")
async def get_expert_context(
    expert_id: str,
    game_id: str,
    run_id: Optional[str] = Query(default=None, description="Run ID for experimental isolation"),
    k: Optional[int] = Query(default=None, description="Number of memories to retrieve (10-20)"),
    alpha: Optional[float] = Query(default=None, description="Recency blending factor (0.0-1.0)")
) -> Dict[str, Any]:
    """
    Get memory context for expert prediction generation

    Args:
        expert_id: Expert identifier (e.g., 'conservative_analyzer')
        game_id: Game identifier
        run_id: Optional run ID for experimental isolation (defaults to current run)
        k: Optional memory count override (defaults to expert persona config)
        alpha: Optional recency alpha override (defaults to expert persona config)

    Returns:
        Memory context including episodic memories, team knowledge, and matchup data
    """
    start_time = datetime.utcnow()

    try:
        # Use provided run_id or default to current run
        effective_run_id = run_id or settings.get_run_id()

        # Build game context from game_id
        game_context = await _build_game_context(game_id)

        # Build persona config if overrides provided
        persona_config = {}
        if k is not None:
            persona_config['memory_k'] = k
        if alpha is not None:
            persona_config['recency_alpha'] = alpha

        # Retrieve memory context
        memory_context = await memory_retrieval_service.retrieve_memory_context(
            expert_id=expert_id,
            game_context=game_context,
            persona_config=persona_config if persona_config else None,
            run_id=effective_run_id
        )

        # Calculate response time
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Build response
        response = {
            "expert_id": expert_id,
            "game_id": game_id,
            "run_id": effective_run_id,
            "game_context": game_context,
            "episodic_memories": [
                {
                    "memory_id": mem.memory_id,
                    "content": mem.content,
                    "similarity_score": float(mem.similarity_score),
                    "recency_score": float(mem.recency_score),
                    "combined_score": float(mem.combined_score),
                    "metadata": mem.metadata
                }
                for mem in memory_context.episodic_memories
            ],
            "team_knowledge": memory_context.team_knowledge,
            "matchup_memories": [
                {
                    "memory_id": mem.memory_id,
                    "content": mem.content,
                    "similarity_score": float(mem.similarity_score),
                    "recency_score": float(mem.recency_score),
                    "combined_score": float(mem.combined_score),
                    "metadata": mem.metadata
                }
                for mem in memory_context.matchup_memories
            ],
            "retrieval_stats": {
                **memory_context.retrieval_stats,
                "api_response_time_ms": response_time_ms
            }
        }

        # Log successful retrieval
        logger.info(f"Context retrieved for {expert_id}/{game_id}", {
            "run_id": effective_run_id,
            "response_time_ms": response_time_ms,
            "episodic_count": len(memory_context.episodic_memories),
            "team_knowledge_keys": len(memory_context.team_knowledge),
            "matchup_count": len(memory_context.matchup_memories)
        })

        return response

    except Exception as e:
        logger.error(f"Context retrieval failed for {expert_id}/{game_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve context: {str(e)}"
        )


@router.get("/context/{expert_id}/{game_id}/stats")
async def get_context_stats(
    expert_id: str,
    game_id: str,
    run_id: Optional[str] = Query(default=None, description="Run ID for experimental isolation")
) -> Dict[str, Any]:
    """
    Get context retrieval statistics without full memory content
    Useful for performance monitoring and debugging
    """
    try:
        effective_run_id = run_id or settings.get_run_id()

        # Build minimal game context
        game_context = {"game_id": game_id}

        # Get retrieval stats only
        memory_context = await memory_retrieval_service.retrieve_memory_context(
            expert_id=expert_id,
            game_context=game_context,
            run_id=effective_run_id
        )

        return {
            "expert_id": expert_id,
            "game_id": game_id,
            "run_id": effective_run_id,
            "stats": memory_context.retrieval_stats,
            "counts": {
                "episodic_memories": len(memory_context.episodic_memories),
                "team_knowledge_keys": len(memory_context.team_knowledge),
                "matchup_memories": len(memory_context.matchup_memories)
            }
        }

    except Exception as e:
        logger.error(f"Context stats retrieval failed for {expert_id}/{game_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve context stats: {str(e)}"
        )


async def _build_game_context(game_id: str) -> Dict[str, Any]:
    """
    Build game context from game_id
    This is a placeholder implementation that should be replaced with actual game data retrieval
    """
    # TODO: Replace with actual game data retrieval from database
    # For now, parse basic info from game_id if it follows a pattern

    try:
        # Example game_id format: "2025_week_1_buf_kc" or similar
        parts = game_id.split('_')

        if len(parts) >= 4:
            season = parts[0] if parts[0].isdigit() else "2025"
            week = parts[2] if len(parts) > 2 and parts[2].isdigit() else "1"
            away_team = parts[-2].upper() if len(parts) >= 2 else "AWAY"
            home_team = parts[-1].upper() if len(parts) >= 1 else "HOME"
        else:
            # Fallback for unrecognized format
            season = "2025"
            week = "1"
            away_team = "AWAY"
            home_team = "HOME"

        return {
            "game_id": game_id,
            "season": season,
            "week": week,
            "away_team": away_team,
            "home_team": home_team,
            "weather": "Unknown",  # TODO: Fetch from weather service
            "game_time": None,     # TODO: Fetch from schedule
            "venue": None          # TODO: Fetch from game data
        }

    except Exception as e:
        logger.warning(f"Failed to parse game_id {game_id}: {e}")
        return {
            "game_id": game_id,
            "season": "2025",
            "week": "1",
            "away_team": "AWAY",
            "home_team": "HOME"
        }


@router.get("/runs/{run_id}/stats")
async def get_run_stats(run_id: str) -> Dict[str, Any]:
    """
    Get statistics for a specific experimental run
    """
    try:
        from src.database.supabase_client import supabase

        # Get run statistics using the RPC function
        result = await supabase.rpc('get_run_statistics', {'p_run_id': run_id}).execute()

        if result.data:
            return result.data
        else:
            return {
                "run_id": run_id,
                "expert_count": 0,
                "prediction_count": 0,
                "bet_count": 0,
                "status": "not_found"
            }

    except Exception as e:
        logger.error(f"Failed to get run stats for {run_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve run statistics: {str(e)}"
        )


@router.get("/runs/current")
async def get_current_run() -> Dict[str, Any]:
    """
    Get information about the current active run
    """
    current_run_id = settings.get_run_id()

    return {
        "run_id": current_run_id,
        "expert_council_enabled": settings.is_expert_council_enabled(),
        "memory_config": settings.get_memory_config(),
        "feature_flags": {
            "shadow_runs": settings.ENABLE_SHADOW_RUNS,
            "post_game_reflection": settings.ENABLE_POST_GAME_REFLECTION
        }
    }
