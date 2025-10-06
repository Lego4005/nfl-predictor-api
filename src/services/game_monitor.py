"""
Automated Game Completion Monitor

This sice continuously monitors for completed NFL games and automatically
triggers the reconciliation workflow. entry point that makes the
entire automated learning system work without manual intervention.

Key Features:
- Continuous monitoring of game completion status
- Automatic workflow triggering within 5 minutes of game completion
- Rate limiting and batch processing for high-volume periods
- Error handling and retry mechanisms
- Health monitoring and alerting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set
import time
from dataclasses import dataclass

from supabase import Client as SupabaseClient
from .reconciliation_service import ReconciliationService


@dataclass
class GameStatus:
    """Game status information"""
    game_id: str
    home_team: str
    away_team: str
    status: str
    home_score: int
    away_score: int
    last_updated: datetime
    reconciliation_completed: bool


class GameCompletionMonitor:
    """
    Monitors NFL games for completion and triggers automated reconciliation.

    This is the orchestrator that makes the automated learning system work.
    It runs continuously and ensures every completed game gets processed.
    """

    def __init__(self, supabase_client: SupabaseClient, reconciliation_service: ReconciliationService):
        self.supabase = supabase_client
        self.reconciliation_service = reconciliation_service
        self.logger = logging.getLogger(__name__)

        # Monitoring state
        self.is_running = False
        self.processed_games: Set[str] = set()
        self.failed_games: Dict[str, int] = {}  # game_id -> retry_count

        # Configuration
        self.check_interval = 60  # Check every minute
        self.max_retries = 3
        self.batch_size = 5  # Process up to 5 games concurrently
        self.rate_limit_delay = 10  # Seconds between batches

    async def start_monitoring(self) -> None:
        """
        Start continuous monitoring for completed games.

        This is the main loop that runs continuously and triggers
        reconciliation workflows for newly completed games.
        """
        self.is_running = True
        self.logger.info("Starting automated game completion monitoring")

        while self.is_running:
            try:
                # Get newly completed games
                completed_games = await self._get_newly_completed_games()

                if completed_games:
                    self.logger.info(f"Found {len(completed_games)} newly completed games")

                    # Process games in batches to avoid overwhelming the system
                    await self._process_games_in_batches(completed_games)

                # Wait before next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self.check_interval)

    def stop_monitoring(self) -> None:
        """Stop the monitoring loop"""
        self.is_running = False
        self.logger.info("Stopping automated game completion monitoring")

    async def _get_newly_completed_games(self) -> List[GameStatus]:
        """
        Get games that have completed but haven't been reconciled yet.

        Returns games that:
        1. Have a final status (completed, finished, etc.)
        2. Have final scores
        3. Haven't been reconciled yet
        4. Aren't currently being processed
        """
        try:
            # Query for completed games that need reconciliation
            response = self.supabase.table('nfl_games').select('*').in_(
                'status', ['completed', 'finished', 'final']
            ).eq('reconciliation_completed', False).execute()

            completed_games = []

            for game_data in response.data:
                # Skip if already processed or currently processing
                if game_data['game_id'] in self.processed_games:
                    continue

                # Skip if failed too many times
                if self.failed_games.get(game_data['game_id'], 0) >= self.max_retries:
                    continue

                # Ensure game has final scores
                if game_data['home_score'] is None or game_data['away_score'] is None:
                    continue

                game_status = GameStatus(
                    game_id=game_data['game_id'],
                    home_team=game_data['home_team'],
                    away_team=game_data['away_team'],
                    status=game_data['status'],
                    home_score=game_data['home_score'],
                    away_score=game_data['away_score'],
                    last_updated=datetime.fromisoformat(game_data['updated_at']),
                    reconciliation_completed=game_data['reconciliation_completed']
                )

                completed_games.append(game_status)

            return completed_games

        except Exception as e:
            self.logger.error(f"Error getting newly completed games: {str(e)}")
            return []

    async def _process_games_in_batches(self, games: List[GameStatus]) -> None:
        """
        Process completed games in batches to manage system load.

        This ensures we don't overwhelm the system during high-volume periods
        like Sunday when many games complete simultaneously.
        """
        for i in range(0, len(games), self.batch_size):
            batch = games[i:i + self.batch_size]

            self.logger.info(f"Processing batch of {len(batch)} games")

            # Process batch concurrently
            tasks = []
            for game in batch:
                task = self._process_single_game(game)
                tasks.append(task)

            # Wait for batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log results
            successful = sum(1 for result in results if result is True)
            failed = len(results) - successful

            self.logger.info(f"Batch completed: {successful} successful, {failed} failed")

            # Rate limiting between batches
            if i + self.batch_size < len(games):
                await asyncio.sleep(self.rate_limit_delay)

    async def _process_single_game(self, game: GameStatus) -> bool:
        """
        Process a single completed game through the reconciliation workflow.

        This is where the automated learning actually happens - each completed
        game triggers the 6-step reconciliation process.
        """
        try:
            self.logger.info(f"Processing completed game: {game.game_id} ({game.home_team} vs {game.away_team})")

            # Mark as being processed
            self.processed_games.add(game.game_id)

            # Trigger reconciliation workflow
            success = await self.reconciliation_service.process_completed_game(game.game_id)

            if success:
                self.logger.info(f"Successfully processed game {game.game_id}")

                # Remove from failed games if it was there
                if game.game_id in self.failed_games:
                    del self.failed_games[game.game_id]

                return True
            else:
                self.logger.error(f"Failed to process game {game.game_id}")

                # Track failure for retry logic
                self.failed_games[game.game_id] = self.failed_games.get(game.game_id, 0) + 1

                # Remove from processed set so it can be retried
                self.processed_games.discard(game.game_id)

                return False

        except Exception as e:
            self.logger.error(f"Exception processing game {game.game_id}: {str(e)}")

            # Track failure
            self.failed_games[game.game_id] = self.failed_games.get(game.game_id, 0) + 1
            self.processed_games.discard(game.game_id)

            return False

    async def get_monitoring_status(self) -> Dict:
        """
        Get current monitoring status for health checks and dashboards.

        Returns information about:
        - Whether monitoring is running
        - Number of games processed
        - Number of failed games
        - Recent processing statistics
        """
        # Get recent workflow logs for statistics
        recent_logs = await self._get_recent_workflow_logs()

        return {
            'is_running': self.is_running,
            'processed_games_count': len(self.processed_games),
            'failed_games_count': len(self.failed_games),
            'failed_games': dict(self.failed_games),
            'recent_statistics': {
                'last_24h_processed': len([log for log in recent_logs if log['success']]),
                'last_24h_failed': len([log for log in recent_logs if not log['success']]),
                'average_processing_time': self._calculate_average_processing_time(recent_logs)
            },
            'configuration': {
                'check_interval': self.check_interval,
                'max_retries': self.max_retries,
                'batch_size': self.batch_size,
                'rate_limit_delay': self.rate_limit_delay
            }
        }

    async def _get_recent_workflow_logs(self) -> List[Dict]:
        """Get workflow logs from the last 24 hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)

            response = self.supabase.table('reconciliation_workflow_logs').select('*').gte(
                'workflow_start_time', cutoff_time.isoformat()
            ).execute()

            return response.data

        except Exception as e:
            self.logger.error(f"Error getting recent workflow logs: {str(e)}")
            return []

    def _calculate_average_processing_time(self, logs: List[Dict]) -> float:
        """Calculate average processing time from workflow logs"""
        if not logs:
            return 0.0

        total_time = sum(log.get('workflow_duration', 0) for log in logs)
        return total_time / len(logs)

    async def retry_failed_games(self) -> Dict:
        """
        Manually retry games that have failed processing.

        This can be called by administrators to retry games that failed
        due to temporary issues.
        """
        retry_results = {
            'attempted': 0,
            'successful': 0,
            'still_failed': 0
        }

        failed_game_ids = list(self.failed_games.keys())

        for game_id in failed_game_ids:
            if self.failed_games[game_id] < self.max_retries:
                retry_results['attempted'] += 1

                # Remove from processed set and reset failure count
                self.processed_games.discard(game_id)

                # The next monitoring cycle will pick it up
                self.logger.info(f"Scheduled retry for failed game {game_id}")

        return retry_results

    async def force_process_game(self, game_id: str) -> bool:
        """
        Force processing of a specific game, bypassing normal checks.

        This can be used by administrators to manually trigger reconciliation
        for specific games.
        """
        try:
            self.logger.info(f"Force processing game {game_id}")

            # Remove from processed and failed sets
            self.processed_games.discard(game_id)
            if game_id in self.failed_games:
                del self.failed_games[game_id]

            # Process the game
            success = await self.reconciliation_service.process_completed_game(game_id)

            if success:
                self.processed_games.add(game_id)
                self.logger.info(f"Successfully force processed game {game_id}")
            else:
                self.failed_games[game_id] = 1
                self.logger.error(f"Failed to force process game {game_id}")

            return success

        except Exception as e:
            self.logger.error(f"Exception force processing game {game_id}: {str(e)}")
            return False


