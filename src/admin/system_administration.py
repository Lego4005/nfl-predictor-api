"""
System Administration and Maintenance Tools for NFLdiction System.
Provides tools for training progress monitoring, memory database maintenance,
expert performance analysis, and system health monitoring.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from contextlib import asynccontextmanager

# Import system components
from config.production_deployment import get_deployment_manager
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from src.ml.comprehensive_expert_predictions import ComprehensiveExpertPrediction


class MaintenanceTaskType(Enum):
    """Types of maintenance tasks"""
    MEMORY_CLEANUP = "memory_cleanup"
    MEMORY_ARCHIVAL = "memory_archival"
    INDEX_OPTIMIZATION = "index_optimization"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    EXPERT_CALIBRATION = "expert_calibration"
    SYSTEM_HEALTH_CHECK = "system_health_check"


class TrainingPhase(Enum):
    """Training phases"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TrainingProgress:
    """Training progress tracking"""
    expert_id: str
    phase: TrainingPhase
    total_games: int
    processed_games: int
    successful_predictions: int
    failed_predictions: int
    memories_created: int
    current_season: int
    current_week: int
    start_time: datetime
    last_update: datetime
    estimated_completion: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_games == 0:
            return 0.0
        return (self.processed_games / self.total_games) * 100

    @property
    def success_rate(self) -> float:
        """Calculate prediction success rate"""
        total_attempts = self.successful_predictions + self.failed_predictions
        if total_attempts == 0:
            return 0.0
        return (self.successful_predictions / total_attempts) * 100

    @property
    def games_per_hour(self) -> float:
        """Calculate processing rate"""
        elapsed = (self.last_update - self.start_time).total_seconds() / 3600
        if elapsed == 0:
            return 0.0
        return self.processed_games / elapsed


@dataclass
class ExpertPerformanceMetrics:
    """Expert performance analysis metrics"""
    expert_id: str
    total_predictions: int
    accuracy_by_category: Dict[str, float]
    confidence_calibration: Dict[str, float]
    memory_utilization: Dict[str, int]
    learning_trajectory: List[Dict[str, Any]]
    recent_performance: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


@dataclass
class SystemHealthMetrics:
    """System health monitoring metrics"""
    timestamp: datetime
    database_health: Dict[str, Any]
    memory_system_health: Dict[str, Any]
    expert_system_health: Dict[str, Any]
    api_health: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    overall_status: str


