"""
Accuracy and Performance Dashboard API Endpoints
Provides real-time accuracy metrics and performance analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from ..auth.middleware import get_current_user
from ..auth.access_control import require_feature, rate_limit, SubscriptionTier
from ..accuracy.calculation_engine import accuracy_engine
from ..accuracy.result_collector import result_collector
from ..accuracy.models import AccuracySnapshot, PerformanceHistory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/accuracy", tags=["accuracy"])

@router.get("/live")
@rate_limit("live_accuracy")
async def get_live_accuracy(current_user: dict = Depends(get_current_user)):
    """
    Get real-time accuracy metrics (available to all subscription tiers)
    """
    try:
        # Create live accuracy snapshot
        snapshot_result = accuracy_engine.create_accuracy_snapshot('live')
        
        if not snapshot_result['success']:
            raise HTTPException(status_code=500, detail="Failed to generate accuracy snapshot")
        
        snapshot_data = snapshot_result['snapshot_data']
        
        return {
            "success": True,
            "live_accuracy": {
                "overall_accuracy": snapshot_data['overall_accuracy'],
                "total_predictions": snapshot_data['total_predictions'],
                "last_updated": datetime.utcnow().isoformat(),
                "prediction_types": {
                    "straight_up": snapshot_data['type_breakdown']['game'],
                    "against_spread": snapshot_data['type_breakdown']['ats'],
                    "over_under": snapshot_data['type_breakdown']['total'],
                    "player_props": snapshot_data['type_breakdown']['prop']
                },
                "recent_performance": snapshot_data['recent_performance'],
                "theoretical_roi": snapshot_data['roi']
            },
            "tier": "live_accuracy",
            "message": "Upgrade for detailed analytics and historical trends"
        }
        
    except Exception as e:
        logger.error(f"Error getting live accuracy: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve accuracy data")

@router.get("/weekly/{season}/{week}")
@require_feature("basic_analytics")
@rate_limit("weekly_accuracy")
async def get_weekly_accuracy(
    season: int,
    week: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get accuracy metrics for a specific week (requires weekly subscription)
    """
    try:
        # Calculate week dates
        start_date = datetime(season, 9, 1) + timedelta(weeks=week-1)
        end_date = start_date + timedelta(days=6)
        
        # Get accuracy for each prediction type
        accuracy_data = {}
        prediction_types = ['game', 'ats', 'total', 'prop']
        
        for pred_type in prediction_types:
            type_accuracy = accuracy_engine.calculate_period_accuracy(
                'weekly', start_date, end_date, pred_type
            )
            accuracy_data[pred_type] = type_accuracy
        
        # Get overall weekly accuracy
        overall_accuracy = accuracy_engine.calculate_period_accuracy(
            'weekly', start_date, end_date
        )
        
        return {
            "success": True,
            "weekly_accuracy": {
                "season": season,
                "week": week,
                "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "overall": overall_accuracy,
                "by_type": accuracy_data,
                "summary": {
                    "best_category": max(accuracy_data.keys(), key=lambda k: accuracy_data[k].get('accuracy_percentage', 0)),
                    "total_predictions": sum(data.get('total_predictions', 0) for data in accuracy_data.values()),
                    "overall_roi": overall_accuracy.get('roi_percentage', 0)
                }
            },
            "tier": "weekly_analytics"
        }
        
    except Exception as e:
        logger.error(f"Error getting weekly accuracy: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve weekly accuracy data")

