#!/usr/bin/env python3
"""
Comprehensive Sys Dashboard for NFL Expert Prediction System.
Provides a unified view of all system components, performance metrics, and health status.
"""

import asyncio
import logging
import sys
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import argparse

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.production_deployment import get_deployment_manager
from src.admin.system_administration import (
    get_training_monitor,
    get_memory_maintenance,
    get_performance_analyzer,
    get_health_monitor
)


class SystemStatusDashboard:
    """Comprehensive system status dashboard"""

    def __init__(self):
        self.logger = logging.getLogger("status_dashboard")
        self.last_update = None
        self.status_data = {}

    async def collect_all_status_data(self):
        """Collect comprehensive status data from all system components"""
        self.logger.info("Collecting system status data...")

        try:
            # Collect data from all components
            health_data = await self._collect_health_data()
            training_data = await self._collect_training_data()
            memory_data = await self._collect_memory_data()
            performance_data = await self._collect_performance_data()
            expert_data = await self._collect_expert_data()
            system_data = await self._collect_system_data()

            # Compile comprehensive status
            self.status_data = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": self._determine_overall_status(health_data),
                "health": health_data,
                "training": training_data,
                "memory": memory_data,
                "performance": performance_data,
                "experts": expert_data,
                "system": system_data,
                "uptime": self._calculate_uptime(),
                "summary": self._generate_summary()
            }

            self.last_update = datetime.now()

        except Exception as e:
            self.logger.error(f"Error collecting status data: {e}")
            self.status_data = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }

    async def _collect_health_data(self):
        """Collect health monitoring data"""
        try:
            health_monitor = await get_health_monitor()
            health_status = await health_monitor.get_comprehensive_health_status()

            return {
                "overall_status": health_status.overall_status,
                "database": health_status.database_health,
                "memory_system": health_status.memory_system_health,
                "expert_system": health_status.expert_system_health,
                "api": health_status.api_health,
                "alerts": health_status.alerts,
                "alert_counts": {
                    "critical": len([a for a in health_status.alerts if a["severity"] == "critical"]),
                    "warning": len([a for a in health_status.alerts if a["severity"] == "warning"]),
                    "info": len([a for a in health_status.alerts if a["severity"] == "info"])
                }
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _collect_training_data(self):
        """Collect training progress data"""
        try:
            training_monitor = await get_training_monitor()
            progress_summary = training_monitor.get_progress_summary()

            return {
                "overall_progress": progress_summary.get("overall_progress", 0),
                "total_experts": progress_summary.get("total_experts", 0),
                "total_memories": progress_summary.get("total_memories", 0),
                "experts_by_phase": progress_summary.get("experts_by_phase", {}),
                "top_experts": self._get_top_experts(progress_summary.get("experts", {})),
                "training_velocity": self._calculate_training_velocity(progress_summary)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _collect_memory_data(self):
        """Collect memory system data"""
        try:
            memory_maintenance = await get_memory_maintenance()
            memory_stats = await memory_maintenance.get_memory_statistics()

            overall = memory_stats.get("overall", {})
            storage = memory_stats.get("storage", {})

            return {
                "total_memories": overall.get("total_memories", 0),
                "active_experts": overall.get("active_experts", 0),
                "average_strength": overall.get("avg_strength", 0),
                "table_size": storage.get("table_size", "unknown"),
                "index_size": storage.get("index_size", "unknown"),
                "memory_distribution": await self._get_memory_distribution(),
                "recent_activity": await self._get_recent_memory_activity()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _collect_performance_data(self):
        """Collect performance metrics"""
        try:
            deployment_manager = await get_deployment_manager()
            metrics = await deployment_manager.collect_metrics()

            # Add response time measurements
            db_response_time = await self._measure_database_response_time()
            redis_response_time = await self._measure_redis_response_time()

            return {
                "database": {
                    **metrics.get("database", {}),
                    "response_time": db_response_time
                },
                "redis": {
                    **metrics.get("redis", {}),
                    "response_time": redis_response_time
                },
                "api_keys": metrics.get("api_keys", {}),
                "system_load": await self._get_system_load()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _collect_expert_data(self):
        """Collect expert system data"""
        try:
            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                # Expert activity summary
                expert_activity = await conn.fetch("""
                    SELECT
                        expert_id,
                        COUNT(*) as prediction_count,
                        MAX(created_at) as last_prediction,
                        AVG(confidence_level) as avg_confidence
                    FROM expert_predictions
                    WHERE created_at > NOW() - INTERVAL '7 days'
                    GROUP BY expert_id
                    ORDER BY prediction_count DESC
                    LIMIT 10
                """)

                # Recent prediction accuracy
                accuracy_data = await conn.fetch("""
                    SELECT
                        ep.expert_id,
                        COUNT(*) as total_predictions,
                        AVG(CASE WHEN ep.prediction_correct THEN 1.0 ELSE 0.0 END) as accuracy
                    FROM expert_predictions ep
                    JOIN games g ON ep.game_id = g.id
                    WHERE g.status = 'final'
                    AND ep.created_at > NOW() - INTERVAL '7 days'
                    GROUP BY ep.expert_id
                    ORDER BY accuracy DESC
                    LIMIT 10
                """)

                return {
                    "top_active_experts": [dict(row) for row in expert_activity],
                    "top_accurate_experts": [dict(row) for row in accuracy_data],
                    "expert_count": len(expert_activity),
                    "total_predictions_7d": sum(row["prediction_count"] for row in expert_activity)
                }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _collect_system_data(self):
        """Collect general system data"""
        try:
            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                # Game data
                game_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_games,
                        COUNT(CASE WHEN status = 'live' THEN 1 END) as live_games,
                        COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled_games,
                        COUNT(CASE WHEN status = 'final' THEN 1 END) as completed_games
                    FROM games
                    WHERE season = 2025
                """)

                # Recent system activity
                recent_activity = await conn.fetchrow("""
                    SELECT
                        (SELECT COUNT(*) FROM expert_predictions WHERE created_at > NOW() - INTERVAL '24 hours') as predictions_24h,
                        (SELECT COUNT(*) FROM expert_episodic_memories WHERE created_at > NOW() - INTERVAL '24 hours') as memories_24h,
                        (SELECT COUNT(*) FROM games WHERE updated_at > NOW() - INTERVAL '24 hours') as games_updated_24h
                """)

                return {
                    "games": dict(game_stats) if game_stats else {},
                    "recent_activity": dict(recent_activity) if recent_activity else {},
                    "environment": os.getenv("ENVIRONMENT", "unknown"),
                    "version": "1.0.0"  # Would come from version file
                }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _get_memory_distribution(self):
        """Get memory distribution by expert"""
        try:
            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                distribution = await conn.fetch("""
                    SELECT
                        expert_id,
                        COUNT(*) as memory_count,
                        AVG(memory_strength) as avg_strength
                    FROM expert_episodic_memories
                    GROUP BY expert_id
                    ORDER BY memory_count DESC
                    LIMIT 15
                """)

                return [dict(row) for row in distribution]

        except Exception as e:
            return []

    async def _get_recent_memory_activity(self):
        """Get recent memory activity"""
        try:
            deployment_manager = await get_deployment_manager()

            async with deployment_manager.get_db_connection() as conn:
                activity = await conn.fetchrow("""
                    SELECT
                        COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' THEN 1 END) as last_hour,
                        COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h,
                        COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as last_7d
                    FROM expert_episodic_memories
                """)

                return dict(activity) if activity else {}

        except Exception as e:
            return {}

    async def _measure_database_response_time(self):
        """Measure database response time"""
        try:
            deployment_manager = await get_deployment_manager()

            start_time = time.time()
            async with deployment_manager.get_db_connection() as conn:
                await conn.execute("SELECT 1")

            return round(time.time() - start_time, 3)

        except Exception as e:
            return -1

    async def _measure_redis_response_time(self):
        """Measure Redis response time"""
        try:
            deployment_manager = await get_deployment_manager()
            redis_client = deployment_manager.get_redis_client()

            start_time = time.time()
            redis_client.ping()

            return round(time.time() - start_time, 3)

        except Exception as e:
            return -1

    async def _get_system_load(self):
        """Get system load metrics"""
        try:
            # Would use psutil for actual system metrics
            # For now, return placeholder data
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "disk_usage_percent": 0.0
            }
        except Exception as e:
            return {}

    def _get_top_experts(self, experts_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get top performing experts"""
        if not experts_data:
            return []

        # Sort by memory count
        sorted_experts = sorted(
            experts_data.items(),
            key=lambda x: x[1].get("memories", 0),
            reverse=True
        )

        return [
            {
                "expert_id": expert_id,
                "memories": data.get("memories", 0),
                "progress": data.get("progress", 0),
                "success_rate": data.get("success_rate", 0),
                "phase": data.get("phase", "unknown")
            }
            for expert_id, data in sorted_experts[:10]
        ]

    def _calculate_training_velocity(self, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate training velocity metrics"""
        # This would require historical data to calculate actual velocity
        # For now, return placeholder
        return {
            "memories_per_hour": 0.0,
            "predictions_per_hour": 0.0,
            "estimated_completion": None
        }

    def _determine_overall_status(self, health_data: Dict[str, Any]) -> str:
        """Determine overall system status"""
        if "error" in health_data:
            return "error"

        overall_status = health_data.get("overall_status", "unknown")

        # Map health status to dashboard status
        status_mapping = {
            "healthy": "operational",
            "warning": "degraded",
            "critical": "critical",
            "error": "error"
        }

        return status_mapping.get(overall_status, "unknown")

    def _calculate_uptime(self) -> Dict[str, Any]:
        """Calculate system uptime"""
        # This would require tracking actual start time
        # For now, return placeholder
        return {
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "uptime_percentage": 99.9
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate system summary"""
        if not self.status_data:
            return {}

        return {
            "total_experts": self.status_data.get("training", {}).get("total_experts", 0),
            "total_memories": self.status_data.get("memory", {}).get("total_memories", 0),
            "active_alerts": self.status_data.get("health", {}).get("alert_counts", {}).get("critical", 0) +
                           self.status_data.get("health", {}).get("alert_counts", {}).get("warning", 0),
            "training_progress": self.status_data.get("training", {}).get("overall_progress", 0),
            "system_health": self.status_data.get("overall_status", "unknown")
        }

    def display_dashboard(self):
        """Display the status dashboard"""
        # Clear screen
        os.system('clear' if os.name == 'posix' else 'cls')

        # Header
        print("=" * 100)
        print("NFL EXPERT PREDICTION SYSTEM - COMPREHENSIVE STATUS DASHBOARD")
        print(f"Last Updated: {self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else 'Never'}")
        print("=" * 100)

        if not self.status_data or "error" in self.status_data:
            print("❌ ERROR: Unable to collect status data")
            if "error" in self.status_data:
                print(f"Error: {self.status_data['error']}")
            return

        # Overall Status
        self._display_overall_status()

        # System Health
        self._display_health_section()

        # Training Progress
        self._display_training_section()

        # Memory System
        self._display_memory_section()

        # Expert Performance
        self._display_expert_section()

        # Performance Metrics
        self._display_performance_section()

        # Recent Activity
        self._display_activity_section()

        # Footer
        print("=" * 100)
        print("System Status Dashboard - Press Ctrl+C to exit")
        print("=" * 100)

    def _display_overall_status(self):
        """Display overall system status"""
        print("\n🎯 OVERALL SYSTEM STATUS")
        print("-" * 50)

        status = self.status_data.get("overall_status", "unknown")
        status_icons = {
            "operational": "✅",
            "degraded": "⚠️",
            "critical": "❌",
            "error": "💥",
            "unknown": "❓"
        }

        icon = status_icons.get(status, "❓")
        print(f"Status: {icon} {status.upper()}")

        summary = self.status_data.get("summary", {})
        print(f"Experts: {summary.get('total_experts', 0)}")
        print(f"Memories: {summary.get('total_memories', 0):,}")
        print(f"Training Progress: {summary.get('training_progress', 0):.1f}%")
        print(f"Active Alerts: {summary.get('active_alerts', 0)}")

    def _display_health_section(self):
        """Display health status section"""
        print("\n🏥 SYSTEM HEALTH")
        print("-" * 50)

        health = self.status_data.get("health", {})

        # Component status
        components = {
            "Database": health.get("database", {}).get("status", "unknown"),
            "Memory System": health.get("memory_system", {}).get("status", "unknown"),
            "Expert System": health.get("expert_system", {}).get("status", "unknown"),
            "API Keys": health.get("api", {}).get("status", "unknown")
        }

        for component, status in components.items():
            icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
            print(f"{component}: {icon} {status}")

        # Alert summary
        alert_counts = health.get("alert_counts", {})
        if any(alert_counts.values()):
            print(f"\nAlerts: 🔴 {alert_counts.get('critical', 0)} Critical, "
                  f"🟡 {alert_counts.get('warning', 0)} Warning, "
                  f"🔵 {alert_counts.get('info', 0)} Info")

    def _display_training_section(self):
        """Display training progress section"""
        print("\n🎯 TRAINING PROGRESS")
        print("-" * 50)

        training = self.status_data.get("training", {})

        print(f"Overall Progress: {training.get('overall_progress', 0):.1f}%")
        print(f"Total Experts: {training.get('total_experts', 0)}")
        print(f"Total Memories: {training.get('total_memories', 0):,}")

        # Experts by phase
        phases = training.get("experts_by_phase", {})
        if phases:
            print("\nExperts by Phase:")
            for phase, count in phases.items():
                phase_icons = {
                    "not_started": "⏸️",
                    "in_progress": "🔄",
                    "paused": "⏸️",
                    "completed": "✅",
                    "failed": "❌"
                }
                icon = phase_icons.get(phase, "❓")
                print(f"  {icon} {phase}: {count}")

    def _display_memory_section(self):
        """Display memory system section"""
        print("\n🧠 MEMORY SYSTEM")
        print("-" * 50)

        memory = self.status_data.get("memory", {})

        print(f"Total Memories: {memory.get('total_memories', 0):,}")
        print(f"Active Experts: {memory.get('active_experts', 0)}")
        print(f"Average Strength: {memory.get('average_strength', 0):.3f}")
        print(f"Storage Size: {memory.get('table_size', 'unknown')}")

        # Recent activity
        activity = memory.get("recent_activity", {})
        if activity:
            print(f"\nRecent Activity:")
            print(f"  Last Hour: {activity.get('last_hour', 0)} memories")
            print(f"  Last 24h: {activity.get('last_24h', 0)} memories")
            print(f"  Last 7d: {activity.get('last_7d', 0)} memories")

    def _display_expert_section(self):
        """Display expert system section"""
        print("\n👥 EXPERT SYSTEM")
        print("-" * 50)

        experts = self.status_data.get("experts", {})

        print(f"Active Experts: {experts.get('expert_count', 0)}")
        print(f"Predictions (7d): {experts.get('total_predictions_7d', 0):,}")

        # Top experts
        top_experts = experts.get("top_accurate_experts", [])[:5]
        if top_experts:
            print("\nTop Accurate Experts (7d):")
            for expert in top_experts:
                accuracy = expert.get("accuracy", 0) * 100
                predictions = expert.get("total_predictions", 0)
                print(f"  {expert['expert_id']}: {accuracy:.1f}% ({predictions} predictions)")

    def _display_performance_section(self):
        """Display performance metrics section"""
        print("\n📊 PERFORMANCE")
        print("-" * 50)

        performance = self.status_data.get("performance", {})

        # Database performance
        db = performance.get("database", {})
        if db:
            response_time = db.get("response_time", -1)
            pool_size = db.get("pool_size", 0)
            pool_free = db.get("pool_free", 0)

            print(f"Database Response: {response_time:.3f}s")
            print(f"DB Pool: {pool_size} total, {pool_free} free")

        # Redis performance
        redis = performance.get("redis", {})
        if redis:
            response_time = redis.get("response_time", -1)
            memory = redis.get("used_memory", 0)

            print(f"Redis Response: {response_time:.3f}s")
            print(f"Redis Memory: {memory:,} bytes")

    def _display_activity_section(self):
        """Display recent activity section"""
        print("\n📈 RECENT ACTIVITY (24h)")
        print("-" * 50)

        system = self.status_data.get("system", {})
        activity = system.get("recent_activity", {})

        if activity:
            print(f"New Predictions: {activity.get('predictions_24h', 0):,}")
            print(f"New Memories: {activity.get('memories_24h', 0):,}")
            print(f"Games Updated: {activity.get('games_updated_24h', 0):,}")

        # Game status
        games = system.get("games", {})
        if games:
            print(f"\nGames (2025 Season):")
            print(f"  Live: {games.get('live_games', 0)}")
            print(f"  Scheduled: {games.get('scheduled_games', 0)}")
            print(f"  Completed: {games.get('completed_games', 0)}")

    def save_status_report(self, filename: Optional[str] = None):
        """Save status report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"./logs/status/status_report_{timestamp}.json"

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w") as f:
            json.dump(self.status_data, f, indent=2, default=str)

        self.logger.info(f"Status report saved to {filename}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="NFL Expert System Status Dashboard")
    parser.add_argument("--refresh", type=int, default=30, help="Refresh interval in seconds")
    parser.add_argument("--save", action="store_true", help="Save status report to file")
    parser.add_argument("--once", action="store_true", help="Run once and exit")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    dashboard = SystemStatusDashboard()

    try:
        if args.once:
            # Run once and exit
            await dashboard.collect_all_status_data()
            dashboard.display_dashboard()

            if args.save:
                dashboard.save_status_report()
        else:
            # Continuous monitoring
            while True:
                await dashboard.collect_all_status_data()
                dashboard.display_dashboard()

                if args.save:
                    dashboard.save_status_report()

                await asyncio.sleep(args.refresh)

    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
    except Exception as e:
        print(f"Dashboard error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
