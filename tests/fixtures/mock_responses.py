"""
Mock API responses and WebSocket messages for testing.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import json
import uuid
from dataclasses import asdict

from .database_fixtures import GameFixture, NFLTestDataFactory


class MockWebSocketMessages:
    """Mock WebSocket message generators."""

    @staticmethod
    def game_update_message(game_id: str,
                          quarter: int = 1,
                          time_remaining: str = "15:00",
                          home_score: int = 0,
                          away_score: int = 0) -> Dict[str, Any]:
        """Generate mock game update WebSocket message."""
        return {
            "type": "game_update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "game_id": game_id,
                "quarter": quarter,
                "time_remaining": time_remaining,
                "home_score": home_score,
                "away_score": away_score,
                "status": "live" if quarter > 0 else "scheduled",
                "last_play": {
                    "type": "rushing",
                    "description": "5 yard rush by RB for first down",
                    "yards": 5,
                    "down": 1,
                    "distance": 10,
                    "field_position": "OWN 35"
                } if quarter > 0 else None
            }
        }

    @staticmethod
    def prediction_update_message(game_id: str,
                                home_win_prob: float = 0.65,
                                confidence: float = 0.82) -> Dict[str, Any]:
        """Generate mock prediction update WebSocket message."""
        return {
            "type": "prediction_update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "game_id": game_id,
                "model_version": "v2.1",
                "home_win_probability": home_win_prob,
                "away_win_probability": 1 - home_win_prob,
                "spread_prediction": -3.5,
                "total_prediction": 48.5,
                "confidence_score": confidence,
                "changed_factors": ["injury_update", "weather_change"],
                "feature_importance": {
                    "current_score": 0.35,
                    "time_remaining": 0.25,
                    "field_position": 0.15,
                    "momentum": 0.12,
                    "weather": 0.08,
                    "injuries": 0.05
                }
            }
        }

    @staticmethod
    def system_health_message(status: str = "healthy") -> Dict[str, Any]:
        """Generate mock system health WebSocket message."""
        return {
            "type": "system_health",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "status": status,
                "services": {
                    "api": {"status": "healthy", "response_time": 120},
                    "database": {"status": "healthy", "connection_count": 15},
                    "redis": {"status": "healthy", "memory_usage": "45%"},
                    "ml_models": {"status": "healthy", "last_prediction": "2024-09-14T15:30:00Z"},
                    "websocket": {"status": "healthy", "active_connections": 234}
                },
                "metrics": {
                    "cpu_usage": 25.6,
                    "memory_usage": 68.2,
                    "disk_usage": 42.1,
                    "network_io": {"in": "1.2MB/s", "out": "3.4MB/s"}
                }
            }
        }

    @staticmethod
    def error_message(error_type: str = "api_error",
                     message: str = "Failed to fetch data") -> Dict[str, Any]:
        """Generate mock error WebSocket message."""
        return {
            "type": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "error_type": error_type,
                "message": message,
                "severity": "warning",
                "retry_available": True,
                "retry_delay": 30,
                "error_code": "E001"
            }
        }


class MockExternalAPIs:
    """Mock external API responses."""

    def __init__(self):
        self.factory = NFLTestDataFactory()

    def nfl_rapid_api_response(self, season: int = 2024, week: int = 1) -> Dict[str, Any]:
        """Mock NFL RapidAPI response."""
        games = [
            self.factory.create_game(
                home_team="KC", away_team="DET",
                season=season, week=week
            ),
            self.factory.create_game(
                home_team="BUF", away_team="MIA",
                season=season, week=week
            )
        ]

        return {
            "success": True,
            "data": [
                {
                    "game_id": game.game_id,
                    "commence_time": game.game_date.isoformat(),
                    "home_team": game.home_team_id,
                    "away_team": game.away_team_id,
                    "bookmakers": [
                        {
                            "key": "draftkings",
                            "title": "DraftKings",
                            "markets": [
                                {
                                    "key": "h2h",
                                    "outcomes": [
                                        {"name": game.home_team_id, "price": 1.85},
                                        {"name": game.away_team_id, "price": 1.95}
                                    ]
                                },
                                {
                                    "key": "spreads",
                                    "outcomes": [
                                        {"name": game.home_team_id, "price": 1.91, "point": -3.5},
                                        {"name": game.away_team_id, "price": 1.91, "point": 3.5}
                                    ]
                                },
                                {
                                    "key": "totals",
                                    "outcomes": [
                                        {"name": "Over", "price": 1.91, "point": 48.5},
                                        {"name": "Under", "price": 1.91, "point": 48.5}
                                    ]
                                }
                            ]
                        }
                    ]
                }
                for game in games
            ]
        }

    def espn_api_response(self, season: int = 2024, week: int = 1) -> Dict[str, Any]:
        """Mock ESPN API response."""
        return {
            "sports": [{
                "leagues": [{
                    "season": {
                        "year": season,
                        "type": 2,
                        "slug": "regular-season"
                    },
                    "events": [
                        {
                            "id": f"401547{week:02d}01",
                            "uid": f"s:20~l:28~e:401547{week:02d}01",
                            "date": (datetime.now() + timedelta(days=1)).isoformat(),
                            "name": "Kansas City Chiefs at Detroit Lions",
                            "shortName": "KC @ DET",
                            "season": {"year": season, "type": 2},
                            "week": {"number": week},
                            "competitions": [{
                                "id": f"401547{week:02d}01",
                                "uid": f"s:20~l:28~c:401547{week:02d}01",
                                "date": (datetime.now() + timedelta(days=1)).isoformat(),
                                "attendance": 0,
                                "type": {"id": "1"},
                                "timeValid": True,
                                "neutralSite": False,
                                "conferenceCompetition": False,
                                "playByPlayAvailable": True,
                                "recent": False,
                                "venue": {
                                    "id": "3558",
                                    "fullName": "Ford Field",
                                    "address": {"city": "Detroit", "state": "MI"}
                                },
                                "competitors": [
                                    {
                                        "id": "8",
                                        "uid": "s:20~l:28~t:8",
                                        "type": "team",
                                        "order": 0,
                                        "homeAway": "away",
                                        "team": {
                                            "id": "8",
                                            "uid": "s:20~l:28~t:8",
                                            "slug": "kansas-city-chiefs",
                                            "location": "Kansas City",
                                            "name": "Chiefs",
                                            "abbreviation": "KC",
                                            "displayName": "Kansas City Chiefs",
                                            "shortDisplayName": "Chiefs",
                                            "color": "e31837",
                                            "alternateColor": "ffb81c"
                                        },
                                        "score": "0"
                                    },
                                    {
                                        "id": "8",
                                        "uid": "s:20~l:28~t:8",
                                        "type": "team",
                                        "order": 1,
                                        "homeAway": "home",
                                        "team": {
                                            "id": "8",
                                            "uid": "s:20~l:28~t:8",
                                            "slug": "detroit-lions",
                                            "location": "Detroit",
                                            "name": "Lions",
                                            "abbreviation": "DET",
                                            "displayName": "Detroit Lions",
                                            "shortDisplayName": "Lions",
                                            "color": "0076b6",
                                            "alternateColor": "b0b7bc"
                                        },
                                        "score": "0"
                                    }
                                ],
                                "status": {
                                    "clock": 0.0,
                                    "displayClock": "0:00",
                                    "period": 0,
                                    "type": {
                                        "id": "1",
                                        "name": "STATUS_SCHEDULED",
                                        "state": "pre",
                                        "completed": False,
                                        "description": "Scheduled",
                                        "detail": "9/14 - 1:00 PM EST",
                                        "shortDetail": "9/14 - 1:00 PM EST"
                                    }
                                }
                            }]
                        }
                    ]
                }]
            }]
        }

    def weather_api_response(self, city: str = "Detroit") -> Dict[str, Any]:
        """Mock weather API response."""
        return {
            "location": {
                "name": city,
                "region": "Michigan" if city == "Detroit" else "Unknown",
                "country": "United States of America",
                "lat": 42.33 if city == "Detroit" else 40.0,
                "lon": -83.05 if city == "Detroit" else -80.0,
                "tz_id": "America/New_York",
                "localtime_epoch": int(datetime.now().timestamp()),
                "localtime": datetime.now().strftime("%Y-%m-%d %H:%M")
            },
            "current": {
                "last_updated_epoch": int(datetime.now().timestamp()),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "temp_c": 22.2,
                "temp_f": 72.0,
                "is_day": 1,
                "condition": {
                    "text": "Clear",
                    "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                    "code": 1000
                },
                "wind_mph": 8.1,
                "wind_kph": 13.0,
                "wind_degree": 240,
                "wind_dir": "WSW",
                "pressure_mb": 1020.0,
                "pressure_in": 30.12,
                "precip_mm": 0.0,
                "precip_in": 0.0,
                "humidity": 65,
                "cloud": 0,
                "feelslike_c": 24.1,
                "feelslike_f": 75.4,
                "vis_km": 16.0,
                "vis_miles": 10.0,
                "uv": 5.0,
                "gust_mph": 12.3,
                "gust_kph": 19.8
            },
            "forecast": {
                "forecastday": [
                    {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "date_epoch": int(datetime.now().timestamp()),
                        "day": {
                            "maxtemp_c": 25.1,
                            "maxtemp_f": 77.2,
                            "mintemp_c": 18.3,
                            "mintemp_f": 65.0,
                            "avgtemp_c": 21.7,
                            "avgtemp_f": 71.1,
                            "maxwind_mph": 10.3,
                            "maxwind_kph": 16.6,
                            "totalprecip_mm": 0.0,
                            "totalprecip_in": 0.0,
                            "totalsnow_cm": 0.0,
                            "avgvis_km": 16.0,
                            "avgvis_miles": 9.9,
                            "avghumidity": 65.0,
                            "daily_will_it_rain": 0,
                            "daily_chance_of_rain": 0,
                            "daily_will_it_snow": 0,
                            "daily_chance_of_snow": 0,
                            "condition": {
                                "text": "Clear",
                                "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                                "code": 1000
                            },
                            "uv": 5.0
                        }
                    }
                ]
            }
        }

    def sportsdata_api_response(self, season: int = 2024) -> Dict[str, Any]:
        """Mock SportsData.io API response."""
        return [
            {
                "GameKey": f"{season}REG01KCDET",
                "SeasonType": 1,
                "Season": season,
                "Week": 1,
                "Date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S"),
                "AwayTeam": "KC",
                "HomeTeam": "DET",
                "Channel": "CBS",
                "PointSpread": 3.5,
                "OverUnder": 48.5,
                "Stadium": "Ford Field",
                "Playing": "Scheduled",
                "Started": False,
                "IsInProgress": False,
                "IsOver": False,
                "Has1stQuarterStarted": False,
                "Has2ndQuarterStarted": False,
                "Has3rdQuarterStarted": False,
                "Has4thQuarterStarted": False,
                "IsOvertime": False,
                "DownAndDistance": "",
                "QuarterDescription": "",
                "PossessionTeam": None,
                "RedZoneTeam": None,
                "AwayScoreQuarter1": None,
                "AwayScoreQuarter2": None,
                "AwayScoreQuarter3": None,
                "AwayScoreQuarter4": None,
                "AwayScoreOvertime": None,
                "HomeScoreQuarter1": None,
                "HomeScoreQuarter2": None,
                "HomeScoreQuarter3": None,
                "HomeScoreQuarter4": None,
                "HomeScoreOvertime": None,
                "HomeScore": None,
                "AwayScore": None,
                "TotalScore": None,
                "HomeRotationNumber": 102,
                "AwayRotationNumber": 101,
                "ForecastTempLow": 65,
                "ForecastTempHigh": 77,
                "ForecastDescription": "Clear",
                "ForecastWindSpeed": 8,
                "ForecastWindDirection": "WSW"
            }
        ]

    def odds_api_response(self, sport: str = "americanfootball_nfl") -> Dict[str, Any]:
        """Mock Odds API response."""
        return [
            {
                "id": "c5c8d5d4e5f6a7b8c9d0e1f2",
                "sport_key": sport,
                "sport_title": "NFL",
                "commence_time": (datetime.now() + timedelta(days=1)).isoformat(),
                "home_team": "Detroit Lions",
                "away_team": "Kansas City Chiefs",
                "bookmakers": [
                    {
                        "key": "draftkings",
                        "title": "DraftKings",
                        "last_update": datetime.now().isoformat(),
                        "markets": [
                            {
                                "key": "h2h",
                                "last_update": datetime.now().isoformat(),
                                "outcomes": [
                                    {
                                        "name": "Detroit Lions",
                                        "price": 2.20
                                    },
                                    {
                                        "name": "Kansas City Chiefs",
                                        "price": 1.67
                                    }
                                ]
                            },
                            {
                                "key": "spreads",
                                "last_update": datetime.now().isoformat(),
                                "outcomes": [
                                    {
                                        "name": "Detroit Lions",
                                        "price": 1.91,
                                        "point": 3.5
                                    },
                                    {
                                        "name": "Kansas City Chiefs",
                                        "price": 1.91,
                                        "point": -3.5
                                    }
                                ]
                            },
                            {
                                "key": "totals",
                                "last_update": datetime.now().isoformat(),
                                "outcomes": [
                                    {
                                        "name": "Over",
                                        "price": 1.91,
                                        "point": 48.5
                                    },
                                    {
                                        "name": "Under",
                                        "price": 1.91,
                                        "point": 48.5
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "key": "fanduel",
                        "title": "FanDuel",
                        "last_update": datetime.now().isoformat(),
                        "markets": [
                            {
                                "key": "h2h",
                                "last_update": datetime.now().isoformat(),
                                "outcomes": [
                                    {
                                        "name": "Detroit Lions",
                                        "price": 2.18
                                    },
                                    {
                                        "name": "Kansas City Chiefs",
                                        "price": 1.69
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]


class MockRedisResponses:
    """Mock Redis responses and data structures."""

    @staticmethod
    def cached_game_data(game_id: str) -> str:
        """Mock cached game data in Redis."""
        data = {
            "game_id": game_id,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "home_team": "DET",
            "away_team": "KC",
            "home_score": 14,
            "away_score": 10,
            "quarter": 2,
            "time_remaining": "8:45",
            "possession": "DET",
            "down_distance": "2nd & 7",
            "field_position": "DET 35"
        }
        return json.dumps(data)

    @staticmethod
    def cached_prediction_data(game_id: str) -> str:
        """Mock cached prediction data in Redis."""
        data = {
            "game_id": game_id,
            "model_version": "v2.1",
            "prediction_time": datetime.now(timezone.utc).isoformat(),
            "home_win_probability": 0.68,
            "away_win_probability": 0.32,
            "spread_prediction": -2.8,
            "total_prediction": 49.2,
            "confidence_score": 0.84,
            "live_adjustments": {
                "score_impact": 0.15,
                "time_remaining_impact": -0.05,
                "field_position_impact": 0.02
            }
        }
        return json.dumps(data)

    @staticmethod
    def system_metrics() -> str:
        """Mock system metrics in Redis."""
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "api_requests_per_minute": 245,
            "websocket_connections": 1834,
            "prediction_accuracy_24h": 0.734,
            "database_connections": 15,
            "cache_hit_rate": 0.892,
            "average_response_time": 0.124,
            "active_games": 16,
            "total_predictions_today": 12847
        }
        return json.dumps(metrics)


# Export convenience functions
def get_mock_websocket_messages() -> MockWebSocketMessages:
    """Get instance of mock WebSocket messages."""
    return MockWebSocketMessages()


def get_mock_external_apis() -> MockExternalAPIs:
    """Get instance of mock external APIs."""
    return MockExternalAPIs()


def get_mock_redis_responses() -> MockRedisResponses:
    """Get instance of mock Redis responses."""
    return MockRedisResponses()


def create_websocket_test_scenario(game_id: str = "test_game_001") -> List[Dict[str, Any]]:
    """Create a sequence of WebSocket messages for testing live game scenarios."""
    ws_mock = MockWebSocketMessages()

    return [
        # Game starts
        ws_mock.game_update_message(game_id, quarter=1, time_remaining="15:00", home_score=0, away_score=0),

        # First touchdown
        ws_mock.game_update_message(game_id, quarter=1, time_remaining="12:34", home_score=7, away_score=0),
        ws_mock.prediction_update_message(game_id, home_win_prob=0.72, confidence=0.85),

        # Away team responds
        ws_mock.game_update_message(game_id, quarter=1, time_remaining="8:21", home_score=7, away_score=7),
        ws_mock.prediction_update_message(game_id, home_win_prob=0.58, confidence=0.81),

        # Half time
        ws_mock.game_update_message(game_id, quarter=2, time_remaining="0:00", home_score=14, away_score=10),
        ws_mock.prediction_update_message(game_id, home_win_prob=0.64, confidence=0.79),

        # System health check
        ws_mock.system_health_message(status="healthy"),

        # Potential error scenario
        ws_mock.error_message(error_type="data_delay", message="Live data feed delayed by 30 seconds")
    ]