class TrainingProgressMonitor:
    """Training progress monitoring and control system"""

    def __init__(self):
        self.logger = logging.getLogger("training_monitor")
        self.progress_data: Dict[str, TrainingProgress] = {}
        self.monitoring_active = False

    async def start_monitoring(self, expert_ids: List[str]):
        """Start monitoring training progress for experts"""
        self.logger.info(f"Starting training progress monitoring for {len(expert_ids)} experts")

        # Initialize progress tracking for each expert
        for expert_id in expert_ids:
            self.progress_data[expert_id] = TrainingProgress(
                expert_id=expert_id,
                phase=TrainingPhase.NOT_STARTED,
                total_games=0,
                processed_games=0,
                successful_predictions=0,
                failed_predictions=0,
                memories_created=0,
                current_season=2020,
                current_week=1,
                start_time=datetime.now(),
                last_update=datetime.now()
            )

        self.monitoring_active = True

        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._update_progress_data()
                await self._check_for_issues()
                await self._save_progress_snapshot()

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _update_progress_data(self):
        """Update progress data from database"""
        deployment_manager = await get_deployment_manager()

        async with deployment_manager.get_db_connection() as conn:
            for expert_id in self.progress_data:
                try:
                    # Get training statistics
                    result = await conn.fetchrow("""
                        SELECT
                            COUNT(*) as total_memories,
                            COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' THEN 1 END) as recent_memories,
                            MAX(created_at) as last_activity
                        FROM expert_episodic_memories
                        WHERE expert_id = $1
                    """, expert_id)

                    if result:
                        progress = self.progress_data[expert_id]
                        progress.memories_created = result["total_memories"]
                        progress.last_update = result["last_activity"] or progress.last_update

                        # Update phase based on recent activity
                        if result["recent_memories"] > 0:
                            progress.phase = TrainingPhase.IN_PROGRESS
                        elif progress.memories_created > 0:
                            progress.phase = TrainingPhase.PAUSED

                except Exception as e:
                    self.logger.error(f"Error updating progress for {expert_id}: {e}")

    async def _check_for_issues(self):
        """Check for training issues and alerts"""
        for expert_id, progress in self.progress_data.items():
            # Check for stalled training
            time_since_update = datetime.now() - progress.last_update
            if time_since_update > timedelta(hours=2) and progress.phase == TrainingPhase.IN_PROGRESS:
                self.logger.warning(f"Training may be stalled for expert {expert_id}")
                progress.phase = TrainingPhase.PAUSED

            # Check error rate
            if progress.error_count > 10:
                self.logger.error(f"High error count for expert {expert_id}: {progress.error_count}")

    async def _save_progress_snapshot(self):
        """Save progress snapshot to file"""
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "experts": {
                    expert_id: asdict(progress)
                    for expert_id, progress in self.progress_data.items()
                }
            }

            os.makedirs("./logs/training", exist_ok=True)
            with open("./logs/training/progress_snapshot.json", "w") as f:
                json.dump(snapshot, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving progress snapshot: {e}")

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get training progress summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_experts": len(self.progress_data),
            "experts_by_phase": {},
            "overall_progress": 0.0,
            "total_memories": 0,
            "experts": {}
        }

        # Count experts by phase
        for progress in self.progress_data.values():
            phase = progress.phase.value
            summary["experts_by_phase"][phase] = summary["experts_by_phase"].get(phase, 0) + 1
            summary["total_memories"] += progress.memories_created
            summary["experts"][progress.expert_id] = {
                "phase": phase,
                "progress": progress.progress_percentage,
                "memories": progress.memories_created,
                "success_rate": progress.success_rate
            }

        # Calculate overall progress
        if self.progress_data:
            summary["overall_progress"] = sum(
                p.progress_percentage for p in self.progress_data.values()
            ) / len(self.progress_data)

        return summary

    async def pause_training(self, expert_id: str):
        """Pause training for specific expert"""
        if expert_id in self.progress_data:
            self.progress_data[expert_id].phase = TrainingPhase.PAUSED
            self.logger.info(f"Training paused for expert {expert_id}")

    async def resume_training(self, expert_id: str):
        """Resume training for specific expert"""
        if expert_id in self.progress_data:
            self.progress_data[expert_id].phase = TrainingPhase.IN_PROGRESS
            self.logger.info(f"Training resumed for expert {expert_id}")

    async def stop_monitoring(self):
        """Stop training progress monitoring"""
        self.monitoring_active = False
        self.logger.info("Training progress monitoring stopped")


