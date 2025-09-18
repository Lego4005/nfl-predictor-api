"""
Real-time Data Pipeline for Live NFL Game Updates

This module orchestrates real-time data collection, transformation, and distribution
for live NFL game updates. It integrates WebSocket broadcasting, data caching,
error handling, and rate limiting for optimal performance.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import weakref

from ..websocket.websocket_manager import websocket_manager
from ..api.espn_api_client import ESPNAPIClient
from ..api.live_data_manager import LiveDataManager, DataType
from ..cache.cache_manager import CacheManager
from ..database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """Pipeline status enumeration"""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class DataPriority(Enum):
    """Data update priority levels"""
    CRITICAL = "critical"  # Live game scores, field position
    HIGH = "high"         # Player stats, possession changes
    MEDIUM = "medium"     # Odds updates, weather changes
    LOW = "low"          # Historical stats, injury reports


@dataclass
class GameState:
    """Tracks the state of a live game"""
    game_id: str
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0
    quarter: str = "1"
    time_remaining: str = "15:00"
    possession: Optional[str] = None
    down: Optional[int] = None
    distance: Optional[int] = None
    field_position: Optional[str] = None
    last_update: datetime = field(default_factory=datetime.utcnow)
    subscribers: Set[str] = field(default_factory=set)
    update_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'game_id': self.game_id,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'quarter': self.quarter,
            'time_remaining': self.time_remaining,
            'possession': self.possession,
            'down': self.down,
            'distance': self.distance,
            'field_position': self.field_position,
            'last_update': self.last_update.isoformat(),
            'update_count': self.update_count
        }


@dataclass
class UpdateMetrics:
    """Tracks update metrics and performance"""
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    avg_response_time: float = 0.0
    last_update_time: Optional[datetime] = None
    update_frequency: float = 0.0  # updates per minute

    def calculate_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_updates == 0:
            return 0.0
        return (self.successful_updates / self.total_updates) * 100


class RateLimiter:
    """Rate limiting for API calls and updates"""

    def __init__(self, max_calls: int, time_window: int = 60):
        """
        Initialize rate limiter

        Args:
            max_calls: Maximum calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()

    def can_proceed(self) -> bool:
        """Check if a call can proceed without violating rate limit"""
        now = datetime.utcnow()

        # Remove old calls outside time window
        while self.calls and (now - self.calls[0]).seconds > self.time_window:
            self.calls.popleft()

        return len(self.calls) < self.max_calls

    def record_call(self):
        """Record a new call"""
        self.calls.append(datetime.utcnow())

    def get_remaining_calls(self) -> int:
        """Get remaining calls in current window"""
        now = datetime.utcnow()

        # Remove old calls
        while self.calls and (now - self.calls[0]).seconds > self.time_window:
            self.calls.popleft()

        return max(0, self.max_calls - len(self.calls))


