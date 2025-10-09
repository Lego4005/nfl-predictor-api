#!/usr/bin/env python3
"""
System MaintenancNFL Expert Prediction System.
Provides automated maintenance tasks, database cleanup, and system optimization.
"""

import asyncio
import logging
import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import schedule
import time

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.production_deployment import get_deployment_manager
from src.admin.system_administration import (
    get_memory_maintenance,
    get_performance_analyzer,
    get_health_monitor,
    MaintenanceTaskType
)


class MaintenanceScheduler:
    """Automated maintenance task scheduler"""

    def __init__(self):
        self.logger = logging.getLogger("maintenance_scheduler")
        self.running = False
        self.maintenance_history = []

    def setup_schedule(self):
        """Setup maintenance schedule"""
        self.logger.info("Setting up maintenance schedule...")

        # Daily tasks (run at 2 AM)
        schedule.every().day.at("02:00").do(self._run_daily_maintenance)

        # Weekly tasks (run on Sunday at 3 AM)
        schedule.every().sunday.at("03:00").do(self._run_weekly_maintenance)

        # Monthly tasks (run on 1st of month at 4 AM)
        schedule.every().month.do(self._run_monthly_maintenance)

        # Hourly health checks
        schedule.every().hour.do(self._run_health_check)

        self.logger.info("Maintenance schedule configured")

    async def start_scheduler(self):
        """Start the maintenance scheduler"""
        self.logger.info("Starting maintenance scheduler...")
        self.running = True

        while self.running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute

    def stop_scheduler(self):
        """Stop the maintenance scheduler"""
        self.running = False
        self.logger.info("Maintenance scheduler stopped")

    async def _run_daily_maintenance(self):
        """Run daily maintenance tasks"""
        self.logger.info("Running daily maintenance tasks...")

        try:
            memory_maintenance = await get_memory_maintenance()

            # Memory cleanup
            cleanup_result = await memory_maintenance.run_maintenance_task(
                MaintenanceTaskType.MEMORY_CLEANUP
            )
            self.logger.info(f"Memory cleanup: {cleanup_result}")

            # Performance analysis
            perf_result = await memory_maintenance.run_maintenance_task(
                MaintenanceTaskType.PERFORMANCE_ANALYSIS
            )
            self.logger.info(f"Performance analysis: {perf_result}")

            # Log maintenance completion
            self._log_maintenance_completion("daily", True)

        except Exception as e:
            self.logger.error(f"Daily maintenance failed: {e}")
            self._log_maintenance_completion("daily", False, str(e))

    async def _run_weekly_maintenance(self):
        """Run weekly maintenance tasks"""
        self.logger.info("Running weekly maintenance tasks...")

        try:
            memory_maintenance = await get_memory_maintenance()

            # Memory archival
            archive_result = await memory_maintenance.run_maintenance_task(
                MaintenanceTaskType.MEMORY_ARCHIVAL
            )
            self.logger.info(f"Memory archival: {archive_result}")

            # Index optimization
            index_result = await memory_maintenance.run_maintenance_task(
                MaintenanceTaskType.INDEX_OPTIMIZATION
            )
            self.logger.info(f"Index optimization: {index_result}")

            # Expert performance analysis
            await self._run_expert_performance_analysis()

            # Log maintenance completion
            self._log_maintenance_completion("weekly", True)

        except Exception as e:
            self.logger.error(f"Weekly maintenance failed: {e}")
            self._log_maintenance_completion("weekly", False, str(e))

    async def _run_monthly_maintenance(self):
        """Run monthly maintenance tasks"""
        self.logger.info("Running monthly maintenance tasks...")

        try:
            # Generate comprehensive system report
            await self._generate_monthly_report()

            # Database optimization
            await self._optimize_database()

            # API key rotation check
            await self._check_api_key_rotation()

            # Log maintenance completion
            self._log_maintenance_completion("monthly", True)

        except Exception as e:
            self.logger.error(f"Monthly maintenance failed: {e}")
            self._log_maintenance_completion("monthly", False, str(e))

    async def _run_health_check(self):
        """Run hourly health check"""
        try:
            health_monitor = await get_health_monitor()
            health_status = await health_monitor.get_comprehensive_health_status()

            # Log critical alerts
            critical_alerts = [
                alert for alert in health_status.alerts
                if alert["severity"] == "critical"
            ]

            if critical_alerts:
                self.logger.error(f"CRITICAL HEALTH ALERTS: {critical_alerts}")

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")

    async def _run_expert_performance_analysis(self):
        """Run expert performance analysis"""
        try:
            performance_analyzer = await get_performance_analyzer()

            expert_ids = [
                "conservative_analyzer", "risk_taking_gambler", "contrarian_rebel",
                "value_hunter", "momentum_rider", "fundamentalist_scholar",
                "gut_instinct_expert", "statistics_purist", "trend_reversal_specialist",
                "underdog_champion", "sharp_money_follower", "popular_narrative_fader",
                "market_inefficiency_exploiter", "chaos_theory_believer", "consensus_follower"
            ]

            report = await performance_analyzer.generate_performance_report(expert_ids)

            # Save report
            os.makedirs("./logs/performance", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"./logs/performance/weekly_report_{timestamp}.json", "w") as f:
                json.dump(report, f, indent=2, default=str)

            self.logger.info("Expert performance analysis completed")

        except Exception as e:
            self.logger.error(f"Expert performance analysis failed: {e}")

    async def _generate_monthly_report(self):
        """Generate comprehensive monthly system report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "report_type": "monthly_system_report",
                "period": {
                    "start": (datetime.now() - timedelta(days=30)).isoformat(),
                    "end": datetime.now().isoformat()
                }
            }

            # System health summary
            health_monitor = await get_health_monitor()
            health_status = await health_monitor.get_comprehensive_health_status()
            report["health_summary"] = {
                "overall_status": health_status.overall_status,
                "alerts_count": len(health_status.alerts),
                "critical_alerts": len([a for a in health_status.alerts if a["severity"] == "critical"])
            }

            # Memory system statistics
            memory_maintenance = await get_memory_maintenance()
            memory_stats = await memory_maintenance.get_memory_statistics()
            report["memory_statistics"] = memory_stats

            # Performance metrics
            deployment_manager = await get_deployment_manager()
            performance_metrics = await deployment_manager.collect_metrics()
            report["performance_metrics"] = performance_metrics

            # Maintenance history
            report["maintenance_history"] = self.maintenance_history[-30:]  # Last 30 entries

            # Save report
            os.makedirs("./logs/reports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m")
            with open(f"./logs/reports/monthly_report_{timestamp}.json", "w") as f:
                json.dump(report, f, indent=2, default=str)

            self.logger.info("Monthly system report generated")

        except Exception as e:
            self.logger.error(f"Monthly report generation failed: {e}")

    async def _optimize_database(self):
        """Optimize database performance"""
        try:
            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                # Update table statistics
                await conn.execute("ANALYZE expert_episodic_memories")
                await conn.execute("ANALYZE expert_predictions")
                await conn.execute("ANALYZE games")

                # Vacuum tables
                await conn.execute("VACUUM ANALYZE expert_episodic_memories")
                await conn.execute("VACUUM ANALYZE expert_predictions")

                self.logger.info("Database optimization completed")

        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")

    async def _check_api_key_rotation(self):
        """Check and report API key rotation needs"""
        try:
            deployment_manager = await get_deployment_manager()
            api_keys = deployment_manager.api_keys

            keys_needing_rotation = []
            for service in api_keys.primary_keys:
                if api_keys.needs_rotation(service):
                    keys_needing_rotation.append(service)

            if keys_needing_rotation:
                self.logger.warning(f"API keys needing rotation: {keys_needing_rotation}")
            else:
                self.logger.info("All API keys are current")

        except Exception as e:
            self.logger.error(f"API key rotation check failed: {e}")

    def _log_maintenance_completion(self, task_type: str, success: bool, error: Optional[str] = None):
        """Log maintenance task completion"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            "success": success,
            "error": error
        }

        self.maintenance_history.append(entry)

        # Keep only last 100 entries
        if len(self.maintenance_history) > 100:
            self.maintenance_history = self.maintenance_history[-100:]


