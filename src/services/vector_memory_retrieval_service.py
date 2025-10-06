"""
Vector Memory Retrieval Service for Expert Prediction Generation

This service integrates vector memory search with expert prediction generation,
providing relevant memories to improve prediction accuracy and reasoning.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
frodataclasses import dataclass

from supabase import Client as SupabaseClient
from .memory_embedding_generator import MemoryEmbeddingGenerator, SimilarityResult


@dataclass
class RetrievedMemory:
    """Memory retrieved for prediction context"""
    memory_id: str
    expert_id: str
    game_id: str
    memory_type: str
    similarity_score: float
    relevance_score: float
    memory_content: Dict[str, Any]
    contextual_factors: List[str]
    lessons_learned: List[str]
    emotional_intensity: float
    retrieval_reason: str


@dataclass
class MemoryRetrievalResult:
    """Result of memory retrieval for prediction"""
    expert_id: str
    query_context: Dict[str, Any]
    retrieved_memories: List[RetrievedMemory]
    retrieval_time_ms: int
    total_memories_searched: int
    relevance_threshold_used: float
    retrieval_strategy: str


@dataclass
class MemoryPerformanceMetrics:
    """Performance metrics for memory retrieval"""
    average_retrieval_time_ms: float
    cache_hit_rate: float
    memory_usage_mb: float
    successful_retrievals: int
    failed_retrievals: int
    total_memories_in_system: int


class VectorMemoryRetrievalService:
    """
    Service that integrates vector memory search with expert prediction generation.
    Provides contextually relevant memories to enhance expert reasoning and accuracy.
    """

    def __init__(
        self,
        supabase_client: SupabaseClient,
        embedding_generator: MemoryEmbeddingGenerator,
        cache_size: int = 1000
    ):
        self.supabase = supabase_client
        self.embedding_generator = embedding_generator
        self.logger = logging.getLogger(__name__)

        # Performance optimization
        self.cache_size = cache_size
        self.memory_cache = {}  # Simple LRU cache for frequently accessed memories
        self.cache_access_times = {}

        # Performance tracking
        self.performance_metrics = {
            'total_retrievals': 0,
            'successful_retrievals': 0,
            'failed_retrievals': 0,
            'total_retrieval_time_ms': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        self.logger.info("VectorMemoryRetrievalService initialized")

    async def retrieve_memories_for_prediction(
        self,
        expert_id: str,
        game_context: Dict[str, Any],
        prediction_context: Optional[Dict[str, Any]] = None,
        max_memories: int = 7,  # Working memory capacity
        relevance_threshold: float = 0.6,
        strategy: str = 'adaptive'
    ) -> MemoryRetrievalResult:
        """
        Retrieve relevant memories for expert prediction generation.

        Args:
            expert_id: ID of the expert making the prediction
            game_context: Current game context
            prediction_context: Additional prediction context (optional)
            max_memories: Maximum memories to retrieve (working memory limit)
            relevance_threshold: Minimum relevance score for memories
            strategy: Retrieval strategy ('adaptive', 'similarity_only', 'recency_weighted')

        Returns:
            MemoryRetrievalResult: Retrieved memories with metadata
        """
        start_time = time.time()

        try:
            self.performance_metrics['total_retrievals'] += 1

            # Check cache first
            cache_key = self._generate_cache_key(expert_id, game_context, max_memories, relevance_threshold)
            cached_result = self._get_from_cache(cache_key)

            if cached_result:
                self.performance_metrics['cache_hits'] += 1
                self.logger.debug(f"Cache hit for expert {expert_id}")
                return cached_result

            self.performance_metrics['cache_misses'] += 1

            # Determine retrieval strategy parameters
            strategy_params = self._get_strategy_parameters(strategy, game_context, prediction_context)

            # Retrieve memories using different embedding types
            all_memories = []

            # Primary retrieval: Combined embeddings for comprehensive similarity
            combined_memories = await self.embedding_generator.find_similar_memories(
                expert_id=expert_id,
                query_game_context=game_context,
                embedding_type='combined',
                similarity_threshold=relevance_threshold,
                max_results=max_memories * 2,  # Get more to filter
                **strategy_params
            )

            # Secondary retrieval: Game context embeddings for situational similarity
            context_memories = await self.embedding_generator.find_similar_memories(
                expert_id=expert_id,
                query_game_context=game_context,
                embedding_type='game_context',
                similarity_threshold=relevance_threshold * 0.9,  # Slightly lower threshold
                max_results=max_memories,
                **strategy_params
            )

            # Merge and deduplicate memories
            memory_map = {}

            # Add combined memories with higher weight
            for memory in combined_memories:
                memory_map[memory.memory_id] = {
                    'memory': memory,
                    'weight': memory.relevance_score * 1.2,  # Boost combined embeddings
                    'source': 'combined'
                }

            # Add context memories
            for memory in context_memories:
                if memory.memory_id not in memory_map:
                    memory_map[memory.memory_id] = {
                        'memory': memory,
                        'weight': memory.relevance_score,
                        'source': 'context'
                    }
                else:
                    # Boost weight if found in both searches
                    memory_map[memory.memory_id]['weight'] *= 1.1
                    memory_map[memory.memory_id]['source'] = 'both'

            # Sort by weight and take top memories
            sorted_memories = sorted(
                memory_map.values(),
                key=lambda x: x['weight'],
                reverse=True
            )[:max_memories]

            # Convert to RetrievedMemory objects with full context
            retrieved_memories = []
            for memory_data in sorted_memories:
                memory = memory_data['memory']

                # Get full memory details
                full_memory = await self._get_full_memory_details(memory.memory_id)

                if full_memory:
                    retrieved_memory = RetrievedMemory(
                        memory_id=memory.memory_id,
                        expert_id=memory.expert_id,
                        game_id=memory.game_id,
                        memory_type=memory.memory_type,
                        similarity_score=memory.similarity_score,
                        relevance_score=memory.relevance_score,
                        memory_content=full_memory.get('prediction_data', {}),
                        contextual_factors=full_memory.get('contextual_factors', []),
                        lessons_learned=full_memory.get('lessons_learned', []),
                        emotional_intensity=full_memory.get('emotional_intensity', 0.5),
                        retrieval_reason=f"Retrieved via {memory_data['source']} embedding (weight: {memory_data['weight']:.3f})"
                    )
                    retrieved_memories.append(retrieved_memory)

            # Create result
            retrieval_time_ms = int((time.time() - start_time) * 1000)

            result = MemoryRetrievalResult(
                expert_id=expert_id,
                query_context=game_context,
                retrieved_memories=retrieved_memories,
                retrieval_time_ms=retrieval_time_ms,
                total_memories_searched=len(combined_memories) + len(context_memories),
                relevance_threshold_used=relevance_threshold,
                retrieval_strategy=strategy
            )

            # Cache the result
            self._add_to_cache(cache_key, result)

            # Update performance metrics
            self.performance_metrics['successful_retrievals'] += 1
            self.performance_metrics['total_retrieval_time_ms'] += retrieval_time_ms

            self.logger.info(f"Retrieved {len(retrieved_memories)} memories for expert {expert_id} in {retrieval_time_ms}ms")
            return result

        except Exception as e:
            self.performance_metrics['failed_retrievals'] += 1
            self.logger.error(f"Error retrieving memories for expert {expert_id}: {str(e)}")

            # Return empty result on error
            return MemoryRetrievalResult(
                expert_id=expert_id,
                query_context=game_context,
                retrieved_memories=[],
                retrieval_time_ms=int((time.time() - start_time) * 1000),
                total_memories_searched=0,
                relevance_threshold_used=relevance_threshold,
                retrieval_strategy=strategy
            )

    def _get_strategy_parameters(
        self,
        strategy: str,
        game_context: Dict[str, Any],
        prediction_context: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Get parameters for different retrieval strategies"""

        if strategy == 'similarity_only':
            return {
                'recency_weight': 0.1,
                'vividness_weight': 0.2,
                'similarity_weight': 0.7
            }

        elif strategy == 'recency_weighted':
            return {
                'recency_weight': 0.5,
                'vividness_weight': 0.3,
                'similarity_weight': 0.2
            }

        elif strategy == 'adaptive':
            # Adaptive strategy based on game context
            week = game_context.get('week', 8)

            if week <= 4:
                # Early season: Prioritize similarity over recency
                return {
                    'recency_weight': 0.2,
                    'vividness_weight': 0.4,
                    'similarity_weight': 0.4
                }
            elif week >= 15:
                # Late season: Balance all factors
                return {
                    'recency_weight': 0.35,
                    'vividness_weight': 0.35,
                    'similarity_weight': 0.3
                }
            else:
                # Mid season: Standard balanced approach
                return {
                    'recency_weight': 0.3,
                    'vividness_weight': 0.4,
                    'similarity_weight': 0.3
                }

        else:
            # Default balanced approach
            return {
                'recency_weight': 0.3,
                'vividness_weight': 0.4,
                'similarity_weight': 0.3
            }

    async def _get_full_memory_details(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get full memory details from database"""
        try:
            response = self.supabase.table('expert_episodic_memories').select('*').eq('memory_id', memory_id).execute()

            if response.data:
                return response.data[0]
            return None

        except Exception as e:
            self.logger.error(f"Error getting full memory details for {memory_id}: {str(e)}")
            return None

    def _generate_cache_key(
        self,
        expert_id: str,
        game_context: Dict[str, Any],
        max_memories: int,
        relevance_threshold: float
    ) -> str:
        """Generate cache key for memory retrieval"""
        import hashlib

        # Create a stable key from the parameters
        key_data = {
            'expert_id': expert_id,
            'home_team': game_context.get('home_team'),
            'away_team': game_context.get('away_team'),
            'week': game_context.get('week'),
            'season': game_context.get('season'),
            'max_memories': max_memories,
            'relevance_threshold': relevance_threshold
        }

        key_string = str(sorted(key_data.items()))
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[MemoryRetrievalResult]:
        """Get result from cache if available and not expired"""
        if cache_key in self.memory_cache:
            cached_data = self.memory_cache[cache_key]

            # Check if cache entry is still valid (5 minutes)
            if time.time() - cached_data['timestamp'] < 300:
                self.cache_access_times[cache_key] = time.time()
                return cached_data['result']
            else:
                # Remove expired entry
                del self.memory_cache[cache_key]
                if cache_key in self.cache_access_times:
                    del self.cache_access_times[cache_key]

        return None

    def _add_to_cache(self, cache_key: str, result: MemoryRetrievalResult) -> None:
        """Add result to cache with LRU eviction"""
        # Implement simple LRU eviction if cache is full
        if len(self.memory_cache) >= self.cache_size:
            # Remove least recently used item
            if self.cache_access_times:
                lru_key = min(self.cache_access_times.keys(), key=lambda k: self.cache_access_times[k])
                del self.memory_cache[lru_key]
                del self.cache_access_times[lru_key]

        # Add new entry
        self.memory_cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
        self.cache_access_times[cache_key] = time.time()

    async def optimize_memory_retrieval_performance(
        self,
        expert_id: str,
        test_contexts: List[Dict[str, Any]],
        target_retrieval_time_ms: int = 100
    ) -> Dict[str, Any]:
        """
        Optimize memory retrieval performance for an expert.

        Args:
            expert_id: ID of the expert to optimize for
            test_contexts: List of game contexts to test with
            target_retrieval_time_ms: Target retrieval time in milliseconds

        Returns:
            Dict with optimization results and recommendations
        """
        try:
            optimization_results = {
                'expert_id': expert_id,
                'test_contexts_count': len(test_contexts),
                'target_time_ms': target_retrieval_time_ms,
                'performance_tests': [],
                'recommendations': []
            }

            # Test different configurations
            configurations = [
                {'max_memories': 5, 'threshold': 0.7, 'strategy': 'similarity_only'},
                {'max_memories': 7, 'threshold': 0.6, 'strategy': 'adaptive'},
                {'max_memories': 10, 'threshold': 0.5, 'strategy': 'recency_weighted'},
            ]

            for config in configurations:
                config_results = []

                for context in test_contexts[:5]:  # Test with first 5 contexts
                    start_time = time.time()

                    result = await self.retrieve_memories_for_prediction(
                        expert_id=expert_id,
                        game_context=context,
                        max_memories=config['max_memories'],
                        relevance_threshold=config['threshold'],
                        strategy=config['strategy']
                    )

                    retrieval_time = (time.time() - start_time) * 1000

                    config_results.append({
                        'retrieval_time_ms': retrieval_time,
                        'memories_retrieved': len(result.retrieved_memories),
                        'avg_relevance_score': sum(m.relevance_score for m in result.retrieved_memories) / len(result.retrieved_memories) if result.retrieved_memories else 0
                    })

                # Calculate averages for this configuration
                avg_time = sum(r['retrieval_time_ms'] for r in config_results) / len(config_results)
                avg_memories = sum(r['memories_retrieved'] for r in config_results) / len(config_results)
                avg_relevance = sum(r['avg_relevance_score'] for r in config_results) / len(config_results)

                optimization_results['performance_tests'].append({
                    'configuration': config,
                    'avg_retrieval_time_ms': avg_time,
                    'avg_memories_retrieved': avg_memories,
                    'avg_relevance_score': avg_relevance,
                    'meets_target': avg_time <= target_retrieval_time_ms
                })

            # Generate recommendations
            best_config = min(
                optimization_results['performance_tests'],
                key=lambda x: abs(x['avg_retrieval_time_ms'] - target_retrieval_time_ms)
            )

            optimization_results['recommendations'].append(
                f"Best configuration for {target_retrieval_time_ms}ms target: {best_config['configuration']}"
            )

            if best_config['avg_retrieval_time_ms'] > target_retrieval_time_ms:
                optimization_results['recommendations'].append(
                    "Consider reducing max_memories or increasing relevance_threshold for better performance"
                )

            if best_config['avg_relevance_score'] < 0.6:
                optimization_results['recommendations'].append(
                    "Consider lowering relevance_threshold to retrieve more relevant memories"
                )

            return optimization_results

        except Exception as e:
            self.logger.error(f"Error optimizing memory retrieval performance: {str(e)}")
            return {
                'expert_id': expert_id,
                'error': str(e),
                'recommendations': ['Performance optimization failed - check logs for details']
            }

    async def get_performance_metrics(self) -> MemoryPerformanceMetrics:
        """Get current performance metrics for the retrieval service"""
        try:
            # Calculate averages
            total_retrievals = self.performance_metrics['total_retrievals']

            avg_retrieval_time = (
                self.performance_metrics['total_retrieval_time_ms'] / total_retrievals
                if total_retrievals > 0 else 0
            )

            cache_hit_rate = (
                self.performance_metrics['cache_hits'] /
                (self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses'])
                if (self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses']) > 0 else 0
            )

            # Get total memories in system
            response = self.supabase.table('expert_episodic_memories').select('id', count='exact').execute()
            total_memories = response.count or 0

            # Estimate memory usage (rough calculation)
            memory_usage_mb = (
                len(self.memory_cache) * 0.1 +  # Rough estimate per cached item
                total_memories * 0.001  # Rough estimate per memory in system
            )

            return MemoryPerformanceMetrics(
                average_retrieval_time_ms=avg_retrieval_time,
                cache_hit_rate=cache_hit_rate,
                memory_usage_mb=memory_usage_mb,
                successful_retrievals=self.performance_metrics['successful_retrievals'],
                failed_retrievals=self.performance_metrics['failed_retrievals'],
                total_memories_in_system=total_memories
            )

        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {str(e)}")
            return MemoryPerformanceMetrics(
                average_retrieval_time_ms=0,
                cache_hit_rate=0,
                memory_usage_mb=0,
                successful_retrievals=0,
                failed_retrievals=0,
                total_memories_in_system=0
            )

    def clear_cache(self) -> None:
        """Clear the memory cache"""
        self.memory_cache.clear()
        self.cache_access_times.clear()
        self.logger.info("Memory cache cleared")

    async def preload_memories_for_expert(self, expert_id: str, upcoming_games: List[Dict[str, Any]]) -> None:
        """Preload memories for upcoming games to improve performance"""
        try:
            self.logger.info(f"Preloading memories for expert {expert_id} for {len(upcoming_games)} upcoming games")

            for game_context in upcoming_games:
                # Preload memories into cache
                await self.retrieve_memories_for_prediction(
                    expert_id=expert_id,
                    game_context=game_context,
                    max_memories=7,
                    relevance_threshold=0.6,
                    strategy='adaptive'
                )

            self.logger.info(f"Preloaded memories for expert {expert_id}")

        except Exception as e:
            self.logger.error(f"Error preloading memories for expert {expert_id}: {str(e)}")


# Global instance for easy access
_retrieval_service = None

def get_retrieval_service(
    supabase_client: SupabaseClient,
    embedding_generator: MemoryEmbeddingGenerator
) -> VectorMemoryRetrievalService:
    """Get global retrieval service instance"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = VectorMemoryRetrievalService(supabase_client, embedding_generator)
    return _retrieval_service
