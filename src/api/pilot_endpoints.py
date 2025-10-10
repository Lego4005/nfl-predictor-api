#!/usr/bin/env python3
"""
4-Expert Pilot FastAPI Endpoints
Core endpoints needed for autonomous expert orchestration
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime

# Import services
from src.services.memory_retrieval_service import MemoryRetrievalService
from src.services.supabase_service import SupabaseService
from src.validation.expert_predictions_validator import ExpertPredictionsValidator

app = FastAPI(title="NFL 4-Expert Pilot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
supabase_service = SupabaseService()
memory_service = MemoryRetrievalService(supabase_service)
validator = ExpertPredictionsValidator()

# Get run_id from environment
RUN_ID = os.getenv("RUN_ID", "run_2025_pilot4")

# Models
class ExpertPredictionBundle(BaseModel):
    expert_id: str
    game_id: str
    predictions: List[Dict[str, Any]]  # 83 predictions
    overall_confidence: float
    winner_team_id: str
    home_win_prob: float
    recency_alpha_used: float
    reasoning_mode: str = "deliberate"
    processing_time_ms: int = 0
    run_id: str = RUN_ID

class ContextResponse(BaseModel):
    game_id: str
    expert_id: str
    memories: List[Dict[str, Any]]
    team_knowledge: Dict[str, Any]
    matchup_memories: List[Dict[str, Any]]
    category_registry: List[Dict[str, Any]]
    recency_alpha: float
    run_id: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "4-expert-pilot-api",
        "run_id": RUN_ID,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/context/{expert_id}/{game_id}")
async def get_expert_context(expert_id: str, game_id: str, run_id: Optional[str] = None) -> ContextResponse:
    """
    Get context for expert prediction generation
    Returns memories, team knowledge, and category registry
    """
    try:
        # Use provided run_id or default
        context_run_id = run_id or RUN_ID

        # Get memories using vector search (K=10-20)
        memories = await memory_service.search_expert_memories(
            expert_id=expert_id,
            query_text=f"Game context for {game_id}",
            k=15,  # Start with 15, can auto-reduce if needed
            run_id=context_run_id
        )

        # Get team knowledge (if available)
        team_knowledge = await get_team_knowledge(game_id, context_run_id)

        # Get matchup memories
        matchup_memories = await get_matchup_memories(game_id, context_run_id)

        # Load category registry
        category_registry = load_category_registry()

        # Calculate recency alpha (persona-specific)
        recency_alpha = get_recency_alpha(expert_id)

        return ContextResponse(
            game_id=game_id,
            expert_id=expert_id,
            memories=memories,
            team_knowledge=team_knowledge,
            matchup_memories=matchup_memories,
            category_registry=category_registry,
            recency_alpha=recency_alpha,
            run_id=context_run_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")

@app.post("/expert/predictions")
async def store_expert_predictions(bundle: ExpertPredictionBundle):
    """
    Store expert predictions bundle (83 assertions + metadata)
    Validates schema and stores in database with run_id
    """
    try:
        # Validate schema
        is_valid = validator.validate_expert_predictions(bundle.dict())
        if not is_valid:
            raise HTTPException(status_code=400, detail="Schema validation failed")

        # Ensure run_id is set
        bundle.run_id = bundle.run_id or RUN_ID

        # Store predictions in database
        result = await store_predictions_in_db(bundle)

        # Enqueue embedding job for new memories
        await enqueue_embedding_job(bundle.expert_id, bundle.game_id, bundle.run_id)

        return {
            "status": "success",
            "expert_id": bundle.expert_id,
            "game_id": bundle.game_id,
            "predictions_count": len(bundle.predictions),
            "schema_valid": True,
            "run_id": bundle.run_id,
            "stored_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction storage failed: {str(e)}")

@app.post("/settle/{game_id}")
async def settle_game(game_id: str, run_id: Optional[str] = None):
    """
    Settle game predictions and update expert learning
    """
    try:
        settle_run_id = run_id or RUN_ID

        # Get game outcome
        outcome = await get_game_outcome(game_id)
        if not outcome:
            raise HTTPException(status_code=404, detail="Game outcome not found")

        # Get all predictions for this game and run
        predictions = await get_game_predictions(game_id, settle_run_id)

        # Grade and settle each prediction
        settlement_results = []
        for prediction in predictions:
            result = await grade_and_settle_prediction(prediction, outcome)
            settlement_results.append(result)

        # Update expert learning (calibration, factor weights)
        await update_expert_learning(game_id, settlement_results, settle_run_id)

        return {
            "status": "settled",
            "game_id": game_id,
            "run_id": settle_run_id,
            "predictions_settled": len(settlement_results),
            "settled_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Settlement failed: {str(e)}")

# Helper functions
async def get_team_knowledge(game_id: str, run_id: str) -> Dict[str, Any]:
    """Get team knowledge for game context"""
    # Placeholder - implement team knowledge retrieval
    return {"home_team": {}, "away_team": {}}

async def get_matchup_memories(game_id: str, run_id: str) -> List[Dict[str, Any]]:
    """Get matchup-specific memories"""
    # Placeholder - implement matchup memory retrieval
    return []

def load_category_registry() -> List[Dict[str, Any]]:
    """Load the 83 betting categories registry"""
    try:
        with open("config/category_registry.json", "r") as f:
            return json.load(f)
    except Exception:
        # Return minimal registry for testing
        return [
            {"category": "winner", "subject": "game", "pred_type": "binary", "description": "Game winner"},
            {"category": "spread", "subject": "game", "pred_type": "numeric", "description": "Point spread"},
            {"category": "total", "subject": "game", "pred_type": "numeric", "description": "Total points"}
        ]

def get_recency_alpha(expert_id: str) -> float:
    """Get persona-specific recency alpha"""
    alphas = {
        "conservative_analyzer": 0.75,  # Less recency bias
        "momentum_rider": 0.90,         # High recency bias
        "contrarian_rebel": 0.80,       # Moderate recency bias
        "value_hunter": 0.78            # Moderate recency bias
    }
    return alphas.get(expert_id, 0.80)

async def store_predictions_in_db(bundle: ExpertPredictionBundle) -> Dict[str, Any]:
    """Store prediction bundle in database"""
    # Placeholder - implement database storage
    return {"stored": True, "id": f"{bundle.expert_id}_{bundle.game_id}"}

async def enqueue_embedding_job(expert_id: str, game_id: str, run_id: str):
    """Enqueue embedding job for new memories"""
    # Placeholder - implement embedding job queue
    pass

async def get_game_outcome(game_id: str) -> Optional[Dict[str, Any]]:
    """Get actual game outcome for settlement"""
    # Placeholder - implement game outcome retrieval
    return None

async def get_game_predictions(game_id: str, run_id: str) -> List[Dict[str, Any]]:
    """Get all predictions for a game and run"""
    # Placeholder - implement prediction retrieval
    return []

async def grade_and_settle_prediction(prediction: Dict[str, Any], outcome: Dict[str, Any]) -> Dict[str, Any]:
    """Grade and settle individual prediction"""
    # Placeholder - implement prediction grading
    return {"graded": True, "correct": False, "pnl": 0.0}

async def update_expert_learning(game_id: str, results: List[Dict[str, Any]], run_id: str):
    """Update expert learning from settlement results"""
    # Placeholder - implement learning updates
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
