#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard for NFL Expert Prediction Sys.
Provides live monitoring of system health, training progress, and performance metrics.
"""

import asyncio
import logging
import sys
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path
import argparse

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.production_deployment import get_deployment_manager
from src.admin.system_administration import (
    get_training_monitor,
    get_memory_maintenance,
    get_performance_analyzer,
    get_health_monitor,
    MaintenanceTaskType
)


class MonitoringDashboard:
    """Real-time monitoring dashboard"""

    def __init__(self, refresh_interval: int = 30):
        self.logger = logging.getLogger("dashboard")
        self.refresh_interval = refresh_interval
        self.running = False

        # Dashboard data
        self.health_data = {}
        self.training_data = {}
        self.performance_data = {}
        self.memory_data = {}

    async def start(self):
        """Start the monitoring dashboard"""
        self.logger.info("Starting monitoring dashboard...")
        self.running = True

        try:
            while self.running:
                # Collect all monitoring data
                await self._collect_data()

                # Display dashboard
                self._display_dashboard()

                # Wait for next refresh
                await asyncio.sleep(self.refresh_interval)

        except KeyboardInterrupt:
            self.logger.info("Dashboard stopped by user")
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")
        finally:
            self.running = False

    async def _collect_data(self):
        """Collect all monitoring data"""
        try:
            # Get health monitor
            health_monitor = await get_health_monitor()
            self.health_data = await health_monitor.get_comprehensive_health_status()

            # Get training monitor
            training_monitor = await get_training_monitor()
            self.training_data = training_monitor.get_progress_summary()

            # Get memory statistics
            memory_maintenance = await get_memory_maintenance()
            self.memory_data = await memory_maintenance.get_memory_statistics()

            # Get deployment manager metrics
            deployment_manager = await get_deployment_manager()
            self.performance_data = await deployment_manager.collect_metrics()

        except Exception as e:
            self.logger.error(f"Error collecting data: {e}")

    def _display_dashboard(self):
        """Display the monitoring dashboard"""
        # Clear screen
        os.system('clear' if os.name == 'posix' else 'cls')

        # Header
        print("=" * 80)
        print("NFL EXPERT PREDICTION SYSTEM - MONITORING DASHBOARD")
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # System Health Section
        self._display_health_section()

        # Training Progress Section
        self._display_training_section()

        # Memory System Section
        self._display_memory_section()

        # Performance Section
        self._display_performance_section()

        # Footer
        print("=" * 80)
        print("Press Ctrl+C to exit")
        print("=" * 80)

    def _display_health_section(self):
        """Display system health section"""
        print("\n🏥 SYSTEM HEALTH")
        print("-" * 40)

        if not self.health_data:
            print("❌ Health data unavailable")
            return

        # Overall status
        status = self.health_data.overall_status
        status_icon = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
        print(f"Overall Status: {status_icon} {status.upper()}")

        # Component status
        components = self.health_data.__dict__ if hasattr(self.health_data, '__dict__') else {}

        if hasattr(self.health_data, 'database_health'):
            db_status = self.health_data.database_health.get("status", "unknown")
            db_icon = "✅" if db_status == "healthy" else "❌"
            print(f"Database: {db_icon} {db_status}")

            if "active_connections" in self.health_data.database_health:
                conn_usage = self.health_data.database_health.get("connection_usage", 0)
                print(f"  Connections: {conn_usage:.1%} usage")

        if hasattr(self.health_data, 'memory_system_health'):
            mem_status = self.health_data.memory_system_health.get("status", "unknown")
            mem_icon = "✅" if mem_status == "healthy" else "❌"
            print(f"Memory System: {mem_icon} {mem_status}")

            if "total_memories" in self.health_data.memory_system_health:
                total_mem = self.health_data.memory_system_health.get("total_memories", 0)
                print(f"  Total Memories: {total_mem:,}")

        if hasattr(self.health_data, 'expert_system_health'):
            expert_status = self.health_data.expert_system_health.get("status", "unknown")
            expert_icon = "✅" if expert_status == "healthy" else "❌"
            print(f"Expert System: {expert_icon} {expert_status}")

            if "active_experts" in self.health_data.expert_system_health:
                active_experts = self.health_data.expert_system_health.get("active_experts", 0)
                print(f"  Active Experts: {active_experts}")

        # Alerts
        if hasattr(self.health_data, 'alerts') and self.health_data.alerts:
            print("\n🚨 ALERTS:")
            for alert in self.health_data.alerts[:5]:  # Show top 5 alerts
                severity_icon = "🔴" if alert["severity"] == "critical" else "🟡"
                print(f"  {severity_icon} {alert['component']}: {alert['message']}")

    def _display_training_section(self):
        """Display training progress section"""
        print("\n🎯 TRAINING PROGRESS")
        print("-" * 40)

        if not self.training_data:
            print("❌ Training data unavailable")
            return

        # Overall progress
        overall_progress = self.training_data.get("overall_progress", 0)
        total_experts = self.training_data.get("total_experts", 0)
        total_memories = self.training_data.get("total_memories", 0)

        print(f"Overall Progress: {overall_progress:.1f}%")
        print(f"Total Experts: {total_experts}")
        print(f"Total Memories: {total_memories:,}")

        # Experts by phase
        experts_by_phase = self.training_data.get("experts_by_phase", {})
        if experts_by_phase:
            print("\nExperts by Phase:")
            for phase, count in experts_by_phase.items():
                phase_icon = self._get_phase_icon(phase)
                print(f"  {phase_icon} {phase}: {count}")

        # Top performing experts
        experts = self.training_data.get("experts", {})
        if experts:
            print("\nTop Experts (by memories):")
            sorted_experts = sorted(
                experts.items(),
                key=lambda x: x[1].get("memories", 0),
                reverse=True
            )[:5]

            for expert_id, data in sorted_experts:
                memories = data.get("memories", 0)
                progress = data.get("progress", 0)
                success_rate = data.get("success_rate", 0)
                print(f"  {expert_id}: {memories:,} memories, {progress:.1f}% progress, {success_rate:.1f}% success")

    def _display_memory_section(self):
        """Display memory system section"""
        print("\n🧠 MEMORY SYSTEM")
        print("-" * 40)

        if not self.memory_data:
            print("❌ Memory data unavailable")
            return

        overall = self.memory_data.get("overall", {})
        storage = self.memory_data.get("storage", {})

        if overall:
            total_memories = overall.get("total_memories", 0)
            active_experts = overall.get("active_experts", 0)
            avg_strength = overall.get("avg_strength", 0)

            print(f"Total Memories: {total_memories:,}")
            print(f"Active Experts: {active_experts}")
            print(f"Avg Memory Strength: {avg_strength:.3f}")

            if "oldest_memory" in overall and overall["oldest_memory"]:
                oldest = overall["oldest_memory"]
                if isinstance(oldest, str):
                    oldest_date = datetime.fromisoformat(oldest.replace('Z', '+00:00'))
                    days_old = (datetime.now() - oldest_date.replace(tzinfo=None)).days
                    print(f"Oldest Memory: {days_old} days ago")

        if storage:
            table_size = storage.get("table_size", "Unknown")
            index_size = storage.get("index_size", "Unknown")
            print(f"Table Size: {table_size}")
            print(f"Index Size: {index_size}")

    def _display_performance_section(self):
        """Display performance metrics section"""
        print("\n📊 PERFORMANCE METRICS")
        print("-" * 40)

        if not self.performance_data:
            print("❌ Performance data unavailable")
            return

        # Database metrics
        database = self.performance_data.get("database", {})
        if database and "error" not in database:
            pool_size = database.get("pool_size", 0)
            pool_free = database.get("pool_free", 0)
            active_connections = database.get("active_connections", 0)

            print(f"DB Pool: {pool_size} total, {pool_free} free")
            print(f"Active Connections: {active_connections}")

            if "avg_query_time" in database and database["avg_query_time"]:
                avg_query_time = database["avg_query_time"]
                print(f"Avg Query Time: {avg_query_time:.3f}s")

        # Redis metrics
        redis = self.performance_data.get("redis", {})
        if redis and "error" not in redis:
            used_memory = redis.get("used_memory", 0)
            connected_clients = redis.get("connected_clients", 0)
            keyspace_hits = redis.get("keyspace_hits", 0)
            keyspace_misses = redis.get("keyspace_misses", 0)

            print(f"Redis Memory: {used_memory:,} bytes")
            print(f"Redis Clients: {connected_clients}")

            if keyspace_hits + keyspace_misses > 0:
                hit_rate = keyspace_hits / (keyspace_hits + keyspace_misses)
                print(f"Cache Hit Rate: {hit_rate:.1%}")

        # API key status
        api_keys = self.performance_data.get("api_keys", {})
        if api_keys:
            keys_needing_rotation = sum(
                1 for data in api_keys.values()
                if data.get("needs_rotation", False)
            )
            if keys_needing_rotation > 0:
                print(f"⚠️ API Keys Needing Rotation: {keys_needing_rotation}")

    def _get_phase_icon(self, phase: str) -> str:
        """Get icon for training phase"""
        icons = {
            "not_started": "⏸️",
            "in_progress": "🔄",
            "paused": "⏸️",
            "completed": "✅",
            "failed": "❌"
        }
        return icons.get(phase, "❓")


class SystemAdminCLI:
    """Command-line interface for system administration"""

    def __init__(self):
        self.logger = logging.getLogger("admin_cli")

    async def run_command(self, command: str, args: List[str]):
        """Run administrative command"""
        if command == "dashboard":
            await self._run_dashboard(args)
        elif command == "health":
            await self._check_health(args)
        elif command == "training":
            await self._manage_training(args)
        elif command == "maintenance":
            await self._run_maintenance(args)
        elif command == "performance":
            await self._analyze_performance(args)
        else:
            print(f"Unknown command: {command}")
            self._print_help()

    async def _run_dashboard(self, args: List[str]):
        """Run monitoring dashboard"""
        refresh_interval = 30
        if args and args[0].isdigit():
            refresh_interval = int(args[0])

        dashboard = MonitoringDashboard(refresh_interval)
        await dashboard.start()

    async def _check_health(self, args: List[str]):
        """Check system health"""
        health_monitor = await get_health_monitor()
        health_status = await health_monitor.get_comprehensive_health_status()

        print(f"System Health: {health_status.overall_status}")
        print(f"Timestamp: {health_status.timestamp}")

        if hasattr(health_status, 'alerts') and health_status.alerts:
            print("\nAlerts:")
            for alert in health_status.alerts:
                print(f"  {alert['severity'].upper()}: {alert['component']} - {alert['message']}")
        else:
            print("\nNo alerts")

    async def _manage_training(self, args: List[str]):
        """Manage training progress"""
        if not args:
            # Show training status
            training_monitor = await get_training_monitor()
            summary = training_monitor.get_progress_summary()
            print(json.dumps(summary, indent=2, default=str))
            return

        action = args[0]
        if action == "pause" and len(args) > 1:
            expert_id = args[1]
            training_monitor = await get_training_monitor()
            await training_monitor.pause_training(expert_id)
            print(f"Training paused for {expert_id}")
        elif action == "resume" and len(args) > 1:
            expert_id = args[1]
            training_monitor = await get_training_monitor()
            await training_monitor.resume_training(expert_id)
            print(f"Training resumed for {expert_id}")
        else:
            print("Usage: training [pause|resume] <expert_id>")

    async def _run_maintenance(self, args: List[str]):
        """Run maintenance tasks"""
        if not args:
            print("Available maintenance tasks:")
            for task_type in MaintenanceTaskType:
                print(f"  {task_type.value}")
            return

        task_name = args[0]
        try:
            task_type = MaintenanceTaskType(task_name)
            memory_maintenance = await get_memory_maintenance()
            result = await memory_maintenance.run_maintenance_task(task_type)
            print(json.dumps(result, indent=2, default=str))
        except ValueError:
            print(f"Unknown maintenance task: {task_name}")

    async def _analyze_performance(self, args: List[str]):
        """Analyze expert performance"""
        performance_analyzer = await get_performance_analyzer()

        if args:
            # Analyze specific expert
            expert_id = args[0]
            days = int(args[1]) if len(args) > 1 else 30
            metrics = await performance_analyzer.analyze_expert_performance(expert_id, days)
            print(json.dumps(metrics.__dict__, indent=2, default=str))
        else:
            # Generate report for all experts
            expert_ids = [
                "conservative_analyzer", "risk_taking_gambler", "contrarian_rebel",
                "value_hunter", "momentum_rider"
            ]
            report = await performance_analyzer.generate_performance_report(expert_ids)
            print(json.dumps(report, indent=2, default=str))

    def _print_help(self):
        """Print help information"""
        print("""
NFL Expert Prediction System - Admin CLI

Commands:
  dashboard [refresh_interval]     - Start monitoring dashboard
  health                          - Check system health
  training [pause|resume] [expert] - Manage training progress
  maintenance [task_type]         - Run maintenance tasks
  performance [expert_id] [days]  - Analyze performance

Examples:
  python monitoring_dashboard.py dashboard 15
  python monitoring_dashboard.py health
  python monitoring_dashboard.py training pause conservative_analyzer
  python monitoring_dashboard.py maintenance memory_cleanup
  python monitoring_dashboard.py performance conservative_analyzer 7
        """)


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="NFL Expert System Admin CLI")
    parser.add_argument("command", nargs="?", default="dashboard",
                       help="Command to run (dashboard, health, training, maintenance, performance)")
    parser.add_argument("args", nargs="*", help="Command arguments")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create admin CLI and run command
    admin_cli = SystemAdminCLI()
    await admin_cli.run_command(args.command, args.args)


if __name__ == "__main__":
    asyncio.run(main())