class DataTransformer:
    """Transforms raw API data into UI-ready format"""

    @staticmethod
    def transform_espn_game_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform ESPN game data to standardized format"""
        try:
            # Extract basic game information
            events = raw_data.get('events', [])
            if not events:
                return {}

            transformed_games = []

            for event in events:
                game_id = event.get('id', '')
                status = event.get('status', {})
                status_type = status.get('type', {})

                # Extract competition data
                competitions = event.get('competitions', [])
                if not competitions:
                    continue

                competition = competitions[0]
                competitors = competition.get('competitors', [])

                # Parse teams and scores
                home_team = away_team = None
                home_score = away_score = 0

                for competitor in competitors:
                    team_info = competitor.get('team', {})
                    team_abbr = team_info.get('abbreviation', '')
                    score = int(competitor.get('score', 0))

                    if competitor.get('homeAway') == 'home':
                        home_team = team_abbr
                        home_score = score
                    else:
                        away_team = team_abbr
                        away_score = score

                # Extract game situation
                situation = competition.get('situation', {})

                transformed_game = {
                    'game_id': game_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': home_score,
                    'away_score': away_score,
                    'status': status_type.get('name', 'scheduled'),
                    'quarter': situation.get('period', 1),
                    'time_remaining': situation.get('displayClock', '15:00'),
                    'possession': situation.get('possession', {}).get('abbreviation'),
                    'down': situation.get('down'),
                    'distance': situation.get('distance'),
                    'field_position': f"{situation.get('possession', {}).get('abbreviation', '')} {situation.get('yardLine', '')}",
                    'last_play': situation.get('lastPlay', {}).get('text'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'week': event.get('week', {}).get('number'),
                    'is_live': status_type.get('name') == 'in'
                }

                transformed_games.append(transformed_game)

            return {'games': transformed_games}

        except Exception as e:
            logger.error(f"Error transforming ESPN data: {e}")
            return {'error': str(e)}

    @staticmethod
    def transform_for_websocket(game_data: Dict[str, Any], priority: DataPriority) -> Dict[str, Any]:
        """Transform game data for WebSocket broadcast"""
        return {
            'type': 'game_update',
            'priority': priority.value,
            'data': game_data,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'real_time_pipeline'
        }


class RealtimeDataPipeline:
    """
    Real-time data pipeline orchestrating live NFL game updates

    Features:
    - Multi-game support with individual state tracking
    - Rate limiting and error handling
    - WebSocket broadcasting with selective updates
    - Redis caching for performance optimization
    - Data transformation and validation
    - Health monitoring and metrics
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        database_manager: Optional[DatabaseManager] = None,
        update_interval: int = 10,  # seconds
        max_concurrent_games: int = 16
    ):
        """
        Initialize real-time data pipeline

        Args:
            cache_manager: Cache manager instance
            database_manager: Database manager instance
            update_interval: Update interval in seconds
            max_concurrent_games: Maximum concurrent games to track
        """
        self.cache_manager = cache_manager or CacheManager()
        self.database_manager = database_manager
        self.update_interval = update_interval
        self.max_concurrent_games = max_concurrent_games

        # Pipeline state
        self.status = PipelineStatus.STOPPED
        self.game_states: Dict[str, GameState] = {}
        self.active_games: Set[str] = set()

        # Data sources
        self.live_data_manager = LiveDataManager()
        self.espn_client = None  # Will be initialized when needed

        # Rate limiting
        self.rate_limiters = {
            'espn': RateLimiter(max_calls=100, time_window=60),  # 100 calls per minute
            'websocket': RateLimiter(max_calls=1000, time_window=60)  # 1000 broadcasts per minute
        }

        # Metrics and monitoring
        self.metrics = UpdateMetrics()
        self.error_count = defaultdict(int)
        self.last_errors = deque(maxlen=50)

        # Background tasks
        self._update_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Event handlers
        self._data_handlers: List[Callable] = []
        self._error_handlers: List[Callable] = []

        # WebSocket channels
        self.ws_channels = {
            'live_games': 'live_games',
            'game_updates': 'game_updates',
            'scores': 'scores'
        }

    async def start(self):
        """Start the real-time data pipeline"""
        if self.status == PipelineStatus.RUNNING:
            logger.warning("Pipeline is already running")
            return

        try:
            self.status = PipelineStatus.STARTING
            logger.info("Starting real-time data pipeline...")

            # Initialize components
            await self._initialize_components()

            # Start background tasks
            self._update_task = asyncio.create_task(self._update_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            # Start WebSocket manager background tasks
            await websocket_manager.start_background_tasks()

            self.status = PipelineStatus.RUNNING
            logger.info("Real-time data pipeline started successfully")

            # Send system notification
            await websocket_manager.send_system_notification(
                "Real-time data pipeline started",
                level="info"
            )

        except Exception as e:
            self.status = PipelineStatus.ERROR
            logger.error(f"Failed to start pipeline: {e}")
            raise

    async def stop(self):
        """Stop the real-time data pipeline"""
        logger.info("Stopping real-time data pipeline...")

        self.status = PipelineStatus.STOPPED

        # Cancel background tasks
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Stop WebSocket manager
        await websocket_manager.stop_background_tasks()

        # Close data manager
        if hasattr(self.live_data_manager, '__aexit__'):
            await self.live_data_manager.__aexit__(None, None, None)

        logger.info("Real-time data pipeline stopped")

    async def _initialize_components(self):
        """Initialize pipeline components"""
        try:
            # Initialize live data manager
            if hasattr(self.live_data_manager, '__aenter__'):
                await self.live_data_manager.__aenter__()

            # Test cache connection
            cache_status = self.cache_manager.get_health_status()
            logger.info(f"Cache status: {cache_status['overall_status']}")

            # Initialize ESPN client if needed
            if not self.espn_client:
                from ..api.client_manager import APIClientManager
                client_manager = APIClientManager()
                self.espn_client = ESPNAPIClient(client_manager)

            logger.info("Pipeline components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    async def _update_loop(self):
        """Main update loop for fetching live data"""
        while self.status == PipelineStatus.RUNNING:
            try:
                start_time = datetime.utcnow()

                # Fetch live games
                await self._fetch_live_games()

                # Update metrics
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds()
                self._update_metrics(response_time, success=True)

                # Wait for next update
                await asyncio.sleep(self.update_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                self._record_error(str(e))
                self._update_metrics(0, success=False)

                # Exponential backoff on errors
                await asyncio.sleep(min(self.update_interval * 2, 60))

    async def _cleanup_loop(self):
        """Cleanup loop for removing stale data"""
        while self.status == PipelineStatus.RUNNING:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_stale_games()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _fetch_live_games(self):
        """Fetch live game data from APIs"""
        try:
            # Check rate limits
            if not self.rate_limiters['espn'].can_proceed():
                logger.warning("ESPN API rate limit reached, skipping update")
                return

            # Get current week
            current_week = self._get_current_week()

            # Fetch live scores from ESPN
            response = await self.espn_client.fetch_live_scores()

            if response.success:
                self.rate_limiters['espn'].record_call()
                await self._process_game_data(response.data)
            else:
                logger.warning(f"Failed to fetch live games: {response.error}")

        except Exception as e:
            logger.error(f"Error fetching live games: {e}")
            self._record_error(str(e))

    async def _process_game_data(self, games_data: List[Any]):
        """Process and distribute game data"""
        try:
            for game_data in games_data:
                game_id = game_data.game_id

                # Transform data
                transformed_data = DataTransformer.transform_espn_game_data({
                    'events': [self._game_to_event_format(game_data)]
                })

                if 'error' in transformed_data:
                    continue

                game_info = transformed_data['games'][0] if transformed_data['games'] else None
                if not game_info:
                    continue

                # Update or create game state
                await self._update_game_state(game_id, game_info)

                # Broadcast updates
                await self._broadcast_game_update(game_id, game_info)

                # Cache the data
                await self._cache_game_data(game_id, game_info)

        except Exception as e:
            logger.error(f"Error processing game data: {e}")
            self._record_error(str(e))

    async def _update_game_state(self, game_id: str, game_info: Dict[str, Any]):
        """Update internal game state"""
        try:
            if game_id not in self.game_states:
                # Create new game state
                self.game_states[game_id] = GameState(
                    game_id=game_id,
                    home_team=game_info['home_team'],
                    away_team=game_info['away_team']
                )
                self.active_games.add(game_id)
                logger.info(f"Started tracking game: {game_id}")

            # Update existing state
            game_state = self.game_states[game_id]

            # Check for significant changes
            significant_change = (
                game_state.home_score != game_info['home_score'] or
                game_state.away_score != game_info['away_score'] or
                game_state.possession != game_info.get('possession') or
                game_state.quarter != str(game_info.get('quarter', 1))
            )

            # Update state
            game_state.home_score = game_info['home_score']
            game_state.away_score = game_info['away_score']
            game_state.quarter = str(game_info.get('quarter', 1))
            game_state.time_remaining = game_info.get('time_remaining', '15:00')
            game_state.possession = game_info.get('possession')
            game_state.down = game_info.get('down')
            game_state.distance = game_info.get('distance')
            game_state.field_position = game_info.get('field_position')
            game_state.last_update = datetime.utcnow()
            game_state.update_count += 1

            # Determine update priority
            if significant_change:
                priority = DataPriority.CRITICAL
            else:
                priority = DataPriority.MEDIUM

            # Store priority for broadcasting
            game_info['_priority'] = priority

        except Exception as e:
            logger.error(f"Error updating game state for {game_id}: {e}")

    async def _broadcast_game_update(self, game_id: str, game_info: Dict[str, Any]):
        """Broadcast game update via WebSocket"""
        try:
            # Check WebSocket rate limit
            if not self.rate_limiters['websocket'].can_proceed():
                return

            priority = game_info.get('_priority', DataPriority.MEDIUM)

            # Transform for WebSocket
            ws_data = DataTransformer.transform_for_websocket(game_info, priority)

            # Broadcast to multiple channels
            await websocket_manager.send_game_update(ws_data)

            # Send to game-specific channel
            game_channel = f"game_{game_id}"
            await websocket_manager.connection_manager.send_to_channel(
                game_channel,
                websocket_manager.connection_manager.create_message(
                    "game_update",
                    ws_data
                )
            )

            self.rate_limiters['websocket'].record_call()

        except Exception as e:
            logger.error(f"Error broadcasting game update: {e}")

    async def _cache_game_data(self, game_id: str, game_info: Dict[str, Any]):
        """Cache game data for performance"""
        try:
            cache_key = f"live_game_{game_id}"

            # Cache with short TTL for live data
            self.cache_manager.set(
                key=cache_key,
                data=game_info,
                source="live_pipeline",
                ttl_minutes=5
            )

            # Also cache in general live games cache
            live_games_key = "live_games_current"
            cached_games = self.cache_manager.get(live_games_key)

            if cached_games:
                games_data = cached_games['data']
            else:
                games_data = {}

            games_data[game_id] = game_info

            self.cache_manager.set(
                key=live_games_key,
                data=games_data,
                source="live_pipeline",
                ttl_minutes=10
            )

        except Exception as e:
            logger.error(f"Error caching game data: {e}")

    async def _cleanup_stale_games(self):
        """Remove stale game states"""
        try:
            current_time = datetime.utcnow()
            stale_threshold = timedelta(hours=6)  # Remove games not updated in 6 hours

            stale_games = []
            for game_id, game_state in self.game_states.items():
                if current_time - game_state.last_update > stale_threshold:
                    stale_games.append(game_id)

            for game_id in stale_games:
                del self.game_states[game_id]
                self.active_games.discard(game_id)
                logger.info(f"Removed stale game state: {game_id}")

            # Cleanup cache
            self.cache_manager.invalidate_pattern("live_game_*")

        except Exception as e:
            logger.error(f"Error cleaning up stale games: {e}")

    def _get_current_week(self) -> int:
        """Get current NFL week"""
        # Simple implementation - in production, this would be more sophisticated
        current_date = datetime.utcnow()

        # NFL season starts around September 8th
        season_start = datetime(current_date.year, 9, 8)
        if current_date < season_start:
            season_start = datetime(current_date.year - 1, 9, 8)

        weeks_elapsed = (current_date - season_start).days // 7
        return max(1, min(weeks_elapsed + 1, 18))

    def _game_to_event_format(self, game_data) -> Dict[str, Any]:
        """Convert game data to ESPN event format for transformation"""
        return {
            'id': game_data.game_id,
            'status': {'type': {'name': game_data.status}},
            'competitions': [{
                'competitors': [
                    {
                        'homeAway': 'home',
                        'team': {'abbreviation': game_data.home_team},
                        'score': game_data.home_score
                    },
                    {
                        'homeAway': 'away',
                        'team': {'abbreviation': game_data.away_team},
                        'score': game_data.away_score
                    }
                ],
                'situation': {
                    'period': getattr(game_data, 'quarter', 1),
                    'displayClock': getattr(game_data, 'time_remaining', '15:00'),
                    'possession': {'abbreviation': getattr(game_data, 'possession', None)},
                    'down': getattr(game_data, 'down', None),
                    'distance': getattr(game_data, 'distance', None),
                    'yardLine': getattr(game_data, 'field_position', None)
                }
            }],
            'week': {'number': getattr(game_data, 'week', self._get_current_week())}
        }

    def _update_metrics(self, response_time: float, success: bool):
        """Update pipeline metrics"""
        self.metrics.total_updates += 1

        if success:
            self.metrics.successful_updates += 1
        else:
            self.metrics.failed_updates += 1

        # Update average response time
        if self.metrics.total_updates == 1:
            self.metrics.avg_response_time = response_time
        else:
            self.metrics.avg_response_time = (
                (self.metrics.avg_response_time * (self.metrics.total_updates - 1) + response_time)
                / self.metrics.total_updates
            )

        self.metrics.last_update_time = datetime.utcnow()

        # Calculate update frequency
        if self.metrics.total_updates > 1:
            time_span = (datetime.utcnow() - self.metrics.last_update_time).total_seconds() / 60
            if time_span > 0:
                self.metrics.update_frequency = self.metrics.total_updates / time_span

    def _record_error(self, error_message: str):
        """Record error for monitoring"""
        self.error_count[error_message] += 1
        self.last_errors.append({
            'message': error_message,
            'timestamp': datetime.utcnow().isoformat(),
            'count': self.error_count[error_message]
        })

    # Public API methods

    async def subscribe_to_game(self, connection_id: str, game_id: str):
        """Subscribe a WebSocket connection to specific game updates"""
        try:
            if game_id in self.game_states:
                self.game_states[game_id].subscribers.add(connection_id)

                # Subscribe to WebSocket channel
                websocket_manager.connection_manager.subscribe_to_channel(
                    connection_id, f"game_{game_id}"
                )

                # Send current game state
                current_state = self.game_states[game_id].to_dict()
                await websocket_manager.connection_manager.send_to_connection(
                    connection_id,
                    websocket_manager.connection_manager.create_message(
                        "game_state",
                        current_state
                    )
                )

                logger.info(f"Connection {connection_id} subscribed to game {game_id}")
            else:
                logger.warning(f"Game {game_id} not found for subscription")

        except Exception as e:
            logger.error(f"Error subscribing to game {game_id}: {e}")

    async def unsubscribe_from_game(self, connection_id: str, game_id: str):
        """Unsubscribe a WebSocket connection from game updates"""
        try:
            if game_id in self.game_states:
                self.game_states[game_id].subscribers.discard(connection_id)

                # Unsubscribe from WebSocket channel
                websocket_manager.connection_manager.unsubscribe_from_channel(
                    connection_id, f"game_{game_id}"
                )

                logger.info(f"Connection {connection_id} unsubscribed from game {game_id}")

        except Exception as e:
            logger.error(f"Error unsubscribing from game {game_id}: {e}")

    def get_active_games(self) -> List[Dict[str, Any]]:
        """Get list of currently active games"""
        return [
            game_state.to_dict()
            for game_state in self.game_states.values()
        ]

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get pipeline status and metrics"""
        return {
            'status': self.status.value,
            'active_games_count': len(self.active_games),
            'total_subscribers': sum(
                len(game_state.subscribers)
                for game_state in self.game_states.values()
            ),
            'metrics': {
                'total_updates': self.metrics.total_updates,
                'success_rate': self.metrics.calculate_success_rate(),
                'avg_response_time': self.metrics.avg_response_time,
                'update_frequency': self.metrics.update_frequency,
                'last_update': self.metrics.last_update_time.isoformat() if self.metrics.last_update_time else None
            },
            'rate_limits': {
                name: limiter.get_remaining_calls()
                for name, limiter in self.rate_limiters.items()
            },
            'cache_status': self.cache_manager.get_health_status(),
            'recent_errors': list(self.last_errors)
        }

    def add_data_handler(self, handler: Callable):
        """Add custom data handler"""
        self._data_handlers.append(handler)

    def add_error_handler(self, handler: Callable):
        """Add custom error handler"""
        self._error_handlers.append(handler)


# Global pipeline instance
real_time_pipeline = RealtimeDataPipeline()