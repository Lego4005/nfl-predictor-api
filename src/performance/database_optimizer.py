#!/usr/bin/env python3
"""
Database Performance Optimizer
Handles connection pooling, query optimization, and batch operations for NFL predictions
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

import asyncpg
from asyncpg import Pool, Connection

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_type: str
    execution_time_ms: float
    rows_affected: int
    cache_hit: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'query_type': self.query_type,
            'execution_time_ms': self.execution_time_ms,
            'rows_affected': self.rows_affected,
            'cache_hit': self.cache_hit,
            'error': self.error
        }


class DatabaseOptimizer:
    """
    High-performance database optimizer for NFL predictions

    Features:
    - Connection pooling with asyncpg
    - Batch operations for bulk data
    - Query optimization and prepared statements
    - Performance monitoring and metrics
    - Intelligent query caching
    """

    def __init__(self, database_config: Optional[Dict[str, Any]] = None):
        self.config = database_config or self._get_default_config()
        self.pool: Optional[Pool] = None
        self.query_metrics: List[QueryMetrics] = []
        self.prepared_statements: Dict[str, str] = {}
        self.query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.cache_ttl_minutes = 5

        # Performance tracking
        self.total_queries = 0
        self.total_query_time = 0.0
        self.connection_errors = 0

    async def initialize(self):
        """Initialize database connection pool and optimization"""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                min_size=self.config.get('min_size', 5),
                max_size=self.config.get('max_size', 20),
                command_timeout=self.config.get('command_timeout', 10),
                server_settings={
                    'jit': 'off',  # Disable JIT for predictable performance
                    'statement_timeout': '30s'
                }
            )

            # Create performance indexes
            await self._create_performance_indexes()

            # Prepare common statements
            await self._prepare_common_statements()

            logger.info("✅ Database optimizer initialized with connection pool")

        except Exception as e:
            logger.error(f"❌ Database optimizer initialization failed: {e}")
            raise

    async def shutdown(self):
        """Shutdown database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ Database connection pool closed")

    async def execute_optimized_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        query_type: str = "select",
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute optimized query with metrics and caching"""

        start_time = time.time()
        cache_hit = False

        try:
            # Check cache first
            if use_cache and query_type.lower() == "select":
                cache_key = self._generate_cache_key(query, params)
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    cache_hit = True
                    execution_time = (time.time() - start_time) * 1000

                    self._record_query_metrics(
                        query_type, execution_time, len(cached_result), cache_hit
                    )

                    return cached_result

            # Execute query
            if not self.pool:
                raise Exception("Database pool not initialized")

            async with self.pool.acquire() as conn:
                if params:
                    rows = await conn.fetch(query, *params)
                else:
                    rows = await conn.fetch(query)

                # Convert to dict format
                results = [dict(row) for row in rows]

                # Cache SELECT results
                if use_cache and query_type.lower() == "select" and results:
                    cache_key = self._generate_cache_key(query, params)
                    self._cache_result(cache_key, results)

                execution_time = (time.time() - start_time) * 1000
                self._record_query_metrics(
                    query_type, execution_time, len(results), cache_hit
                )

                return results

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._record_query_metrics(
                query_type, execution_time, 0, cache_hit, str(e)
            )
            logger.error(f"Database query error: {e}")
            raise

    async def execute_batch_operation(
        self,
        operation_type: str,
        data_batches: List[List[Tuple]],
        prepared_statement_name: str
    ) -> int:
        """Execute batch operations for optimal performance"""

        if not self.pool:
            raise Exception("Database pool not initialized")

        total_affected = 0
        start_time = time.time()

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for batch in data_batches:
                        if prepared_statement_name in self.prepared_statements:
                            # Use prepared statement
                            stmt = await conn.prepare(
                                self.prepared_statements[prepared_statement_name]
                            )
                            await stmt.executemany(batch)
                        else:
                            # Fallback to regular batch execution
                            await conn.executemany(
                                self.prepared_statements.get(prepared_statement_name, ""),
                                batch
                            )

                        total_affected += len(batch)

            execution_time = (time.time() - start_time) * 1000
            self._record_query_metrics(
                f"batch_{operation_type}", execution_time, total_affected
            )

            logger.info(f"✅ Batch {operation_type}: {total_affected} records in {execution_time:.1f}ms")
            return total_affected

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._record_query_metrics(
                f"batch_{operation_type}", execution_time, 0, False, str(e)
            )
            logger.error(f"Batch operation error: {e}")
            raise

    async def get_optimized_predictions_data(
        self,
        game_ids: List[str],
        prediction_types: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get prediction data with optimized queries and joins"""

        results = {}

        try:
            # Batch query for game information
            if game_ids:
                game_data = await self._get_games_batch(game_ids)
                results['games'] = game_data

            # Batch query for expert predictions
            if 'expert' in prediction_types:
                expert_data = await self._get_expert_predictions_batch(game_ids)
                results['expert_predictions'] = expert_data

            # Batch query for ML predictions
            if 'ml' in prediction_types:
                ml_data = await self._get_ml_predictions_batch(game_ids)
                results['ml_predictions'] = ml_data

            # Batch query for player props
            if 'props' in prediction_types:
                props_data = await self._get_player_props_batch(game_ids)
                results['player_props'] = props_data

            # Batch query for odds data
            if 'odds' in prediction_types:
                odds_data = await self._get_odds_batch(game_ids)
                results['odds'] = odds_data

            return results

        except Exception as e:
            logger.error(f"Optimized predictions data error: {e}")
            raise

    async def _get_games_batch(self, game_ids: List[str]) -> List[Dict[str, Any]]:
        """Get game information in batch"""

        if not game_ids:
            return []

        placeholders = ','.join(f'${i+1}' for i in range(len(game_ids)))

        query = f"""
            SELECT
                game_id,
                home_team,
                away_team,
                game_date,
                week,
                season,
                status,
                weather_conditions,
                stadium
            FROM games
            WHERE game_id = ANY($1::text[])
            ORDER BY game_date ASC;
        """

        return await self.execute_optimized_query(
            query, (game_ids,), "select", use_cache=True
        )

    async def _get_expert_predictions_batch(self, game_ids: List[str]) -> List[Dict[str, Any]]:
        """Get expert predictions in batch with optimized join"""

        if not game_ids:
            return []

        query = """
            SELECT
                ep.game_id,
                ep.expert_id,
                ep.expert_name,
                ep.prediction_type,
                ep.prediction_value,
                ep.confidence,
                ep.reasoning,
                ep.created_at
            FROM expert_predictions ep
            INNER JOIN games g ON ep.game_id = g.game_id
            WHERE ep.game_id = ANY($1::text[])
                AND ep.created_at > CURRENT_TIMESTAMP - INTERVAL '1 day'
            ORDER BY ep.game_id, ep.expert_id, ep.prediction_type;
        """

        return await self.execute_optimized_query(
            query, (game_ids,), "select", use_cache=True
        )

    async def _get_ml_predictions_batch(self, game_ids: List[str]) -> List[Dict[str, Any]]:
        """Get ML predictions in batch"""

        if not game_ids:
            return []

        query = """
            SELECT
                p.game_id,
                p.model_type,
                p.prediction_type,
                p.predicted_value,
                p.confidence_score,
                p.model_version,
                p.created_at
            FROM predictions p
            WHERE p.game_id = ANY($1::text[])
                AND p.created_at > CURRENT_TIMESTAMP - INTERVAL '1 day'
            ORDER BY p.game_id, p.model_type, p.prediction_type;
        """

        return await self.execute_optimized_query(
            query, (game_ids,), "select", use_cache=True
        )

    async def _get_player_props_batch(self, game_ids: List[str]) -> List[Dict[str, Any]]:
        """Get player props in batch"""

        if not game_ids:
            return []

        query = """
            SELECT
                pp.game_id,
                pp.player_id,
                pp.player_name,
                pp.team,
                pp.position,
                pp.prop_type,
                pp.predicted_value,
                pp.over_under_line,
                pp.confidence,
                pp.created_at
            FROM player_props pp
            WHERE pp.game_id = ANY($1::text[])
                AND pp.created_at > CURRENT_TIMESTAMP - INTERVAL '1 day'
            ORDER BY pp.game_id, pp.player_name, pp.prop_type;
        """

        return await self.execute_optimized_query(
            query, (game_ids,), "select", use_cache=True
        )

    async def _get_odds_batch(self, game_ids: List[str]) -> List[Dict[str, Any]]:
        """Get latest odds data in batch"""

        if not game_ids:
            return []

        query = """
            SELECT DISTINCT ON (o.game_id, o.sportsbook)
                o.game_id,
                o.sportsbook,
                o.home_spread,
                o.away_spread,
                o.total_over_under,
                o.home_moneyline,
                o.away_moneyline,
                o.timestamp
            FROM odds o
            WHERE o.game_id = ANY($1::text[])
                AND o.timestamp > CURRENT_TIMESTAMP - INTERVAL '1 day'
            ORDER BY o.game_id, o.sportsbook, o.timestamp DESC;
        """

        return await self.execute_optimized_query(
            query, (game_ids,), "select", use_cache=True
        )

    async def _create_performance_indexes(self):
        """Create performance indexes for faster queries"""

        indexes = [
            # Core game indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_games_date_status
            ON games (game_date DESC, status)
            WHERE status IN ('scheduled', 'in_progress', 'completed');
            """,

            # Expert predictions indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_predictions_game_created
            ON expert_predictions (game_id, created_at DESC);
            """,

            # ML predictions indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_game_model_created
            ON predictions (game_id, model_type, created_at DESC);
            """,

            # Player props indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_player_props_game_player
            ON player_props (game_id, player_id, created_at DESC);
            """,

            # Odds indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_odds_game_sportsbook_timestamp
            ON odds (game_id, sportsbook, timestamp DESC);
            """,

            # Composite index for recent data
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recent_predictions_composite
            ON predictions (created_at DESC, game_id, model_type)
            WHERE created_at > CURRENT_DATE - INTERVAL '7 days';
            """
        ]

        if self.pool:
            async with self.pool.acquire() as conn:
                for index_sql in indexes:
                    try:
                        await conn.execute(index_sql)
                        logger.info(f"✅ Created performance index")
                    except Exception as e:
                        logger.warning(f"Index creation warning: {e}")

    async def _prepare_common_statements(self):
        """Prepare commonly used SQL statements"""

        self.prepared_statements = {
            'insert_prediction': """
                INSERT INTO predictions (
                    game_id, model_type, prediction_type, predicted_value,
                    confidence_score, model_version, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7);
            """,

            'insert_expert_prediction': """
                INSERT INTO expert_predictions (
                    game_id, expert_id, expert_name, prediction_type,
                    prediction_value, confidence, reasoning, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
            """,

            'insert_player_prop': """
                INSERT INTO player_props (
                    game_id, player_id, player_name, team, position,
                    prop_type, predicted_value, confidence, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);
            """,

            'update_game_status': """
                UPDATE games
                SET status = $2, last_updated = $3
                WHERE game_id = $1;
            """
        }

        logger.info(f"✅ Prepared {len(self.prepared_statements)} SQL statements")

    def _generate_cache_key(self, query: str, params: Optional[Tuple]) -> str:
        """Generate cache key for query result"""
        import hashlib

        key_data = query
        if params:
            key_data += str(params)

        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached query result if not expired"""

        if cache_key in self.query_cache:
            result, timestamp = self.query_cache[cache_key]
            if datetime.now() - timestamp < timedelta(minutes=self.cache_ttl_minutes):
                return result
            else:
                # Remove expired cache entry
                del self.query_cache[cache_key]

        return None

    def _cache_result(self, cache_key: str, result: List[Dict[str, Any]]):
        """Cache query result with timestamp"""

        # Limit cache size
        if len(self.query_cache) > 1000:
            # Remove oldest entries
            oldest_keys = sorted(
                self.query_cache.keys(),
                key=lambda k: self.query_cache[k][1]
            )[:100]

            for key in oldest_keys:
                del self.query_cache[key]

        self.query_cache[cache_key] = (result, datetime.now())

    def _record_query_metrics(
        self,
        query_type: str,
        execution_time_ms: float,
        rows_affected: int,
        cache_hit: bool = False,
        error: Optional[str] = None
    ):
        """Record query performance metrics"""

        metric = QueryMetrics(
            query_type=query_type,
            execution_time_ms=execution_time_ms,
            rows_affected=rows_affected,
            cache_hit=cache_hit,
            error=error
        )

        self.query_metrics.append(metric)

        # Keep only recent metrics
        if len(self.query_metrics) > 10000:
            self.query_metrics = self.query_metrics[-5000:]

        # Update aggregate stats
        self.total_queries += 1
        self.total_query_time += execution_time_ms

        if error:
            self.connection_errors += 1

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default database configuration"""
        import os

        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'nfl_predictor'),
            'min_size': 5,
            'max_size': 20,
            'command_timeout': 10
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""

        if not self.query_metrics:
            return {'no_data': True}

        # Calculate metrics from recent queries
        recent_metrics = self.query_metrics[-1000:]  # Last 1000 queries

        total_time = sum(m.execution_time_ms for m in recent_metrics)
        avg_time = total_time / len(recent_metrics) if recent_metrics else 0

        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        cache_hit_rate = cache_hits / len(recent_metrics) * 100 if recent_metrics else 0

        errors = sum(1 for m in recent_metrics if m.error)
        error_rate = errors / len(recent_metrics) * 100 if recent_metrics else 0

        query_types = {}
        for metric in recent_metrics:
            if metric.query_type not in query_types:
                query_types[metric.query_type] = {
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0
                }

            query_types[metric.query_type]['count'] += 1
            query_types[metric.query_type]['total_time'] += metric.execution_time_ms

        # Calculate averages
        for qtype in query_types:
            if query_types[qtype]['count'] > 0:
                query_types[qtype]['avg_time'] = (
                    query_types[qtype]['total_time'] / query_types[qtype]['count']
                )

        return {
            'total_queries': self.total_queries,
            'recent_queries_analyzed': len(recent_metrics),
            'avg_query_time_ms': round(avg_time, 2),
            'cache_hit_rate_percent': round(cache_hit_rate, 1),
            'error_rate_percent': round(error_rate, 1),
            'query_types_performance': query_types,
            'connection_pool_healthy': self.pool is not None and not self.pool.is_closing(),
            'cached_results_count': len(self.query_cache)
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""

        try:
            if not self.pool:
                return {'healthy': False, 'error': 'Pool not initialized'}

            # Test query
            start_time = time.time()
            result = await self.execute_optimized_query(
                "SELECT 1 as health_check;",
                query_type="health_check",
                use_cache=False
            )
            query_time = (time.time() - start_time) * 1000

            pool_info = {
                'size': self.pool.get_size(),
                'min_size': self.pool.get_min_size(),
                'max_size': self.pool.get_max_size(),
                'idle_connections': self.pool.get_idle_size()
            }

            return {
                'healthy': True,
                'query_time_ms': round(query_time, 2),
                'connection_pool': pool_info,
                'performance_metrics': self.get_performance_metrics()
            }

        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'connection_errors': self.connection_errors
            }


# Global database optimizer instance
database_optimizer = DatabaseOptimizer()

async def get_database_optimizer() -> DatabaseOptimizer:
    """Get the initialized database optimizer"""
    if database_optimizer.pool is None:
        await database_optimizer.initialize()
    return database_optimizer