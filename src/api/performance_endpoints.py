#!/usr/bin/env python3
"""
High-Performance NFL Prediction API Endpoints
Optimized for 375+ predictions per game with sub-second response times
"""

import asyncio
import logging
import json
import gzip
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
import asyncpg

# Import our optimized service
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from performance.optimized_prediction_service import (
    OptimizedPredictionService,
    PredictionRequest,
    PredictionResponse,
    PerformanceMetrics,
    get_optimized_service
)

logger = logging.getLogger(__name__)

# Create performance-optimized router
router = APIRouter(prefix="/api/v2/performance", tags=["High-Performance Predictions"])


class DatabaseOptimizer:
    """Database optimization utilities"""

    @staticmethod
    async def create_performance_indexes(db_pool: asyncpg.Pool):
        """Create indexes for optimal query performance"""

        indexes = [
            # Game predictions index
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_games_date_teams ON games (game_date, home_team, away_team);",

            # Predictions by game and model
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_game_model ON predictions (game_id, model_type, created_at DESC);",

            # Expert predictions index
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_predictions_game ON expert_predictions (game_id, expert_id, prediction_type);",

            # Player stats index for props
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_player_stats_game_player ON player_stats (game_id, player_id, stat_type);",

            # Composite index for team performance queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_performance_season_week ON team_stats (season, week, team, stat_category);",

            # Index for odds and betting data
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_odds_game_timestamp ON odds (game_id, timestamp DESC);",

            # Partial index for active games only
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_active_games ON games (game_id) WHERE status IN ('scheduled', 'in_progress');",

            # Index for recent predictions (last 30 days)
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recent_predictions ON predictions (created_at DESC) WHERE created_at > CURRENT_DATE - INTERVAL '30 days';"
        ]

        if db_pool:
            try:
                async with db_pool.acquire() as conn:
                    for index_sql in indexes:
                        try:
                            await conn.execute(index_sql)
                            logger.info(f"✅ Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                        except Exception as e:
                            logger.warning(f"Index creation skipped: {e}")

                logger.info("🚀 Database performance indexes created")

            except Exception as e:
                logger.error(f"Database index creation failed: {e}")


class ResponseOptimizer:
    """Response optimization utilities"""

    @staticmethod
    def compress_response_data(data: Dict[str, Any], threshold: int = 1024) -> bytes:
        """Compress response data if above threshold"""

        json_data = json.dumps(data, default=str).encode('utf-8')

        if len(json_data) > threshold:
            return gzip.compress(json_data)

        return json_data

    @staticmethod
    def create_optimized_response(
        data: Dict[str, Any],
        compress: bool = True,
        headers: Optional[Dict[str, str]] = None
    ) -> Response:
        """Create optimized response with compression"""

        response_headers = headers or {}

        if compress and len(json.dumps(data, default=str)) > 1024:
            compressed_data = gzip.compress(
                json.dumps(data, default=str).encode('utf-8')
            )

            response_headers.update({
                'Content-Encoding': 'gzip',
                'Content-Type': 'application/json',
                'Content-Length': str(len(compressed_data))
            })

            return Response(
                content=compressed_data,
                headers=response_headers,
                media_type='application/json'
            )
        else:
            return JSONResponse(content=data, headers=response_headers)


@router.on_event("startup")
async def setup_database_optimization():
    """Setup database optimization on startup"""
    try:
        service = await get_optimized_service()
        if service.db_pool:
            await DatabaseOptimizer.create_performance_indexes(service.db_pool)
    except Exception as e:
        logger.warning(f"Database optimization setup failed: {e}")


@router.get("/predictions/batch", response_model=PredictionResponse)
async def get_batch_predictions(
    game_ids: List[str] = Query(..., description="List of game IDs (format: home_team-away_team)"),
    include_experts: bool = Query(True, description="Include expert predictions"),
    include_ml: bool = Query(True, description="Include ML predictions"),
    include_props: bool = Query(True, description="Include player props"),
    include_totals: bool = Query(True, description="Include totals predictions"),
    expert_count: int = Query(15, ge=1, le=15, description="Number of experts (1-15)"),
    fields: Optional[List[str]] = Query(None, description="Field selection for response optimization"),
    compress_response: bool = Query(True, description="Enable response compression"),
    service: OptimizedPredictionService = Depends(get_optimized_service)
):
    """
    Get batch predictions with high-performance optimization

    Features:
    - Sub-second response times for 375+ predictions
    - Redis caching with 5-minute TTL
    - Parallel processing of all experts
    - Response compression for large datasets
    - Field selection to reduce payload size
    """

    if len(game_ids) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 games per batch request. Use multiple requests for larger datasets."
        )

    try:
        # Create optimized request
        request = PredictionRequest(
            game_ids=game_ids,
            include_expert_predictions=include_experts,
            include_ml_predictions=include_ml,
            include_props=include_props,
            include_totals=include_totals,
            expert_count=expert_count,
            field_selection=fields
        )

        # Get optimized predictions
        response = await service.get_optimized_predictions(request)

        # Log performance metrics
        logger.info(
            f"📊 Batch prediction: {len(game_ids)} games, "
            f"{response.performance_metrics['total_predictions']} predictions, "
            f"{response.performance_metrics['response_time_ms']:.1f}ms"
        )

        # Return optimized response
        if compress_response:
            return ResponseOptimizer.create_optimized_response(
                response.dict(),
                compress=True,
                headers={
                    'X-Prediction-Count': str(response.performance_metrics['total_predictions']),
                    'X-Response-Time-Ms': str(response.performance_metrics['response_time_ms']),
                    'X-Cache-Hit': str(response.performance_metrics['cache_hit'])
                }
            )
        else:
            return response

    except Exception as e:
        logger.error(f"❌ Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction service error: {str(e)}")