class DatabaseMaintenanceTools:
    """Database-specific maintenance tools"""

    def __init__(self):
        self.logger = logging.getLogger("db_maintenance")

    async def cleanup_old_data(self, days: int = 365):
        """Clean up old data beyond retention period"""
        self.logger.info(f"Cleaning up data older than {days} days...")

        deployment_manager = await get_deployment_manager()
        cutoff_date = datetime.now() - timedelta(days=days)

        async with deployment_manager.get_db_connection() as conn:
            # Clean up old predictions
            result = await conn.execute("""
                DELETE FROM expert_predictions
                WHERE created_at < $1
            """, cutoff_date)

            predictions_deleted = int(result.split()[-1])

            # Clean up old games (keep current season)
            current_year = datetime.now().year
            result = await conn.execute("""
                DELETE FROM games
                WHERE season < $1 AND status = 'final'
            """, current_year - 2)  # Keep last 2 seasons

            games_deleted = int(result.split()[-1])

            self.logger.info(f"Cleaned up {predictions_deleted} predictions and {games_deleted} games")

            return {
                "predictions_deleted": predictions_deleted,
                "games_deleted": games_deleted,
                "cutoff_date": cutoff_date.isoformat()
            }

    async def optimize_indexes(self):
        """Optimize database indexes"""
        self.logger.info("Optimizing database indexes...")

        deployment_manager = await get_deployment_manager()

        async with deployment_manager.get_db_connection() as conn:
            # Reindex all tables
            await conn.execute("REINDEX TABLE expert_episodic_memories")
            await conn.execute("REINDEX TABLE expert_predictions")
            await conn.execute("REINDEX TABLE games")

            # Update statistics
            await conn.execute("ANALYZE expert_episodic_memories")
            await conn.execute("ANALYZE expert_predictions")
            await conn.execute("ANALYZE games")

            self.logger.info("Database indexes optimized")

    async def backup_critical_data(self):
        """Backup critical system data"""
        self.logger.info("Backing up critical data...")

        deployment_manager = await get_deployment_manager()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        async with deployment_manager.get_db_connection() as conn:
            # Export expert configurations
            experts = await conn.fetch("SELECT * FROM expert_configurations")

            # Export recent memories
            recent_memories = await conn.fetch("""
                SELECT * FROM expert_episodic_memories
                WHERE created_at > NOW() - INTERVAL '30 days'
            """)

            # Export recent predictions
            recent_predictions = await conn.fetch("""
                SELECT * FROM expert_predictions
                WHERE created_at > NOW() - INTERVAL '30 days'
            """)

            # Save backups
            os.makedirs("./backups", exist_ok=True)

            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "experts": [dict(row) for row in experts],
                "recent_memories": [dict(row) for row in recent_memories],
                "recent_predictions": [dict(row) for row in recent_predictions]
            }

            with open(f"./backups/critical_data_{timestamp}.json", "w") as f:
                json.dump(backup_data, f, indent=2, default=str)

            self.logger.info(f"Critical data backed up to critical_data_{timestamp}.json")

            return {
                "backup_file": f"critical_data_{timestamp}.json",
                "experts_count": len(experts),
                "memories_count": len(recent_memories),
                "predictions_count": len(recent_predictions)
            }


