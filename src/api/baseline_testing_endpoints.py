"""
API Endpoints for 2024 Baselines A/B Testing

Provides endpoints for runng baseline model comparisons and managing
model switching policies.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from src.services.supabase_service import SupabaseService
from src.services.baseline_models_service import BaselineModelsService, BaselineResult
from src.services.model_switching_service import ModelSwitchingService, SwitchingDecision

logger = logging.getLogger(__name__)

# Request/Response Models
class BaselineComparisonRequest(BaseModel):
    game_ids: List[str]
    expert_ids: List[str]
    baseline_types: Optional[List[str]] = None
    include_expert_comparison: bool = True

class BaselineComparisonResponse(BaseModel):
    baseline_results: Dict[str, List[Dict[str, Any]]]
    expert_results: Dict[str, List[Dict[str, Any]]]
    comparison_metrics: Dict[str, Dict[str, float]]
    summary: Dict[str, Any]
    execution_time: float

class ModelSwitchRequest(BaseModel):
    expert_id: str
    new_model: str
    reason: str
    force_switch: bool = False

class ModelSwitchResponse(BaseModel):
    success: bool
    expert_id: str
    old_model: str
    new_model: str
    reason: str
    dwell_time_reset: bool

class SwitchingRecommendationsResponse(BaseModel):
    recommendations: Dict[str, Dict[str, Any]]
    summary: Dict[str, Any]
    timestamp: str

# Initialize router
router = APIRouter(prefix="/api/baseline-testing", tags=["baseline-testing"])

# Dependency injection
def get_supabase_service():
    return SupabaseService()

def get_baseline_service(supabase: SupabaseService = Depends(get_supabase_service)):
    return BaselineModelsService(supabase)

def get_switching_service(
    supabase: SupabaseService = Depends(get_supabase_service),
    baseline: BaselineModelsService = Depends(get_baseline_service)
):
    return ModelSwitchingService(supabase, baseline)

@router.post("/compare", response_model=BaselineComparisonResponse)
async def run_baseline_comparison(
    request: BaselineComparisonRequest,
    baseline_service: BaselineModelsService = Depends(get_baseline_service)
):
    """
    Run comprehensive baseline model comparison

    Compares baseline models (coin-flip, market-only, one-shot, deliberate)
    against expert predictions using Brier score, MAE, ROI, and accuracy metrics.
    """
    try:
        logger.info(f"Starting baseline comparison for {len(request.game_ids)} games, {len(request.expert_ids)} experts")

        # Run the comparison
        results = await baseline_service.run_baseline_comparison(
            game_ids=request.game_ids,
            expert_ids=request.expert_ids
        )

        # Filter baseline types if specified
        if request.baseline_types:
            filtered_results = {}
            for baseline_type in request.baseline_types:
                if baseline_type in results['baseline_results']:
                    filtered_results[baseline_type] = results['baseline_results'][baseline_type]
            results['baseline_results'] = filtered_results

        # Remove expert results if not requested
        if not request.include_expert_comparison:
            results['expert_results'] = {}

        return BaselineComparisonResponse(
            baseline_results=results['baseline_results'],
            expert_results=results['expert_results'],
            comparison_metrics=results['comparison_metrics'],
            summary=results['summary'],
            execution_time=results.get('execution_time', 0.0)
        )

    except Exception as e:
        logger.error(f"Baseline comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Baseline comparison failed: {str(e)}")

@router.post("/baseline/{baseline_type}/predict")
async def generate_baseline_prediction(
    baseline_type: str,
    game_id: str = Query(..., description="Game ID for prediction"),
    expert_id: str = Query(..., description="Expert ID for context"),
    baseline_service: BaselineModelsService = Depends(get_baseline_service)
):
    """
    Generate prediction using specific baseline model

    Available baseline types:
    - coin_flip: Random 50/50 predictions
    - market_only: Market odds-based predictions
    - one_shot: Single LLM call without memory
    - deliberate: Rule-based heuristic predictions
    """
    try:
        if baseline_type not in ['coin_flip', 'market_only', 'one_shot', 'deliberate']:
            raise HTTPException(status_code=400, detail=f"Invalid baseline type: {baseline_type}")

        # Generate prediction based on type
        if baseline_type == 'coin_flip':
            result = await baseline_service.generate_coin_flip_predictions(game_id, expert_id)
        elif baseline_type == 'market_only':
            result = await baseline_service.generate_market_only_predictions(game_id, expert_id)
        elif baseline_type == 'one_shot':
            result = await baseline_service.generate_one_shot_predictions(game_id, expert_id)
        elif baseline_type == 'deliberate':
            result = await baseline_service.generate_deliberate_predictions(game_id, expert_id)

        return {
            "model_type": result.model_type,
            "predictions": result.predictions,
            "confidence": result.confidence,
            "execution_time": result.execution_time,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Baseline prediction failed for {baseline_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Baseline prediction failed: {str(e)}")

@router.get("/switching/recommendations", response_model=SwitchingRecommendationsResponse)
async def get_switching_recommendations(
    expert_ids: List[str] = Query(..., description="Expert IDs to evaluate"),
    switching_service: ModelSwitchingService = Depends(get_switching_service)
):
    """
    Get model switching recommendations for experts

    Evaluates each expert's performance and recommends model switches
    based on eligibility gates, performance degradation, and bandit exploration.
    """
    try:
        recommendations = await switching_service.get_switching_recommendations(expert_ids)

        # Convert to serializable format
        serialized_recommendations = {}
        for expert_id, decision in recommendations.items():
            serialized_recommendations[expert_id] = {
                "expert_id": decision.expert_id,
                "current_model": decision.current_model,
                "recommended_model": decision.recommended_model,
                "reason": decision.reason,
                "confidence": decision.confidence,
                "switch_recommended": decision.switch_recommended,
                "dwell_time_remaining": decision.dwell_time_remaining
            }

        # Generate summary
        total_experts = len(recommendations)
        switches_recommended = sum(1 for d in recommendations.values() if d.switch_recommended)

        summary = {
            "total_experts_evaluated": total_experts,
            "switches_recommended": switches_recommended,
            "switch_rate": switches_recommended / total_experts if total_experts > 0 else 0,
            "most_common_reason": "performance_satisfactory",  # Would calculate from actual data
            "experts_in_dwell_time": sum(1 for d in recommendations.values() if d.dwell_time_remaining > 0)
        }

        return SwitchingRecommendationsResponse(
            recommendations=serialized_recommendations,
            summary=summary,
            timestamp=str(datetime.now())
        )

    except Exception as e:
        logger.error(f"Failed to get switching recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.post("/switching/implement", response_model=ModelSwitchResponse)
async def implement_model_switch(
    request: ModelSwitchRequest,
    switching_service: ModelSwitchingService = Depends(get_switching_service)
):
    """
    Implement a model switch for an expert

    Switches an expert from their current model to a new model,
    recording the change and resetting dwell time.
    """
    try:
        # Get current model
        current_model = await switching_service._get_current_model(request.expert_id)

        # Check if switch is needed
        if current_model == request.new_model and not request.force_switch:
            return ModelSwitchResponse(
                success=False,
                expert_id=request.expert_id,
                old_model=current_model,
                new_model=request.new_model,
                reason="No change needed - already using requested model",
                dwell_time_reset=False
            )

        # Implement the switch
        success = await switching_service.implement_model_switch(
            expert_id=request.expert_id,
            new_model=request.new_model,
            reason=request.reason
        )

        return ModelSwitchResponse(
            success=success,
            expert_id=request.expert_id,
            old_model=current_model,
            new_model=request.new_model,
            reason=request.reason,
            dwell_time_reset=success
        )

    except Exception as e:
        logger.error(f"Failed to implement model switch: {e}")
        raise HTTPException(status_code=500, detail=f"Model switch failed: {str(e)}")

@router.get("/switching/analytics")
async def get_switching_analytics(
    switching_service: ModelSwitchingService = Depends(get_switching_service)
):
    """
    Get analytics on model switching performance

    Returns statistics on switching frequency, success rates,
    and model performance comparisons.
    """
    try:
        analytics = await switching_service.get_switching_analytics()
        return analytics

    except Exception as e:
        logger.error(f"Failed to get switching analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")

@router.post("/performance/update")
async def update_model_performance(
    expert_id: str = Query(..., description="Expert ID"),
    model_type: str = Query(..., description="Model type"),
    metrics: Dict[str, float] = ...,
    switching_service: ModelSwitchingService = Depends(get_switching_service)
):
    """
    Update performance metrics for a model

    Updates Brier score, MAE, ROI, accuracy, and other performance
    metrics used for switching decisions.
    """
    try:
        await switching_service.update_model_performance(expert_id, model_type, metrics)

        return {
            "success": True,
            "expert_id": expert_id,
            "model_type": model_type,
            "metrics_updated": list(metrics.keys()),
            "timestamp": str(datetime.now())
        }

    except Exception as e:
        logger.error(f"Failed to update model performance: {e}")
        raise HTTPException(status_code=500, detail=f"Performance update failed: {str(e)}")

@router.get("/models/available")
async def get_available_models():
    """
    Get list of available models for switching

    Returns all baseline and expert models available for assignment.
    """
    return {
        "expert_models": [
            "expert"
        ],
        "baseline_models": [
            "coin_flip",
            "market_only",
            "one_shot",
            "deliberate"
        ],
        "model_descriptions": {
            "expert": "Full expert model with memory and context",
            "coin_flip": "Random 50/50 predictions with noise",
            "market_only": "Predictions based on market odds",
            "one_shot": "Single LLM call without memory",
            "deliberate": "Rule-based heuristic predictions"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint for baseline testing service"""
    return {
        "status": "healthy",
        "service": "baseline-testing",
        "timestamp": str(datetime.now()),
        "version": "1.0.0"
    }

# Add missing import
from datetime import datetime
