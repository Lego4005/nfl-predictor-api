#!/usr/bin/env python3
"""
Productioyment Script for NFL Expert Prediction System.
Handles complete production deployment with monitoring, logging, and health checks.
"""

import asyncio
import logging
import sys
import os
import json
import signal
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.production_deployment import (
    initialize_production_deployment,
    shutdown_production_deployment,
    get_deployment_manager
)
from src.admin.system_administration import (
    get_training_monitor,
    get_memory_maintenance,
    get_performance_analyzer,
    get_health_monitor,
    MaintenanceTaskType
)


class ProductionDeploymentOrchestrator:
    """Orchestrates complete production deployment"""

    def __init__(self):
        self.logger = logging.getLogger("deployment")
        self.running = False
        self.deployment_manager = None
        self.training_monitor = None
        self.health_monitor = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False

    async def deploy(self):
        """Execute complete production deployment"""
        self.logger.info("Starting NFL Expert Prediction System production deployment...")

        try:
            # Phase 1: Initialize core infrastructure
            await self._initialize_infrastructure()

            # Phase 2: Validate system health
            await self._validate_system_health()

            # Phase 3: Start monitoring systems
            await self._start_monitoring_systems()

            # Phase 4: Run initial maintenance
            await self._run_initial_maintenance()

            # Phase 5: Start main application loop
            await self._start_application_loop()

        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            await self._emergency_shutdown()
            raise

    async def _initialize_infrastructure(self):
        """Initialize core infrastructure components"""
        self.logger.info("Phase 1: Initializing infrastructure...")

        # Initialize deployment manager
        await initialize_production_deployment()
        self.deployment_manager = await get_deployment_manager()

        # Log configuration summary
        config_summary = self.deployment_manager.get_configuration_summary()
        self.logger.info(f"Configuration: {json.dumps(config_summary, indent=2)}")

        # Initialize admin components
        self.training_monitor = await get_training_monitor()
        self.health_monitor = await get_health_monitor()

        self.logger.info("Infrastructure initialization completed")

    async def _validate_system_health(self):
        """Validate system health before full deployment"""
        self.logger.info("Phase 2: Validating system health...")

        # Get comprehensive health status
        health_status = await self.health_monitor.get_comprehensive_health_status()

        # Log health status
        self.logger.info(f"System health: {health_status.overall_status}")

        # Check for critical issues
        critical_alerts = [
            alert for alert in health_status.alerts
            if alert["severity"] == "critical"
        ]

        if critical_alerts:
            self.logger.error(f"Critical health issues detected: {critical_alerts}")
            raise RuntimeError("System health validation failed - critical issues detected")

        # Log warnings
        warning_alerts = [
            alert for alert in health_status.alerts
            if alert["severity"] == "warning"
        ]

        if warning_alerts:
            self.logger.warning(f"Health warnings: {warning_alerts}")

        self.logger.info("System health validation completed")

    async def _start_monitoring_systems(self):
        """Start monitoring and health check systems"""
        self.logger.info("Phase 3: Starting monitoring systems...")

        # Start training progress monitoring for all experts
        expert_ids = [
            "conservative_analyzer", "risk_taking_gambler", "contrarian_rebel",
            "value_hunter", "momentum_rider", "fundamentalist_scholar",
            "gut_instinct_expert", "statistics_purist", "trend_reversal_specialist",
            "underdog_champion", "sharp_money_follower", "popular_narrative_fader",
            "market_inefficiency_exploiter", "chaos_theory_believer", "consensus_follower"
        ]

        await self.training_monitor.start_monitoring(expert_ids)

        self.logger.info("Monitoring systems started")

    async def _run_initial_maintenance(self):
        """Run initial maintenance tasks"""
        self.logger.info("Phase 4: Running initial maintenance...")

        memory_maintenance = await get_memory_maintenance()

        # Run performance analysis
        perf_result = await memory_maintenance.run_maintenance_task(
            MaintenanceTaskType.PERFORMANCE_ANALYSIS
        )
        self.logger.info(f"Performance analysis: {perf_result}")

        # Optimize vector indexes
        index_result = await memory_maintenance.run_maintenance_task(
            MaintenanceTaskType.INDEX_OPTIMIZATION
        )
        self.logger.info(f"Index optimization: {index_result}")

        self.logger.info("Initial maintenance completed")

    async def _start_application_loop(self):
        """Start main application monitoring loop"""
        self.logger.info("Phase 5: Starting application monitoring loop...")

        self.running = True

        # Schedule periodic tasks
        tasks = [
            asyncio.create_task(self._health_monitoring_loop()),
            asyncio.create_task(self._maintenance_loop()),
            asyncio.create_task(self._performance_monitoring_loop()),
            asyncio.create_task(self._training_monitoring_loop())
        ]

        try:
            # Wait for shutdown signal
            while self.running:
                await asyncio.sleep(1)

            self.logger.info("Shutdown signal received, stopping application...")

        finally:
            # Cancel all tasks
            for task in tasks:
                task.cancel()

            # Wait for tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

            await self._graceful_shutdown()

    async def _health_monitoring_loop(self):
        """Continuous health monitoring loop"""
        while self.running:
            try:
                # Get health status every 5 minutes
                health_status = await self.health_monitor.get_comprehensive_health_status()

                # Log health summary
                self.logger.info(f"Health check: {health_status.overall_status}")

                # Handle critical alerts
                critical_alerts = [
                    alert for alert in health_status.alerts
                    if alert["severity"] == "critical"
                ]

                if critical_alerts:
                    self.logger.error(f"CRITICAL ALERTS: {critical_alerts}")
                    # Could trigger emergency procedures here

                await asyncio.sleep(300)  # 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _maintenance_loop(self):
        """Periodic maintenance loop"""
        while self.running:
            try:
                # Run maintenance every 6 hours
                await asyncio.sleep(6 * 3600)

                if not self.running:
                    break

                self.logger.info("Running scheduled maintenance...")

                memory_maintenance = await get_memory_maintenance()

                # Clean up old memories
                cleanup_result = await memory_maintenance.run_maintenance_task(
                    MaintenanceTaskType.MEMORY_CLEANUP
                )
                self.logger.info(f"Memory cleanup: {cleanup_result}")

                # Archive very old memories
                archive_result = await memory_maintenance.run_maintenance_task(
                    MaintenanceTaskType.MEMORY_ARCHIVAL
                )
                self.logger.info(f"Memory archival: {archive_result}")

                self.logger.info("Scheduled maintenance completed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Maintenance loop error: {e}")

    async def _performance_monitoring_loop(self):
        """Performance monitoring and reporting loop"""
        while self.running:
            try:
                # Generate performance report every hour
                await asyncio.sleep(3600)

                if not self.running:
                    break

                self.logger.info("Generating performance report...")

                performance_analyzer = await get_performance_analyzer()

                expert_ids = [
                    "conservative_analyzer", "risk_taking_gambler", "contrarian_rebel",
                    "value_hunter", "momentum_rider"  # Sample of experts
                ]

                report = await performance_analyzer.generate_performance_report(expert_ids)

                # Log performance summary
                summary = report.get("summary", {})
                self.logger.info(f"Performance summary: {json.dumps(summary, indent=2)}")

                # Save detailed report
                os.makedirs("./logs/performance", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(f"./logs/performance/report_{timestamp}.json", "w") as f:
                    json.dump(report, f, indent=2, default=str)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")

    async def _training_monitoring_loop(self):
        """Training progress monitoring loop"""
        while self.running:
            try:
                # Check training progress every 10 minutes
                await asyncio.sleep(600)

                if not self.running:
                    break

                # Get training progress summary
                progress_summary = self.training_monitor.get_progress_summary()

                # Log progress
                self.logger.info(f"Training progress: {progress_summary['overall_progress']:.1f}%")
                self.logger.info(f"Total memories: {progress_summary['total_memories']}")

                # Check for stalled experts
                for expert_id, expert_data in progress_summary["experts"].items():
                    if expert_data["phase"] == "paused":
                        self.logger.warning(f"Expert {expert_id} training is paused")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Training monitoring error: {e}")

    async def _graceful_shutdown(self):
        """Perform graceful shutdown"""
        self.logger.info("Performing graceful shutdown...")

        try:
            # Stop training monitoring
            if self.training_monitor:
                await self.training_monitor.stop_monitoring()

            # Shutdown deployment manager
            await shutdown_production_deployment()

            self.logger.info("Graceful shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}")

    async def _emergency_shutdown(self):
        """Perform emergency shutdown"""
        self.logger.error("Performing emergency shutdown...")

        try:
            await shutdown_production_deployment()
        except Exception as e:
            self.logger.error(f"Error during emergency shutdown: {e}")


async def main():
    """Main deployment function"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("./logs/deployment.log")
        ]
    )

    logger = logging.getLogger("main")

    # Create logs directory
    os.makedirs("./logs", exist_ok=True)

    try:
        # Create and run deployment orchestrator
        orchestrator = ProductionDeploymentOrchestrator()
        await orchestrator.deploy()

    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
