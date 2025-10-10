"""
Council API Endpoints

Implements council selection and platformneration with coherence projection.
Provides endpoints for:
- POST /api/council/select/:game_id - Select council and generate aggregated predictions
- GET /api/platform/slate/:game_id - Get coherent platform slate for client consumption

Requirements: 2.3, 2.8
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from src.api.services.database import db_service
from src.services.coherence_projection_service import CoherenceProjectionService
from src.ml.expert_competition.council_selector import AICouncilSelector, SelectionCriteria
from src.api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Council & Platform Slate"])

# Initialize services
coherence_service = CoherenceProjectionService()
council_selector = AICouncilSelector()

# Pydantic models
class CouncilSelectionRequest(BaseModel):
    """Request for council selection"""
    game_id: str
    run_id: Optional[str] = None
    evaluation_window_weeks: int = Field(default=4, ge=1, le=12)
    force_reselection: bool = False

class CouncilSelectionResponse(BaseModel):
    """Response from council selection"""
    success: bool
    game_id: str
    run_id: str
    council_members: List[str]
    selection_timestamp: datetime
    aggregated_predictions: Dict[str, Any]
    coherence_applied: bool
    processing_time_ms: float
    metadata: Dict[str, Any]

class PlatformSlateResponse(BaseModel):
    """Response for platform slate"""
    success: bool
    game_id: str
    run_id: str
    platform_slate: Dict[str, Any]
    council_info: Dict[str, Any]
    coherence_info: Dict[str, Any]
    generated_at: datetime
    cache_status: str
    processing_time_ms: float

@router.post("/council/select/{game_id}", response_model=CouncilSelectionResponse)
async def select_council_for_game(
    game_id: str,
    request: CouncilSelectionRequest,
    background_tasks: BackgroundTasks
) -> CouncilSelectionResponse:
    """
    Select AI Council and generate aggregated predictions for a specific game

    This endpoint:
    1. Retrieves expert predictions for the game
    2. Selects top-5 experts using council selection criteria
    3. Aggregates predictions using weighted methods
    4. Applies coherence projection to ensure mathematical consistency
    5. Stores results for platform slate consumption

    Args:
        game_id: Game identifier
        request: Council selection parameters

    Returns:
        CouncilSelectionResponse with council members and aggregated predictions
    """
    start_time = time.time()

    try:
        effective_run_id = request.run_id or settings.get_run_id()

        logger.info(f"Starting council selection for game {game_id}, run {effective_run_id}")

        # Step 1: Retrieve expert predictions for this game
        expert_predictions = await get_expert_predictions_for_game(game_id, effective_run_id)

        if not expert_predictions:
            raise HTTPException(
                status_code=404,
                detail=f"No expert predictions found for game {game_id} in run {effective_run_id}"
            )

        # Step 2: Get expert performance data for council selection
        expert_performance = await get_expert_performance_data(effective_run_id, request.evaluation_window_weeks)

        # Step 3: Select AI Council (top-5 experts)
        council_members = await council_selector.select_top_performers(
            expert_performance,
            request.evaluation_window_weeks
        )

        logger.info(f"Selected council members: {council_members}")

        # Step 4: Aggregate predictions from council members
        aggregated_predictions = await aggregate_council_predictions(
            expert_predictions,
            council_members,
            expert_performance
        )

        # Step 5: Apply coherence projection
        game_context = {'game_id': game_id, 'run_id': effective_run_id}
        coherence_result = coherence_service.project_coherent_predictions(
            aggregated_predictions,
            game_context
        )

        # Use coherent predictions if successful, otherwise use original aggregation
        final_predictions = (
            coherence_result.projected_predictions
            if coherence_result.success
            else aggregated_predictions
        )

        # Step 6: Store council selection and aggregated predictions
        await store_council_selection_result(
            game_id=game_id,
            run_id=effective_run_id,
            council_members=council_members,
            aggregated_predictions=final_predictions,
            coherence_result=coherence_result
        )

        processing_time = (time.time() - start_time) * 1000

        # Background task: Update council performance metrics
        background_tasks.add_task(
            update_council_performance_metrics,
            council_members,
            coherence_result,
            processing_time
        )

        logger.info(f"Council selection completed in {processing_time:.1f}ms")

        return CouncilSelectionResponse(
            success=True,
            game_id=game_id,
            run_id=effective_run_id,
            council_members=council_members,
            selection_timestamp=datetime.utcnow(),
            aggregated_predictions=final_predictions,
            coherence_applied=coherence_result.success,
            processing_time_ms=processing_time,
            metadata={
                'expert_predictions_count': len(expert_predictions),
                'coherence_satisfaction': coherence_result.constraint_satisfaction,
                'deltas_applied': len(coherence_result.deltas_applied),
                'evaluation_window_weeks': request.evaluation_window_weeks
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Council selection failed for game {game_id}: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Council selection failed: {str(e)}"
        )

@router.get("/platform/slate/{game_id}", response_model=PlatformSlateResponse)
async def get_platform_slate(
    game_id: str,
    run_id: Optional[str] = None,
    force_refresh: bool = False
) -> PlatformSlateResponse:
    """
    Get coherent platform slate for client consumption

    This endpoint returns the final, coherent predictions that should be displayed
    to users. It includes council information and coherence details for transparency.

    Args:
        game_id: Game identifier
        run_id: Optional run identifier (defaults to current run)
        force_refresh: Force regeneration of slate (bypasses cache)

    Returns:
        PlatformSlateResponse with coherent predictions and metadata
    """
    start_time = time.time()

    try:
        effective_run_id = run_id or settings.get_run_id()

        logger.info(f"Retrieving platform slate for game {game_id}, run {effective_run_id}")

        # Check for cached slate first (unless force refresh)
        if not force_refresh:
            cached_slate = await get_cached_platform_slate(game_id, effective_run_id)
            if cached_slate:
                processing_time = (time.time() - start_time) * 1000
                logger.info(f"Returning cached platform slate in {processing_time:.1f}ms")

                return PlatformSlateResponse(
                    success=True,
                    game_id=game_id,
                    run_id=effective_run_id,
                    platform_slate=cached_slate['platform_slate'],
                    council_info=cached_slate['council_info'],
                    coherence_info=cached_slate['coherence_info'],
                    generated_at=cached_slate['generated_at'],
                    cache_status='hit',
                    processing_time_ms=processing_time
                )

        # Retrieve council selection result
        council_result = await get_council_selection_result(game_id, effective_run_id)

        if not council_result:
            # No council selection found, trigger council selection first
            logger.info(f"No council selection found for game {game_id}, triggering selection")

            selection_request = CouncilSelectionRequest(
                game_id=game_id,
                run_id=effective_run_id
            )

            # This will create the council selection
            council_response = await select_council_for_game(
                game_id,
                selection_request,
                BackgroundTasks()
            )

            council_result = {
                'council_members': council_response.council_members,
                'aggregated_predictions': council_response.aggregated_predictions,
                'coherence_applied': council_response.coherence_applied,
                'selection_timestamp': council_response.selection_timestamp,
                'metadata': council_response.metadata
            }

        # Format platform slate for client consumption
        platform_slate = format_platform_slate(council_result['aggregated_predictions'])

        # Prepare council information for transparency
        council_info = {
            'members': council_result['council_members'],
            'selection_timestamp': council_result['selection_timestamp'],
            'evaluation_criteria': council_selector.get_current_criteria()
        }

        # Prepare coherence information
        coherence_info = {
            'coherence_applied': council_result['coherence_applied'],
            'constraint_satisfaction': council_result.get('metadata', {}).get('coherence_satisfaction', 1.0),
            'deltas_applied': council_result.get('metadata', {}).get('deltas_applied', 0)
        }

        # Cache the result for future requests
        await cache_platform_slate(
            game_id=game_id,
            run_id=effective_run_id,
            platform_slate=platform_slate,
            council_info=council_info,
            coherence_info=coherence_info
        )

        processing_time = (time.time() - start_time) * 1000

        logger.info(f"Platform slate generated in {processing_time:.1f}ms")

        return PlatformSlateResponse(
            success=True,
            game_id=game_id,
            run_id=effective_run_id,
            platform_slate=platform_slate,
            council_info=council_info,
            coherence_info=coherence_info,
            generated_at=datetime.utcnow(),
            cache_status='miss' if not force_refresh else 'refresh',
            processing_time_ms=processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Platform slate generation failed for game {game_id}: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Platform slate generation failed: {str(e)}"
        )

# Helper functions

async def get_expert_predictions_for_game(game_id: str, run_id: str) -> Dict[str, Any]:
    """Retrieve all expert predictions for a specific game"""
    try:
        result = await db_service.client.table('expert_predictions_comprehensive').select(
            'expert_id, betting_markets, game_outcome, confidence_overall, created_at'
        ).eq('game_id', game_id).eq('run_id', run_id).execute()

        predictions = {}
        for row in result.data or []:
            predictions[row['expert_id']] = {
                'betting_markets': row['betting_markets'],
                'game_outcome': row['game_outcome'],
                'confidence_overall': row['confidence_overall'],
                'created_at': row['created_at']
            }

        return predictions

    except Exception as e:
        logger.error(f"Failed to retrieve expert predictions for game {game_id}: {e}")
        return {}

async def get_expert_performance_data(run_id: str, window_weeks: int) -> Dict[str, Any]:
    """Get expert performance data for council selection"""
    try:
        # This would typically query expert performance metrics
        # For now, return mock data structure that matches what council_selector expects

        result = await db_service.client.table('expert_bankroll').select(
            'expert_id, current_balance, total_bets, win_rate'
        ).eq('run_id', run_id).execute()

        experts = {}
        for row in result.data or []:
            class MockExpert:
                def __init__(self, expert_id: str, data: Dict[str, Any]):
                    self.expert_id = expert_id
                    self.name = f"Expert {expert_id}"
                    self.total_predictions = data.get('total_bets', 10)
                    self.overall_accuracy = data.get('win_rate', 0.5)
                    self.recent_trend = 'stable'  # Would be calculated from recent performance
                    self.consistency_score = 0.6  # Would be calculated from prediction variance
                    self.confidence_calibration = 0.7  # Would be calculated from confidence vs accuracy
                    self.specialization_strength = {'general': 0.6}  # Would be category-specific

            experts[row['expert_id']] = MockExpert(row['expert_id'], row)

        return experts

    except Exception as e:
        logger.error(f"Failed to retrieve expert performance data: {e}")
        return {}

async def aggregate_council_predictions(
    expert_predictions: Dict[str, Any],
    council_members: List[str],
    expert_performance: Dict[str, Any]
) -> Dict[str, Any]:
    """Aggregate predictions from council members using weighted methods"""
    try:
        # Filter predictions to only council members
        council_predictions = {
            expert_id: pred for expert_id, pred in expert_predictions.items()
            if expert_id in council_members
        }

        if not council_predictions:
            raise ValueError("No predictions found for council members")

        # Calculate weights based on expert performance
        weights = {}
        total_weight = 0

        for expert_id in council_members:
            if expert_id in expert_performance:
                expert = expert_performance[expert_id]
                # Weight = accuracy * confidence * stake_intensity
                weight = (
                    expert.overall_accuracy * 0.5 +
                    expert.confidence_calibration * 0.3 +
                    min(1.0, expert.total_predictions / 20) * 0.2  # Stake intensity proxy
                )
                weights[expert_id] = weight
                total_weight += weight
            else:
                weights[expert_id] = 1.0
                total_weight += 1.0

        # Normalize weights
        if total_weight > 0:
            for expert_id in weights:
                weights[expert_id] /= total_weight

        # Aggregate predictions
        aggregated = {
            'overall': {},
            'predictions': []
        }

        # Aggregate overall predictions (weighted average for numeric, weighted log-odds for binary)
        overall_predictions = {}
        for expert_id, pred in council_predictions.items():
            weight = weights[expert_id]
            game_outcome = pred.get('game_outcome', {})

            for key, value in game_outcome.items():
                if key not in overall_predictions:
                    overall_predictions[key] = []
                overall_predictions[key].append((value, weight))

        # Calculate weighted averages
        for key, values in overall_predictions.items():
            if isinstance(values[0][0], (int, float)):
                # Numeric: weighted average
                weighted_sum = sum(val * weight for val, weight in values)
                aggregated['overall'][key] = weighted_sum
            else:
                # Non-numeric: take most common weighted value
                aggregated['overall'][key] = values[0][0]  # Simplified

        # Aggregate individual predictions (simplified - would need category-specific logic)
        prediction_categories = set()
        for pred in council_predictions.values():
            betting_markets = pred.get('betting_markets', {})
            if 'predictions' in betting_markets:
                for p in betting_markets['predictions']:
                    prediction_categories.add(p.get('category', ''))

        for category in prediction_categories:
            category_predictions = []
            category_weights = []

            for expert_id, pred in council_predictions.items():
                betting_markets = pred.get('betting_markets', {})
                if 'predictions' in betting_markets:
                    for p in betting_markets['predictions']:
                        if p.get('category') == category:
                            category_predictions.append(p)
                            category_weights.append(weights[expert_id])
                            break

            if category_predictions:
                # Aggregate this category (simplified)
                aggregated_pred = category_predictions[0].copy()  # Start with first prediction

                # Weighted average for numeric values
                if aggregated_pred.get('pred_type') == 'numeric':
                    values = [p.get('value', 0) for p in category_predictions]
                    weighted_value = sum(v * w for v, w in zip(values, category_weights))
                    aggregated_pred['value'] = weighted_value

                # Weighted average for confidence
                confidences = [p.get('confidence', 0.5) for p in category_predictions]
                aggregated_pred['confidence'] = sum(c * w for c, w in zip(confidences, category_weights))

                aggregated['predictions'].append(aggregated_pred)

        return aggregated

    except Exception as e:
        logger.error(f"Failed to aggregate council predictions: {e}")
        raise

async def store_council_selection_result(
    game_id: str,
    run_id: str,
    council_members: List[str],
    aggregated_predictions: Dict[str, Any],
    coherence_result: Any
) -> None:
    """Store council selection result in database"""
    try:
        data = {
            'game_id': game_id,
            'run_id': run_id,
            'council_members': council_members,
            'aggregated_predictions': aggregated_predictions,
            'coherence_applied': coherence_result.success,
            'coherence_satisfaction': coherence_result.constraint_satisfaction,
            'deltas_applied': coherence_result.deltas_applied,
            'selection_timestamp': datetime.utcnow().isoformat(),
            'processing_time_ms': coherence_result.processing_time_ms
        }

        # Store in council_selections table (would need to be created)
        await db_service.client.table('council_selections').upsert(data).execute()

        logger.info(f"Stored council selection result for game {game_id}")

    except Exception as e:
        logger.error(f"Failed to store council selection result: {e}")

async def get_council_selection_result(game_id: str, run_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve stored council selection result"""
    try:
        result = await db_service.client.table('council_selections').select('*').eq(
            'game_id', game_id
        ).eq('run_id', run_id).order('selection_timestamp', desc=True).limit(1).execute()

        if result.data:
            return result.data[0]
        return None

    except Exception as e:
        logger.error(f"Failed to retrieve council selection result: {e}")
        return None

