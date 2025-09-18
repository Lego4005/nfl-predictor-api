#!/usr/bin/env python3
"""
Improved database indexing script for NFL Predictor API
Addresses security, performance, and error handling concerns

Expected Performance Improvement: 10-100x for common queries
Security: Input validation, proper error handling, privilege checking
"""

import logging
import re
import sys
from typing import List, Tuple, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, OperationalError
from src.database.config import db_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IndexCreationError(Exception):
    """Custom exception for index creation failures"""
    pass

class DatabaseIndexManager:
    """Secure database index management"""
    
    def __init__(self):
        self.engine = db_config.engine
        self.valid_tables = {
            'users', 'user_sessions', 'subscriptions', 'subscription_tiers',
            'predictions', 'affiliates', 'referrals', 'free_access_grants',
            'admin_users', 'payments', 'audit_logs', 'game_results'
        }
    
    def validate_table_name(self, table_name: str) -> bool:
        """Validate table name against known schema"""
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            return False
        return table_name in self.valid_tables
    
    def validate_index_name(self, index_name: str) -> bool:
        """Validate index name follows conventions"""
        if not re.match(r'^idx_[a-zA-Z0-9_]+$', index_name):
            return False
        return len(index_name) <= 63  # PostgreSQL limit
    
    def check_privileges(self) -> bool:
        """Check if current user has index creation privileges"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT has_database_privilege(current_user, current_database(), 'CREATE')"
                ))
                return result.scalar()
        except Exception as e:
            logger.error(f"Failed to check privileges: {e}")
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """Verify table exists in database"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = :table_name 
                        AND table_schema = 'public'
                    )
                """), {"table_name": table_name})
                return result.scalar()
        except Exception as e:
            logger.error(f"Failed to check table existence: {e}")
            return False
    
    def index_exists(self, index_name: str) -> bool:
        """Check if index already exists"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = :index_name
                    )
                """), {"index_name": index_name})
                return result.scalar()
        except Exception as e:
            logger.error(f"Failed to check index existence: {e}")
            return False
    
    def estimate_table_size(self, table_name: str) -> str:
        """Estimate table size for index planning"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT pg_size_pretty(pg_total_relation_size(:table_name))
                """), {"table_name": table_name})
                return result.scalar() or "Unknown"
        except Exception:
            return "Unknown"
    
    def create_single_index(self, index_definition: Dict[str, Any]) -> bool:
        """
        Create a single index with comprehensive error handling
        
        Args:
            index_definition: Dict with 'name', 'table', 'sql', 'description'
        
        Returns:
            bool: True if created successfully, False if skipped
        
        Raises:
            IndexCreationError: If creation fails
        """
        index_name = index_definition['name']
        table_name = index_definition['table']
        sql = index_definition['sql']
        description = index_definition.get('description', '')
        
        # Validation checks
        if not self.validate_index_name(index_name):
            raise IndexCreationError(f"Invalid index name: {index_name}")
        
        if not self.validate_table_name(table_name):
            raise IndexCreationError(f"Invalid or unknown table: {table_name}")
        
        # Check if table exists
        if not self.table_exists(table_name):
            logger.warning(f"Table {table_name} does not exist, skipping index {index_name}")
            return False
        
        # Check if index already exists
        if self.index_exists(index_name):
            logger.info(f"Index {index_name} already exists, skipping")
            return False
        
        # Log table size for monitoring
        table_size = self.estimate_table_size(table_name)
        logger.info(f"Creating index {index_name} on table {table_name} (size: {table_size})")
        if description:
            logger.info(f"Purpose: {description}")
        
        try:
            # Note: CONCURRENTLY cannot be used in transactions
            with self.engine.connect() as conn:
                # Set statement timeout for large indexes
                conn.execute(text("SET statement_timeout = '1h'"))
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"✅ Successfully created index: {index_name}")
                return True
                
        except ProgrammingError as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg:
                logger.info(f"Index {index_name} already exists (race condition), skipping")
                return False
            elif "does not exist" in error_msg:
                logger.error(f"Table or column referenced in {index_name} does not exist: {e}")
                raise IndexCreationError(f"Schema error for index {index_name}: {e}")
            else:
                logger.error(f"SQL error creating index {index_name}: {e}")
                raise IndexCreationError(f"SQL error for index {index_name}: {e}")
                
        except OperationalError as e:
            if "timeout" in str(e).lower():
                logger.error(f"Timeout creating index {index_name} - consider creating during maintenance window")
                raise IndexCreationError(f"Timeout creating index {index_name}")
            else:
                logger.error(f"Database operational error creating index {index_name}: {e}")
                raise IndexCreationError(f"Operational error for index {index_name}: {e}")
                
        except Exception as e:
            logger.error(f"Unexpected error creating index {index_name}: {e}")
            raise IndexCreationError(f"Unexpected error for index {index_name}: {e}")
    
    def get_index_definitions(self) -> List[Dict[str, Any]]:
        """Get all index definitions with metadata"""
        return [
            {
                'name': 'idx_predictions_season_week_type',
                'table': 'predictions',
                'sql': """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_season_week_type 
                         ON predictions (season, week, prediction_type)""",
                'description': 'Primary query pattern for predictions by season/week/type'
            },
            {
                'name': 'idx_predictions_user_season_active',
                'table': 'predictions', 
                'sql': """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_user_season_active
                         ON predictions (user_id, season) WHERE status = 'completed'""",
                'description': 'User prediction history queries'
            },
            {
                'name': 'idx_predictions_created_desc',
                'table': 'predictions',
                'sql': """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_created_desc
                         ON predictions (created_at DESC)""",
                'description': 'Recent predictions ordering'
            },
            {
                'name': 'idx_subs_user_status_active',
                'table': 'subscriptions',
                'sql': """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subs_user_status_active
                         ON subscriptions (user_id, status) 
                         WHERE status IN ('active', 'trial')""",
                'description': 'Critical auth checks for active subscriptions'
            },
            {
                'name': 'idx_subs_expires_active',
                'table': 'subscriptions',
                'sql': """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subs_expires_active
                         ON subscriptions (expires_at) 
                         WHERE status = 'active'""",
                'description': 'Subscription expiration monitoring'
            },
            {
                'name': 'idx_users_email_verified',
                'table': 'users',
                'sql': """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_verified
                         ON users (email, email_verified) 
                         WHERE email_verified = true""",
                'description': 'Authentication login queries'
            },
            {
                'name': 'idx_sessions_token_expires',
                'table': 'user_sessions',
                'sql': """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_token_expires
                         ON user_sessions (token_hash, expires_at) 
                         WHERE is_active = true""",
                'description': 'Session token validation'
            },
            {
                'name': 'idx_affiliates_code_active',
                'table': 'affiliates',
                'sql': """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_affiliates_code_active
                         ON affiliates (referral_code) 
                         WHERE is_active = true""",
                'description': 'Affiliate code lookups'
            },
            {
                'name': 'idx_predictions_data_gin',
                'table': 'predictions',
                'sql': """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_data_gin
                         ON predictions USING gin (prediction_data)""",
                'description': 'JSON field search optimization'
            }
        ]
    
    def create_all_indexes(self) -> Tuple[int, int, List[str]]:
        """
        Create all performance indexes
        
        Returns:
            Tuple of (successful_count, failed_count, error_messages)
        """
        if not self.check_privileges():
            raise IndexCreationError("Insufficient database privileges to create indexes")
        
        indexes = self.get_index_definitions()
        successful = 0
        failed = 0
        errors = []
        
        logger.info(f"Starting creation of {len(indexes)} performance indexes...")
        
        for index_def in indexes:
            try:
                if self.create_single_index(index_def):
                    successful += 1
                else:
                    # Skipped (already exists or table missing)
                    pass
            except IndexCreationError as e:
                logger.error(f"Failed to create index {index_def['name']}: {e}")
                errors.append(str(e))
                failed += 1
            except Exception as e:
                logger.error(f"Unexpected error with index {index_def['name']}: {e}")
                errors.append(f"Unexpected error: {e}")
                failed += 1
        
        return successful, failed, errors
    
    def generate_usage_report(self) -> str:
        """Generate index usage report"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_tup_read,
                        idx_tup_fetch,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                    FROM pg_stat_user_indexes 
                    WHERE indexname LIKE 'idx_%'
                    ORDER BY idx_tup_read DESC
                    LIMIT 20;
                """))
                
                rows = result.fetchall()
                if not rows:
                    return "No index usage statistics available"
                
                report = "\n📊 Index Usage Report (Top 20):\n"
                report += "-" * 80 + "\n"
                report += f"{'Index Name':<30} {'Table':<15} {'Reads':<10} {'Size':<10}\n"
                report += "-" * 80 + "\n"
                
                for row in rows:
                    report += f"{row.indexname:<30} {row.tablename:<15} {row.idx_tup_read:<10} {row.index_size:<10}\n"
                
                return report
                
        except Exception as e:
            return f"Error generating usage report: {e}"

def main():
    """Main execution function"""
    try:
        manager = DatabaseIndexManager()
        
        logger.info("🚀 Starting database index optimization...")
        logger.info("This process uses CONCURRENTLY to avoid blocking production traffic")
        
        successful, failed, errors = manager.create_all_indexes()
        
        # Results summary
        logger.info("\n" + "="*60)
        logger.info("📈 DATABASE INDEX OPTIMIZATION COMPLETE")
        logger.info("="*60)
        logger.info(f"✅ Successfully created: {successful} indexes")
        logger.info(f"❌ Failed/Skipped: {failed} indexes")
        
        if errors:
            logger.error("\n🚨 Errors encountered:")
            for error in errors:
                logger.error(f"   • {error}")
        
        logger.info(f"\n🎯 Expected performance improvement: 10-100x for common queries")
        
        # Generate usage report if any indexes were created
        if successful > 0:
            logger.info("\n⏳ Index usage statistics will be available after some query activity...")
            # Optionally print current stats
            usage_report = manager.generate_usage_report()
            logger.info(usage_report)
        
        return 0 if failed == 0 else 1
        
    except IndexCreationError as e:
        logger.error(f"🚨 Index creation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"🚨 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)