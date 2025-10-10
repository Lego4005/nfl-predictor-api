"""
Context Pack API - Provides memory + game context to Agentuity agents
GET /api/context/:expert_id/:game_id?run_id=X
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import json
import os

router = APIRouter()

# Load category registry
CATEGORY_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "../config/category_registry.json")
with open(CATEGORY_REGISTRY_PATH, 'r') as f:
    CATEGORY_REGISTRY = json.load(f)


@router.get("/api/context/{expert_id}/{game_id}")
async def get_context_pack(
    expert_id: str,
    game_id: str,
    run_id: Optional[str] = Query(None)
):
    """
    Returns Context Pack for expert agent prediction generation
    
    Includes:
    - Top K (10-20) episodic memories with combined scores
    - Team knowledge (home/away)
    - Matchup memories (role-aware H2H)
    - Recency alpha (temporal decay weight)
    - Category registry (83 prediction categories)
    """
    
    try:
        # TODO: Replace with actual memory service call
        # from src.ml.expert_memory_service import ExpertMemoryService
        # memory_service = ExpertMemoryService(supabase_client)
        # memories = await memory_service.get_similar_games(expert_id, context, limit=15)
        
        # STUB: Return mock context pack for now
        context_pack = {
            "game": {
                "game_id": game_id,
                "season": 2025,
                "week": 1,
                "home": "IND",
                "away": "MIA",
                "market": {
                    "spread_home": 1.5,
                    "total": 47.5,
                    "ml_home": -112,
                    "ml_away": -108
                },
                "env": {
                    "roof": "closed",
                    "surface": "fieldturf",
                    "weather": None
                }
            },
            "recency": {
                "alpha": get_recency_alpha(expert_id)
            },
            "memories": generate_stub_memories(expert_id, game_id, k=12),
            "team_knowledge": {
                "home": {"avg_score": 24.5, "def_rank": 8},
                "away": {"avg_score": 22.1, "def_rank": 12}
            },
            "matchup_memory": {
                "role_aware": {"h2h_games": 3, "home_wins": 2},
                "sorted_key": "IND|MIA"
            },
            "registry": CATEGORY_REGISTRY,
            "run_id": run_id
        }
        
        return context_pack
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context pack generation failed: {str(e)}")


def get_recency_alpha(expert_id: str) -> float:
    """Returns recency_alpha based on expert personality"""
    alpha_map = {
        "the-analyst": 0.50,
        "the-gambler": 0.70,
        "the-rebel": 0.65,
        "the-hunter": 0.55,
        "the-rider": 0.80,  # Momentum-heavy
        "the-scholar": 0.40,
        "the-chaos": 0.75,
        "the-intuition": 0.60,
        "the-quant": 0.45,
        "the-reversal": 0.50,
        "the-fader": 0.65,
        "the-sharp": 0.55,
        "the-underdog": 0.70,
        "the-consensus": 0.60,
        "the-exploiter": 0.55
    }
    return alpha_map.get(expert_id, 0.60)


def generate_stub_memories(expert_id: str, game_id: str, k: int = 12) -> List[Dict[str, Any]]:
    """Generate stub memories for development/testing"""
    memories = []
    for i in range(k):
        memories.append({
            "memory_id": f"mem_{game_id}_{expert_id}_{i:03d}",
            "combined_score": 0.85 - (i * 0.03),  # Decreasing scores
            "similarity": 0.80 - (i * 0.02),
            "recency_score": 0.90 - (i * 0.04),
            "summary": f"Similar game {i+1}: Team matchup with defensive focus",
            "outcome": "home_win" if i % 2 == 0 else "away_win",
            "margin": 7 if i % 2 == 0 else -3
        })
    return memories
