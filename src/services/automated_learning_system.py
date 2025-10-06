"""
Automated Learning System Integration

This is the main orchestrator that brings together all components of the
automated learning system. It provides a single interface for sg,
stopping, and monitoring the entire automated learning infrastructure.

Components integrated:
- ReconciliationService: Processes completed games
- GameCompletionMonitor: Monitors for completed games
- Health monitoring and alerting
- Configuration management
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
import signal
import sys

from supabase import Client as SupabaseClient
from .reconciliation_service import ReconciliationService
from .game_monitor import GameCompletionMonitor, GameMonitorHealthCheck


class AutomatedLearningSystem:
    """
    Main orchestrator for the automated learning system.

    This class provides a single interface to start, stop, and monitor
    the entire automated learning infrastructure that makes the AI
    get smarter after every game.
    """

    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
        self.logger = logging.getLogger(__name__)

        # Initialize core services
        self.reconciliation_service = ReconciliationService(supabase_client)
        self.game_monitor = GameCompletionMonitor(supabase_client, self.reconciliation_service)
        self.health_check = GameMonitorHealthCheck(self.game_monitor)

        # System state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.monitoring_task: Optional[asyncio.Task] = None

        # Setup graceful shutdown
        self._setup_signal_handlers()

    async def start(self) -> None:
        """
        Start the automated learning system.

        This starts continuous monitoring for completed games and
        automatic triggering of reconciliation workflows.
        """
        if self.is_running:
            self.logger.warning("Automated learning system is already running")
            return

        self.logger.info("Starting Automated Learning System")
        self.start_time = datetime.now()
        self.is_running = True

        try:
            # Validate system prerequisites
            await self._validate_system_prerequisites()

            # Start the game completion monitor
            self.monitoring_task = asyncio.create_task(self.game_monitor.start_monitoring())

            self.logger.info("Automated Learning System started successfully")
            self.logger.info("System will now automatically process completed games and learn from outcomes")

            # Wait for the monitoring task to complete (it runs indefinitely)
            await self.monitoring_task

        except Exception as e:
            self.logger.error(f"Failed to start Automated Learning System: {str(e)}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """
        Stop the automated learning system gracefully.

        This stops all monitoring and processing, allowing current
        workflows to complete before shutting down.
        """
        if not self.is_running:
            self.logger.warning("Automated learning system is not running")
            return

        self.logger.info("Stopping Automated Learning System")
        self.is_running = False

        # Stop the game monitor
        self.game_monitor.stop_monitoring()

        # Cancel the monitoring task if it exists
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        self.logger.info(f"Automated Learning System stopped after {uptime}")

    async def get_system_status(self) -> Dict:
        """
        Get comprehensive system status for monitoring and dashboards.

        Returns detailed information about:
        - System running status
        - Recent processing statistics
        - Health check results
        - Performance metrics
        """
        # Get health check results
        health_status = await self.health_check.check_system_health()

        # Get performance metrics
        performance_metrics = await self.health_check.get_performance_metrics()

        # Get monitor status
        monitor_status = await self.game_monitor.get_monitoring_status()

        uptime = datetime.now() - self.start_time if self.start_time else None

        return {
            'system_info': {
                'is_running': self.is_running,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'uptime_seconds': uptime.total_seconds() if uptime else 0,
                'version': '1.0.0'
            },
            'health_status': health_status,
            'performance_metrics': performance_metrics,
            'monitor_status': monitor_status,
            'timestamp': datetime.now().isoformat()
        }

    async def process_game_manually(self, game_id: str) -> Dict:
        """
        Manually trigger processing for a specific game.

        This can be used by administrators to force processing of
        specific games or to test the reconciliation workflow.
        """
        self.logger.info(f"Manual processing requested for game {game_id}")

        try:
            success = await self.game_monitor.force_process_game(game_id)

            return {
                'game_id': game_id,
                'success': success,
                'message': 'Game processed successfully' if success else 'Game processing failed',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in manual game processing for {game_id}: {str(e)}")
            return {
                'game_id': game_id,
                'success': False,
                'message': f'Error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

    async def retry_failed_games(self) -> Dict:
        """
        Retry all games that have failed processing.

        This can be used by administrators to retry games that failed
        due to temporary issues.
        """
        self.logger.info("Retrying failed games")

        try:
            results = await self.game_monitor.retry_failed_games()

            return {
                'success': True,
                'results': results,
                'message': f"Scheduled retry for {results['attempted']} games",
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error retrying failed games: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

    async def get_learning_statistics(self) -> Dict:
        """
        Get statistics about the learning system's performance.

        Returns information about:
        - Total games processed
        - Learning patterns discovered
        - Memory updates applied
        - System effectiveness metrics
        """
        try:
            # Get workflow statistics
            workflow_logs = await self.supabase.table('reconciliation_workflow_logs').select('*').execute()

            # Get team knowledge statistics
            team_knowledge = await self.supabase.table('team_knowledge').select('*').execute()

            # Get matchup memory statistics
            matchup_memories = await self.supabase.table('matchup_memories').select('*').execute()

            # Calculate statistics
            total_workflows = len(workflow_logs.data)
            successful_workflows = len([log for log in workflow_logs.data if log['success']])

            # Count patterns across all team knowledge records
            total_patterns = 0
            for record in team_knowledge.data:
                patterns = record.get('pattern_confidence_scores', {})
                total_patterns += len(patterns)

            return {
                'processing_statistics': {
                    'total_games_processed': total_workflows,
                    'successful_workflows': successful_workflows,
                    'success_rate': successful_workflows / total_workflows if total_workflows > 0 else 0,
                    'average_processing_time': self._calculate_average_processing_time(workflow_logs.data)
                },
                'learning_statistics': {
                    'total_team_knowledge_records': len(team_knowledge.data),
                    'total_patterns_learned': total_patterns,
                    'total_matchup_memories': len(matchup_memories.data),
                    'unique_teams_with_knowledge': len(set(record['team_id'] for record in team_knowledge.data)),
                    'unique_experts_learning': len(set(record['expert_id'] for record in team_knowledge.data))
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting learning statistics: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _validate_system_prerequisites(self) -> None:
        """
        Validate that all system prerequisites are met before starting.

        Checks:
        - Database connectivity
        - Required tables exist
        - Expert models are configured
        """
        self.logger.info("Validating system prerequisites")

        # Check database connectivity
        try:
            await self.supabase.table('nfl_games').select('game_id').limit(1).execute()
        except Exception as e:
            raise RuntimeError(f"Database connectivity check failed: {str(e)}")

        # Check required tables exist
        required_tables = [
            'nfl_games', 'team_knowledge', 'matchup_memories',
            'reconciliation_workflow_logs', 'workflow_failures',
            'expert_reasoning_chains', 'personality_experts'
        ]

        for table in required_tables:
            try:
                await self.supabase.table(table).select('*').limit(1).execute()
            except Exception as e:
                raise RuntimeError(f"Required table '{table}' check failed: {str(e)}")

        # Check that expert models exist
        experts_response = await self.supabase.table('personality_experts').select('expert_id').execute()
        if not experts_response.data:
            raise RuntimeError("No expert models found - automated learning requires expert models to be configured")

        self.logger.info(f"System prerequisites validated - found {len(experts_response.data)} expert models")

    def _calculate_average_processing_time(self, workflow_logs: list) -> float:
        """Calculate average processing time from workflow logs"""
        if not workflow_logs:
            return 0.0

        total_time = sum(log.get('workflow_duration', 0) for log in workflow_logs)
        return total_time / len(workflow_logs)

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


# Convenience function for starting the system
async def start_automated_learning_system(supabase_client: SupabaseClient) -> AutomatedLearningSystem:
    """
    Convenience function to create and start the automated learning system.

    Usage:
        system = await start_automated_learning_system(supabase_client)
        # System is now running and will process games automatically
    """
    system = AutomatedLearningSystem(supabase_client)
    await system.start()
    return system


# CLI interface for running the system standalone
async def main():
    """
    Main entry point for running the automated learning system as a standalone service.

    This can be used to run the system independently of the main application.
    """
    import os
    from supabase import create_client

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Get Supabase credentials from environment
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")
        sys.exit(1)

    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)

    # Create and start the system
    system = AutomatedLearningSystem(supabase)

    try:
        await system.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"System error: {str(e)}")
        sys.exit(1)
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
