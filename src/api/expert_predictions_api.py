"""
Expert Predictions API - Store and validate expert prediction bundles
Handles 83-assertion predictions with JSON schema validation and bet creation
"""

from fastapi import HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
import json
import jsonschema
import logging
from datetime import datetime
import uuid

from src.config import settings
from src.database.supabase_client import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Expert Predictions"])

# Load the JSON schema for validation
try:
    with open("schemas/expert_predictions_v1.schema.json", "r") as f:
        PREDICTION_SCHEMA = json.load(f)
except FileNotFoundError:
    logger.error("Expert predictions schema file not found")
    PREDICTION_SCHEMA = None

# Pydantic models for request/response
class PredictionItem(BaseModel):
    category: str
    subject: str
    pred_type: str
    value: Union[bool, float, str]
    confidence: float = Field(..., ge=0, le=1)
    stake_units: float = Field(..., ge=0)
    odds: Dict[str, Any]
    why: List[Dict[str, Any]] = []

class OverallPrediction(BaseModel):
    winner_team_id: str
    home_win_prob: float = Field(..., ge=0, le=1)
    away_win_prob: Optional[float] = Field(None, ge=0, le=1)
    overall_confidence: float = Field(..., ge=0, le=1)
    recency_alpha_used: Optional[float] = Field(None, ge=0, le=1)

class ExpertPredictionBundle(BaseModel):
    expert_id: str
    game_id: str
    run_id: Optional[str] = None
    overall: OverallPrediction
    predictions: List[PredictionItem]
    orchestration_metadata: Optional[Dict[str, Any]] = {}

class PredictionResponse(BaseModel):
    success: bool
    prediction_id: str
    expert_id: str
    game_id: str
    run_id: str
    schema_valid: bool
    validation_errors: List[str] = []
    bets_created: int
    processing_time_ms: float
    metadata: Dict[str, Any] = {}

class ValidationStats(BaseModel):
    total_validations: int
    successful_validations: int
    pass_rate: float
    common_errors: List[Dict[str, Any]]
    last_updated: datetime

# Global validation statistics
validation_stats = {
    "total": 0,
    "successful": 0,
    "errors": {}
}

@router.post("/expert/predictions", response_model=PredictionResponse)
async def store_expert_predictions(
    bundle: ExpertPredictionBundle,
    background_tasks: BackgroundTasks
) -> PredictionResponse:
    """
    Store expert prediction bundle with schema validation and bet creation

    Args:
        bundle: Complete 83-assertion prediction bundle from expert

    Returns:
        PredictionResponse with validation results and processing stats
    """
    start_time = datetime.utcnow()

    try:
        # Use provided run_id or default to current run
        effective_run_id = bundle.run_id or settings.get_run_id()

        # Convert to dict for schema validation
        bundle_dict = bundle.dict()

        # Validate against JSON schema
        schema_valid, validation_errors = validate_prediction_schema(bundle_dict)

        # Update validation statistics
        update_validation_stats(schema_valid, validation_errors)

        # Generate prediction ID
        prediction_id = str(uuid.uuid4())

        # Store prediction in database
        stored_prediction = await store_prediction_bundle(
            prediction_id=prediction_id,
            expert_id=bundle.expert_id,
            game_id=bundle.game_id,
            run_id=effective_run_id,
            bundle_data=bundle_dict,
            schema_valid=schema_valid
        )

        # Create individual bets (background task for performance)
        bets_created = 0
        if schema_valid and stored_prediction:
            background_tasks.add_task(
                create_expert_bets,
                prediction_id,
                bundle.expert_id,
                bundle.game_id,
                effective_run_id,
                bundle.predictions
            )
            bets_created = len(bundle.predictions)

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Log successful storage
        logger.info(f"Prediction stored for {bundle.expert_id}/{bundle.game_id}", {
            "prediction_id": prediction_id,
            "run_id": effective_run_id,
            "schema_valid": schema_valid,
            "processing_time_ms": processing_time,
            "predictions_count": len(bundle.predictions)
        })

        return PredictionResponse(
            success=True,
            prediction_id=prediction_id,
            expert_id=bundle.expert_id,
            game_id=bundle.game_id,
            run_id=effective_run_id,
            schema_valid=schema_valid,
            validation_errors=validation_errors,
            bets_created=bets_created,
            processing_time_ms=processing_time,
            metadata={
                "predictions_count": len(bundle.predictions),
                "overall_confidence": bundle.overall.overall_confidence,
                "orchestration_metadata": bundle.orchestration_metadata
            }
        )

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"Prediction storage failed for {bundle.expert_id}/{bundle.game_id}: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Failed to store predictions: {str(e)}"
        )

