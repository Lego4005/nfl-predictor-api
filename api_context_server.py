"""
Standalone FastAPI server for Context Pack and Predictions endpoints
Run with: uvicorn api_context_server:app --reload --port 8000
"""

from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
import json
import os
from datetime import datetime

app = FastAPI(title="NFL Expert Context & Predictions API", version="1.0.0")

# Enable CORS for Agentuity agents (localhost:3500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3500", "http://127.0.0.1:3500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load category registry
CATEGORY_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "config/category_registry.json")
with open(CATEGORY_REGISTRY_PATH, 'r') as f:
    CATEGORY_REGISTRY = json.load(f)


# ============================================================================
# Context Pack Endpoint
# ============================================================================

@app.get("/api/context/{expert_id}/{game_id}")
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
                "home": {"avg_score": 24.5, "def_rank": 8, "recent_form": "W-W-L-W"},
                "away": {"avg_score": 22.1, "def_rank": 12, "recent_form": "L-W-W-L"}
            },
            "matchup_memory": {
                "role_aware": {"h2h_games": 3, "home_wins": 2, "avg_margin": 5.3},
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
            "combined_score": 0.85 - (i * 0.03),
            "similarity": 0.80 - (i * 0.02),
            "recency_score": 0.90 - (i * 0.04),
            "summary": f"Similar matchup {i+1}: {['Home favored', 'Close game', 'Defensive battle', 'High scoring'][i % 4]}",
            "outcome": "home_win" if i % 2 == 0 else "away_win",
            "margin": [7, -3, 14, -10, 3, -7, 21, -14][i % 8]
        })
    return memories


# ============================================================================
# Predictions Storage Endpoint
# ============================================================================

class PredictionOverall(BaseModel):
    winner_team_id: str
    home_win_prob: float = Field(ge=0, le=1)
    away_win_prob: float = Field(ge=0, le=1)
    overall_confidence: float = Field(ge=0, le=1)
    recency_alpha_used: Optional[float] = Field(None, ge=0, le=1)


class PredictionWhy(BaseModel):
    memory_id: str
    weight: float = Field(ge=0)


class PredictionItem(BaseModel):
    category: str
    subject: str
    pred_type: str
    value: Any
    confidence: float = Field(ge=0, le=1)
    stake_units: float = Field(ge=0)
    odds: Dict[str, Any]
    why: List[PredictionWhy] = []


class ExpertPredictionBundle(BaseModel):
    overall: PredictionOverall
    predictions: List[PredictionItem] = Field(min_items=83, max_items=83)
    
    @validator('predictions')
    def validate_prediction_count(cls, v):
        if len(v) != 83:
            raise ValueError(f"Expected exactly 83 predictions, got {len(v)}")
        return v


class PredictionSubmission(BaseModel):
    run_id: str
    expert_id: str
    game_id: str
    bundle: ExpertPredictionBundle
    timestamp: Optional[str] = None
    model_type: Optional[str] = "primary"


@app.post("/api/expert/predictions")
async def store_expert_predictions(
    submission: PredictionSubmission,
    run_id: Optional[str] = Query(None)
):
    """Store validated 83-item prediction bundle"""
    
    try:
        effective_run_id = run_id or submission.run_id
        bundle = submission.bundle
        
        if len(bundle.predictions) != 83:
            raise HTTPException(
                status_code=400,
                detail=f"Schema validation failed: Expected 83 predictions, got {len(bundle.predictions)}"
            )
        
        prediction_id = f"pred_{effective_run_id}_{submission.expert_id}_{submission.game_id}"
        
        return {
            "status": "ok",
            "prediction_id": prediction_id,
            "run_id": effective_run_id,
            "expert_id": submission.expert_id,
            "game_id": submission.game_id,
            "assertions_count": len(bundle.predictions),
            "timestamp": submission.timestamp or datetime.utcnow().isoformat(),
            "model_type": submission.model_type
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")


@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "NFL Expert Context & Predictions API",
        "version": "1.0.0",
        "endpoints": {
            "context": "GET /api/context/{expert_id}/{game_id}?run_id=X",
            "predictions": "POST /api/expert/predictions?run_id=X"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)