def format_platform_slate(aggregated_predictions: Dict[str, Any]) -> Dict[str, Any]:
    """Format aggregated predictions for client consumption"""
    try:
        # Format for client-friendly consumption
        formatted = {
            'game_outcome': aggregated_predictions.get('overall', {}),
            'predictions': aggregated_predictions.get('predictions', []),
            'metadata': {
                'prediction_count': len(aggregated_predictions.get('predictions', [])),
                'generated_by': 'ai_council',
                'coherence_applied': True
            }
        }

        return formatted

    except Exception as e:
        logger.error(f"Failed to format platform slate: {e}")
        return aggregated_predictions

async def get_cached_platform_slate(game_id: str, run_id: str) -> Optional[Dict[str, Any]]:
    """Get cached platform slate if available"""
    try:
        # Check cache table (would need to be implemented)
        result = await db_service.client.table('platform_slate_cache').select('*').eq(
            'game_id', game_id
        ).eq('run_id', run_id).gte(
            'created_at', (datetime.utcnow() - timedelta(hours=1)).isoformat()  # 1 hour cache
        ).order('created_at', desc=True).limit(1).execute()

        if result.data:
            return result.data[0]
        return None

    except Exception as e:
        logger.debug(f"Cache lookup failed (expected if table doesn't exist): {e}")
        return None