class MemoryDatabaseMaintenance:
    """Memory database maintenance and archival tools"""

    def __init__(self):
        self.logger = logging.getLogger("memory_maintenance")
        self.memory_manager = SupabaseEpisodicMemoryManager()

    async def run_maintenance_task(self, task_type: MaintenanceTaskType) -> Dict[str, Any]:
        """Run specific maintenance task"""
        self.logger.info(f"Running maintenance task: {task_type.value}")

        start_time = datetime.now()
        result = {"task_type": task_type.value, "start_time": start_time.isoformat()}

        try:
            if task_type == MaintenanceTaskType.MEMORY_CLEANUP:
                result.update(await self._cleanup_old_memories())
            elif task_type == MaintenanceTaskType.MEMORY_ARCHIVAL:
                result.update(await self._archive_old_memories())
            elif task_type == MaintenanceTaskType.INDEX_OPTIMIZATION:
                result.update(await self._optimize_vector_indexes())
            elif task_type == MaintenanceTaskType.PERFORMANCE_ANALYSIS:
                result.update(await self._analyze_memory_performance())
            else:
                result["error"] = f"Unknown task type: {task_type.value}"

            result["success"] = True
            result["duration"] = (datetime.now() - start_time).total_seconds()

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            result["duration"] = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Maintenance task {task_type.value} failed: {e}")

        return result

    async def _cleanup_old_memories(self) -> Dict[str, Any]:
        """Clean up old, low-strength memories"""
        deployment_manager = await get_deployment_manager()

        # Define cleanup criteria
        cutoff_date = datetime.now() - timedelta(days=365)  # 1 year old
        min_strength_threshold = 0.1
        min_access_count = 2

        async with deployment_manager.get_db_connection() as conn:
            # Find memories to clean up
            memories_to_delete = await conn.fetch("""
                SELECT memory_id, expert_id, memory_strength, access_count
                FROM expert_episodic_memories
                WHERE created_at < $1
                AND memory_strength < $2
                AND access_count < $3
            """, cutoff_date, min_strength_threshold, min_access_count)

            if not memories_to_delete:
                return {"cleaned_memories": 0, "message": "No memories met cleanup criteria"}

            # Delete old memories
            memory_ids = [row["memory_id"] for row in memories_to_delete]
            await conn.execute("""
                DELETE FROM expert_episodic_memories
                WHERE memory_id = ANY($1)
            """, memory_ids)

            # Log cleanup by expert
            cleanup_by_expert = {}
            for row in memories_to_delete:
                expert_id = row["expert_id"]
                cleanup_by_expert[expert_id] = cleanup_by_expert.get(expert_id, 0) + 1

            self.logger.info(f"Cleaned up {len(memory_ids)} old memories")

            return {
                "cleaned_memories": len(memory_ids),
                "cleanup_by_expert": cleanup_by_expert,
                "criteria": {
                    "older_than_days": 365,
                    "min_strength": min_strength_threshold,
                    "min_access_count": min_access_count
                }
            }

    async def _archive_old_memories(self) -> Dict[str, Any]:
        """Archive old memories to separate table"""
        deployment_manager = await get_deployment_manager()

        # Archive memories older than 2 years
        cutoff_date = datetime.now() - timedelta(days=730)

        async with deployment_manager.get_db_connection() as conn:
            # Create archive table if not exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS expert_episodic_memories_archive (
                    LIKE expert_episodic_memories INCLUDING ALL
                )
            """)

            # Move old memories to archive
            result = await conn.execute("""
                WITH moved_memories AS (
                    DELETE FROM expert_episodic_memories
                    WHERE created_at < $1
                    RETURNING *
                )
                INSERT INTO expert_episodic_memories_archive
                SELECT * FROM moved_memories
            """, cutoff_date)

            archived_count = int(result.split()[-1])  # Extract count from result

            self.logger.info(f"Archived {archived_count} old memories")

            return {
                "archived_memories": archived_count,
                "cutoff_date": cutoff_date.isoformat()
            }

    async def _optimize_vector_indexes(self) -> Dict[str, Any]:
        """Optimize vector search indexes"""
        deployment_manager = await get_deployment_manager()

        async with deployment_manager.get_db_connection() as conn:
            # Reindex vector columns
            await conn.execute("REINDEX INDEX CONCURRENTLY expert_memories_embedding_idx")

            # Update table statistics
            await conn.execute("ANALYZE expert_episodic_memories")

            # Get index statistics
            index_stats = await conn.fetchrow("""
                SELECT
                    schemaname, tablename, indexname,
                    idx_tup_read, idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE indexname = 'expert_memories_embedding_idx'
            """)

            self.logger.info("Vector indexes optimized")

            return {
                "reindexed": True,
                "index_stats": dict(index_stats) if index_stats else None
            }

    async def _analyze_memory_performance(self) -> Dict[str, Any]:
        """Analyze memory system performance"""
        deployment_manager = await get_deployment_manager()

        async with deployment_manager.get_db_connection() as conn:
            # Memory distribution by expert
            memory_distribution = await conn.fetch("""
                SELECT
                    expert_id,
                    COUNT(*) as total_memories,
                    AVG(memory_strength) as avg_strength,
                    AVG(access_count) as avg_access_count,
                    MAX(last_accessed) as last_activity
                FROM expert_episodic_memories
                GROUP BY expert_id
                ORDER BY total_memories DESC
            """)

            # Memory types distribution
            memory_types = await conn.fetch("""
                SELECT
                    memory_type,
                    COUNT(*) as count,
                    AVG(memory_strength) as avg_strength
                FROM expert_episodic_memories
                GROUP BY memory_type
                ORDER BY count DESC
            """)

            # Recent activity
            recent_activity = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_memories,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as last_7d,
                    COUNT(CASE WHEN last_accessed > NOW() - INTERVAL '24 hours' THEN 1 END) as accessed_24h
                FROM expert_episodic_memories
            """)

            return {
                "memory_distribution": [dict(row) for row in memory_distribution],
                "memory_types": [dict(row) for row in memory_types],
                "recent_activity": dict(recent_activity) if recent_activity else {}
            }

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        deployment_manager = await get_deployment_manager()

        async with deployment_manager.get_db_connection() as conn:
            # Overall statistics
            overall_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_memories,
                    COUNT(DISTINCT expert_id) as active_experts,
                    AVG(memory_strength) as avg_strength,
                    AVG(access_count) as avg_access_count,
                    MIN(created_at) as oldest_memory,
                    MAX(created_at) as newest_memory
                FROM expert_episodic_memories
            """)

            # Storage usage
            storage_stats = await conn.fetchrow("""
                SELECT
                    pg_size_pretty(pg_total_relation_size('expert_episodic_memories')) as table_size,
                    pg_size_pretty(pg_relation_size('expert_memories_embedding_idx')) as index_size
            """)

            return {
                "overall": dict(overall_stats) if overall_stats else {},
                "storage": dict(storage_stats) if storage_stats else {},
                "timestamp": datetime.now().isoformat()
            }


class ExpertPerformanceAnalyzer:
    """Expert performance analysis and reporting system"""

    def __init__(self):
        self.logger = logging.getLogger("expert_analyzer")

    async def analyze_expert_performance(self, expert_id: str, days: int = 30) -> ExpertPerformanceMetrics:
        """Comprehensive expert performance analysis"""
        self.logger.info(f"Analyzing performance for expert {expert_id} over {days} days")

        deployment_manager = await get_deployment_manager()

        async with deployment_manager.get_db_connection() as conn:
            # Get prediction accuracy by category
            accuracy_data = await conn.fetch("""
                SELECT
                    prediction_category,
                    COUNT(*) as total_predictions,
                    AVG(CASE WHEN prediction_correct THEN 1.0 ELSE 0.0 END) as accuracy
                FROM expert_predictions ep
                JOIN games g ON ep.game_id = g.id
                WHERE ep.expert_id = $1
                AND g.game_time > NOW() - INTERVAL '%s days'
                AND g.status = 'final'
                GROUP BY prediction_category
            """, expert_id, days)

            accuracy_by_category = {
                row["prediction_category"]: row["accuracy"]
                for row in accuracy_data
            }

            # Get confidence calibration
            confidence_data = await conn.fetch("""
                SELECT
                    CASE
                        WHEN confidence_level >= 0.8 THEN 'high'
                        WHEN confidence_level >= 0.6 THEN 'medium'
                        ELSE 'low'
                    END as confidence_bucket,
                    AVG(CASE WHEN prediction_correct THEN 1.0 ELSE 0.0 END) as actual_accuracy,
                    AVG(confidence_level) as avg_confidence
                FROM expert_predictions ep
                JOIN games g ON ep.game_id = g.id
                WHERE ep.expert_id = $1
                AND g.game_time > NOW() - INTERVAL '%s days'
                AND g.status = 'final'
                GROUP BY confidence_bucket
            """, expert_id, days)

            confidence_calibration = {
                row["confidence_bucket"]: {
                    "actual_accuracy": row["actual_accuracy"],
                    "avg_confidence": row["avg_confidence"]
                }
                for row in confidence_data
            }

            # Get memory utilization
            memory_data = await conn.fetch("""
                SELECT
                    memory_type,
                    COUNT(*) as count,
                    AVG(access_count) as avg_access_count
                FROM expert_episodic_memories
                WHERE expert_id = $1
                GROUP BY memory_type
            """, expert_id)

            memory_utilization = {
                row["memory_type"]: {
                    "count": row["count"],
                    "avg_access": row["avg_access_count"]
                }
                for row in memory_data
            }

            # Calculate total predictions
            total_predictions = sum(row["total_predictions"] for row in accuracy_data)

            # Generate insights
            strengths, weaknesses, recommendations = self._generate_insights(
                accuracy_by_category, confidence_calibration, memory_utilization
            )

            return ExpertPerformanceMetrics(
                expert_id=expert_id,
                total_predictions=total_predictions,
                accuracy_by_category=accuracy_by_category,
                confidence_calibration=confidence_calibration,
                memory_utilization=memory_utilization,
                learning_trajectory=[],  # Would need historical data
                recent_performance={},   # Would need recent comparison
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations
            )

    def _generate_insights(self, accuracy: Dict, confidence: Dict, memory: Dict) -> Tuple[List[str], List[str], List[str]]:
        """Generate performance insights"""
        strengths = []
        weaknesses = []
        recommendations = []

        # Analyze accuracy
        if accuracy:
            best_category = max(accuracy.items(), key=lambda x: x[1])
            worst_category = min(accuracy.items(), key=lambda x: x[1])

            if best_category[1] > 0.6:
                strengths.append(f"Strong performance in {best_category[0]} ({best_category[1]:.1%} accuracy)")

            if worst_category[1] < 0.4:
                weaknesses.append(f"Poor performance in {worst_category[0]} ({worst_category[1]:.1%} accuracy)")
                recommendations.append(f"Focus training on {worst_category[0]} predictions")

        # Analyze confidence calibration
        for bucket, data in confidence.items():
            confidence_gap = abs(data["actual_accuracy"] - data["avg_confidence"])
            if confidence_gap > 0.2:
                if data["actual_accuracy"] < data["avg_confidence"]:
                    weaknesses.append(f"Overconfident in {bucket} confidence predictions")
                    recommendations.append(f"Calibrate {bucket} confidence predictions downward")
                else:
                    strengths.append(f"Conservative {bucket} confidence predictions")

        # Analyze memory utilization
        if memory:
            total_memories = sum(data["count"] for data in memory.values())
            if total_memories < 100:
                recommendations.append("Increase memory accumulation through more training")

            # Check for balanced memory types
            memory_types = len(memory)
            if memory_types < 3:
                recommendations.append("Diversify memory types for better pattern recognition")

        return strengths, weaknesses, recommendations

    async def generate_performance_report(self, expert_ids: List[str]) -> Dict[str, Any]:
        """Generate comprehensive performance report for multiple experts"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "experts": {},
            "summary": {
                "total_experts": len(expert_ids),
                "avg_accuracy": 0.0,
                "top_performers": [],
                "needs_attention": []
            }
        }

        expert_accuracies = []

        for expert_id in expert_ids:
            try:
                metrics = await self.analyze_expert_performance(expert_id)
                report["experts"][expert_id] = asdict(metrics)

                # Calculate overall accuracy
                if metrics.accuracy_by_category:
                    overall_accuracy = np.mean(list(metrics.accuracy_by_category.values()))
                    expert_accuracies.append((expert_id, overall_accuracy))

            except Exception as e:
                self.logger.error(f"Error analyzing expert {expert_id}: {e}")
                report["experts"][expert_id] = {"error": str(e)}

        # Generate summary
        if expert_accuracies:
            report["summary"]["avg_accuracy"] = np.mean([acc for _, acc in expert_accuracies])

            # Sort by accuracy
            expert_accuracies.sort(key=lambda x: x[1], reverse=True)

            # Top performers (top 25%)
            top_count = max(1, len(expert_accuracies) // 4)
            report["summary"]["top_performers"] = [
                {"expert_id": expert_id, "accuracy": accuracy}
                for expert_id, accuracy in expert_accuracies[:top_count]
            ]

            # Needs attention (bottom 25%)
            bottom_count = max(1, len(expert_accuracies) // 4)
            report["summary"]["needs_attention"] = [
                {"expert_id": expert_id, "accuracy": accuracy}
                for expert_id, accuracy in expert_accuracies[-bottom_count:]
            ]

        return report


class SystemHealthMonitor:
    """System health monitoring and diagnostic capabilities"""

    def __init__(self):
        self.logger = logging.getLogger("health_monitor")

    async def get_comprehensive_health_status(self) -> SystemHealthMetrics:
        """Get comprehensive system health status"""
        timestamp = datetime.now()

        # Get component health
        database_health = await self._check_database_health()
        memory_health = await self._check_memory_system_health()
        expert_health = await self._check_expert_system_health()
        api_health = await self._check_api_health()
        performance_metrics = await self._collect_performance_metrics()

        # Generate alerts
        alerts = self._generate_health_alerts(
            database_health, memory_health, expert_health, api_health, performance_metrics
        )

        # Determine overall status
        overall_status = self._determine_overall_status(alerts)

        return SystemHealthMetrics(
            timestamp=timestamp,
            database_health=database_health,
            memory_system_health=memory_health,
            expert_system_health=expert_health,
            api_health=api_health,
            performance_metrics=performance_metrics,
            alerts=alerts,
            overall_status=overall_status
        )

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                # Connection test
                await conn.execute("SELECT 1")

                # Get database statistics
                stats = await conn.fetchrow("""
                    SELECT
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections,
                        (SELECT count(*) FROM expert_episodic_memories) as total_memories,
                        (SELECT count(*) FROM games WHERE status = 'live') as live_games
                """)

                return {
                    "status": "healthy",
                    "active_connections": stats["active_connections"],
                    "max_connections": stats["max_connections"],
                    "connection_usage": stats["active_connections"] / stats["max_connections"],
                    "total_memories": stats["total_memories"],
                    "live_games": stats["live_games"]
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def _check_memory_system_health(self) -> Dict[str, Any]:
        """Check memory system health"""
        try:
            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                # Memory system statistics
                stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_memories,
                        COUNT(CASE WHEN embedding_status = 'completed' THEN 1 END) as embedded_memories,
                        COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_memories,
                        AVG(memory_strength) as avg_strength
                    FROM expert_episodic_memories
                """)

                embedding_rate = 0.0
                if stats["total_memories"] > 0:
                    embedding_rate = stats["embedded_memories"] / stats["total_memories"]

                return {
                    "status": "healthy" if embedding_rate > 0.8 else "degraded",
                    "total_memories": stats["total_memories"],
                    "embedding_completion_rate": embedding_rate,
                    "recent_activity": stats["recent_memories"],
                    "avg_memory_strength": float(stats["avg_strength"] or 0)
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def _check_expert_system_health(self) -> Dict[str, Any]:
        """Check expert system health"""
        try:
            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                # Expert activity statistics
                stats = await conn.fetchrow("""
                    SELECT
                        COUNT(DISTINCT expert_id) as active_experts,
                        COUNT(*) as total_predictions,
                        COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_predictions
                    FROM expert_predictions
                    WHERE created_at > NOW() - INTERVAL '7 days'
                """)

                return {
                    "status": "healthy" if stats["active_experts"] >= 10 else "degraded",
                    "active_experts": stats["active_experts"],
                    "total_predictions_7d": stats["total_predictions"],
                    "recent_predictions_24h": stats["recent_predictions"]
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def _check_api_health(self) -> Dict[str, Any]:
        """Check API health"""
        deployment_manager = await get_deployment_manager()
        api_keys = deployment_manager.api_keys

        key_status = {}
        for service, key in api_keys.primary_keys.items():
            key_status[service] = {
                "configured": bool(key),
                "needs_rotation": api_keys.needs_rotation(service),
                "has_backup": bool(api_keys.backup_keys.get(service))
            }

        healthy_keys = sum(1 for status in key_status.values() if status["configured"])
        total_keys = len(key_status)

        return {
            "status": "healthy" if healthy_keys >= total_keys * 0.8 else "degraded",
            "configured_keys": healthy_keys,
            "total_keys": total_keys,
            "key_status": key_status
        }

    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        try:
            deployment_manager = await get_deployment_manager()

            # Get Redis metrics
            redis_client = deployment_manager.get_redis_client()
            redis_info = redis_client.info()

            return {
                "redis": {
                    "used_memory": redis_info.get("used_memory", 0),
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0)
                },
                "system": {
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            return {
                "error": str(e)
            }

    def _generate_health_alerts(self, database: Dict, memory: Dict, expert: Dict, api: Dict, performance: Dict) -> List[Dict[str, Any]]:
        """Generate health alerts based on metrics"""
        alerts = []

        # Database alerts
        if database.get("status") == "unhealthy":
            alerts.append({
                "severity": "critical",
                "component": "database",
                "message": f"Database connection failed: {database.get('error', 'Unknown error')}"
            })
        elif database.get("connection_usage", 0) > 0.9:
            alerts.append({
                "severity": "warning",
                "component": "database",
                "message": f"High database connection usage: {database['connection_usage']:.1%}"
            })

        # Memory system alerts
        if memory.get("status") == "unhealthy":
            alerts.append({
                "severity": "critical",
                "component": "memory",
                "message": f"Memory system failed: {memory.get('error', 'Unknown error')}"
            })
        elif memory.get("embedding_completion_rate", 0) < 0.8:
            alerts.append({
                "severity": "warning",
                "component": "memory",
                "message": f"Low embedding completion rate: {memory['embedding_completion_rate']:.1%}"
            })

        # Expert system alerts
        if expert.get("status") == "unhealthy":
            alerts.append({
                "severity": "critical",
                "component": "expert_system",
                "message": f"Expert system failed: {expert.get('error', 'Unknown error')}"
            })
        elif expert.get("active_experts", 0) < 10:
            alerts.append({
                "severity": "warning",
                "component": "expert_system",
                "message": f"Low expert activity: {expert['active_experts']} active experts"
            })

        # API alerts
        if api.get("status") == "degraded":
            alerts.append({
                "severity": "warning",
                "component": "api",
                "message": f"API key issues: {api['configured_keys']}/{api['total_keys']} keys configured"
            })

        return alerts

    def _determine_overall_status(self, alerts: List[Dict[str, Any]]) -> str:
        """Determine overall system status"""
        if any(alert["severity"] == "critical" for alert in alerts):
            return "critical"
        elif any(alert["severity"] == "warning" for alert in alerts):
            return "warning"
        else:
            return "healthy"


# Global instances
training_monitor = TrainingProgressMonitor()
memory_maintenance = MemoryDatabaseMaintenance()
performance_analyzer = ExpertPerformanceAnalyzer()
health_monitor = SystemHealthMonitor()


async def get_training_monitor() -> TrainingProgressMonitor:
    """Get training progress monitor instance"""
    return training_monitor


async def get_memory_maintenance() -> MemoryDatabaseMaintenance:
    """Get memory maintenance instance"""
    return memory_maintenance


async def get_performance_analyzer() -> ExpertPerformanceAnalyzer:
    """Get performance analyzer instance"""
    return performance_analyzer


async def get_health_monitor() -> SystemHealthMonitor:
    """Get health monitor instance"""
    return health_monitor
