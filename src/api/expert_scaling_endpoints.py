"""
Expert Pool Scaling API Endpoints

Provides REST API endpoints for expert pool scaling, shadel management,
and expert performance comparison dashboards.

Requirements: 4.7 - Scale to full expert pool
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from ..services.expert_pool_scaling_service import (
    ExpertPoolScalingService, ExpertStatus, ExpertTier
)

logger = logging.getLogger(__name__)

# Global scaling service instance
scaling_service = None

def get_scaling_service() -> ExpertPoolScalingService:
    """Get or create scaling service instance"""
    global scaling_service
    if scaling_service is None:
        scaling_service = ExpertPoolScalingService()
    return scaling_service

# Create router
router = APIRouter(prefix="/api/experts", tags=["expert_scaling"])

@router.get("/pool/status")
async def get_expert_pool_status():
    """Get current expert pool status and statistics"""
    try:
        service = get_scaling_service()
        status = service.get_expert_pool_status()

        if 'error' in status:
            raise HTTPException(status_code=500, detail=status['error'])

        return status
    except Exception as e:
        logger.error(f"Expert pool status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pool/scale")
async def scale_expert_pool(
    run_id: str = Query("run_2025_pilot4", description="Run ID for scaling operation")
):
    """Scale expert pool from 4 to 15 experts"""
    try:
        service = get_scaling_service()
        result = service.scale_to_full_expert_pool(run_id)

        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])

        return result
    except Exception as e:
        logger.error(f"Expert pool scaling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_expert_performance(
    expert_id: Optional[str] = Query(None, description="Specific expert ID (optional)")
):
    """Get expert performance metrics"""
    try:
        service = get_scaling_service()
        metrics = service.get_expert_performance_metrics(expert_id)

        if 'error' in metrics:
            raise HTTPException(status_code=404, detail=metrics['error'])

        return metrics
    except Exception as e:
        logger.error(f"Expert performance retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard")
async def get_expert_leaderboard():
    """Get expert performance leaderboard"""
    try:
        service = get_scaling_service()
        leaderboard = service._generate_expert_leaderboard()

        if not leaderboard:
            raise HTTPException(status_code=500, detail="Failed to generate leaderboard")

        return leaderboard
    except Exception as e:
        logger.error(f"Expert leaderboard retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison-matrix")
async def get_expert_comparison_matrix():
    """Get expert performance comparison matrix"""
    try:
        service = get_scaling_service()
        matrix = service._generate_comparison_matrix()

        if not matrix:
            raise HTTPException(status_code=500, detail="Failed to generate comparison matrix")

        return matrix
    except Exception as e:
        logger.error(f"Expert comparison matrix retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shadow-performance")
async def get_shadow_performance():
    """Get shadow model performance data"""
    try:
        service = get_scaling_service()
        shadow_data = service._generate_shadow_performance_dashboard()

        if not shadow_data:
            raise HTTPException(status_code=500, detail="Failed to generate shadow performance data")

        return shadow_data
    except Exception as e:
        logger.error(f"Shadow performance retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tier-analysis")
async def get_tier_analysis():
    """Get expert tier analysis"""
    try:
        service = get_scaling_service()
        tier_data = service._generate_tier_analysis_dashboard()

        if not tier_data:
            raise HTTPException(status_code=500, detail="Failed to generate tier analysis")

        return tier_data
    except Exception as e:
        logger.error(f"Tier analysis retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/performance/update")
async def update_expert_performance(
    expert_id: str,
    prediction_result: Dict[str, Any]
):
    """Update expert performance based on prediction result"""
    try:
        service = get_scaling_service()
        success = service.update_expert_performance(expert_id, prediction_result)

        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to update performance for expert {expert_id}")

        return {
            'success': True,
            'expert_id': expert_id,
            'updated_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Expert performance update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/comprehensive")
async def get_comprehensive_dashboard():
    """Get comprehensive expert performance dashboard data"""
    try:
        service = get_scaling_service()

        # Gather all dashboard components
        pool_status = service.get_expert_pool_status()
        leaderboard = service._generate_expert_leaderboard()
        comparison_matrix = service._generate_comparison_matrix()
        shadow_performance = service._generate_shadow_performance_dashboard()
        tier_analysis = service._generate_tier_analysis_dashboard()

        dashboard_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'pool_status': pool_status,
            'leaderboard': leaderboard,
            'comparison_matrix': comparison_matrix,
            'shadow_performance': shadow_performance,
            'tier_analysis': tier_analysis,
            'summary': {
                'total_experts': pool_status.get('expert_pool_size', 0),
                'scaling_complete': pool_status.get('scaling_complete', False),
                'shadow_models_active': len(shadow_performance.get('shadow_data', [])),
                'elite_tier_experts': tier_analysis.get('tier_distribution', {}).get('elite', 0),
                'average_accuracy': pool_status.get('aggregate_metrics', {}).get('average_accuracy', 0.0),
                'average_roi': pool_status.get('aggregate_metrics', {}).get('average_roi', 0.0)
            }
        }

        return dashboard_data
    except Exception as e:
        logger.error(f"Comprehensive dashboard retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Convenience endpoints for specific expert groups

@router.get("/pilot-experts")
async def get_pilot_experts():
    """Get pilot expert (original 4) performance"""
    try:
        service = get_scaling_service()
        pilot_metrics = {}

        for expert_id in service.pilot_experts:
            metrics = service.get_expert_performance_metrics(expert_id)
            if 'error' not in metrics:
                pilot_metrics[expert_id] = metrics

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'pilot_expert_count': len(service.pilot_experts),
            'pilot_experts': pilot_metrics
        }
    except Exception as e:
        logger.error(f"Pilot experts retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/new-experts")
async def get_new_experts():
    """Get new expert (added in scaling) performance"""
    try:
        service = get_scaling_service()
        new_expert_ids = [expert for expert in service.full_expert_pool if expert not in service.pilot_experts]
        new_metrics = {}

        for expert_id in new_expert_ids:
            metrics = service.get_expert_performance_metrics(expert_id)
            if 'error' not in metrics:
                new_metrics[expert_id] = metrics

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'new_expert_count': len(new_expert_ids),
            'new_experts': new_metrics
        }
    except Exception as e:
        logger.error(f"New experts retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/elite-tier")
async def get_elite_tier_experts():
    """Get elite tier expert performance"""
    try:
        service = get_scaling_service()
        elite_experts = {}

        for expert_id, metrics in service.expert_metrics.items():
            if metrics.tier == ExpertTier.ELITE:
                expert_data = service.get_expert_performance_metrics(expert_id)
                if 'error' not in expert_data:
                    elite_experts[expert_id] = expert_data

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'elite_expert_count': len(elite_experts),
            'elite_experts': elite_experts
        }
    except Exception as e:
        logger.error(f"Elite tier experts retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shadow-models")
async def get_shadow_model_status():
    """Get shadow model configuration and status"""
    try:
        service = get_scaling_service()

        shadow_experts = []
        for expert_id, metrics in service.expert_metrics.items():
            if metrics.status == ExpertStatus.SHADOW or metrics.shadow_predictions > 0:
                shadow_experts.append({
                    'expert_id': expert_id,
                    'name': metrics.name,
                    'shadow_predictions': metrics.shadow_predictions,
                    'shadow_accuracy': metrics.shadow_accuracy,
                    'main_accuracy': metrics.accuracy,
                    'performance_delta': metrics.shadow_vs_main_delta
                })

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'shadow_enabled': service.shadow_enabled,
            'shadow_percentage': service.shadow_percentage,
            'experts_with_shadow': len(shadow_experts),
            'shadow_experts': shadow_experts
        }
    except Exception as e:
        logger.error(f"Shadow model status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/shadow-models/toggle")
async def toggle_shadow_models(
    enabled: bool = Query(..., description="Enable or disable shadow models")
):
    """Toggle shadow model execution"""
    try:
        service = get_scaling_service()
        service.shadow_enabled = enabled

        return {
            'success': True,
            'shadow_enabled': service.shadow_enabled,
            'updated_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Shadow model toggle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
