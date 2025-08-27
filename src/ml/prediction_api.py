"""
Real-time Prediction API
Serves all ML models with caching, concurrent handling, and performance optimization
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor
import json
from dataclasses import dataclass, asdict
import hashlib

# Try to import caching libraries
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from .simple_enhanced_models import SimpleEnhancedModels
    from .player_props_engine import PlayerPropsEngine
    from .fantasy_optimizer import FantasyOptimizer
except ImportError:
    # Handle relative import issues
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from simple_enhanced_models import SimpleEnhancedModels
    from player_props_engine import PlayerPropsEngine
    from fantasy_optimizer import FantasyOptimizer

logger = logging.getLogger(__name__)

@dataclass
class PredictionRequest:
    """Structured prediction request"""
    request_id: str
    request_type: str  # 'game', 'props', 'fantasy'
    data: Dict[str, Any]
    timestamp: datetime
    cache_ttl: int = 300  # 5 minutes default

@dataclass
class PredictionResponse:
    """Structured prediction response"""
    request_id: str
    success: bool
    predictions: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    cached: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class PredictionCache:
    """Intelligent caching system for predictions"""
    
    def __init__(self, use_redis: bool = True):
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.local_cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0, 'sets': 0}
        
        if self.use_redis:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis unavailable, using local cache: {e}")
                self.use_redis = False
    
    def _generate_cache_key(self, request: PredictionRequest) -> str:
        """Generate cache key from request"""
        # Create deterministic hash from request data
        request_str = json.dumps({
            'type': request.request_type,
            'data': request.data
        }, sort_keys=True)
        
        return f"pred:{hashlib.md5(request_str.encode()).hexdigest()}"
    
    def get(self, request: PredictionRequest) -> Optional[PredictionResponse]:
        """Get cached prediction"""
        try:
            cache_key = self._generate_cache_key(request)
            
            if self.use_redis:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_stats['hits'] += 1
                    response_data = json.loads(cached_data)
                    response_data['cached'] = True
                    response_data['timestamp'] = datetime.fromisoformat(response_data['timestamp'])
                    return PredictionResponse(**response_data)
            else:
                if cache_key in self.local_cache:
                    cached_response, expiry = self.local_cache[cache_key]
                    if datetime.utcnow() < expiry:
                        self.cache_stats['hits'] += 1
                        cached_response.cached = True
                        return cached_response
                    else:
                        del self.local_cache[cache_key]
            
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats['misses'] += 1
            return None
    
    def set(self, request: PredictionRequest, response: PredictionResponse):
        """Cache prediction response"""
        try:
            cache_key = self._generate_cache_key(request)
            
            # Prepare response for caching
            cache_data = asdict(response)
            cache_data['timestamp'] = response.timestamp.isoformat()
            cache_data['cached'] = False  # Will be set to True when retrieved
            
            if self.use_redis:
                self.redis_client.setex(
                    cache_key, 
                    request.cache_ttl, 
                    json.dumps(cache_data)
                )
            else:
                expiry = datetime.utcnow() + timedelta(seconds=request.cache_ttl)
                self.local_cache[cache_key] = (response, expiry)
            
            self.cache_stats['sets'] += 1
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            if self.use_redis:
                keys = self.redis_client.keys(f"pred:*{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} cache entries matching '{pattern}'")
            else:
                keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.local_cache[key]
                logger.info(f"Invalidated {len(keys_to_delete)} local cache entries")
                
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets'],
            'hit_rate': hit_rate,
            'cache_type': 'redis' if self.use_redis else 'local',
            'local_cache_size': len(self.local_cache)
        }

class PredictionEngine:
    """
    Real-time prediction engine with caching and concurrent request handling
    """
    
    def __init__(self, max_workers: int = 4):
        # Initialize ML models
        self.game_models = SimpleEnhancedModels()
        self.props_engine = PlayerPropsEngine()
        self.fantasy_optimizer = FantasyOptimizer()
        
        # Initialize cache
        self.cache = PredictionCache()
        
        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Performance tracking
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_processing_time': 0,
            'cache_hit_rate': 0
        }
        
        # Train models on startup
        self._initialize_models()
        
        logger.info(f"🚀 Prediction Engine initialized with {max_workers} workers")
    
    def _initialize_models(self):
        """Initialize and train all ML models"""
        try:
            logger.info("🏋️ Training ML models...")
            
            # Train game models
            game_results = self.game_models.train_models()
            logger.info(f"✅ Game models trained: {len(game_results['model_performance'])} models")
            
            # Train props models
            props_results = self.props_engine.train_prop_models()
            logger.info(f"✅ Props models trained: {len(props_results['model_performance'])} models")
            
            logger.info("🎉 All models initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Model initialization failed: {e}")
            raise
    
    async def predict(self, request: PredictionRequest) -> PredictionResponse:
        """Main prediction endpoint with caching and async processing"""
        start_time = time.time()
        
        try:
            # Check cache first
            cached_response = self.cache.get(request)
            if cached_response:
                logger.info(f"📦 Cache hit for request {request.request_id}")
                return cached_response
            
            # Process prediction based on type
            if request.request_type == 'game':
                response = await self._predict_game(request)
            elif request.request_type == 'props':
                response = await self._predict_props(request)
            elif request.request_type == 'fantasy':
                response = await self._predict_fantasy(request)
            else:
                response = PredictionResponse(
                    request_id=request.request_id,
                    success=False,
                    error=f"Unknown request type: {request.request_type}"
                )
            
            # Add processing time
            response.processing_time = time.time() - start_time
            
            # Cache successful responses
            if response.success:
                self.cache.set(request, response)
            
            # Update stats
            self._update_stats(response)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Prediction error for {request.request_id}: {e}")
            response = PredictionResponse(
                request_id=request.request_id,
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )
            self._update_stats(response)
            return response
    
    async def _predict_game(self, request: PredictionRequest) -> PredictionResponse:
        """Predict game outcomes"""
        try:
            game_data = request.data
            
            # Validate required fields
            required_fields = ['home_team', 'away_team', 'week', 'season']
            for field in required_fields:
                if field not in game_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Run prediction in thread pool
            loop = asyncio.get_event_loop()
            prediction_result = await loop.run_in_executor(
                self.executor,
                self.game_models.predict_game,
                game_data
            )
            
            if prediction_result['success']:
                return PredictionResponse(
                    request_id=request.request_id,
                    success=True,
                    predictions={
                        'game_predictions': prediction_result['predictions'],
                        'confidence_scores': {
                            k: v.get('confidence', 0.5) 
                            for k, v in prediction_result['predictions'].items()
                        },
                        'model_info': {
                            k: v.get('model_name', 'unknown')
                            for k, v in prediction_result['predictions'].items()
                        }
                    }
                )
            else:
                return PredictionResponse(
                    request_id=request.request_id,
                    success=False,
                    error=prediction_result.get('error', 'Game prediction failed')
                )
                
        except Exception as e:
            logger.error(f"Game prediction error: {e}")
            return PredictionResponse(
                request_id=request.request_id,
                success=False,
                error=str(e)
            )
    
    async def _predict_props(self, request: PredictionRequest) -> PredictionResponse:
        """Predict player props"""
        try:
            props_data = request.data
            
            # Validate required fields
            required_fields = ['player_data', 'matchup_data']
            for field in required_fields:
                if field not in props_data:
                    raise ValueError(f"Missing required field: {field}")
            
            player_data = props_data['player_data']
            matchup_data = props_data['matchup_data']
            historical_data = props_data.get('historical_data', [])
            
            # Run prediction in thread pool
            loop = asyncio.get_event_loop()
            prediction_result = await loop.run_in_executor(
                self.executor,
                self.props_engine.predict_player_props,
                player_data,
                matchup_data,
                historical_data
            )
            
            if prediction_result['success']:
                # Calculate edges if betting lines provided
                edges = {}
                if 'betting_lines' in props_data:
                    edges = self.props_engine.calculate_prop_edges(
                        prediction_result['predictions'],
                        props_data['betting_lines']
                    )
                
                return PredictionResponse(
                    request_id=request.request_id,
                    success=True,
                    predictions={
                        'player_props': prediction_result['predictions'],
                        'edges': edges,
                        'player_info': {
                            'name': prediction_result['player_name'],
                            'position': prediction_result['position']
                        }
                    }
                )
            else:
                return PredictionResponse(
                    request_id=request.request_id,
                    success=False,
                    error=prediction_result.get('error', 'Props prediction failed')
                )
                
        except Exception as e:
            logger.error(f"Props prediction error: {e}")
            return PredictionResponse(
                request_id=request.request_id,
                success=False,
                error=str(e)
            )
    
    async def _predict_fantasy(self, request: PredictionRequest) -> PredictionResponse:
        """Optimize fantasy lineups"""
        try:
            fantasy_data = request.data
            
            # Validate required fields
            if 'player_pool' not in fantasy_data:
                raise ValueError("Missing required field: player_pool")
            
            player_pool_data = fantasy_data['player_pool']
            strategy = fantasy_data.get('strategy', 'balanced')
            num_lineups = fantasy_data.get('num_lineups', 1)
            
            # Convert player pool to DataFrame
            import pandas as pd
            player_pool = pd.DataFrame(player_pool_data)
            
            # Run optimization in thread pool
            loop = asyncio.get_event_loop()
            
            if num_lineups == 1:
                optimization_result = await loop.run_in_executor(
                    self.executor,
                    self.fantasy_optimizer.optimize_lineup,
                    player_pool,
                    strategy
                )
                
                if optimization_result['success']:
                    # Analyze lineup
                    correlation_analysis = self.fantasy_optimizer.analyze_lineup_correlation(
                        optimization_result['lineup']
                    )
                    value_analysis = self.fantasy_optimizer.calculate_lineup_value(
                        optimization_result['lineup']
                    )
                    
                    return PredictionResponse(
                        request_id=request.request_id,
                        success=True,
                        predictions={
                            'lineup': optimization_result['lineup'],
                            'lineup_metrics': {
                                'total_projection': optimization_result['total_projection'],
                                'total_salary': optimization_result['total_salary'],
                                'remaining_salary': optimization_result['remaining_salary'],
                                'total_ownership': optimization_result['total_ownership']
                            },
                            'correlation_analysis': correlation_analysis,
                            'value_analysis': value_analysis,
                            'strategy': strategy
                        }
                    )
                else:
                    return PredictionResponse(
                        request_id=request.request_id,
                        success=False,
                        error=optimization_result.get('error', 'Fantasy optimization failed')
                    )
            else:
                # Multiple lineups
                lineups_result = await loop.run_in_executor(
                    self.executor,
                    self.fantasy_optimizer.generate_multiple_lineups,
                    player_pool,
                    num_lineups
                )
                
                if lineups_result:
                    return PredictionResponse(
                        request_id=request.request_id,
                        success=True,
                        predictions={
                            'lineups': lineups_result,
                            'lineup_count': len(lineups_result),
                            'strategies_used': list(set(l['strategy'] for l in lineups_result))
                        }
                    )
                else:
                    return PredictionResponse(
                        request_id=request.request_id,
                        success=False,
                        error='Failed to generate multiple lineups'
                    )
                
        except Exception as e:
            logger.error(f"Fantasy prediction error: {e}")
            return PredictionResponse(
                request_id=request.request_id,
                success=False,
                error=str(e)
            )
    
    async def batch_predict(self, requests: List[PredictionRequest]) -> List[PredictionResponse]:
        """Process multiple prediction requests concurrently"""
        try:
            logger.info(f"🔄 Processing batch of {len(requests)} requests")
            
            # Process all requests concurrently
            tasks = [self.predict(request) for request in requests]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            processed_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    processed_responses.append(PredictionResponse(
                        request_id=requests[i].request_id,
                        success=False,
                        error=str(response)
                    ))
                else:
                    processed_responses.append(response)
            
            logger.info(f"✅ Batch processing completed: {len(processed_responses)} responses")
            return processed_responses
            
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}")
            return [PredictionResponse(
                request_id=req.request_id,
                success=False,
                error=f"Batch processing failed: {str(e)}"
            ) for req in requests]
    
    def _update_stats(self, response: PredictionResponse):
        """Update performance statistics"""
        self.performance_stats['total_requests'] += 1
        
        if response.success:
            self.performance_stats['successful_requests'] += 1
        else:
            self.performance_stats['failed_requests'] += 1
        
        # Update average processing time
        if response.processing_time:
            current_avg = self.performance_stats['avg_processing_time']
            total_requests = self.performance_stats['total_requests']
            
            self.performance_stats['avg_processing_time'] = (
                (current_avg * (total_requests - 1) + response.processing_time) / total_requests
            )
        
        # Update cache hit rate
        cache_stats = self.cache.get_stats()
        self.performance_stats['cache_hit_rate'] = cache_stats['hit_rate']
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get engine health and performance status"""
        cache_stats = self.cache.get_stats()
        
        return {
            'status': 'healthy',
            'models_loaded': {
                'game_models': len(self.game_models.model_configs),
                'props_models': len(self.props_engine.prop_configs),
                'fantasy_optimizer': True
            },
            'performance_stats': self.performance_stats,
            'cache_stats': cache_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate cache entries"""
        if pattern:
            self.cache.invalidate_pattern(pattern)
        else:
            # Clear all cache
            self.cache.invalidate_pattern('')
        
        logger.info(f"🗑️ Cache invalidated: {pattern or 'all entries'}")

# Example usage and testing
async def test_prediction_engine():
    """Test the prediction engine"""
    print("🚀 Testing Prediction Engine...")
    
    # Initialize engine
    engine = PredictionEngine(max_workers=2)
    
    # Test game prediction
    game_request = PredictionRequest(
        request_id='test_game_1',
        request_type='game',
        data={
            'home_team': 'KC',
            'away_team': 'BUF',
            'week': 13,
            'season': 2024,
            'point_spread': -2.5,
            'total_line': 48.5
        }
    )
    
    game_response = await engine.predict(game_request)
    print(f"✅ Game prediction: {game_response.success}")
    if game_response.success:
        predictions = game_response.predictions['game_predictions']
        for pred_type, pred_data in predictions.items():
            print(f"  {pred_type}: {pred_data['prediction']}")
    
    # Test props prediction
    props_request = PredictionRequest(
        request_id='test_props_1',
        request_type='props',
        data={
            'player_data': {
                'name': 'Test Player',
                'position': 'WR',
                'season_receiving_yards_avg': 75.5,
                'season_receptions_avg': 5.2
            },
            'matchup_data': {
                'is_home': True,
                'opponent_pass_defense_rank': 22,
                'game_total_line': 48.5
            },
            'historical_data': [
                {'receiving_yards': 82, 'receptions': 6},
                {'receiving_yards': 65, 'receptions': 4}
            ]
        }
    )
    
    props_response = await engine.predict(props_request)
    print(f"✅ Props prediction: {props_response.success}")
    if props_response.success:
        props = props_response.predictions['player_props']
        for prop_type, value in props.items():
            print(f"  {prop_type}: {value['prediction']:.1f}")
    
    # Test batch processing
    batch_requests = [game_request, props_request]
    batch_responses = await engine.batch_predict(batch_requests)
    print(f"✅ Batch processing: {len(batch_responses)} responses")
    
    # Show health status
    health = engine.get_health_status()
    print(f"\\n📊 Engine Health:")
    print(f"  Total requests: {health['performance_stats']['total_requests']}")
    print(f"  Success rate: {health['performance_stats']['successful_requests'] / max(health['performance_stats']['total_requests'], 1):.1%}")
    print(f"  Avg processing time: {health['performance_stats']['avg_processing_time']:.3f}s")
    print(f"  Cache hit rate: {health['cache_stats']['hit_rate']:.1%}")
    
    print("\\n🎉 Prediction Engine test completed!")

if __name__ == "__main__":
    asyncio.run(test_prediction_engine())