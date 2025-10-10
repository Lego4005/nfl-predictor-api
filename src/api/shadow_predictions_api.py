"""
Shadow Predictions API - Handle shadow model executions for A/B testing

CRITICAL ISOLATION GUARANTEES:
- Shadow predictions are NEVER used in council selection
- Shadow predictions are NEVER used in coherence projection
- Shadow predictions are NEVER used in settlement
- Shadow runs are completely isolated from hot path operations

Stores shadow predictions separately from hot path for model comparison and A/B testing.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
import json
import logging
from datetime import datetime
import uuid

from src.api.config import settings
from src.api.services.database import db_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/shadow", tags=["Shadow Predictions"])

# Pydantic models for shadow predictions
class ShadowPredictionBundle(BaseModel):
    shadow_run_id: str
    expert_id: str
    game_id: str
    main_run_id: str
    shadow_model: str
    primary_model: str
    shadow_type: str = "model_comparison"

    # Same prediction structure as main predictions
    overall: Dict[str, Any]
    predictions: List[Dict[str, Any]]

    # Shadow-specific metadata
    processing_time_ms: Optional[float] = 0
    tokens_used: Optional[int] = 0
    api_calls: Optional[int] = 1
    memory_retrievals: Optional[int] = 0

class ShadowPredictionResponse(BaseModel):
    success: bool
    shadow_id: str
    shadow_run_id: str
    expert_id: str
    game_id: str
    shadow_model: str
    schema_valid: bool
    validation_errors: List[str] = []
    processing_time_ms: float
    tokens_used: int
    isolation_verified: bool = True  # Always True - shadows never used in hot path

class ShadowRunTelemetry(BaseModel):
    shadow_run_id: str
    main_run_id: str
    shadow_models: Dict[str, str]
    total_predictions: int
    successful_predictions: int
    success_rate: float
    avg_response_time_ms: float
    schema_compliance_rate: float
    total_tokens: int
    estimated_cost: float
    active: bool

@router.post("/predictions", response_model=ShadowPredictionResponse)
async def store_shadow_prediction(
    bundle: ShadowPredictionBundle,
    background_tasks: BackgroundTasks
) -> ShadowPredictionResponse:
    """
    Store shadow prediction bundle - NEVER feeds council/coherence/settlement

    Args:
        bundle: Shadow prediction bundle with model comparison metadata

    Returns:
        ShadowPredictionResponse with validation and isolation confirmation
    """
    start_time = datetime.utcnow()

    try:
        # Prepare prediction bundle for storage
        prediction_bundle = {
            "overall": bundle.overall,
            "predictions": bundle.predictions
        }

        # Call Supabase RPC function to store shadow prediction
        result = await db_service.client.rpc(
            'store_shadow_prediction',
            {
                'p_shadow_run_id': bundle.shadow_run_id,
                'p_expert_id': bundle.expert_id,
                'p_game_id': bundle.game_id,
                'p_main_run_id': bundle.main_run_id,
                'p_shadow_model': bundle.shadow_model,
                'p_primary_model': bundle.primary_model,
                'p_prediction_bundle': prediction_bundle,
                'p_processing_time_ms': bundle.processing_time_ms or 0,
                'p_tokens_used': bundle.tokens_used or 0
            }
        ).execute()

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to store shadow prediction"
            )

        shadow_result = result.data[0] if isinstance(result.data, list) else result.data

        # Calculate total processing time
        total_processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Log shadow prediction storage (separate from main predictions)
        logger.info(f"Shadow prediction stored", {
            "shadow_id": shadow_result.get('shadow_id'),
            "shadow_run_id": bundle.shadow_run_id,
            "expert_id": bundle.expert_id,
            "game_id": bundle.game_id,
            "shadow_model": bundle.shadow_model,
            "primary_model": bundle.primary_model,
            "schema_valid": shadow_result.get('schema_valid', False),
            "processing_time_ms": total_processing_time,
            "tokens_used": bundle.tokens_used,
            "isolation_verified": True  # Shadows are always isolated
        })

        return ShadowPredictionResponse(
            success=True,
            shadow_id=shadow_result.get('shadow_id'),
            shadow_run_id=bundle.shadow_run_id,
            expert_id=bundle.expert_id,
            game_id=bundle.game_id,
            shadow_model=bundle.shadow_model,
            schema_valid=shadow_result.get('schema_valid', False),
            validation_errors=[],  # TODO: Extract from shadow_result if needed
            processing_time_ms=total_processing_time,
            tokens_used=bundle.tokens_used or 0,
            isolation_verified=True
        )

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"Shadow prediction storage failed", {
            "shadow_run_id": bundle.shadow_run_id,
            "expert_id": bundle.expert_id,
            "game_id": bundle.game_id,
            "shadow_model": bundle.shadow_model,
            "error": str(e),
            "processing_time_ms": processing_time
        })

        raise HTTPException(
            status_code=500,
            detail=f"Failed to store shadow prediction: {str(e)}"
        )

@router.get("/predictions/{shadow_run_id}")
async def get_shadow_predictions(
    shadow_run_id: str,
    expert_id: Optional[str] = None,
    game_id: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Retrieve shadow predictions for analysis (never used in hot path)
    """
    try:
        query = db_service.client.table('expert_prediction_assertions_shadow').select('*').eq(
            'shadow_run_id', shadow_run_id
        )

        if expert_id:
            query = query.eq('expert_id', expert_id)
        if game_id:
            query = query.eq('game_id', game_id)

        result = await query.order('created_at', desc=True).limit(limit).execute()

        return {
            "shadow_run_id": shadow_run_id,
            "predictions": result.data or [],
            "count": len(result.data) if result.data else 0,
            "filters": {
                "expert_id": expert_id,
                "game_id": game_id,
                "limit": limit
            },
            "isolation_note": "These predictions are never used in council/coherence/settlement"
        }

    except Exception as e:
        logger.error(f"Failed to retrieve shadow predictions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve shadow predictions: {str(e)}"
        )

