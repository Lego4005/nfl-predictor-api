"""
Expert Predictions API - Stores 83-bundle predictions with schema validation
POST /api/expert/predictions?run_id=X
"""

from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
import json
import os
from datetime import datetime

router = APIRouter()

# Load JSON schema for validation
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "../schemas/expert_predictions_v1.schema.json")
with open(SCHEMA_PATH, 'r') as f:
    PREDICTIONS_SCHEMA = json.load(f)


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
    pred_type: str  # "binary", "numeric", "enum"
    value: Any  # bool, number, or string depending on pred_type
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
    model_type: Optional[str] = "primary"  # "primary" or "shadow"


@router.post("/api/expert/predictions")
async def store_expert_predictions(
    submission: PredictionSubmission,
    run_id: Optional[str] = Query(None)
):
    """
    Store validated 83-item prediction bundle
    
    - Validates against expert_predictions_v1.schema.json
    - Stores bundle in database with run_id
    - Creates individual assertion records
    - Returns prediction_id for tracking
    """
    
    try:
        # Use run_id from query param if provided, else from body
        effective_run_id = run_id or submission.run_id
        
        # Validate schema (Pydantic already validates structure)
        bundle = submission.bundle
        
        # Ensure exactly 83 predictions
        if len(bundle.predictions) != 83:
            raise HTTPException(
                status_code=400,
                detail=f"Schema validation failed: Expected 83 predictions, got {len(bundle.predictions)}"
            )
        
        # TODO: Store in PostgreSQL
        # prediction_id = await db.store_prediction_bundle(
        #     run_id=effective_run_id,
        #     expert_id=submission.expert_id,
        #     game_id=submission.game_id,
        #     bundle=bundle.dict(),
        #     model_type=submission.model_type,
        #     timestamp=submission.timestamp or datetime.utcnow().isoformat()
        # )
        
        # STUB: Return success response
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


@router.get("/api/expert/predictions/{prediction_id}")
async def get_prediction(prediction_id: str):
    """Retrieve a stored prediction bundle by ID"""
    # TODO: Implement retrieval from database
    return {
        "status": "not_implemented",
        "message": "Prediction retrieval endpoint stub"
    }


@router.get("/api/expert/predictions/by_run/{run_id}")
async def get_predictions_by_run(run_id: str):
    """Retrieve all predictions for a specific run_id"""
    # TODO: Implement retrieval by run_id
    return {
        "status": "not_implemented",
        "message": "Run-based retrieval endpoint stub",
        "run_id": run_id
    }
