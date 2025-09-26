"""
Production database optimization configuration and utilities.
Handles Supabase connection optimization, query performance, and monitoring.
"""

import os
import asyncio
import asyncpg
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class DatabaseOptimizationConfig:
    """Configuration for database optimization settings"""
    # Connection pool settings
    min_pool_size: int = 5
    max_pool_size: int = 20
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0
    
    # Query optimization
    statement_cache_size: int = 1024
    prepared_statement_cache_size: int = 100
    query_timeout: float = 30.0
    
    # Monitoring settings
    slow_query_threshold: float = 1.0
    enable_query_logging: bool = True
    log_slow_queries: bool = True
    
    # Index optimization
    auto_analyze_threshold: int = 1000
    enable_auto_vacuum: bool = True
    
    # Performance settings
    shared_buffers: str = "256MB"
    effective_cache_size: str = "1GB"
    work_mem: str = "4MB"
    maintenance_work_mem: str = "64MB"
    
    # Supabase specific settings
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""
    database_url: str = ""


class DatabaseOptimizer:
    """Database optimization and monitoring utilities"""
    
    def __init__(self, config: DatabaseOptimizationConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        
    async def initialize_pool(self) -> None:
        """Initialize optimized database connection pool"""
        try:
            # Parse database URL from Supabase URL
            db_url = self._construct_database_url()
            
            self.pool = await asyncpg.create_pool(
                db_url,
                min_size=self.config.min_pool_size,
                max_size=self.config.max_pool_size,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                command_timeout=self.config.query_timeout,
                statement_cache_size=self.config.statement_cache_size,
                setup=self._setup_connection
            )
            
            logger.info(f"Database pool initialized with {self.config.min_pool_size}-{self.config.max_pool_size} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    def _construct_database_url(self) -> str:
        """Construct PostgreSQL connection URL from Supabase config"""
        if self.config.database_url:
            return self.config.database_url
        
        # Extract database connection details from Supabase URL
        # Format: postgresql://postgres:[password]@[host]:5432/postgres
        if self.config.supabase_url:
            # Parse Supabase URL to get host
            host = self.config.supabase_url.replace("https://", "").replace("http://", "")
            if host.endswith("/"):
                host = host[:-1]
            
            # Default Supabase database connection
            password = os.getenv("SUPABASE_DB_PASSWORD", "")
            return f"postgresql://postgres:{password}@db.{host}:5432/postgres"
        
        # Fallback to local development
        return "postgresql://postgres:postgres@localhost:54322/postgres"
    
    async def _setup_connection(self, connection: asyncpg.Connection) -> None:
        """Setup individual database connection with optimizations"""
        # Set connection-level optimizations
        await connection.execute("SET statement_timeout = '30s'")
        await connection.execute("SET lock_timeout = '10s'")
        await connection.execute("SET idle_in_transaction_session_timeout = '60s'")
        
        # Enable query plan caching
        await connection.execute("SET plan_cache_mode = 'force_generic_plan'")
        
        # Optimize for read-heavy workloads
        await connection.execute("SET effective_io_concurrency = 200")
        await connection.execute("SET random_page_cost = 1.1")
        
        logger.debug("Database connection optimized")
    
    async def close_pool(self) -> None:
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get optimized database connection from pool"""
        if not self.pool:
            await self.initialize_pool()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_optimized_query(
        self, 
        query: str, 
        *args, 
        query_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute query with optimization and monitoring"""
        start_time = datetime.now()
        query_id = query_name or query[:50]
        
        try:
            async with self.get_connection() as conn:
                # Enable detailed query logging if configured
                if self.config.enable_query_logging:
                    await conn.execute("SET log_statement = 'all'")
                
                # Execute query
                result = await conn.fetch(query, *args)
                
                # Convert to list of dictionaries
                result_list = [dict(row) for row in result]
                
                # Track query performance
                execution_time = (datetime.now() - start_time).total_seconds()
                await self._track_query_performance(query_id, execution_time, len(result_list))
                
                return result_list
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Query failed ({execution_time:.3f}s): {query_id} - {e}")
            raise
    
    async def _track_query_performance(
        self, 
        query_id: str, 
        execution_time: float, 
        row_count: int
    ) -> None:
        """Track and log query performance statistics"""
        if query_id not in self.query_stats:
            self.query_stats[query_id] = {
                "total_calls": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "max_time": 0.0,
                "min_time": float('inf'),
                "total_rows": 0
            }
        
        stats = self.query_stats[query_id]
        stats["total_calls"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["total_calls"]
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["min_time"] = min(stats["min_time"], execution_time)
        stats["total_rows"] += row_count
        
        # Log slow queries
        if self.config.log_slow_queries and execution_time > self.config.slow_query_threshold:
            logger.warning(f"Slow query detected: {query_id} took {execution_time:.3f}s")
    
    async def optimize_tables(self) -> None:
        """Run database optimization maintenance"""
        try:
            async with self.get_connection() as conn:
                logger.info("Starting database optimization maintenance")
                
                # Update table statistics
                await conn.execute("ANALYZE")
                logger.info("Table statistics updated")
                
                # Vacuum tables if auto-vacuum is enabled
                if self.config.enable_auto_vacuum:
                    await conn.execute("VACUUM")
                    logger.info("Database vacuum completed")
                
                # Reindex heavily used tables
                critical_tables = [
                    "enhanced_expert_models",
                    "expert_predictions_enhanced", 
                    "ai_council_selections",
                    "expert_performance_analytics",
                    "prediction_categories"
                ]
                
                for table in critical_tables:
                    try:
                        await conn.execute(f"REINDEX TABLE {table}")
                        logger.info(f"Reindexed table: {table}")
                    except Exception as e:
                        logger.warning(f"Failed to reindex {table}: {e}")
                
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise
    
    async def create_performance_indexes(self) -> None:
        """Create optimized indexes for better query performance"""
        indexes = [
            # Expert competition framework indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_models_status_priority 
            ON enhanced_expert_models(is_active, expertise_areas, current_rank)
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_predictions_game_time 
            ON expert_predictions_enhanced(game_id, prediction_timestamp, expert_id)
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_council_round_performance 
            ON ai_council_selections(round_id, selection_timestamp, expert_performance_score)
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_analytics_category 
            ON expert_performance_analytics(expert_id, category, metric_type, timestamp)
            """,
            # Query optimization indexes
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_confidence_accuracy 
            ON expert_predictions_enhanced(confidence_score, accuracy_score) 
            WHERE accuracy_score IS NOT NULL
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_trends_recent 
            ON expert_performance_analytics(expert_id, timestamp DESC) 
            WHERE timestamp > NOW() - INTERVAL '30 days'
            """,
            # Composite indexes for complex queries
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_council_consensus_voting 
            ON ai_council_voting(round_id, expert_id, weight, vote_timestamp)
            """,
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_self_healing_events_recent 
            ON self_healing_events(trigger_type, event_timestamp DESC, expert_id)
            WHERE event_timestamp > NOW() - INTERVAL '7 days'
            """
        ]
        
        try:
            async with self.get_connection() as conn:
                logger.info("Creating performance-optimized indexes")
                
                for idx, query in enumerate(indexes):
                    try:
                        await conn.execute(query)
                        logger.info(f"Created index {idx + 1}/{len(indexes)}")
                    except Exception as e:
                        logger.warning(f"Index creation failed for query {idx + 1}: {e}")
                
                logger.info("Performance index creation completed")
                
        except Exception as e:
            logger.error(f"Failed to create performance indexes: {e}")
            raise
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate database performance report"""
        if not self.query_stats:
            return {"message": "No query statistics available"}
        
        # Calculate aggregate statistics
        total_queries = sum(stats["total_calls"] for stats in self.query_stats.values())
        total_time = sum(stats["total_time"] for stats in self.query_stats.values())
        avg_query_time = total_time / total_queries if total_queries > 0 else 0
        
        # Find slowest queries
        slowest_queries = sorted(
            self.query_stats.items(),
            key=lambda x: x[1]["avg_time"],
            reverse=True
        )[:5]
        
        # Find most frequent queries
        frequent_queries = sorted(
            self.query_stats.items(),
            key=lambda x: x[1]["total_calls"],
            reverse=True
        )[:5]
        
        return {
            "summary": {
                "total_queries": total_queries,
                "total_execution_time": round(total_time, 3),
                "average_query_time": round(avg_query_time, 3),
                "unique_queries": len(self.query_stats)
            },
            "slowest_queries": [
                {
                    "query": query,
                    "avg_time": round(stats["avg_time"], 3),
                    "max_time": round(stats["max_time"], 3),
                    "total_calls": stats["total_calls"]
                }
                for query, stats in slowest_queries
            ],
            "most_frequent_queries": [
                {
                    "query": query,
                    "total_calls": stats["total_calls"],
                    "avg_time": round(stats["avg_time"], 3),
                    "total_time": round(stats["total_time"], 3)
                }
                for query, stats in frequent_queries
            ],
            "pool_status": {
                "min_size": self.config.min_pool_size,
                "max_size": self.config.max_pool_size,
                "current_size": len(self.pool._holders) if self.pool else 0
            }
        }


# Production database configuration
def get_production_db_config() -> DatabaseOptimizationConfig:
    """Get production database configuration from environment"""
    return DatabaseOptimizationConfig(
        # Connection pool optimization
        min_pool_size=int(os.getenv("DB_MIN_POOL_SIZE", "10")),
        max_pool_size=int(os.getenv("DB_MAX_POOL_SIZE", "50")),
        max_queries=int(os.getenv("DB_MAX_QUERIES", "100000")),
        max_inactive_connection_lifetime=float(os.getenv("DB_MAX_INACTIVE_LIFETIME", "600")),
        
        # Query optimization
        statement_cache_size=int(os.getenv("DB_STATEMENT_CACHE_SIZE", "2048")),
        prepared_statement_cache_size=int(os.getenv("DB_PREPARED_CACHE_SIZE", "200")),
        query_timeout=float(os.getenv("DB_QUERY_TIMEOUT", "60")),
        
        # Monitoring
        slow_query_threshold=float(os.getenv("DB_SLOW_QUERY_THRESHOLD", "2.0")),
        enable_query_logging=os.getenv("DB_ENABLE_QUERY_LOGGING", "true").lower() == "true",
        log_slow_queries=os.getenv("DB_LOG_SLOW_QUERIES", "true").lower() == "true",
        
        # Supabase configuration
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=os.getenv("SUPABASE_ANON_KEY", ""),
        supabase_service_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        database_url=os.getenv("DATABASE_URL", "")
    )


# Global database optimizer instance
db_optimizer: Optional[DatabaseOptimizer] = None


async def initialize_database_optimization() -> DatabaseOptimizer:
    """Initialize global database optimizer"""
    global db_optimizer
    config = get_production_db_config()
    db_optimizer = DatabaseOptimizer(config)
    await db_optimizer.initialize_pool()
    
    # Create performance indexes
    await db_optimizer.create_performance_indexes()
    
    logger.info("Database optimization initialized successfully")
    return db_optimizer


async def cleanup_database_optimization() -> None:
    """Cleanup database optimization resources"""
    global db_optimizer
    if db_optimizer:
        await db_optimizer.close_pool()
        db_optimizer = None
        logger.info("Database optimization cleaned up")


def get_db_optimizer() -> Optional[DatabaseOptimizer]:
    """Get the global database optimizer instance"""
    return db_optimizer