class SystemDiagnostics:
    """System diagnostic tools"""

    def __init__(self):
        self.logger = logging.getLogger("diagnostics")

    async def run_full_diagnostics(self):
        """Run comprehensive system diagnostics"""
        self.logger.info("Running full system diagnostics...")

        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "database": await self._diagnose_database(),
            "memory_system": await self._diagnose_memory_system(),
            "expert_system": await self._diagnose_expert_system(),
            "performance": await self._diagnose_performance()
        }

        # Save diagnostics report
        os.makedirs("./logs/diagnostics", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"./logs/diagnostics/full_diagnostics_{timestamp}.json", "w") as f:
            json.dump(diagnostics, f, indent=2, default=str)

        self.logger.info("Full diagnostics completed")
        return diagnostics

    async def _diagnose_database(self):
        """Diagnose database health"""
        try:
            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                # Connection pool status
                pool_info = {
                    "pool_size": deployment_manager._db_pool.get_size(),
                    "pool_free": deployment_manager._db_pool.get_idle_size()
                }

                # Table sizes
                table_sizes = await conn.fetch("""
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)

                # Index usage
                index_usage = await conn.fetch("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_tup_read DESC
                """)

                return {
                    "status": "healthy",
                    "pool_info": pool_info,
                    "table_sizes": [dict(row) for row in table_sizes],
                    "index_usage": [dict(row) for row in index_usage]
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _diagnose_memory_system(self):
        """Diagnose memory system health"""
        try:
            memory_maintenance = await get_memory_maintenance()
            memory_stats = await memory_maintenance.get_memory_statistics()

            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                # Memory distribution by expert
                expert_distribution = await conn.fetch("""
                    SELECT
                        expert_id,
                        COUNT(*) as memory_count,
                        AVG(memory_strength) as avg_strength,
                        MAX(created_at) as last_memory
                    FROM expert_episodic_memories
                    GROUP BY expert_id
                    ORDER BY memory_count DESC
                """)

                # Memory types distribution
                type_distribution = await conn.fetch("""
                    SELECT
                        memory_type,
                        COUNT(*) as count,
                        AVG(memory_strength) as avg_strength
                    FROM expert_episodic_memories
                    GROUP BY memory_type
                    ORDER BY count DESC
                """)

                return {
                    "status": "healthy",
                    "overall_stats": memory_stats,
                    "expert_distribution": [dict(row) for row in expert_distribution],
                    "type_distribution": [dict(row) for row in type_distribution]
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _diagnose_expert_system(self):
        """Diagnose expert system health"""
        try:
            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                # Expert activity
                expert_activity = await conn.fetch("""
                    SELECT
                        expert_id,
                        COUNT(*) as prediction_count,
                        MAX(created_at) as last_prediction,
                        AVG(confidence_level) as avg_confidence
                    FROM expert_predictions
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    GROUP BY expert_id
                    ORDER BY prediction_count DESC
                """)

                # Prediction accuracy by expert
                accuracy_stats = await conn.fetch("""
                    SELECT
                        ep.expert_id,
                        COUNT(*) as total_predictions,
                        AVG(CASE WHEN ep.prediction_correct THEN 1.0 ELSE 0.0 END) as accuracy
                    FROM expert_predictions ep
                    JOIN games g ON ep.game_id = g.id
                    WHERE g.status = 'final'
                    AND ep.created_at > NOW() - INTERVAL '30 days'
                    GROUP BY ep.expert_id
                    ORDER BY accuracy DESC
                """)

                return {
                    "status": "healthy",
                    "expert_activity": [dict(row) for row in expert_activity],
                    "accuracy_stats": [dict(row) for row in accuracy_stats]
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _diagnose_performance(self):
        """Diagnose system performance"""
        try:
            deployment_manager = await get_deployment_manager()

            # Database performance
            start_time = datetime.now()
            async with deployment_manager.get_db_connection() as conn:
                await conn.execute("SELECT COUNT(*) FROM expert_episodic_memories")
            db_response_time = (datetime.now() - start_time).total_seconds()

            # Redis performance
            start_time = datetime.now()
            redis_client = deployment_manager.get_redis_client()
            redis_client.ping()
            redis_response_time = (datetime.now() - start_time).total_seconds()

            # Memory usage (would need psutil for actual system metrics)
            return {
                "status": "healthy",
                "database_response_time": db_response_time,
                "redis_response_time": redis_response_time,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


async def main():
    """Main function for maintenance tools"""
    parser = argparse.ArgumentParser(description="NFL Expert System Maintenance Tools")
    parser.add_argument("command", choices=[
        "schedule", "cleanup", "optimize", "backup", "diagnostics"
    ], help="Maintenance command to run")
    parser.add_argument("--days", type=int, default=365, help="Days for cleanup operations")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if args.command == "schedule":
        # Start maintenance scheduler
        scheduler = MaintenanceScheduler()
        scheduler.setup_schedule()
        await scheduler.start_scheduler()

    elif args.command == "cleanup":
        # Run database cleanup
        db_tools = DatabaseMaintenanceTools()
        result = await db_tools.cleanup_old_data(args.days)
        print(json.dumps(result, indent=2))

    elif args.command == "optimize":
        # Optimize database
        db_tools = DatabaseMaintenanceTools()
        await db_tools.optimize_indexes()

    elif args.command == "backup":
        # Backup critical data
        db_tools = DatabaseMaintenanceTools()
        result = await db_tools.backup_critical_data()
        print(json.dumps(result, indent=2))

    elif args.command == "diagnostics":
        # Run full diagnostics
        diagnostics = SystemDiagnostics()
        result = await diagnostics.run_full_diagnostics()
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