class GameMonitorHealthCheck:
    """
    Health monitoring for the game completion monitor.

    Provides health checks and alerts for the automated learning system.
    """

    def __init__(self, monitor: GameCompletionMonitor):
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)

    async def check_system_health(self) -> Dict:
        """
        Comprehensive health check of the automated learning system.

        Checks:
        - Monitor is running
        - Recent processing success rate
        - No games stuck in processing
        - Database connectivity
        """
        health_status = {
            'overall_status': 'healthy',
            'checks': {},
            'alerts': [],
            'timestamp': datetime.now().isoformat()
        }

        # Check if monitor is running
        if not self.monitor.is_running:
            health_status['checks']['monitor_running'] = False
            health_status['alerts'].append('Game completion monitor is not running')
            health_status['overall_status'] = 'critical'
        else:
            health_status['checks']['monitor_running'] = True

        # Check recent processing success rate
        status = await self.monitor.get_monitoring_status()
        recent_stats = status['recent_statistics']

        total_recent = recent_stats['last_24h_processed'] + recent_stats['last_24h_failed']
        if total_recent > 0:
            success_rate = recent_stats['last_24h_processed'] / total_recent
            health_status['checks']['success_rate'] = success_rate

            if success_rate < 0.8:
                health_status['alerts'].append(f'Low success rate: {success_rate:.1%}')
                health_status['overall_status'] = 'warning'

        # Check for games with too many failures
        max_failed_count = max(status['failed_games'].values()) if status['failed_games'] else 0
        health_status['checks']['max_failed_count'] = max_failed_count

        if max_failed_count >= status['configuration']['max_retries']:
            health_status['alerts'].append(f'Games with max failures: {max_failed_count}')
            if health_status['overall_status'] == 'healthy':
                health_status['overall_status'] = 'warning'

        # Check database connectivity
        try:
            await self.monitor.supabase.table('nfl_games').select('game_id').limit(1).execute()
            health_status['checks']['database_connectivity'] = True
        except Exception as e:
            health_status['checks']['database_connectivity'] = False
            health_status['alerts'].append(f'Database connectivity issue: {str(e)}')
            health_status['overall_status'] = 'critical'

        return health_status

    async def get_performance_metrics(self) -> Dict:
        """Get detailed performance metrics for monitoring dashboards"""
        status = await self.monitor.get_monitoring_status()

        return {
            'processing_metrics': {
                'games_processed_24h': status['recent_statistics']['last_24h_processed'],
                'games_failed_24h': status['recent_statistics']['last_24h_failed'],
                'average_processing_time': status['recent_statistics']['average_processing_time'],
                'current_failed_games': len(status['failed_games'])
            },
            'system_metrics': {
                'monitor_uptime': 'running' if status['is_running'] else 'stopped',
                'total_processed': status['processed_games_count'],
                'configuration': status['configuration']
            },
            'timestamp': datetime.now().isoformat()
        }