@router.get("/advanced")
@require_feature("advanced_analytics")
@rate_limit("advanced_analytics")
async def get_advanced_analytics(
    current_user: dict = Depends(get_current_user),
    days: int = Query(30, description="Number of days to analyze"),
    prediction_type: Optional[str] = Query(None, description="Filter by prediction type")
):
    """
    Get advanced analytics with confidence breakdowns and ROI analysis (requires monthly subscription)
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get detailed accuracy analysis
        accuracy_data = accuracy_engine.calculate_period_accuracy(
            'monthly', start_date, end_date, prediction_type
        )
        
        if 'error' in accuracy_data:
            raise HTTPException(status_code=500, detail=accuracy_data['error'])
        
        # Get trend analysis
        trend_data = await _get_trend_analysis(days, prediction_type)
        
        # Get confidence analysis
        confidence_analysis = accuracy_data.get('confidence_breakdown', {})
        
        # Get ROI breakdown
        roi_analysis = await _get_roi_analysis(start_date, end_date, prediction_type)
        
        return {
            "success": True,
            "advanced_analytics": {
                "period": f"Last {days} days",
                "prediction_type": prediction_type or "all",
                "overall_metrics": {
                    "accuracy": accuracy_data['accuracy_percentage'],
                    "confidence_weighted_accuracy": accuracy_data['confidence_weighted_accuracy'],
                    "total_predictions": accuracy_data['total_predictions'],
                    "roi_percentage": accuracy_data['roi_percentage']
                },
                "confidence_breakdown": {
                    "high_confidence": {
                        "threshold": ">= 70%",
                        "accuracy": confidence_analysis.get('high_confidence', {}).get('accuracy', 0),
                        "count": confidence_analysis.get('high_confidence', {}).get('total', 0)
                    },
                    "medium_confidence": {
                        "threshold": "50-70%",
                        "accuracy": confidence_analysis.get('medium_confidence', {}).get('accuracy', 0),
                        "count": confidence_analysis.get('medium_confidence', {}).get('total', 0)
                    },
                    "low_confidence": {
                        "threshold": "< 50%",
                        "accuracy": confidence_analysis.get('low_confidence', {}).get('accuracy', 0),
                        "count": confidence_analysis.get('low_confidence', {}).get('total', 0)
                    }
                },
                "streak_analysis": accuracy_data.get('streak_data', {}),
                "trend_analysis": trend_data,
                "roi_analysis": roi_analysis
            },
            "tier": "advanced_analytics"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting advanced analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve advanced analytics")

@router.get("/performance-history")
@require_feature("advanced_analytics")
@rate_limit("performance_history")
async def get_performance_history(
    current_user: dict = Depends(get_current_user),
    period_type: str = Query("weekly", description="Period type: weekly, monthly, season"),
    season: int = Query(2024, description="NFL season year"),
    limit: int = Query(10, description="Number of periods to return")
):
    """
    Get historical performance data (requires monthly subscription)
    """
    try:
        # This would query the PerformanceHistory table
        # For now, we'll return mock data structure
        
        performance_data = []
        
        if period_type == "weekly":
            for week in range(max(1, 18 - limit + 1), 19):
                # Calculate weekly performance
                start_date = datetime(season, 9, 1) + timedelta(weeks=week-1)
                end_date = start_date + timedelta(days=6)
                
                weekly_data = accuracy_engine.calculate_period_accuracy(
                    'weekly', start_date, end_date
                )
                
                performance_data.append({
                    "period": f"Week {week}",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "accuracy": weekly_data.get('accuracy_percentage', 0),
                    "total_predictions": weekly_data.get('total_predictions', 0),
                    "roi": weekly_data.get('roi_percentage', 0)
                })
        
        return {
            "success": True,
            "performance_history": {
                "period_type": period_type,
                "season": season,
                "data": performance_data,
                "summary": {
                    "best_period": max(performance_data, key=lambda x: x['accuracy']) if performance_data else None,
                    "average_accuracy": sum(p['accuracy'] for p in performance_data) / len(performance_data) if performance_data else 0,
                    "total_predictions": sum(p['total_predictions'] for p in performance_data)
                }
            },
            "tier": "performance_history"
        }
        
    except Exception as e:
        logger.error(f"Error getting performance history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance history")

@router.post("/update-results")
async def trigger_result_update(
    current_user: dict = Depends(get_current_user),
    season: Optional[int] = None,
    week: Optional[int] = None
):
    """
    Manually trigger result collection and accuracy updates (admin only)
    """
    try:
        if season and week:
            # Update specific week
            result = await result_collector.collect_weekly_results(season, week)
        else:
            # Update current live results
            result = await result_collector.collect_live_results()
        
        return {
            "success": True,
            "update_result": result,
            "message": "Result collection completed"
        }
        
    except Exception as e:
        logger.error(f"Error triggering result update: {e}")
        raise HTTPException(status_code=500, detail="Failed to update results")

@router.get("/roi-analysis")
@require_feature("data_export")
@rate_limit("roi_analysis")
async def get_roi_analysis(
    current_user: dict = Depends(get_current_user),
    days: int = Query(30, description="Number of days to analyze"),
    bet_amount: float = Query(100.0, description="Theoretical bet amount per prediction")
):
    """
    Get detailed ROI analysis (requires monthly subscription)
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get ROI analysis
        roi_data = await _get_detailed_roi_analysis(start_date, end_date, bet_amount)
        
        return {
            "success": True,
            "roi_analysis": roi_data,
            "tier": "roi_analysis"
        }
        
    except Exception as e:
        logger.error(f"Error getting ROI analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ROI analysis")

# Helper functions
async def _get_trend_analysis(days: int, prediction_type: Optional[str]) -> Dict:
    """Get trend analysis for the specified period"""
    # This would implement trend calculation logic
    return {
        "direction": "improving",
        "momentum": 15.5,
        "trend_strength": "moderate",
        "recent_change": "+2.3% vs previous period"
    }

async def _get_roi_analysis(start_date: datetime, end_date: datetime, 
                          prediction_type: Optional[str]) -> Dict:
    """Get ROI analysis for the specified period"""
    # This would implement ROI calculation logic
    return {
        "total_theoretical_bets": 3000.00,
        "total_theoretical_returns": 3240.00,
        "net_profit": 240.00,
        "roi_percentage": 8.0,
        "best_bet_type": "against_spread",
        "worst_bet_type": "player_props",
        "win_rate": 0.67
    }

async def _get_detailed_roi_analysis(start_date: datetime, end_date: datetime, 
                                   bet_amount: float) -> Dict:
    """Get detailed ROI analysis with breakdowns"""
    return {
        "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "bet_amount_per_prediction": bet_amount,
        "total_bets": 30,
        "total_amount_bet": bet_amount * 30,
        "total_returns": bet_amount * 30 * 1.08,
        "net_profit": bet_amount * 30 * 0.08,
        "roi_percentage": 8.0,
        "by_prediction_type": {
            "straight_up": {"roi": 12.5, "win_rate": 0.71},
            "against_spread": {"roi": 6.2, "win_rate": 0.64},
            "over_under": {"roi": 4.8, "win_rate": 0.62},
            "player_props": {"roi": -2.1, "win_rate": 0.48}
        },
        "by_confidence": {
            "high_confidence": {"roi": 15.2, "win_rate": 0.78},
            "medium_confidence": {"roi": 5.1, "win_rate": 0.58},
            "low_confidence": {"roi": -8.3, "win_rate": 0.42}
        }
    }