"""
Vegas Odds Service
Fetches betting lines from The Odds API with line movement detection.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class VegasLine(BaseModel):
    """Vegas line data model matching database schema"""
    game_id: str
    sportsbook: str
    spread: Optional[float] = None
    spread_odds_home: Optional[str] = None
    spread_odds_away: Optional[str] = None
    moneyline_home: Optional[int] = None
    moneyline_away: Optional[int] = None
    total: Optional[float] = None
    total_over_odds: Optional[str] = None
    total_under_odds: Optional[str] = None
    opening_spread: Optional[float] = None
    opening_total: Optional[float] = None
    line_movement: float = 0.0
    sharp_money_indicator: bool = False
    public_bet_percentage_home: Optional[float] = None
    public_bet_percentage_away: Optional[float] = None
    money_percentage_home: Optional[float] = None
    data_source: str = "TheOddsAPI"
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class VegasOddsService:
    """
    Service for fetching Vegas odds from The Odds API.

    Features:
    - Free tier: 500 requests/day
    - Fetches from multiple sportsbooks
    - Detects line movements > 3 points
    - Identifies sharp money (line moves against public)
    - Redis caching to conserve API calls
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        supabase_client: Optional[Any] = None,
        redis_client: Optional[Any] = None
    ):
        """
        Initialize Vegas odds service.

        Args:
            api_key: The Odds API key (or from env var)
            supabase_client: Supabase client for database storage
            redis_client: Redis client for caching
        """
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("The Odds API key is required")

        self.supabase = supabase_client
        self.redis = redis_client
        self.base_url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
        self.request_count = 0
        self.max_daily_requests = 500

        # Preferred sportsbooks (most liquid markets)
        self.preferred_books = [
            "draftkings",
            "fanduel",
            "betmgm",
            "caesars",
            "pinnacle"  # Pinnacle is considered "sharp" book
        ]

    def _american_odds_to_probability(self, odds: int) -> float:
        """Convert American odds to implied probability"""
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)

    def _detect_sharp_money(
        self,
        line_movement: float,
        public_percentage: Optional[float]
    ) -> bool:
        """
        Detect sharp money indicator.

        Sharp money = line moves AGAINST public betting percentage.
        Example: 70% of public on Team A, but line moves in favor of Team B.
        """
        if public_percentage is None:
            return False

        # Sharp money if:
        # - Public is >60% on home team but line moved toward away team (negative movement)
        # - OR public is >60% on away team but line moved toward home team (positive movement)
        if public_percentage > 0.60 and line_movement < -1.0:
            return True
        if public_percentage < 0.40 and line_movement > 1.0:
            return True

        return False

    async def _fetch_odds_data(
        self,
        regions: str = "us",
        markets: str = "h2h,spreads,totals"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch odds from The Odds API.

        Args:
            regions: Geographic regions (us, uk, eu, au)
            markets: Bet types (h2h=moneyline, spreads, totals)

        Returns:
            Raw API response or None
        """
        try:
            # Check rate limit
            if self.request_count >= self.max_daily_requests:
                logger.error("The Odds API rate limit reached")
                return None

            url = f"{self.base_url}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": regions,
                "markets": markets,
                "oddsFormat": "american",
                "dateFormat": "iso"
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                # Track usage from response headers
                remaining = response.headers.get("x-requests-remaining")
                if remaining:
                    logger.info(f"Odds API requests remaining: {remaining}")

                self.request_count += 1
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching odds: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching odds: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching odds: {e}")
            return None

    async def get_current_lines(
        self,
        game_id: str,
        home_team: str,
        away_team: str
    ) -> List[VegasLine]:
        """
        Get current betting lines for a specific game.

        Args:
            game_id: Unique game identifier
            home_team: Home team code
            away_team: Away team code

        Returns:
            List of VegasLine objects (one per sportsbook)
        """
        # Check Redis cache first (30 min TTL)
        if self.redis:
            cache_key = f"odds:{game_id}"
            cached = await self.redis.get(cache_key)
            if cached:
                logger.info(f"Odds cache hit for {game_id}")
                import json
                cached_data = json.loads(cached)
                return [VegasLine(**line) for line in cached_data]

        # Fetch from API
        raw_data = await self._fetch_odds_data()
        if not raw_data:
            return []

        lines = []

        # Find our game in the response
        for event in raw_data:
            # Match by team names (API uses full names, we need to map)
            if not self._is_our_game(event, home_team, away_team):
                continue

            # Parse each sportsbook
            for bookmaker in event.get("bookmakers", []):
                book_name = bookmaker["key"]

                # Skip if not in preferred books
                if book_name not in self.preferred_books:
                    continue

                markets = bookmaker.get("markets", [])

                # Parse spread
                spread_data = next((m for m in markets if m["key"] == "spreads"), None)
                spread = None
                spread_home_odds = None
                spread_away_odds = None

                if spread_data:
                    outcomes = spread_data.get("outcomes", [])
                    home_outcome = next((o for o in outcomes if o["name"] == event["home_team"]), None)
                    away_outcome = next((o for o in outcomes if o["name"] == event["away_team"]), None)

                    if home_outcome:
                        spread = home_outcome.get("point")
                        spread_home_odds = str(home_outcome.get("price", ""))
                    if away_outcome:
                        spread_away_odds = str(away_outcome.get("price", ""))

                # Parse moneyline
                h2h_data = next((m for m in markets if m["key"] == "h2h"), None)
                ml_home = None
                ml_away = None

                if h2h_data:
                    outcomes = h2h_data.get("outcomes", [])
                    home_outcome = next((o for o in outcomes if o["name"] == event["home_team"]), None)
                    away_outcome = next((o for o in outcomes if o["name"] == event["away_team"]), None)

                    if home_outcome:
                        ml_home = home_outcome.get("price")
                    if away_outcome:
                        ml_away = away_outcome.get("price")

                # Parse totals
                totals_data = next((m for m in markets if m["key"] == "totals"), None)
                total = None
                total_over_odds = None
                total_under_odds = None

                if totals_data:
                    outcomes = totals_data.get("outcomes", [])
                    over_outcome = next((o for o in outcomes if o["name"] == "Over"), None)
                    under_outcome = next((o for o in outcomes if o["name"] == "Under"), None)

                    if over_outcome:
                        total = over_outcome.get("point")
                        total_over_odds = str(over_outcome.get("price", ""))
                    if under_outcome:
                        total_under_odds = str(under_outcome.get("price", ""))

                # Get opening lines from database (if available)
                opening_spread = await self._get_opening_spread(game_id, book_name)
                line_movement = 0.0
                if opening_spread is not None and spread is not None:
                    line_movement = spread - opening_spread

                # Detect sharp money
                # (Would need public betting percentages from another source)
                sharp_indicator = self._detect_sharp_money(line_movement, None)

                line = VegasLine(
                    game_id=game_id,
                    sportsbook=book_name,
                    spread=spread,
                    spread_odds_home=spread_home_odds,
                    spread_odds_away=spread_away_odds,
                    moneyline_home=ml_home,
                    moneyline_away=ml_away,
                    total=total,
                    total_over_odds=total_over_odds,
                    total_under_odds=total_under_odds,
                    opening_spread=opening_spread,
                    line_movement=round(line_movement, 1),
                    sharp_money_indicator=sharp_indicator
                )

                lines.append(line)

        # Cache for 30 minutes
        if self.redis and lines:
            cache_data = [line.model_dump(mode='json') for line in lines]
            await self.redis.setex(
                f"odds:{game_id}",
                1800,  # 30 minutes
                str(cache_data)
            )

        # Store in database
        if self.supabase and lines:
            for line in lines:
                try:
                    await self._store_odds_data(line)
                except Exception as e:
                    logger.error(f"Failed to store odds data: {e}")

        logger.info(f"Fetched {len(lines)} lines for {game_id}")
        return lines

    def _is_our_game(
        self,
        event: Dict[str, Any],
        home_team: str,
        away_team: str
    ) -> bool:
        """Check if API event matches our game"""
        # Simple team name matching
        # In production, would need more sophisticated matching
        event_home = event.get("home_team", "").lower()
        event_away = event.get("away_team", "").lower()

        return (
            home_team.lower() in event_home and
            away_team.lower() in event_away
        )

    async def _get_opening_spread(
        self,
        game_id: str,
        sportsbook: str
    ) -> Optional[float]:
        """Get opening spread from database"""
        if not self.supabase:
            return None

        try:
            result = await self.supabase.table("vegas_lines") \
                .select("spread") \
                .eq("game_id", game_id) \
                .eq("sportsbook", sportsbook) \
                .order("fetched_at", desc=False) \
                .limit(1) \
                .execute()

            if result.data:
                return result.data[0].get("spread")
        except Exception as e:
            logger.error(f"Error fetching opening spread: {e}")

        return None

    async def _store_odds_data(self, line: VegasLine):
        """Store odds data in Supabase"""
        data = line.model_dump()
        data["fetched_at"] = data["fetched_at"].isoformat()

        await self.supabase.table("vegas_lines").insert(data).execute()

    async def detect_significant_movements(
        self,
        threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Detect significant line movements (>3 points).

        Args:
            threshold: Minimum point movement to flag

        Returns:
            List of games with significant movements
        """
        if not self.supabase:
            return []

        try:
            # Query recent line movements
            result = await self.supabase.table("vegas_lines") \
                .select("game_id, sportsbook, line_movement, spread, opening_spread") \
                .gte("line_movement", threshold) \
                .or_(f"line_movement.lte.-{threshold}") \
                .order("fetched_at", desc=True) \
                .limit(50) \
                .execute()

            movements = []
            for row in result.data:
                movements.append({
                    "game_id": row["game_id"],
                    "sportsbook": row["sportsbook"],
                    "opening_spread": row["opening_spread"],
                    "current_spread": row["spread"],
                    "movement": row["line_movement"],
                    "alert_level": "significant" if abs(row["line_movement"]) > 5 else "notable"
                })

            return movements

        except Exception as e:
            logger.error(f"Error detecting line movements: {e}")
            return []

    async def fetch_all_week_odds(self, week: int) -> List[VegasLine]:
        """
        Fetch odds for all games in a specific week.

        Args:
            week: NFL week number

        Returns:
            List of all VegasLine objects for the week
        """
        # Would need game schedule from another source
        # This is a placeholder showing the pattern

        all_lines = []

        # Example: Fetch from game schedule
        # games = await self._get_week_schedule(week)
        #
        # for game in games:
        #     lines = await self.get_current_lines(
        #         game["game_id"],
        #         game["home_team"],
        #         game["away_team"]
        #     )
        #     all_lines.extend(lines)
        #
        #     # Rate limit: 1 request per 2 seconds
        #     await asyncio.sleep(2)

        return all_lines

    def get_api_usage(self) -> Dict[str, Any]:
        """Get current API usage statistics"""
        return {
            "requests_today": self.request_count,
            "daily_limit": self.max_daily_requests,
            "remaining": self.max_daily_requests - self.request_count,
            "percentage_used": (self.request_count / self.max_daily_requests) * 100
        }