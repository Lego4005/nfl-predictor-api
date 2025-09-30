"""
Data Coordinator
Orchestrates all data ingestion services with priority-based scheduling.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

from .weather_ingestion_service import WeatherIngestionService, WeatherData
from .vegas_odds_service import VegasOddsService, VegasLine

logger = logging.getLogger(__name__)


class DataPriority(Enum):
    """Data source priority levels"""
    CRITICAL = 1  # Vegas odds, injuries
    HIGH = 2      # Weather, news
    MEDIUM = 3    # Social sentiment
    LOW = 4       # Advanced stats (weekly updates)


class RefreshSchedule(Enum):
    """Refresh intervals for different data types"""
    REALTIME = 60         # 1 minute
    FREQUENT = 1800       # 30 minutes
    HOURLY = 3600         # 1 hour
    EVERY_4_HOURS = 14400 # 4 hours
    EVERY_12_HOURS = 43200 # 12 hours
    DAILY = 86400         # 24 hours
    WEEKLY = 604800       # 7 days


class DataCoordinator:
    """
    Coordinates all data ingestion services with intelligent scheduling.

    Features:
    - Priority-based refresh scheduling
    - Automatic error handling and retries
    - Data validation layer
    - API usage optimization
    - Health monitoring
    """

    def __init__(
        self,
        weather_service: WeatherIngestionService,
        odds_service: VegasOddsService,
        supabase_client: Optional[Any] = None,
        redis_client: Optional[Any] = None
    ):
        """
        Initialize data coordinator.

        Args:
            weather_service: Weather ingestion service
            odds_service: Vegas odds service
            supabase_client: Supabase client
            redis_client: Redis client
        """
        self.weather = weather_service
        self.odds = odds_service
        self.supabase = supabase_client
        self.redis = redis_client

        # Track last successful fetches
        self.last_fetch_times: Dict[str, datetime] = {}

        # Track errors for exponential backoff
        self.error_counts: Dict[str, int] = {}

        # Health status
        self.service_health: Dict[str, bool] = {
            "weather": True,
            "odds": True,
        }

    async def gather_game_data(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        game_time: datetime
    ) -> Dict[str, Any]:
        """
        Gather ALL data for a specific game.

        Args:
            game_id: Unique game identifier
            home_team: Home team code
            away_team: Away team code
            game_time: Scheduled game time

        Returns:
            Dictionary with all game data
        """
        logger.info(f"Gathering data for game {game_id}")

        # Fetch data concurrently for speed
        weather_task = self._safe_fetch_weather(game_id, home_team, game_time)
        odds_task = self._safe_fetch_odds(game_id, home_team, away_team)

        weather, odds = await asyncio.gather(
            weather_task,
            odds_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(weather, Exception):
            logger.error(f"Weather fetch failed: {weather}")
            weather = None

        if isinstance(odds, Exception):
            logger.error(f"Odds fetch failed: {odds}")
            odds = None

        # Validate data quality
        data_quality = self._validate_data_quality({
            "weather": weather,
            "odds": odds
        })

        result = {
            "game_id": game_id,
            "weather": weather,
            "odds": odds,
            "data_quality": data_quality,
            "fetched_at": datetime.utcnow().isoformat()
        }

        # Update health monitoring
        await self._update_data_freshness("weather", weather is not None)
        await self._update_data_freshness("odds", odds is not None)

        return result

    async def _safe_fetch_weather(
        self,
        game_id: str,
        home_team: str,
        game_time: datetime
    ) -> Optional[WeatherData]:
        """Fetch weather with error handling and retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                weather = await self.weather.get_game_weather(
                    game_id,
                    home_team,
                    game_time
                )

                if weather:
                    self.error_counts["weather"] = 0
                    self.service_health["weather"] = True
                    return weather

            except Exception as e:
                logger.error(f"Weather fetch attempt {attempt + 1} failed: {e}")
                self.error_counts["weather"] = self.error_counts.get("weather", 0) + 1

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff

        # All retries failed
        self.service_health["weather"] = False
        return None

    async def _safe_fetch_odds(
        self,
        game_id: str,
        home_team: str,
        away_team: str
    ) -> Optional[List[VegasLine]]:
        """Fetch odds with error handling and retry logic"""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                odds = await self.odds.get_current_lines(
                    game_id,
                    home_team,
                    away_team
                )

                if odds:
                    self.error_counts["odds"] = 0
                    self.service_health["odds"] = True
                    return odds

            except Exception as e:
                logger.error(f"Odds fetch attempt {attempt + 1} failed: {e}")
                self.error_counts["odds"] = self.error_counts.get("odds", 0) + 1

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))

        # All retries failed
        self.service_health["odds"] = False
        return None

    def _validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data quality and freshness.

        Args:
            data: Dictionary with fetched data

        Returns:
            Quality metrics
        """
        quality = {
            "overall_score": 1.0,
            "issues": [],
            "warnings": []
        }

        # Check weather quality
        weather = data.get("weather")
        if weather:
            if weather.forecast_confidence < 0.6:
                quality["warnings"].append(
                    f"Low weather confidence: {weather.forecast_confidence:.2f}"
                )
                quality["overall_score"] *= 0.9

            if weather.hours_before_game and weather.hours_before_game > 24:
                quality["warnings"].append(
                    f"Weather forecast very early: {weather.hours_before_game}h before game"
                )
                quality["overall_score"] *= 0.95
        else:
            quality["issues"].append("Weather data missing")
            quality["overall_score"] *= 0.7

        # Check odds quality
        odds = data.get("odds")
        if odds:
            if len(odds) < 2:
                quality["warnings"].append(
                    f"Limited sportsbooks available: {len(odds)}"
                )
                quality["overall_score"] *= 0.9

            # Check for missing spread data
            missing_spreads = sum(1 for line in odds if line.spread is None)
            if missing_spreads > 0:
                quality["warnings"].append(
                    f"{missing_spreads} sportsbooks missing spread data"
                )
        else:
            quality["issues"].append("Odds data missing")
            quality["overall_score"] *= 0.6

        return quality

    async def _update_data_freshness(
        self,
        data_source: str,
        success: bool
    ):
        """Update data freshness monitor in database"""
        if not self.supabase:
            return

        try:
            status = "success" if success else "failure"
            consecutive_failures = 0 if success else self.error_counts.get(data_source, 0)

            update_data = {
                "last_attempted_fetch": datetime.utcnow().isoformat(),
                "fetch_status": status,
                "consecutive_failures": consecutive_failures,
                "is_healthy": consecutive_failures < 3,
                "updated_at": datetime.utcnow().isoformat()
            }

            if success:
                update_data["last_successful_fetch"] = datetime.utcnow().isoformat()

            await self.supabase.table("data_freshness_monitor") \
                .update(update_data) \
                .eq("data_source", data_source) \
                .execute()

        except Exception as e:
            logger.error(f"Failed to update data freshness: {e}")

    async def refresh_week_data(
        self,
        week: int,
        games: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Refresh data for all games in a week.

        Args:
            week: Week number
            games: List of game dicts with game_id, home_team, away_team, game_time

        Returns:
            Summary of refresh operation
        """
        logger.info(f"Refreshing data for week {week} ({len(games)} games)")

        results = {
            "week": week,
            "total_games": len(games),
            "successful": 0,
            "failed": 0,
            "warnings": [],
            "game_results": []
        }

        for game in games:
            try:
                game_data = await self.gather_game_data(
                    game["game_id"],
                    game["home_team"],
                    game["away_team"],
                    game["game_time"]
                )

                results["game_results"].append(game_data)

                # Check data quality
                if game_data["data_quality"]["overall_score"] >= 0.8:
                    results["successful"] += 1
                else:
                    results["warnings"].append(
                        f"Low quality data for {game['game_id']}: "
                        f"{game_data['data_quality']['overall_score']:.2f}"
                    )

            except Exception as e:
                logger.error(f"Failed to fetch data for {game['game_id']}: {e}")
                results["failed"] += 1

            # Rate limiting between games
            await asyncio.sleep(2)

        logger.info(
            f"Week {week} refresh complete: "
            f"{results['successful']} success, {results['failed']} failed"
        )

        return results

    async def scheduled_refresh_loop(
        self,
        games: List[Dict[str, Any]],
        stop_event: asyncio.Event
    ):
        """
        Continuous refresh loop with intelligent scheduling.

        Args:
            games: List of upcoming games
            stop_event: Event to signal loop termination
        """
        logger.info("Starting scheduled refresh loop")

        while not stop_event.is_set():
            try:
                current_time = datetime.utcnow()

                for game in games:
                    game_time = game["game_time"]
                    hours_until = (game_time - current_time).total_seconds() / 3600

                    # Skip past games
                    if hours_until < 0:
                        continue

                    # Determine refresh schedule based on time until game
                    should_refresh = False

                    if hours_until <= 1:
                        # 1 hour before: refresh every 5 minutes
                        refresh_interval = 300
                        should_refresh = True
                    elif hours_until <= 4:
                        # 4 hours before: refresh every 30 minutes
                        refresh_interval = RefreshSchedule.FREQUENT.value
                        should_refresh = self._should_refresh(
                            game["game_id"],
                            refresh_interval
                        )
                    elif hours_until <= 12:
                        # 12 hours before: refresh every hour
                        refresh_interval = RefreshSchedule.HOURLY.value
                        should_refresh = self._should_refresh(
                            game["game_id"],
                            refresh_interval
                        )
                    else:
                        # More than 12 hours: refresh every 4 hours
                        refresh_interval = RefreshSchedule.EVERY_4_HOURS.value
                        should_refresh = self._should_refresh(
                            game["game_id"],
                            refresh_interval
                        )

                    if should_refresh:
                        await self.gather_game_data(
                            game["game_id"],
                            game["home_team"],
                            game["away_team"],
                            game_time
                        )

                        self.last_fetch_times[game["game_id"]] = current_time

                        # Rate limiting
                        await asyncio.sleep(2)

                # Sleep before next iteration
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in refresh loop: {e}")
                await asyncio.sleep(60)

        logger.info("Scheduled refresh loop stopped")

    def _should_refresh(self, game_id: str, interval: int) -> bool:
        """Check if game data should be refreshed based on interval"""
        last_fetch = self.last_fetch_times.get(game_id)

        if not last_fetch:
            return True

        time_since_fetch = (datetime.utcnow() - last_fetch).total_seconds()
        return time_since_fetch >= interval

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        return {
            "services": self.service_health,
            "error_counts": self.error_counts,
            "api_usage": {
                "weather": self.weather.get_api_usage(),
                "odds": self.odds.get_api_usage()
            },
            "overall_healthy": all(self.service_health.values()),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalous data that may indicate errors"""
        anomalies = []

        # Check for stale data
        if self.supabase:
            try:
                result = await self.supabase.table("data_freshness_monitor") \
                    .select("*") \
                    .eq("is_healthy", False) \
                    .execute()

                for row in result.data:
                    anomalies.append({
                        "type": "stale_data",
                        "source": row["data_source"],
                        "consecutive_failures": row["consecutive_failures"],
                        "last_success": row.get("last_successful_fetch")
                    })

            except Exception as e:
                logger.error(f"Error checking data freshness: {e}")

        # Check for significant line movements
        try:
            movements = await self.odds.detect_significant_movements(threshold=3.0)
            for movement in movements:
                anomalies.append({
                    "type": "significant_line_movement",
                    "game_id": movement["game_id"],
                    "movement": movement["movement"],
                    "alert_level": movement["alert_level"]
                })
        except Exception as e:
            logger.error(f"Error detecting line movements: {e}")

        return anomalies