async def cache_platform_slate(
    game_id: str,
    run_id: str,
    platform_slate: Dict[str, Any],
    council_info: Dict[str, Any],
    coherence_info: Dict[str, Any]
) -> None:
    """Cache platform slate for future requests"""
    try:
        data = {
            'game_id': game_id,
            'run_id': run_id,
            'platform_slate': platform_slate,
            'council_info': council_info,
            'coherence_info': coherence_info,
            'generated_at': datetime.utcnow().isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }

        # Store in cache table (would need to be created)
        await db_service.client.table('platform_slate_cache').upsert(data).execute()

    except Exception as e:
        logger.debug(f"Cache storage failed (expected if table doesn't exist): {e}")

async def update_council_performance_metrics(
    council_members: List[str],
    coherence_result: Any,
    processing_time: float
) -> None:
    """Update performance metrics for council members (background task)"""
    try:
        # Update council performance tracking
        for member in council_members:
            # This would update council member performance metrics
            pass

        # Update coherence service metrics
        coherence_service.projection_times.append(coherence_result.processing_time_ms)

        logger.info(f"Updated performance metrics for {len(council_members)} council members")

    except Exception as e:
        logger.error(f"Failed to update council performance metrics: {e}")

# Health check endpoint
@router.get("/council/health")
async def council_health_check() -> Dict[str, Any]:
    """Health check for council and platform slate services"""
    try:
        # Check coherence service health
        coherence_metrics = coherence_service.get_performance_metrics()

        # Check council selector health
        council_criteria = council_selector.get_current_criteria()

        return {
            'status': 'healthy',
            'coherence_service': {
                'projections_processed': coherence_metrics['projection_count'],
                'avg_time_ms': coherence_metrics['avg_time_ms'],
                'performance_ok': coherence_metrics['performance_ok']
            },
            'council_selector': {
                'criteria_valid': council_criteria['weights_valid'],
                'evaluation_window_weeks': council_criteria['evaluation_window_weeks']
            },
            'last_check': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Council health check failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'last_check': datetime.utcnow().isoformat()
        }
