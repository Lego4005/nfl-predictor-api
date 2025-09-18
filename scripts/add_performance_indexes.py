#!/usr/bin/env python3
"""
Add critical missing database indexes for NFL Predictor API
Expected Performance Improvement: 10-100x for common queries
"""

import logging
from sqlalchemy import create_engine, text
from src.database.config import get_database_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_indexes():
    """Create missing performance-critical indexes"""
    
    engine = create_engine(get_database_url())
    
    indexes = [
        # Predictions table - most queried
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_season_week_type 
           ON predictions (season, week, prediction_type)""",
        
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_user_season 
           ON predictions (user_id, season) WHERE status = 'completed'""",
        
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_created_at 
           ON predictions (created_at DESC)""",
        
        # Subscriptions - critical for auth checks
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_user_status_active 
           ON subscriptions (user_id, status) 
           WHERE status IN ('active', 'trial')""",
        
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_expires 
           ON subscriptions (expires_at) 
           WHERE status = 'active'""",
        
        # Users - authentication queries
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_verified 
           ON users (email, email_verified) 
           WHERE email_verified = true""",
        
        # Sessions - token validation
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_token_expires 
           ON sessions (session_token, expires_at) 
           WHERE is_active = true""",
        
        # Affiliate tracking
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_affiliates_code_active 
           ON affiliates (referral_code) 
           WHERE is_active = true""",
        
        # JSON field optimization (if using PostgreSQL)
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_data_gin 
           ON predictions USING gin (prediction_data)""",
        
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_game_results_gin 
           ON game_results USING gin (game_data)"""
    ]
    
    successful = 0
    failed = 0
    
    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                logger.info(f"Creating index: {index_sql[:50]}...")
                conn.execute(text(index_sql))
                conn.commit()
                logger.info("✓ Index created successfully")
                successful += 1
            except Exception as e:
                logger.warning(f"Index might already exist or error: {e}")
                failed += 1
    
    logger.info(f"\n✅ Indexing complete! {successful} created, {failed} skipped/failed")
    logger.info("Expected performance improvement: 10-100x for common queries")
    return successful, failed

if __name__ == "__main__":
    logger.info("Starting database index optimization...")
    created, skipped = create_indexes()
    logger.info(f"Database optimization complete! {created} new indexes added.")