@router.get("/predictions/game/{game_id}", response_model=Dict[str, Any])
async def get_single_game_predictions(
    game_id: str,
    include_experts: bool = Query(True),
    include_ml: bool = Query(True),
    include_props: bool = Query(True),
    include_totals: bool = Query(True),
    expert_count: int = Query(15, ge=1, le=15),
    fields: Optional[List[str]] = Query(None),
    service: OptimizedPredictionService = Depends(get_optimized_service)
):
    """Get optimized predictions for a single game"""

    try:
        request = PredictionRequest(
            game_ids=[game_id],
            include_expert_predictions=include_experts,
            include_ml_predictions=include_ml,
            include_props=include_props,
            include_totals=include_totals,
            expert_count=expert_count,
            field_selection=fields
        )

        response = await service.get_optimized_predictions(request)

        if response.predictions:
            return ResponseOptimizer.create_optimized_response(
                {
                    'prediction': response.predictions[0],
                    'metadata': response.metadata,
                    'performance': response.performance_metrics
                }
            )
        else:
            raise HTTPException(status_code=404, detail=f"No predictions found for game {game_id}")

    except Exception as e:
        logger.error(f"Single game prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/live", response_model=Dict[str, Any])
async def get_live_game_predictions(
    week: int = Query(..., description="NFL week number"),
    season: int = Query(2024, description="NFL season"),
    include_experts: bool = Query(True),
    include_ml: bool = Query(True),
    expert_count: int = Query(15, ge=1, le=15),
    service: OptimizedPredictionService = Depends(get_optimized_service)
):
    """Get predictions for all live games in a week"""

    try:
        # Get live games for the week (mock implementation)
        live_games = [
            "KC-BAL", "BUF-MIA", "SF-DAL", "PHI-NYG", "DET-GB",
            "MIN-CHI", "CIN-PIT", "LAR-SEA", "LV-LAC", "DEN-KC"
        ]

        # Limit to first 10 games for demo
        game_ids = live_games[:10]

        request = PredictionRequest(
            game_ids=game_ids,
            include_expert_predictions=include_experts,
            include_ml_predictions=include_ml,
            include_props=False,  # Skip props for live updates
            include_totals=True,
            expert_count=expert_count
        )

        response = await service.get_optimized_predictions(request)

        return ResponseOptimizer.create_optimized_response({
            'week': week,
            'season': season,
            'live_games': response.predictions,
            'summary': {
                'total_games': len(response.predictions),
                'total_predictions': response.performance_metrics['total_predictions'],
                'response_time_ms': response.performance_metrics['response_time_ms'],
                'cache_hit_rate': response.cache_info['hit_rate']
            },
            'metadata': response.metadata
        })

    except Exception as e:
        logger.error(f"Live predictions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/experts/parallel", response_model=Dict[str, Any])
async def get_parallel_expert_predictions(
    home_team: str = Query(..., description="Home team abbreviation"),
    away_team: str = Query(..., description="Away team abbreviation"),
    expert_count: int = Query(15, ge=1, le=15),
    service: OptimizedPredictionService = Depends(get_optimized_service)
):
    """
    Get expert predictions using parallel processing

    Demonstrates parallel execution of all 15 experts for maximum performance
    """

    try:
        # Use the optimized parallel expert prediction method
        expert_predictions = await service._get_expert_predictions_parallel(
            home_team, away_team, expert_count
        )

        return ResponseOptimizer.create_optimized_response({
            'matchup': f"{away_team} @ {home_team}",
            'expert_predictions': expert_predictions['expert_predictions'],
            'consensus': expert_predictions['consensus'],
            'performance': {
                'expert_count': expert_predictions['count'],
                'parallel_execution': True,
                'processing_method': 'asyncio.gather() with thread pool'
            }
        })

    except Exception as e:
        logger.error(f"Parallel expert predictions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/stats", response_model=Dict[str, Any])
async def get_performance_statistics(
    service: OptimizedPredictionService = Depends(get_optimized_service)
):
    """Get detailed performance statistics"""

    try:
        stats = await service.get_performance_stats()

        return ResponseOptimizer.create_optimized_response({
            'performance_stats': stats,
            'optimization_features': [
                'Redis caching with 5-minute TTL',
                'Parallel processing with asyncio.gather()',
                'Database connection pooling',
                'Response compression (gzip)',
                'Field selection and pagination',
                'Intelligent cache invalidation',
                'Performance monitoring and alerting'
            ],
            'target_metrics': {
                'max_response_time_ms': 1000,
                'min_predictions_per_game': 375,
                'cache_hit_rate_target': 80,
                'concurrent_request_capacity': 100
            }
        })

    except Exception as e:
        logger.error(f"Performance stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/benchmark", response_model=Dict[str, Any])
