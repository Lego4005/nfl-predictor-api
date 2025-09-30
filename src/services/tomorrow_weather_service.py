"""
Tomorrow.io Weather Service
Fetches weather data using Tomorrow.io API for NFL game predictions.
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import httpx
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class WeatherData(BaseModel):
    """Weather data model matching database schema"""
    game_id: str
    temperature: Optional[float] = None  # Fahrenheit
    wind_speed: Optional[float] = None  # MPH
    wind_direction: Optional[str] = None
    precipitation: Optional[float] = None  # Inches
    humidity: Optional[float] = None  # Percentage
    conditions: Optional[str] = None
    field_conditions: Optional[str] = None
    dome_stadium: bool = False
    forecast_confidence: float = 0.0
    data_source: str = "Tomorrow.io"
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    game_time: Optional[datetime] = None
    hours_before_game: Optional[int] = None


class TomorrowWeatherService:
    """
    Service for fetching weather data from Tomorrow.io API.

    Features:
    - Real-time and forecast weather data
    - High accuracy predictions
    - Converts to imperial units
    - Caches results to minimize API calls
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        supabase_client: Optional[Any] = None,
        redis_client: Optional[Any] = None
    ):
        """
        Initialize Tomorrow.io weather service.

        Args:
            api_key: Tomorrow.io API key (or from env var)
            supabase_client: Supabase client for database storage
            redis_client: Redis client for caching
        """
        self.api_key = api_key or os.getenv("TOMORROW_IO_API_KEY")
        if not self.api_key:
            raise ValueError("Tomorrow.io API key is required")

        self.supabase = supabase_client
        self.redis = redis_client
        self.base_url = "https://api.tomorrow.io/v4/weather"

        # Stadium locations (lat, lon)
        self.stadium_locations = self._load_stadium_locations()

    def _load_stadium_locations(self) -> Dict[str, tuple]:
        """Load NFL stadium coordinates"""
        return {
            "ARI": (33.5276, -112.2626),  # State Farm Stadium
            "ATL": (33.7554, -84.4008),    # Mercedes-Benz Stadium
            "BAL": (39.2780, -76.6227),    # M&T Bank Stadium
            "BUF": (42.7738, -78.7870),    # Highmark Stadium
            "CAR": (35.2258, -80.8528),    # Bank of America Stadium
            "CHI": (41.8623, -87.6167),    # Soldier Field
            "CIN": (39.0954, -84.5160),    # Paycor Stadium
            "CLE": (41.5061, -81.6995),    # Cleveland Browns Stadium
            "DAL": (32.7473, -97.0945),    # AT&T Stadium (dome)
            "DEN": (39.7439, -105.0201),   # Empower Field
            "DET": (42.3400, -83.0456),    # Ford Field (dome)
            "GB": (44.5013, -88.0622),     # Lambeau Field
            "HOU": (29.6847, -95.4107),    # NRG Stadium (retractable)
            "IND": (39.7601, -86.1639),    # Lucas Oil Stadium (retractable)
            "JAX": (30.3239, -81.6373),    # TIAA Bank Field
            "KC": (39.0489, -94.4839),     # ARROWHEAD Stadium
            "LAC": (33.8644, -118.3392),   # SoFi Stadium (indoor-outdoor)
            "LAR": (33.8644, -118.3392),   # SoFi Stadium
            "LV": (36.0909, -115.1833),    # Allegiant Stadium (dome)
            "MIA": (25.9580, -80.2389),    # Hard Rock Stadium
            "MIN": (44.9738, -93.2577),    # U.S. Bank Stadium (dome)
            "NE": (42.0909, -71.2643),     # Gillette Stadium
            "NO": (29.9511, -90.0812),     # Caesars Superdome (dome)
            "NYG": (40.8128, -74.0742),    # MetLife Stadium
            "NYJ": (40.8128, -74.0742),    # MetLife Stadium
            "PHI": (39.9008, -75.1675),    # Lincoln Financial Field
            "PIT": (40.4468, -80.0158),    # Acrisure Stadium
            "SF": (37.4030, -121.9700),    # Levi's Stadium
            "SEA": (47.5952, -122.3316),   # Lumen Field
            "TB": (27.9759, -82.5033),     # Raymond James Stadium
            "TEN": (36.1665, -86.7713),    # Nissan Stadium
            "WAS": (38.9076, -76.8645),    # FedExField
        }

    def _is_dome_stadium(self, team: str) -> bool:
        """Check if stadium is a dome (weather doesn't matter)"""
        dome_teams = {"DAL", "DET", "LV", "MIN", "NO"}
        return team in dome_teams

    def _celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius to Fahrenheit"""
        return celsius * 9/5 + 32

    def _ms_to_mph(self, ms: float) -> float:
        """Convert meters/sec to miles/hour"""
        return ms * 2.23694

    def _mm_to_inches(self, mm: float) -> float:
        """Convert millimeters to inches"""
        return mm * 0.0393701

    def _wind_degrees_to_direction(self, degrees: float) -> str:
        """Convert wind degrees to cardinal direction"""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = round(degrees / 45) % 8
        return directions[idx]

    def _weather_code_to_description(self, code: int) -> str:
        """Convert Tomorrow.io weather code to description"""
        codes = {
            0: "Unknown",
            1000: "Clear",
            1100: "Mostly Clear",
            1101: "Partly Cloudy",
            1102: "Mostly Cloudy",
            1001: "Cloudy",
            2000: "Fog",
            2100: "Light Fog",
            4000: "Drizzle",
            4001: "Rain",
            4200: "Light Rain",
            4201: "Heavy Rain",
            5000: "Snow",
            5001: "Flurries",
            5100: "Light Snow",
            5101: "Heavy Snow",
            6000: "Freezing Drizzle",
            6001: "Freezing Rain",
            6200: "Light Freezing Rain",
            6201: "Heavy Freezing Rain",
            7000: "Ice Pellets",
            7101: "Heavy Ice Pellets",
            7102: "Light Ice Pellets",
            8000: "Thunderstorm",
        }
        return codes.get(code, "Unknown")

    def _determine_field_conditions(
        self,
        temp: float,
        precipitation: float,
        conditions: str
    ) -> str:
        """Determine field conditions from weather"""
        conditions_lower = conditions.lower()
        if "snow" in conditions_lower or "ice" in conditions_lower:
            return "snow-covered"
        elif "freezing" in conditions_lower:
            return "frozen"
        elif precipitation > 0.5:
            return "muddy"
        elif precipitation > 0.1:
            return "wet"
        elif temp < 32:
            return "frozen"
        else:
            return "dry"

    async def _fetch_weather_data(
        self,
        lat: float,
        lon: float,
        game_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data from Tomorrow.io API.

        Args:
            lat: Latitude
            lon: Longitude
            game_time: Scheduled game time

        Returns:
            Weather data dict or None if error
        """
        try:
            # Use forecast endpoint
            url = f"{self.base_url}/forecast"

            # Format location as "lat,lon"
            location = f"{lat},{lon}"

            params = {
                "location": location,
                "apikey": self.api_key,
                "units": "metric"  # We'll convert to imperial
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                # Get timelines data
                timelines = data.get("timelines", {})
                hourly = timelines.get("hourly", [])

                if not hourly:
                    logger.error("No hourly forecast data available")
                    return None

                # Find forecast closest to game time
                # Ensure game_time is timezone-aware
                if game_time.tzinfo is None:
                    game_time = game_time.replace(tzinfo=timezone.utc)

                closest_forecast = min(
                    hourly,
                    key=lambda x: abs(
                        datetime.fromisoformat(x["time"].replace("Z", "+00:00")) - game_time
                    )
                )

                return closest_forecast

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching weather: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
            return None

    async def get_game_weather(
        self,
        game_id: str,
        home_team: str,
        game_time: datetime
    ) -> Optional[WeatherData]:
        """
        Get weather for a specific game.

        Args:
            game_id: Unique game identifier
            home_team: Home team code (e.g., 'KC')
            game_time: Scheduled game time

        Returns:
            WeatherData object or None
        """
        # Check if dome stadium (skip API call)
        if self._is_dome_stadium(home_team):
            return WeatherData(
                game_id=game_id,
                temperature=72.0,
                wind_speed=0.0,
                humidity=50.0,
                conditions="Indoor",
                field_conditions="dry",
                dome_stadium=True,
                forecast_confidence=1.0,
                game_time=game_time,
                hours_before_game=0
            )

        # Check Redis cache first
        if self.redis:
            cache_key = f"weather:tomorrow:{game_id}:{datetime.now(timezone.utc).hour}"
            cached = await self.redis.get(cache_key)
            if cached:
                logger.info(f"Weather cache hit for {game_id}")
                return WeatherData.model_validate_json(cached)

        # Get stadium location
        if home_team not in self.stadium_locations:
            logger.error(f"Unknown stadium location for team {home_team}")
            return None

        lat, lon = self.stadium_locations[home_team]

        # Fetch from API
        raw_data = await self._fetch_weather_data(lat, lon, game_time)
        if not raw_data:
            return None

        # Parse values from Tomorrow.io response
        values = raw_data.get("values", {})

        # Extract and convert values
        temp_c = values.get("temperature", 0)
        temp_f = self._celsius_to_fahrenheit(temp_c)

        wind_speed_ms = values.get("windSpeed", 0)
        wind_mph = self._ms_to_mph(wind_speed_ms)

        wind_direction_deg = values.get("windDirection", 0)
        wind_direction = self._wind_degrees_to_direction(wind_direction_deg)

        precip_mm = values.get("precipitationIntensity", 0)
        precip_inches = self._mm_to_inches(precip_mm)

        humidity = values.get("humidity", 50)

        weather_code = values.get("weatherCode", 0)
        conditions_desc = self._weather_code_to_description(weather_code)

        field_conds = self._determine_field_conditions(
            temp_f,
            precip_inches,
            conditions_desc
        )

        # Calculate confidence based on hours until game
        # Ensure game_time is timezone-aware
        if game_time.tzinfo is None:
            game_time = game_time.replace(tzinfo=timezone.utc)
        hours_until = (game_time - datetime.now(timezone.utc)).total_seconds() / 3600
        if hours_until < 1:
            confidence = 0.95
        elif hours_until < 4:
            confidence = 0.90
        elif hours_until < 12:
            confidence = 0.85
        elif hours_until < 48:
            confidence = 0.75
        else:
            confidence = 0.65

        weather_data = WeatherData(
            game_id=game_id,
            temperature=round(temp_f, 1),
            wind_speed=round(wind_mph, 1),
            wind_direction=wind_direction,
            precipitation=round(precip_inches, 2),
            humidity=round(humidity, 1),
            conditions=conditions_desc,
            field_conditions=field_conds,
            dome_stadium=False,
            forecast_confidence=confidence,
            game_time=game_time,
            hours_before_game=int(hours_until)
        )

        # Cache for 1 hour
        if self.redis:
            await self.redis.setex(
                f"weather:tomorrow:{game_id}:{datetime.now(timezone.utc).hour}",
                3600,
                weather_data.model_dump_json()
            )

        # Store in database
        if self.supabase:
            try:
                await self._store_weather_data(weather_data)
            except Exception as e:
                logger.error(f"Failed to store weather data: {e}")

        logger.info(
            f"Fetched weather for {game_id}: {temp_f:.1f}°F, "
            f"{wind_mph:.1f} mph wind, {conditions_desc}"
        )

        return weather_data

    async def _store_weather_data(self, weather: WeatherData):
        """Store weather data in Supabase"""
        data = weather.model_dump()
        data["fetched_at"] = data["fetched_at"].isoformat()
        if data.get("game_time"):
            data["game_time"] = data["game_time"].isoformat()

        await self.supabase.table("weather_conditions").upsert(data).execute()

    async def fetch_scheduled_weather(
        self,
        games: List[Dict[str, Any]],
        hours_before: List[int] = [48, 24, 12, 4, 1]
    ) -> List[WeatherData]:
        """
        Fetch weather for multiple games at scheduled intervals.

        Args:
            games: List of game dicts with 'game_id', 'home_team', 'game_time'
            hours_before: Hours before game to fetch weather

        Returns:
            List of WeatherData objects
        """
        results = []

        for game in games:
            game_time = game["game_time"]
            if game_time.tzinfo is None:
                game_time = game_time.replace(tzinfo=timezone.utc)
            hours_until = (game_time - datetime.now(timezone.utc)).total_seconds() / 3600

            # Only fetch if we're at a scheduled checkpoint
            should_fetch = False
            for checkpoint in hours_before:
                if abs(hours_until - checkpoint) < 0.5:  # Within 30 min of checkpoint
                    should_fetch = True
                    break

            if not should_fetch:
                continue

            weather = await self.get_game_weather(
                game["game_id"],
                game["home_team"],
                game_time
            )

            if weather:
                results.append(weather)

            # Rate limiting: 1 request per second to be safe
            await asyncio.sleep(1)

        return results

    async def bulk_fetch_weather_for_week(
        self,
        games: List[Dict[str, Any]]
    ) -> List[WeatherData]:
        """
        Fetch weather for all games in a week.

        Args:
            games: List of game dicts with 'game_id', 'home_team', 'game_time'

        Returns:
            List of WeatherData objects
        """
        results = []

        for game in games:
            weather = await self.get_game_weather(
                game["game_id"],
                game["home_team"],
                game["game_time"]
            )

            if weather:
                results.append(weather)

            # Rate limiting
            await asyncio.sleep(0.5)

        logger.info(f"Fetched weather for {len(results)} games")
        return results