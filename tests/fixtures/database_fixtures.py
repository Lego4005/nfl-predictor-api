"""
Database fixtures and test data for NFL Predictor API tests.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import uuid
from decimal import Decimal

import pandas as pd
import numpy as np


@dataclass
class TeamFixture:
    """NFL team fixture data."""
    team_id: str
    name: str
    abbreviation: str
    conference: str
    division: str
    city: str
    primary_color: str
    secondary_color: str
    logo_url: Optional[str] = None


@dataclass
class PlayerFixture:
    """NFL player fixture data."""
    player_id: str
    name: str
    team_id: str
    position: str
    jersey_number: int
    height: str
    weight: int
    birth_date: datetime
    experience_years: int
    college: str


@dataclass
class GameFixture:
    """NFL game fixture data."""
    game_id: str
    season: int
    week: int
    game_type: str  # regular, playoff, preseason
    home_team_id: str
    away_team_id: str
    game_date: datetime
    venue: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    quarter: Optional[int] = None
    time_remaining: Optional[str] = None
    status: str = "scheduled"  # scheduled, live, completed, postponed
    weather_temperature: Optional[float] = None
    weather_humidity: Optional[float] = None
    weather_wind_speed: Optional[float] = None
    weather_conditions: Optional[str] = None


@dataclass
class GameStatsFixture:
    """Game statistics fixture data."""
    stats_id: str
    game_id: str
    team_id: str
    is_home: bool
    total_yards: int
    passing_yards: int
    rushing_yards: int
    turnovers: int
    penalties: int
    penalty_yards: int
    first_downs: int
    third_down_attempts: int
    third_down_conversions: int
    red_zone_attempts: int
    red_zone_conversions: int
    time_of_possession: str  # "MM:SS"
    sacks_allowed: int


@dataclass
class PredictionFixture:
    """ML prediction fixture data."""
    prediction_id: str
    game_id: str
    model_version: str
    prediction_time: datetime
    home_win_probability: float
    away_win_probability: float
    spread_prediction: float
    total_prediction: float
    confidence_score: float
    feature_importance: Dict[str, float]
    model_accuracy: float


class NFLTestDataFactory:
    """Factory for creating NFL test data."""

    def __init__(self):
        self._teams = self._create_teams()
        self._players = self._create_players()

    def _create_teams(self) -> List[TeamFixture]:
        """Create NFL team fixtures."""
        teams_data = [
            # AFC East
            ("BUF", "Buffalo Bills", "AFC", "East", "Buffalo", "#00338D", "#C60C30"),
            ("MIA", "Miami Dolphins", "AFC", "East", "Miami", "#008E97", "#FC4C02"),
            ("NE", "New England Patriots", "AFC", "East", "Foxborough", "#002244", "#C60C30"),
            ("NYJ", "New York Jets", "AFC", "East", "East Rutherford", "#125740", "#FFFFFF"),

            # AFC North
            ("BAL", "Baltimore Ravens", "AFC", "North", "Baltimore", "#241773", "#000000"),
            ("CIN", "Cincinnati Bengals", "AFC", "North", "Cincinnati", "#FB4F14", "#000000"),
            ("CLE", "Cleveland Browns", "AFC", "North", "Cleveland", "#311D00", "#FF3C00"),
            ("PIT", "Pittsburgh Steelers", "AFC", "North", "Pittsburgh", "#FFB612", "#101820"),

            # AFC South
            ("HOU", "Houston Texans", "AFC", "South", "Houston", "#03202F", "#A71930"),
            ("IND", "Indianapolis Colts", "AFC", "South", "Indianapolis", "#002C5F", "#A2AAAD"),
            ("JAX", "Jacksonville Jaguars", "AFC", "South", "Jacksonville", "#101820", "#D7A22A"),
            ("TEN", "Tennessee Titans", "AFC", "South", "Nashville", "#0C2340", "#4B92DB"),

            # AFC West
            ("DEN", "Denver Broncos", "AFC", "West", "Denver", "#FB4F14", "#002244"),
            ("KC", "Kansas City Chiefs", "AFC", "West", "Kansas City", "#E31837", "#FFB81C"),
            ("LV", "Las Vegas Raiders", "AFC", "West", "Las Vegas", "#000000", "#A5ACAF"),
            ("LAC", "Los Angeles Chargers", "AFC", "West", "Los Angeles", "#0080C6", "#FFC20E"),

            # NFC East
            ("DAL", "Dallas Cowboys", "NFC", "East", "Arlington", "#003594", "#869397"),
            ("NYG", "New York Giants", "NFC", "East", "East Rutherford", "#0B2265", "#A71930"),
            ("PHI", "Philadelphia Eagles", "NFC", "East", "Philadelphia", "#004C54", "#A5ACAF"),
            ("WAS", "Washington Commanders", "NFC", "East", "Landover", "#5A1414", "#FFB612"),

            # NFC North
            ("CHI", "Chicago Bears", "NFC", "North", "Chicago", "#0B162A", "#C83803"),
            ("DET", "Detroit Lions", "NFC", "North", "Detroit", "#0076B6", "#B0B7BC"),
            ("GB", "Green Bay Packers", "NFC", "North", "Green Bay", "#203731", "#FFB612"),
            ("MIN", "Minnesota Vikings", "NFC", "North", "Minneapolis", "#4F2683", "#FFC62F"),

            # NFC South
            ("ATL", "Atlanta Falcons", "NFC", "South", "Atlanta", "#A71930", "#000000"),
            ("CAR", "Carolina Panthers", "NFC", "South", "Charlotte", "#0085CA", "#101820"),
            ("NO", "New Orleans Saints", "NFC", "South", "New Orleans", "#D3BC8D", "#101820"),
            ("TB", "Tampa Bay Buccaneers", "NFC", "South", "Tampa", "#D50A0A", "#FF7900"),

            # NFC West
            ("ARI", "Arizona Cardinals", "NFC", "West", "Glendale", "#97233F", "#000000"),
            ("LAR", "Los Angeles Rams", "NFC", "West", "Los Angeles", "#003594", "#FFA300"),
            ("SF", "San Francisco 49ers", "NFC", "West", "Santa Clara", "#AA0000", "#B3995D"),
            ("SEA", "Seattle Seahawks", "NFC", "West", "Seattle", "#002244", "#69BE28"),
        ]

        return [
            TeamFixture(
                team_id=abbr,
                name=name,
                abbreviation=abbr,
                conference=conf,
                division=div,
                city=city,
                primary_color=primary,
                secondary_color=secondary,
                logo_url=f"https://example.com/logos/{abbr.lower()}.png"
            )
            for abbr, name, conf, div, city, primary, secondary in teams_data
        ]

    def _create_players(self) -> List[PlayerFixture]:
        """Create sample player fixtures."""
        players = []
        positions = ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S", "K", "P"]

        # Create a few key players per team
        for team in self._teams[:4]:  # First 4 teams for test data
            for i, pos in enumerate(positions[:3]):  # 3 players per team
                player_id = f"{team.team_id.lower()}_{pos.lower()}_{i+1}"
                players.append(PlayerFixture(
                    player_id=player_id,
                    name=f"Test {pos} {i+1}",
                    team_id=team.team_id,
                    position=pos,
                    jersey_number=(i + 1) * 10,
                    height="6'2\"",
                    weight=220 + (i * 10),
                    birth_date=datetime(1995 + i, 1, 1),
                    experience_years=3 + i,
                    college=f"Test University {i+1}"
                ))

        return players

    def get_teams(self, limit: Optional[int] = None) -> List[TeamFixture]:
        """Get team fixtures."""
        return self._teams[:limit] if limit else self._teams

    def get_players(self, team_id: Optional[str] = None, limit: Optional[int] = None) -> List[PlayerFixture]:
        """Get player fixtures."""
        players = self._players
        if team_id:
            players = [p for p in players if p.team_id == team_id]
        return players[:limit] if limit else players

    def create_game(self,
                   home_team: str = "KC",
                   away_team: str = "DET",
                   season: int = 2024,
                   week: int = 1,
                   game_date: Optional[datetime] = None,
                   status: str = "scheduled") -> GameFixture:
        """Create a game fixture."""
        if not game_date:
            game_date = datetime.now(timezone.utc) + timedelta(days=1)

        return GameFixture(
            game_id=f"{season}_W{week:02d}_{away_team}_{home_team}",
            season=season,
            week=week,
            game_type="regular",
            home_team_id=home_team,
            away_team_id=away_team,
            game_date=game_date,
            venue=f"{home_team} Stadium",
            status=status,
            weather_temperature=72.0,
            weather_humidity=65.0,
            weather_wind_speed=8.0,
            weather_conditions="Clear"
        )

    def create_game_stats(self, game: GameFixture, team_id: str, is_home: bool) -> GameStatsFixture:
        """Create game statistics fixture."""
        # Generate realistic but random stats
        np.random.seed(hash(f"{game.game_id}_{team_id}") % (2**32))

        total_yards = np.random.randint(250, 450)
        passing_yards = np.random.randint(150, 350)
        rushing_yards = total_yards - passing_yards

        return GameStatsFixture(
            stats_id=f"{game.game_id}_{team_id}_stats",
            game_id=game.game_id,
            team_id=team_id,
            is_home=is_home,
            total_yards=total_yards,
            passing_yards=passing_yards,
            rushing_yards=rushing_yards,
            turnovers=np.random.randint(0, 4),
            penalties=np.random.randint(5, 12),
            penalty_yards=np.random.randint(40, 100),
            first_downs=np.random.randint(15, 25),
            third_down_attempts=np.random.randint(10, 16),
            third_down_conversions=np.random.randint(3, 8),
            red_zone_attempts=np.random.randint(2, 6),
            red_zone_conversions=np.random.randint(1, 4),
            time_of_possession=f"{np.random.randint(25, 35)}:{np.random.randint(0, 59):02d}",
            sacks_allowed=np.random.randint(0, 5)
        )

    def create_prediction(self, game: GameFixture, model_version: str = "v2.1") -> PredictionFixture:
        """Create ML prediction fixture."""
        np.random.seed(hash(game.game_id) % (2**32))

        home_win_prob = np.random.beta(2, 2)  # Beta distribution for probability
        home_win_prob = max(0.1, min(0.9, home_win_prob))  # Clamp between 10-90%

        return PredictionFixture(
            prediction_id=f"{game.game_id}_prediction",
            game_id=game.game_id,
            model_version=model_version,
            prediction_time=datetime.now(timezone.utc),
            home_win_probability=home_win_prob,
            away_win_probability=1 - home_win_prob,
            spread_prediction=np.random.normal(0, 7),
            total_prediction=np.random.normal(45, 8),
            confidence_score=np.random.beta(3, 1),  # Higher confidence on average
            feature_importance={
                "offensive_efficiency": 0.25,
                "defensive_rating": 0.22,
                "recent_form": 0.18,
                "home_field_advantage": 0.15,
                "weather_conditions": 0.08,
                "injury_impact": 0.12
            },
            model_accuracy=0.65 + np.random.normal(0, 0.05)
        )

    def create_season_schedule(self, season: int = 2024, weeks: int = 18) -> List[GameFixture]:
        """Create a full season schedule of games."""
        games = []
        teams = [t.team_id for t in self._teams]

        for week in range(1, weeks + 1):
            # Create games for this week
            week_games = []
            available_teams = teams.copy()

            # Create random matchups (simplified scheduling)
            while len(available_teams) >= 2:
                home_team = available_teams.pop(np.random.randint(len(available_teams)))
                away_team = available_teams.pop(np.random.randint(len(available_teams)))

                game_date = datetime(season, 9, 1) + timedelta(weeks=week-1)
                game = self.create_game(
                    home_team=home_team,
                    away_team=away_team,
                    season=season,
                    week=week,
                    game_date=game_date
                )
                week_games.append(game)

            games.extend(week_games)

        return games

    def create_historical_data(self, seasons: List[int] = [2020, 2021, 2022, 2023]) -> Dict[str, List]:
        """Create historical data for multiple seasons."""
        historical_data = {
            "games": [],
            "stats": [],
            "predictions": []
        }

        for season in seasons:
            season_games = self.create_season_schedule(season)
            historical_data["games"].extend(season_games)

            for game in season_games:
                # Add completed game stats for historical seasons
                if season < 2024:
                    game.status = "completed"
                    game.home_score = np.random.randint(7, 35)
                    game.away_score = np.random.randint(7, 35)

                    # Create stats for both teams
                    home_stats = self.create_game_stats(game, game.home_team_id, True)
                    away_stats = self.create_game_stats(game, game.away_team_id, False)
                    historical_data["stats"].extend([home_stats, away_stats])

                # Create predictions for all games
                prediction = self.create_prediction(game)
                historical_data["predictions"].append(prediction)

        return historical_data


class MockAPIResponseFactory:
    """Factory for creating mock API responses."""

    @staticmethod
    def nfl_api_games_response(games: List[GameFixture]) -> Dict[str, Any]:
        """Create mock NFL API games response."""
        return {
            "status": "success",
            "data": {
                "games": [
                    {
                        "id": game.game_id,
                        "season": game.season,
                        "week": game.week,
                        "date": game.game_date.isoformat(),
                        "home_team": {
                            "id": game.home_team_id,
                            "name": game.home_team_id,  # Simplified
                            "score": game.home_score
                        },
                        "away_team": {
                            "id": game.away_team_id,
                            "name": game.away_team_id,  # Simplified
                            "score": game.away_score
                        },
                        "status": game.status,
                        "venue": game.venue,
                        "weather": {
                            "temperature": game.weather_temperature,
                            "humidity": game.weather_humidity,
                            "wind_speed": game.weather_wind_speed,
                            "conditions": game.weather_conditions
                        }
                    }
                    for game in games
                ]
            },
            "pagination": {
                "total": len(games),
                "page": 1,
                "per_page": 100
            }
        }

    @staticmethod
    def espn_api_scoreboard_response(games: List[GameFixture]) -> Dict[str, Any]:
        """Create mock ESPN API scoreboard response."""
        return {
            "leagues": [{
                "season": {
                    "year": 2024,
                    "type": 2  # Regular season
                },
                "events": [
                    {
                        "id": game.game_id,
                        "date": game.game_date.isoformat(),
                        "status": {
                            "type": {"id": "1" if game.status == "scheduled" else "3"},
                            "detail": game.status.title()
                        },
                        "competitions": [{
                            "competitors": [
                                {
                                    "team": {"abbreviation": game.home_team_id},
                                    "homeAway": "home",
                                    "score": str(game.home_score) if game.home_score else "0"
                                },
                                {
                                    "team": {"abbreviation": game.away_team_id},
                                    "homeAway": "away",
                                    "score": str(game.away_score) if game.away_score else "0"
                                }
                            ],
                            "venue": {"fullName": game.venue}
                        }]
                    }
                    for game in games
                ]
            }]
        }

    @staticmethod
    def weather_api_response(temperature: float = 72.0,
                           humidity: float = 65.0,
                           wind_speed: float = 8.0,
                           conditions: str = "Clear") -> Dict[str, Any]:
        """Create mock weather API response."""
        return {
            "current": {
                "temp_f": temperature,
                "humidity": humidity,
                "wind_mph": wind_speed,
                "condition": {
                    "text": conditions,
                    "code": 1000
                },
                "vis_miles": 10.0,
                "pressure_in": 30.12,
                "feelslike_f": temperature + 2
            },
            "forecast": {
                "forecastday": [
                    {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "day": {
                            "maxtemp_f": temperature + 5,
                            "mintemp_f": temperature - 10,
                            "condition": {"text": conditions}
                        }
                    }
                ]
            }
        }


# Export convenience functions
def get_test_data_factory() -> NFLTestDataFactory:
    """Get instance of test data factory."""
    return NFLTestDataFactory()


def get_mock_api_factory() -> MockAPIResponseFactory:
    """Get instance of mock API response factory."""
    return MockAPIResponseFactory()


def create_sample_dataset(size: int = 100) -> pd.DataFrame:
    """Create sample ML training dataset."""
    factory = NFLTestDataFactory()
    np.random.seed(42)

    # Generate feature data
    features = {
        'home_offensive_rating': np.random.normal(0.5, 0.15, size),
        'home_defensive_rating': np.random.normal(0.5, 0.12, size),
        'away_offensive_rating': np.random.normal(0.5, 0.15, size),
        'away_defensive_rating': np.random.normal(0.5, 0.12, size),
        'home_recent_form': np.random.normal(0.5, 0.2, size),
        'away_recent_form': np.random.normal(0.5, 0.2, size),
        'weather_impact': np.random.normal(0.0, 0.1, size),
        'rest_days_diff': np.random.randint(-7, 8, size),
        'home_field_advantage': np.random.normal(0.1, 0.05, size),
        'injury_impact': np.random.normal(0.0, 0.08, size)
    }

    df = pd.DataFrame(features)

    # Create target based on features (home team wins)
    home_advantage = (
        df['home_offensive_rating'] - df['away_defensive_rating'] +
        df['home_field_advantage'] +
        (df['home_recent_form'] - df['away_recent_form']) * 0.3 +
        df['weather_impact'] * 0.1 +
        df['injury_impact'] * -0.5
    )

    df['home_win'] = (home_advantage + np.random.normal(0, 0.1, size) > 0).astype(int)
    df['home_score'] = np.clip(np.random.poisson(24, size), 0, 50)
    df['away_score'] = np.clip(np.random.poisson(21, size), 0, 50)
    df['total_points'] = df['home_score'] + df['away_score']

    return df