async def run_performance_benchmark(
    game_count: int = Query(10, ge=1, le=20, description="Number of games to benchmark"),
    iterations: int = Query(3, ge=1, le=10, description="Number of benchmark iterations"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: OptimizedPredictionService = Depends(get_optimized_service)
):
    """
    Run performance benchmark test

    Tests the system's ability to handle multiple games with 375+ predictions each
    """

    try:
        # Run benchmark
        benchmark_results = await service.benchmark_performance(game_count, iterations)

        # Add background task to log detailed results
        background_tasks.add_task(
            _log_benchmark_results,
            benchmark_results
        )

        return ResponseOptimizer.create_optimized_response({
            'benchmark_results': benchmark_results,
            'performance_evaluation': {
                'target_met': benchmark_results.get('target_met', False),
                'performance_rating': _calculate_performance_rating(benchmark_results),
                'recommendations': _get_performance_recommendations(benchmark_results)
            }
        })

    except Exception as e:
        logger.error(f"Performance benchmark error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/warm", response_model=Dict[str, Any])
async def warm_prediction_cache(
    game_ids: List[str] = Query(..., description="Game IDs to warm in cache"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: OptimizedPredictionService = Depends(get_optimized_service)
):
    """Warm the cache with predictions for specified games"""

    try:
        if len(game_ids) > 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 games per cache warming request"
            )

        # Create warming functions for each game
        warm_functions = {}
        for game_id in game_ids:
            if "-" not in game_id:
                continue

            home_team, away_team = game_id.split("-", 1)

            async def create_warming_func(h_team, a_team):
                async def warming_func():
                    request = PredictionRequest(
                        game_ids=[f"{h_team}-{a_team}"],
                        include_expert_predictions=True,
                        include_ml_predictions=True,
                        include_props=True,
                        include_totals=True,
                        expert_count=15
                    )
                    response = await service.get_optimized_predictions(request)
                    return response.predictions

                return warming_func

            cache_key = service._generate_cache_key(
                PredictionRequest(game_ids=[game_id])
            )
            warm_functions[cache_key] = await create_warming_func(home_team, away_team)

        # Warm cache
        warming_results = await service.cache_manager.warm_cache(warm_functions)

        return ResponseOptimizer.create_optimized_response({
            'cache_warming_results': warming_results,
            'games_warmed': len([r for r in warming_results.values() if r]),
            'total_games_requested': len(game_ids),
            'success_rate': sum(warming_results.values()) / len(warming_results) * 100
        })

    except Exception as e:
        logger.error(f"Cache warming error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/invalidate", response_model=Dict[str, Any])
async def invalidate_prediction_cache(
    pattern: str = Query("nfl:predictions*", description="Cache key pattern to invalidate"),
    service: OptimizedPredictionService = Depends(get_optimized_service)
):
    """Invalidate cache entries matching pattern"""

    try:
        if not service.cache_manager:
            raise HTTPException(status_code=503, detail="Cache manager not available")

        invalidated_count = await service.cache_manager.invalidate_pattern(pattern)

        return ResponseOptimizer.create_optimized_response({
            'invalidated_count': invalidated_count,
            'pattern': pattern,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _log_benchmark_results(results: Dict[str, Any]):
    """Background task to log detailed benchmark results"""
    logger.info(f"📊 Benchmark Results: {json.dumps(results, indent=2)}")


def _calculate_performance_rating(benchmark_results: Dict[str, Any]) -> str:
    """Calculate performance rating based on benchmark results"""

    if not benchmark_results.get('successful_runs'):
        return "F - Failed"

    avg_response_time = benchmark_results.get('avg_response_time_ms', float('inf'))
    avg_predictions = benchmark_results.get('avg_predictions_per_run', 0)

    if avg_response_time < 500 and avg_predictions > 300:
        return "A+ - Excellent"
    elif avg_response_time < 1000 and avg_predictions > 250:
        return "A - Very Good"
    elif avg_response_time < 2000 and avg_predictions > 200:
        return "B - Good"
    elif avg_response_time < 5000:
        return "C - Acceptable"
    else:
        return "D - Needs Improvement"


def _get_performance_recommendations(benchmark_results: Dict[str, Any]) -> List[str]:
    """Get performance recommendations based on benchmark results"""

    recommendations = []

    avg_response_time = benchmark_results.get('avg_response_time_ms', 0)

    if avg_response_time > 1000:
        recommendations.append("Consider increasing Redis cache TTL")
        recommendations.append("Enable more parallel workers")

    if avg_response_time > 2000:
        recommendations.append("Implement database query optimization")
        recommendations.append("Add more aggressive caching strategies")

    if avg_response_time > 5000:
        recommendations.append("Scale horizontally with multiple service instances")
        recommendations.append("Implement request queuing")

    if not recommendations:
        recommendations.append("Performance is optimal - no improvements needed")

    return recommendations