@router.get("/expert/predictions/{expert_id}/{game_id}")
async def get_expert_predictions(
    expert_id: str,
    game_id: str,
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve stored expert predictions for a specific game
    """
    try:
        effective_run_id = run_id or settings.get_run_id()

        # Query predictions from database
        result = await supabase.table('expert_predictions_comprehensive').select('*').eq(
            'expert_id', expert_id
        ).eq(
            'game_id', game_id
        ).eq(
            'run_id', effective_run_id
        ).order('created_at', desc=True).limit(1).execute()

        if result.data:
            prediction = result.data[0]
            return {
                "expert_id": expert_id,
                "game_id": game_id,
                "run_id": effective_run_id,
                "prediction_id": prediction['id'],
                "overall": prediction.get('game_outcome', {}),
                "predictions": prediction.get('betting_markets', {}),
                "created_at": prediction['created_at'],
                "confidence_overall": prediction.get('confidence_overall'),
                "schema_valid": prediction.get('points_earned', 0) >= 0  # Proxy for validation
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No predictions found for {expert_id}/{game_id} in run {effective_run_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve predictions for {expert_id}/{game_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve predictions: {str(e)}"
        )

@router.get("/expert/predictions/{expert_id}/recent")
async def get_recent_predictions(
    expert_id: str,
    limit: int = 10,
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get recent predictions for an expert
    """
    try:
        effective_run_id = run_id or settings.get_run_id()

        result = await supabase.table('expert_predictions_comprehensive').select(
            'id, game_id, created_at, confidence_overall, points_earned'
        ).eq(
            'expert_id', expert_id
        ).eq(
            'run_id', effective_run_id
        ).order('created_at', desc=True).limit(limit).execute()

        return {
            "expert_id": expert_id,
            "run_id": effective_run_id,
            "predictions": result.data or [],
            "count": len(result.data) if result.data else 0
        }

    except Exception as e:
        logger.error(f"Failed to retrieve recent predictions for {expert_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent predictions: {str(e)}"
        )

@router.get("/validation/stats")
async def get_validation_stats() -> ValidationStats:
    """
    Get validation statistics for monitoring schema compliance
    """
    try:
        total = validation_stats["total"]
        successful = validation_stats["successful"]
        pass_rate = (successful / total * 100) if total > 0 else 0

        # Get common errors (top 5)
        error_counts = validation_stats["errors"]
        common_errors = [
            {"error": error, "count": count}
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        return ValidationStats(
            total_validations=total,
            successful_validations=successful,
            pass_rate=pass_rate,
            common_errors=common_errors,
            last_updated=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Failed to get validation stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve validation statistics: {str(e)}"
        )

@router.post("/validation/test")
async def test_schema_validation(
    test_bundle: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Test schema validation without storing the prediction
    Useful for debugging and testing
    """
    try:
        schema_valid, validation_errors = validate_prediction_schema(test_bundle)

        return {
            "schema_valid": schema_valid,
            "validation_errors": validation_errors,
            "predictions_count": len(test_bundle.get("predictions", [])),
            "has_overall": "overall" in test_bundle,
            "schema_version": "v1"
        }

    except Exception as e:
        logger.error(f"Schema validation test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Schema validation test failed: {str(e)}"
        )

# Helper functions

def validate_prediction_schema(bundle_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate prediction bundle against JSON schema

    Returns:
        Tuple of (is_valid, error_messages)
    """
    if not PREDICTION_SCHEMA:
        return False, ["Schema file not loaded"]

    try:
        jsonschema.validate(bundle_data, PREDICTION_SCHEMA)
        return True, []
    except jsonschema.ValidationError as e:
        error_msg = f"Schema validation failed: {e.message}"
        if e.path:
            error_msg += f" at path: {'.'.join(str(p) for p in e.path)}"
        return False, [error_msg]
    except Exception as e:
        return False, [f"Validation error: {str(e)}"]

def update_validation_stats(schema_valid: bool, errors: List[str]):
    """Update global validation statistics"""
    validation_stats["total"] += 1

    if schema_valid:
        validation_stats["successful"] += 1
    else:
        for error in errors:
            # Simplify error message for counting
            simple_error = error.split(":")[0] if ":" in error else error
            validation_stats["errors"][simple_error] = validation_stats["errors"].get(simple_error, 0) + 1

async def store_prediction_bundle(
    prediction_id: str,
    expert_id: str,
    game_id: str,
    run_id: str,
    bundle_data: Dict[str, Any],
    schema_valid: bool
) -> bool:
    """
    Store prediction bundle in expert_predictions_comprehensive table
    """
    try:
        # Prepare data for storage
        insert_data = {
            "id": prediction_id,
            "expert_id": expert_id,
            "game_id": game_id,
            "run_id": run_id,
            "prediction_timestamp": datetime.utcnow().isoformat(),
            "confidence_overall": bundle_data["overall"]["overall_confidence"],

            # Store predictions in JSONB fields
            "game_outcome": bundle_data["overall"],
            "betting_markets": {
                "predictions": bundle_data["predictions"],
                "schema_valid": schema_valid
            },

            # Additional metadata
            "reasoning": f"Expert {expert_id} predictions for {game_id}",
            "key_factors": [pred["category"] for pred in bundle_data["predictions"][:5]],  # Top 5 categories

            # Performance tracking (will be updated after game completion)
            "points_earned": 0 if schema_valid else -10,  # Penalty for invalid schema
        }

        # Insert into database
        result = await supabase.table('expert_predictions_comprehensive').insert(insert_data).execute()

        return bool(result.data)

    except Exception as e:
        logger.error(f"Failed to store prediction bundle: {e}")
        return False

async def create_expert_bets(
    prediction_id: str,
    expert_id: str,
    game_id: str,
    run_id: str,
    predictions: List[PredictionItem]
):
    """
    Create individual bet records from predictions (background task)
    """
    try:
        bets_data = []

        for prediction in predictions:
            bet_data = {
                "id": str(uuid.uuid4()),
                "expert_id": expert_id,
                "game_id": game_id,
                "prediction_id": prediction_id,
                "run_id": run_id,

                # Bet details
                "category": prediction.category,
                "subject": prediction.subject,
                "pred_type": prediction.pred_type,
                "value": json.dumps(prediction.value),  # Store as JSON string
                "confidence": prediction.confidence,
                "stake_units": prediction.stake_units,

                # Odds information
                "odds_type": prediction.odds["type"],
                "odds_value": json.dumps(prediction.odds["value"]),

                # Settlement (will be updated later)
                "settled": False,
                "settlement_result": None,
                "payout": 0,

                "created_at": datetime.utcnow().isoformat()
            }
            bets_data.append(bet_data)

        # Batch insert bets
        if bets_data:
            result = await supabase.table('expert_bets').insert(bets_data).execute()
            logger.info(f"Created {len(bets_data)} bets for {expert_id}/{game_id}")

    except Exception as e:
        logger.error(f"Failed to create expert bets: {e}")

# Validation monitoring endpoint
@router.get("/validation/monitor")
async def monitor_validation_health() -> Dict[str, Any]:
    """
    Monitor validation system health for alerting
    """
    try:
        total = validation_stats["total"]
        successful = validation_stats["successful"]
        pass_rate = (successful / total * 100) if total > 0 else 100

        # Health status based on pass rate
        if pass_rate >= 98.5:
            status = "healthy"
        elif pass_rate >= 95.0:
            status = "warning"
        else:
            status = "critical"

        return {
            "status": status,
            "pass_rate": pass_rate,
            "target_pass_rate": 98.5,
            "total_validations": total,
            "successful_validations": successful,
            "failed_validations": total - successful,
            "health_check_time": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Validation health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "health_check_time": datetime.utcnow().isoformat()
        }