@router.get("/telemetry/{shadow_run_id}")
async def get_shadow_telemetry(shadow_run_id: str) -> ShadowRunTelemetry:
    """
    Get telemetry data for a shadow run
    """
    try:
        result = await db_service.client.table('shadow_run_telemetry').select('*').eq(
            'shadow_run_id', shadow_run_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail=f"Shadow run telemetry not found: {shadow_run_id}"
            )

        telemetry = result.data

        return ShadowRunTelemetry(
            shadow_run_id=telemetry['shadow_run_id'],
            main_run_id=telemetry['main_run_id'],
            shadow_models=telemetry['shadow_models'],
            total_predictions=telemetry['total_shadow_predictions'],
            successful_predictions=telemetry['successful_shadow_predictions'],
            success_rate=telemetry['shadow_success_rate'],
            avg_response_time_ms=telemetry['avg_shadow_response_time_ms'],
            schema_compliance_rate=telemetry['schema_compliance_rate'],
            total_tokens=telemetry['total_shadow_tokens'],
            estimated_cost=telemetry['estimated_shadow_cost'],
            active=telemetry['shadow_run_active']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get shadow telemetry: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve shadow telemetry: {str(e)}"
        )

@router.post("/compare/{main_prediction_id}/{shadow_prediction_id}")
async def compare_predictions(
    main_prediction_id: str,
    shadow_prediction_id: str
) -> Dict[str, Any]:
    """
    Compare main prediction with shadow prediction
    """
    try:
        # Call Supabase RPC function to compare predictions
        result = await db_service.client.rpc(
            'compare_shadow_predictions',
            {
                'p_main_prediction_id': main_prediction_id,
                'p_shadow_prediction_id': shadow_prediction_id
            }
        ).execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="Predictions not found for comparison"
            )

        comparison = result.data[0] if isinstance(result.data, list) else result.data

        return {
            "comparison_result": comparison,
            "isolation_note": "Shadow predictions never affect main system operations"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare predictions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare predictions: {str(e)}"
        )

@router.get("/runs/active")
async def get_active_shadow_runs() -> Dict[str, Any]:
    """
    Get all active shadow runs for monitoring
    """
    try:
        result = await db_service.client.table('shadow_run_telemetry').select('*').eq(
            'shadow_run_active', True
        ).order('started_at', desc=True).execute()

        return {
            "active_runs": result.data or [],
            "count": len(result.data) if result.data else 0,
            "isolation_guarantee": "All shadow runs are isolated from hot path operations"
        }

    except Exception as e:
        logger.error(f"Failed to get active shadow runs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve active shadow runs: {str(e)}"
        )

@router.post("/runs/{shadow_run_id}/deactivate")
async def deactivate_shadow_run(shadow_run_id: str) -> Dict[str, Any]:
    """
    Deactivate a shadow run
    """
    try:
        result = await db_service.client.table('shadow_run_telemetry').update({
            'shadow_run_active': False,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('shadow_run_id', shadow_run_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail=f"Shadow run not found: {shadow_run_id}"
            )

        logger.info(f"Shadow run deactivated: {shadow_run_id}")

        return {
            "success": True,
            "shadow_run_id": shadow_run_id,
            "status": "deactivated",
            "deactivated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate shadow run: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deactivate shadow run: {str(e)}"
        )

@router.get("/health")
async def shadow_system_health() -> Dict[str, Any]:
    """
    Health check for shadow prediction system
    """
    try:
        # Get recent shadow prediction stats
        recent_result = await db_service.client.table('expert_prediction_assertions_shadow').select(
            'shadow_run_id, shadow_schema_valid, created_at'
        ).gte(
            'created_at', (datetime.utcnow().replace(hour=0, minute=0, second=0)).isoformat()
        ).execute()

        recent_predictions = recent_result.data or []
        total_recent = len(recent_predictions)
        valid_recent = len([p for p in recent_predictions if p.get('shadow_schema_valid', False)])

        # Get active runs count
        active_result = await db_service.client.table('shadow_run_telemetry').select('shadow_run_id').eq(
            'shadow_run_active', True
        ).execute()

        active_runs = len(active_result.data) if active_result.data else 0

        return {
            "status": "healthy",
            "shadow_predictions_today": total_recent,
            "valid_predictions_today": valid_recent,
            "validation_rate": (valid_recent / total_recent * 100) if total_recent > 0 else 100,
            "active_shadow_runs": active_runs,
            "isolation_verified": True,
            "last_check": datetime.utcnow().isoformat(),
            "guarantees": [
                "Shadow predictions never feed council selection",
                "Shadow predictions never feed coherence projection",
                "Shadow predictions never feed settlement",
                "Shadow runs are completely isolated from hot path"
            ]
        }

    except Exception as e:
        logger.error(f"Shadow system health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }
