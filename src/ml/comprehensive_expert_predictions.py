"""
Enhanced Expert Prediction Models
Generates all 30+ prediction categories per expert as outlined in system overview
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import logging
from dataclasses import dataclass, field
from enum import Enum
import json
import random

logger = logging.getLogger(__name__)

class PredictionCategory(Enum):
    """Enumeration of all prediction categories"""
    GAME_WINNER = "game_winner"
    POINT_SPREAD = "point_spread"
    TOTAL_POINTS = "total_points"
    MONEYLINE = "moneyline"
    EXACT_SCORE = "exact_score"
    MARGIN_OF_VICTORY = "margin_of_victory"

    # Quarter predictions
    Q1_SCORE = "q1_score"
    Q2_SCORE = "q2_score"
    Q3_SCORE = "q3_score"
    Q4_SCORE = "q4_score"
    FIRST_HALF_WINNER = "first_half_winner"
    HIGHEST_SCORING_QUARTER = "highest_scoring_quarter"

    # Player props
    QB_PASSING_YARDS = "qb_passing_yards"
    QB_TOUCHDOWNS = "qb_touchdowns"
    QB_COMPLETIONS = "qb_completions"
    QB_INTERCEPTIONS = "qb_interceptions"
    RB_RUSHING_YARDS = "rb_rushing_yards"
    RB_ATTEMPTS = "rb_attempts"
    RB_TOUCHDOWNS = "rb_touchdowns"
    WR_RECEIVING_YARDS = "wr_receiving_yards"
    WR_RECEPTIONS = "wr_receptions"
    WR_TOUCHDOWNS = "wr_touchdowns"

    # Situational
    TURNOVER_DIFFERENTIAL = "turnover_differential"
    RED_ZONE_EFFICIENCY = "red_zone_efficiency"
    THIRD_DOWN_CONVERSION = "third_down_conversion"
    TIME_OF_POSSESSION = "time_of_possession"
    SACKS = "sacks"
    PENALTIES = "penalties"

    # Advanced
    WEATHER_IMPACT = "weather_impact"
    INJURY_IMPACT = "injury_impact"
    MOMENTUM_ANALYSIS = "momentum_analysis"
    SPECIAL_TEAMS = "special_teams"
    COACHING_MATCHUP = "coaching_matchup"

@dataclass
class PredictionWithConfidence:
    """Base prediction structure with confidence and reasoning"""
    prediction: Any
    confidence: float  # 0.0 to 1.0
    reasoning: str
    key_factors: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence prediction"""
        return self.confidence >= 0.7

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'prediction': self.prediction,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'key_factors': self.key_factors
        }

@dataclass
class QuarterPrediction:
    """Quarter-specific prediction structure"""
    quarter: int  # 1, 2, 3, 4
    home_score: int
    away_score: int
    total_points: int
    confidence: float
    key_factors: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.quarter not in [1, 2, 3, 4]:
            raise ValueError(f"Quarter must be 1, 2, 3, or 4, got {self.quarter}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.home_score < 0 or self.away_score < 0:
            raise ValueError("Scores cannot be negative")
        if self.total_points != self.home_score + self.away_score:
            raise ValueError("Total points must equal sum of home and away scores")

    def get_winner(self) -> str:
        """Get the winning team for this quarter"""
        if self.home_score > self.away_score:
            return "home"
        elif self.away_score > self.home_score:
            return "away"
        else:
            return "tie"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'quarter': self.quarter,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'total_points': self.total_points,
            'confidence': self.confidence,
            'key_factors': self.key_factors,
            'winner': self.get_winner()
        }

@dataclass
class PlayerPropPrediction:
    """Player prop prediction structure"""
    player_name: str
    position: str
    team: str
    prop_type: str  # e.g., "passing_yards", "rushing_touchdowns"
    over_under_line: float
    prediction: str  # "over" or "under"
    projected_value: float
    confidence: float
    reasoning: str

    def __post_init__(self):
        if self.prediction not in ["over", "under"]:
            raise ValueError(f"Prediction must be 'over' or 'under', got {self.prediction}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.projected_value < 0:
            raise ValueError("Projected value cannot be negative")

    def get_edge(self) -> float:
        """Calculate the edge (projected value vs line)"""
        return self.projected_value - self.over_under_line

    def is_strong_play(self) -> bool:
        """Check if this is a strong play (high confidence + good edge)"""
        edge = abs(self.get_edge())
        return self.confidence >= 0.65 and edge >= (self.over_under_line * 0.1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'player_name': self.player_name,
            'position': self.position,
            'team': self.team,
            'prop_type': self.prop_type,
            'over_under_line': self.over_under_line,
            'prediction': self.prediction,
            'projected_value': self.projected_value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'edge': self.get_edge(),
            'is_strong_play': self.is_strong_play()
        }

@dataclass
class WeatherData:
    """Weather conditions for game context"""
    temperature: Optional[float] = None  # Fahrenheit
    wind_speed: Optional[float] = None  # MPH
    wind_direction: Optional[str] = None
    precipitation: Optional[float] = None  # Inches
    humidity: Optional[float] = None  # Percentage
    conditions: Optional[str] = None  # "Clear", "Rain", "Snow", etc.

    def is_adverse_weather(self) -> bool:
        """Check if weather conditions are adverse for gameplay"""
        if self.wind_speed and self.wind_speed > 15:
            return True
        if self.precipitation and self.precipitation > 0.1:
            return True
        if self.temperature and self.temperature < 32:
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'temperature': self.temperature,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'precipitation': self.precipitation,
            'humidity': self.humidity,
            'conditions': self.conditions,
            'is_adverse': self.is_adverse_weather()
        }

@dataclass
class StadiumData:
    """Stadium information for game context"""
    name: str
    city: str
    state: str
    surface_type: Optional[str] = None  # "Grass", "Turf", etc.
    dome_status: Optional[str] = None  # "Dome", "Retractable", "Open"
    elevation: Optional[int] = None  # Feet above sea level
    capacity: Optional[int] = None

    def is_dome(self) -> bool:
        """Check if stadium is domed or has retractable roof"""
        return self.dome_status in ["Dome", "Retractable"]

    def is_high_altitude(self) -> bool:
        """Check if stadium is at high altitude (affects kicking)"""
        return self.elevation and self.elevation > 3000

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'surface_type': self.surface_type,
            'dome_status': self.dome_status,
            'elevation': self.elevation,
            'capacity': self.capacity,
            'is_dome': self.is_dome(),
            'is_high_altitude': self.is_high_altitude()
        }

@dataclass
class TeamStats:
    """Team statistics for game context"""
    team_name: str
    season: int
    week: int

    # Offensive stats
    points_per_game: Optional[float] = None
    yards_per_game: Optional[float] = None
    passing_yards_per_game: Optional[float] = None
    rushing_yards_per_game: Optional[float] = None
    turnovers_per_game: Optional[float] = None

    # Defensive stats
    points_allowed_per_game: Optional[float] = None
    yards_allowed_per_game: Optional[float] = None
    sacks_per_game: Optional[float] = None
    interceptions_per_game: Optional[float] = None

    # Special teams
    field_goal_percentage: Optional[float] = None
    punt_return_average: Optional[float] = None

    # Record and trends
    wins: Optional[int] = None
    losses: Optional[int] = None
    win_percentage: Optional[float] = None
    home_record: Optional[str] = None
    away_record: Optional[str] = None
    last_5_games: Optional[str] = None  # "W-L-W-W-L" format

    def get_record_string(self) -> str:
        """Get formatted record string"""
        if self.wins is not None and self.losses is not None:
            return f"{self.wins}-{self.losses}"
        return "Unknown"

    def get_recent_form(self) -> str:
        """Analyze recent form from last 5 games"""
        if not self.last_5_games:
            return "Unknown"

        wins = self.last_5_games.count('W')
        if wins >= 4:
            return "Hot"
        elif wins >= 3:
            return "Good"
        elif wins >= 2:
            return "Average"
        else:
            return "Cold"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'team_name': self.team_name,
            'season': self.season,
            'week': self.week,
            'points_per_game': self.points_per_game,
            'yards_per_game': self.yards_per_game,
            'passing_yards_per_game': self.passing_yards_per_game,
            'rushing_yards_per_game': self.rushing_yards_per_game,
            'turnovers_per_game': self.turnovers_per_game,
            'points_allowed_per_game': self.points_allowed_per_game,
            'yards_allowed_per_game': self.yards_allowed_per_game,
            'sacks_per_game': self.sacks_per_game,
            'interceptions_per_game': self.interceptions_per_game,
            'field_goal_percentage': self.field_goal_percentage,
            'punt_return_average': self.punt_return_average,
            'wins': self.wins,
            'losses': self.losses,
            'win_percentage': self.win_percentage,
            'home_record': self.home_record,
            'away_record': self.away_record,
            'last_5_games': self.last_5_games,
            'record_string': self.get_record_string(),
            'recent_form': self.get_recent_form()
        }

@dataclass
class PlayerData:
    """Individual player data for injury reports and props"""
    name: str
    position: str
    team: str
    jersey_number: Optional[int] = None

    # Injury information
    injury_status: Optional[str] = None  # "Healthy", "Questionable", "Doubtful", "Out"
    injury_description: Optional[str] = None

    # Season stats (for prop betting context)
    games_played: Optional[int] = None
    season_stats: Optional[Dict[str, float]] = None

    # Recent performance
    last_3_games_avg: Optional[Dict[str, float]] = None

    def is_available(self) -> bool:
        """Check if player is likely to play"""
        return self.injury_status not in ["Out", "Doubtful"]

    def get_injury_impact(self) -> str:
        """Assess injury impact level"""
        if self.injury_status == "Out":
            return "High"
        elif self.injury_status == "Doubtful":
            return "High"
        elif self.injury_status == "Questionable":
            return "Medium"
        else:
            return "None"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'position': self.position,
            'team': self.team,
            'jersey_number': self.jersey_number,
            'injury_status': self.injury_status,
            'injury_description': self.injury_description,
            'games_played': self.games_played,
            'season_stats': self.season_stats,
            'last_3_games_avg': self.last_3_games_avg,
            'is_available': self.is_available(),
            'injury_impact': self.get_injury_impact()
        }

@dataclass
class GameContext:
    """Complete game context for AI orchestration"""
    # Basic game info
    game_id: str
    home_team: str
    away_team: str
    season: int
    week: int
    game_date: datetime

    # Environmental factors
    weather_conditions: Optional[WeatherData] = None
    stadium_info: Optional[StadiumData] = None

    # Team states
    home_team_stats: Optional[TeamStats] = None
    away_team_stats: Optional[TeamStats] = None

    # Situational context
    is_divisional: bool = False
    is_primetime: bool = False
    playoff_implications: bool = False

    # Betting context
    opening_spread: Optional[float] = None
    current_spread: Optional[float] = None
    total_line: Optional[float] = None
    public_betting_percentage: Optional[float] = None

    # Injury reports
    home_injuries: List[PlayerData] = field(default_factory=list)
    away_injuries: List[PlayerData] = field(default_factory=list)

    def __post_init__(self):
        if self.week < 1 or self.week > 22:
            raise ValueError(f"Week must be between 1 and 22, got {self.week}")
        if self.season < 2000 or self.season > 2030:
            raise ValueError(f"Season must be between 2000 and 2030, got {self.season}")

    def get_matchup_key(self) -> str:
        """Get a unique key for this matchup"""
        return f"{self.away_team}@{self.home_team}_{self.season}W{self.week}"

    def has_significant_injuries(self) -> bool:
        """Check if there are significant injuries affecting the game"""
        key_positions = ['QB', 'RB', 'WR', 'TE', 'OL']

        for injury_list in [self.home_injuries, self.away_injuries]:
            for player in injury_list:
                if (player.position in key_positions and
                    player.injury_status in ['Out', 'Doubtful']):
                    return True
        return False

    def get_weather_impact_level(self) -> str:
        """Get weather impact assessment"""
        if not self.weather_conditions:
            return "None"
        return "High" if self.weather_conditions.is_adverse_weather() else "Low"

    def get_stadium_advantages(self) -> List[str]:
        """Get list of stadium-related advantages"""
        advantages = []
        if self.stadium_info:
            if self.stadium_info.is_dome():
                advantages.append("Climate controlled")
            if self.stadium_info.is_high_altitude():
                advantages.append("High altitude kicking")
        return advantages

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'game_id': self.game_id,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'season': self.season,
            'week': self.week,
            'game_date': self.game_date.isoformat(),
            'weather_conditions': self.weather_conditions.to_dict() if self.weather_conditions else None,
            'stadium_info': self.stadium_info.to_dict() if self.stadium_info else None,
            'home_team_stats': self.home_team_stats.to_dict() if self.home_team_stats else None,
            'away_team_stats': self.away_team_stats.to_dict() if self.away_team_stats else None,
            'is_divisional': self.is_divisional,
            'is_primetime': self.is_primetime,
            'playoff_implications': self.playoff_implications,
            'opening_spread': self.opening_spread,
            'current_spread': self.current_spread,
            'total_line': self.total_line,
            'public_betting_percentage': self.public_betting_percentage,
            'home_injuries': [player.to_dict() for player in self.home_injuries],
            'away_injuries': [player.to_dict() for player in self.away_injuries],
            'matchup_key': self.get_matchup_key(),
            'has_significant_injuries': self.has_significant_injuries(),
            'weather_impact_level': self.get_weather_impact_level(),
            'stadium_advantages': self.get_stadium_advantages()
        }

@dataclass
class MemoryInfluence:
    """Tracks how episodic memories influence predictions"""
    memory_id: str
    similarity_score: float  # 0.0 to 1.0
    temporal_weight: float  # 0.0 to 1.0 (after decay)
    influence_strength: float  # Combined similarity and temporal weight
    memory_summary: str
    why_relevant: str
    memory_type: str  # team_pattern, matchup_pattern, situational, personal_learning

    def __post_init__(self):
        if not 0.0 <= self.similarity_score <= 1.0:
            raise ValueError(f"Similarity score must be between 0.0 and 1.0, got {self.similarity_score}")
        if not 0.0 <= self.temporal_weight <= 1.0:
            raise ValueError(f"Temporal weight must be between 0.0 and 1.0, got {self.temporal_weight}")
        if not 0.0 <= self.influence_strength <= 1.0:
            raise ValueError(f"Influence strength must be between 0.0 and 1.0, got {self.influence_strength}")

    def is_strong_influence(self) -> bool:
        """Check if this memory has strong influence on the prediction"""
        return self.influence_strength >= 0.6

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'memory_id': self.memory_id,
            'similarity_score': self.similarity_score,
            'temporal_weight': self.temporal_weight,
            'influence_strength': self.influence_strength,
            'memory_summary': self.memory_summary,
            'why_relevant': self.why_relevant,
            'memory_type': self.memory_type,
            'is_strong_influence': self.is_strong_influence()
        }

@dataclass
class ComprehensiveExpertPrediction:
    """Complete expert prediction covering all 30+ categories from system overview"""
    expert_id: str
    expert_name: str
    game_context: GameContext

    # 1. Core Game Predictions
    game_winner: PredictionWithConfidence
    point_spread: PredictionWithConfidence
    total_points: PredictionWithConfidence
    moneyline: PredictionWithConfidence
    exact_score: PredictionWithConfidence
    margin_of_victory: PredictionWithConfidence

    # 2. Quarter-by-Quarter Predictions
    q1_score: QuarterPrediction
    q2_score: QuarterPrediction
    q3_score: QuarterPrediction
    q4_score: QuarterPrediction
    first_half_winner: PredictionWithConfidence
    highest_scoring_quarter: PredictionWithConfidence

    # 3. Player Props Predictions
    qb_passing_yards: List[PlayerPropPrediction]
    qb_touchdowns: List[PlayerPropPrediction]
    qb_completions: List[PlayerPropPrediction]
    qb_interceptions: List[PlayerPropPrediction]
    rb_rushing_yards: List[PlayerPropPrediction]
    rb_attempts: List[PlayerPropPrediction]
    rb_touchdowns: List[PlayerPropPrediction]
    wr_receiving_yards: List[PlayerPropPrediction]
    wr_receptions: List[PlayerPropPrediction]
    wr_touchdowns: List[PlayerPropPrediction]

    # 4. Situational Predictions
    turnover_differential: PredictionWithConfidence
    red_zone_efficiency: PredictionWithConfidence
    third_down_conversion: PredictionWithConfidence
    time_of_possession: PredictionWithConfidence
    sacks: PredictionWithConfidence
    penalties: PredictionWithConfidence

    # 5. Environmental & Advanced Analysis
    weather_impact: PredictionWithConfidence
    injury_impact: PredictionWithConfidence
    momentum_analysis: PredictionWithConfidence
    special_teams: PredictionWithConfidence
    coaching_matchup: PredictionWithConfidence

    # Meta information
    confidence_overall: float
    reasoning: str
    key_factors: List[str]
    prediction_timestamp: datetime
    memory_influences: List[MemoryInfluence] = field(default_factory=list)

    # Performance tracking
    historical_accuracy: Optional[float] = None
    recent_form: Optional[str] = None
    specialty_confidence: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the prediction data after initialization"""
        self.validate_all_predictions()

    def validate_all_predictions(self) -> bool:
        """Validate all prediction categories with comprehensive checks"""
        try:
            # Validate core predictions
            self._validate_core_predictions()

            # Validate quarter predictions
            self._validate_quarter_predictions()

            # Validate player props
            self._validate_player_props()

            # Validate situational predictions
            self._validate_situational_predictions()

            # Validate meta information
            self._validate_meta_information()

            # NEW: Cross-prediction consistency checks
            self._validate_cross_prediction_consistency()

            # NEW: Confidence score validation
            self._validate_confidence_scores()

            # NEW: Prediction value validation
            self._validate_prediction_values()

            logger.info(f"All predictions validated for expert {self.expert_id}")
            return True

        except Exception as e:
            logger.error(f"Validation failed for expert {self.expert_id}: {str(e)}")
            raise

    def _validate_core_predictions(self):
        """Validate core game predictions"""
        core_predictions = [
            self.game_winner, self.point_spread, self.total_points,
            self.moneyline, self.exact_score, self.margin_of_victory
        ]

        for pred in core_predictions:
            if not isinstance(pred, PredictionWithConfidence):
                raise ValueError(f"Core prediction must be PredictionWithConfidence, got {type(pred)}")

    def _validate_quarter_predictions(self):
        """Validate quarter-by-quarter predictions"""
        quarters = [self.q1_score, self.q2_score, self.q3_score, self.q4_score]

        for i, quarter in enumerate(quarters, 1):
            if not isinstance(quarter, QuarterPrediction):
                raise ValueError(f"Quarter {i} prediction must be QuarterPrediction, got {type(quarter)}")
            if quarter.quarter != i:
                raise ValueError(f"Quarter {i} prediction has wrong quarter number: {quarter.quarter}")

    def _validate_player_props(self):
        """Validate player prop predictions"""
        prop_lists = [
            self.qb_passing_yards, self.qb_touchdowns, self.qb_completions, self.qb_interceptions,
            self.rb_rushing_yards, self.rb_attempts, self.rb_touchdowns,
            self.wr_receiving_yards, self.wr_receptions, self.wr_touchdowns
        ]

        for prop_list in prop_lists:
            if not isinstance(prop_list, list):
                raise ValueError(f"Player prop must be a list, got {type(prop_list)}")
            for prop in prop_list:
                if not isinstance(prop, PlayerPropPrediction):
                    raise ValueError(f"Player prop must be PlayerPropPrediction, got {type(prop)}")

    def _validate_situational_predictions(self):
        """Validate situational predictions"""
        situational_predictions = [
            self.turnover_differential, self.red_zone_efficiency, self.third_down_conversion,
            self.time_of_possession, self.sacks, self.penalties,
            self.weather_impact, self.injury_impact, self.momentum_analysis,
            self.special_teams, self.coaching_matchup
        ]

        for pred in situational_predictions:
            if not isinstance(pred, PredictionWithConfidence):
                raise ValueError(f"Situational prediction must be PredictionWithConfidence, got {type(pred)}")

    def _validate_meta_information(self):
        """Validate meta information"""
        if not 0.0 <= self.confidence_overall <= 1.0:
            raise ValueError(f"Overall confidence must be between 0.0 and 1.0, got {self.confidence_overall}")

        if not isinstance(self.reasoning, str) or len(self.reasoning.strip()) == 0:
            raise ValueError("Reasoning must be a non-empty string")

        if not isinstance(self.key_factors, list):
            raise ValueError(f"Key factors must be a list, got {type(self.key_factors)}")

        for influence in self.memory_influences:
            if not isinstance(influence, MemoryInfluence):
                raise ValueError(f"Memory influence must be MemoryInfluence, got {type(influence)}")

    def get_prediction_count(self) -> int:
        """Get total number of predictions made"""
        count = 6  # Core predictions
        count += 4  # Quarter predictions
        count += 2  # Game segment predictions
        count += sum(len(prop_list) for prop_list in [
            self.qb_passing_yards, self.qb_touchdowns, self.qb_completions, self.qb_interceptions,
            self.rb_rushing_yards, self.rb_attempts, self.rb_touchdowns,
            self.wr_receiving_yards, self.wr_receptions, self.wr_touchdowns
        ])  # Player props
        count += 6  # Situational predictions
        count += 5  # Environmental/advanced predictions
        return count

    def get_high_confidence_predictions(self) -> List[str]:
        """Get list of high confidence prediction categories"""
        high_confidence = []

        # Check core predictions
        core_preds = {
            'game_winner': self.game_winner,
            'point_spread': self.point_spread,
            'total_points': self.total_points,
            'moneyline': self.moneyline,
            'exact_score': self.exact_score,
            'margin_of_victory': self.margin_of_victory
        }

        for name, pred in core_preds.items():
            if pred.is_high_confidence():
                high_confidence.append(name)

        # Check player props
        prop_categories = {
            'qb_passing_yards': self.qb_passing_yards,
            'qb_touchdowns': self.qb_touchdowns,
            'rb_rushing_yards': self.rb_rushing_yards,
            'wr_receiving_yards': self.wr_receiving_yards
        }

        for category, props in prop_categories.items():
            for prop in props:
                if prop.is_strong_play():
                    high_confidence.append(f"{category}_{prop.player_name}")

        return high_confidence

    def get_strong_memory_influences(self) -> List[MemoryInfluence]:
        """Get memories with strong influence on predictions"""
        return [mem for mem in self.memory_influences if mem.is_strong_influence()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage and API responses"""
        return {
            'expert_id': self.expert_id,
            'expert_name': self.expert_name,
            'game_context': self.game_context.to_dict(),

            # Core predictions
            'game_winner': self.game_winner.to_dict(),
            'point_spread': self.point_spread.to_dict(),
            'total_points': self.total_points.to_dict(),
            'moneyline': self.moneyline.to_dict(),
            'exact_score': self.exact_score.to_dict(),
            'margin_of_victory': self.margin_of_victory.to_dict(),

            # Quarter predictions
            'q1_score': self.q1_score.to_dict(),
            'q2_score': self.q2_score.to_dict(),
            'q3_score': self.q3_score.to_dict(),
            'q4_score': self.q4_score.to_dict(),
            'first_half_winner': self.first_half_winner.to_dict(),
            'highest_scoring_quarter': self.highest_scoring_quarter.to_dict(),

            # Player props
            'qb_passing_yards': [prop.to_dict() for prop in self.qb_passing_yards],
            'qb_touchdowns': [prop.to_dict() for prop in self.qb_touchdowns],
            'qb_completions': [prop.to_dict() for prop in self.qb_completions],
            'qb_interceptions': [prop.to_dict() for prop in self.qb_interceptions],
            'rb_rushing_yards': [prop.to_dict() for prop in self.rb_rushing_yards],
            'rb_attempts': [prop.to_dict() for prop in self.rb_attempts],
            'rb_touchdowns': [prop.to_dict() for prop in self.rb_touchdowns],
            'wr_receiving_yards': [prop.to_dict() for prop in self.wr_receiving_yards],
            'wr_receptions': [prop.to_dict() for prop in self.wr_receptions],
            'wr_touchdowns': [prop.to_dict() for prop in self.wr_touchdowns],

            # Situational predictions
            'turnover_differential': self.turnover_differential.to_dict(),
            'red_zone_efficiency': self.red_zone_efficiency.to_dict(),
            'third_down_conversion': self.third_down_conversion.to_dict(),
            'time_of_possession': self.time_of_possession.to_dict(),
            'sacks': self.sacks.to_dict(),
            'penalties': self.penalties.to_dict(),

            # Environmental/advanced
            'weather_impact': self.weather_impact.to_dict(),
            'injury_impact': self.injury_impact.to_dict(),
            'momentum_analysis': self.momentum_analysis.to_dict(),
            'special_teams': self.special_teams.to_dict(),
            'coaching_matchup': self.coaching_matchup.to_dict(),

            # Meta information
            'confidence_overall': self.confidence_overall,
            'reasoning': self.reasoning,
            'key_factors': self.key_factors,
            'prediction_timestamp': self.prediction_timestamp.isoformat(),
            'memory_influences': [mem.to_dict() for mem in self.memory_influences],
            'historical_accuracy': self.historical_accuracy,
            'recent_form': self.recent_form,
            'specialty_confidence': self.specialty_confidence,

            # Computed metrics
            'prediction_count': self.get_prediction_count(),
            'high_confidence_predictions': self.get_high_confidence_predictions(),
            'strong_memory_influences': len(self.get_strong_memory_influences())
        }

    def _validate_cross_prediction_consistency(self):
        """Validate consistency across related predictions"""
        # Validate quarter scores sum to game total
        quarter_total = (self.q1_score.total_points + self.q2_score.total_points +
                        self.q3_score.total_points + self.q4_score.total_points)

        # Extract predicted total from total_points prediction
        if hasattr(self.total_points.prediction, 'split'):
            # Handle "over 45.5" or "under 45.5" format
            total_pred_str = str(self.total_points.prediction).lower()
            if 'over' in total_pred_str or 'under' in total_pred_str:
                # For over/under predictions, allow reasonable variance
                pass
        elif isinstance(self.total_points.prediction, (int, float)):
            predicted_total = float(self.total_points.prediction)
            if abs(quarter_total - predicted_total) > 7:  # Allow 1 TD variance
                logger.warning(f"Quarter totals ({quarter_total}) don't align with game total ({predicted_total})")

        # Validate game winner consistency with point spread
        winner = self.game_winner.prediction.lower()
        spread_pred = str(self.point_spread.prediction).lower()

        if winner == 'home' and 'away' in spread_pred:
            logger.warning("Game winner (home) conflicts with spread prediction (away)")
        elif winner == 'away' and 'home' in spread_pred:
            logger.warning("Game winner (away) conflicts with spread prediction (home)")

        # Validate exact score consistency with margin of victory
        if hasattr(self.exact_score.prediction, 'split'):
            try:
                score_parts = str(self.exact_score.prediction).split('-')
                if len(score_parts) == 2:
                    home_score = int(score_parts[0].strip())
                    away_score = int(score_parts[1].strip())
                    actual_margin = abs(home_score - away_score)

                    if isinstance(self.margin_of_victory.prediction, (int, float)):
                        predicted_margin = float(self.margin_of_victory.prediction)
                        if abs(actual_margin - predicted_margin) > 3:
                            logger.warning(f"Exact score margin ({actual_margin}) doesn't match margin prediction ({predicted_margin})")
            except (ValueError, IndexError):
                pass  # Skip validation if exact score format is unexpected

    def _validate_confidence_scores(self):
        """Validate all confidence scores are within valid ranges and reasonable"""
        confidence_scores = []

        # Collect all confidence scores
        core_predictions = [
            self.game_winner, self.point_spread, self.total_points,
            self.moneyline, self.exact_score, self.margin_of_victory,
            self.first_half_winner, self.highest_scoring_quarter
        ]

        for pred in core_predictions:
            confidence_scores.append(pred.confidence)

        # Quarter predictions
        for quarter in [self.q1_score, self.q2_score, self.q3_score, self.q4_score]:
            confidence_scores.append(quarter.confidence)

        # Player props
        prop_lists = [
            self.qb_passing_yards, self.qb_touchdowns, self.qb_completions, self.qb_interceptions,
            self.rb_rushing_yards, self.rb_attempts, self.rb_touchdowns,
            self.wr_receiving_yards, self.wr_receptions, self.wr_touchdowns
        ]

        for prop_list in prop_lists:
            for prop in prop_list:
                confidence_scores.append(prop.confidence)

        # Situational predictions
        situational_predictions = [
            self.turnover_differential, self.red_zone_efficiency, self.third_down_conversion,
            self.time_of_possession, self.sacks, self.penalties,
            self.weather_impact, self.injury_impact, self.momentum_analysis,
            self.special_teams, self.coaching_matchup
        ]

        for pred in situational_predictions:
            confidence_scores.append(pred.confidence)

        # Validate confidence score distribution
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            high_confidence_count = sum(1 for c in confidence_scores if c >= 0.7)
            low_confidence_count = sum(1 for c in confidence_scores if c <= 0.4)

            # Warn if all predictions are extremely high confidence (unrealistic)
            if avg_confidence > 0.85:
                logger.warning(f"Average confidence ({avg_confidence:.2f}) is unusually high - may indicate overconfidence")

            # Warn if too many high confidence predictions (should be selective)
            high_confidence_ratio = high_confidence_count / len(confidence_scores)
            if high_confidence_ratio > 0.3:
                logger.warning(f"High confidence ratio ({high_confidence_ratio:.2f}) suggests lack of selectivity")

    def _validate_prediction_values(self):
        """Validate prediction values are within reasonable ranges"""
        # Validate quarter scores are reasonable
        for i, quarter in enumerate([self.q1_score, self.q2_score, self.q3_score, self.q4_score], 1):
            if quarter.home_score > 35 or quarter.away_score > 35:
                logger.warning(f"Q{i} score unusually high: {quarter.home_score}-{quarter.away_score}")
            if quarter.total_points > 50:
                logger.warning(f"Q{i} total points unusually high: {quarter.total_points}")

        # Validate player prop projections are reasonable
        for qb_prop in self.qb_passing_yards:
            if qb_prop.projected_value > 500 or qb_prop.projected_value < 100:
                logger.warning(f"QB passing yards projection unusual: {qb_prop.projected_value} for {qb_prop.player_name}")

        for rb_prop in self.rb_rushing_yards:
            if rb_prop.projected_value > 250 or rb_prop.projected_value < 0:
                logger.warning(f"RB rushing yards projection unusual: {rb_prop.projected_value} for {rb_prop.player_name}")

        for td_prop in self.qb_touchdowns:
            if td_prop.projected_value > 6 or td_prop.projected_value < 0:
                logger.warning(f"QB touchdowns projection unusual: {td_prop.projected_value} for {td_prop.player_name}")

        # Validate situational predictions have reasonable values
        if hasattr(self.turnover_differential.prediction, 'split'):
            try:
                turnover_val = float(str(self.turnover_differential.prediction).replace('+', '').replace('-', ''))
                if turnover_val > 4:
                    logger.warning(f"Turnover differential prediction unusually high: {turnover_val}")
            except (ValueError, AttributeError):
                pass

        # Validate time of possession is reasonable (should be close to 30 minutes total)
        if hasattr(self.time_of_possession.prediction, 'split'):
            try:
                top_str = str(self.time_of_possession.prediction)
                if ':' in top_str:
                    minutes = int(top_str.split(':')[0])
                    if minutes > 40 or minutes < 20:
                        logger.warning(f"Time of possession prediction unusual: {top_str}")
            except (ValueError, AttributeError):
                pass


class ComprehensiveBaseExpert:
    """Enhanced base class for comprehensive expert predictions"""

    def __init__(self, expert_id: str, name: str, personality: str, specializations: List[str]):
        self.expert_id = expert_id
        self.name = name
        self.personality = personality
        self.specializations = specializations
        self.total_predictions = 0
        self.correct_predictions = 0
        self.accuracy_by_category = {}
        self.confidence_adjustments = {}

    def predict_comprehensive(self, game_context: GameContext, memory_influences: List[MemoryInfluence] = None) -> ComprehensiveExpertPrediction:
        """Generate all 30+ prediction categories using new structured approach"""

        if memory_influences is None:
            memory_influences = []

        # Core game analysis
        core_predictions = self._generate_core_predictions(game_context)

        # Quarter predictions
        quarter_predictions = self._generate_quarter_predictions(game_context)

        # Player props
        player_props = self._generate_player_props(game_context)

        # Situational predictions
        situational_predictions = self._generate_situational_predictions(game_context)

        # Environmental/advanced predictions
        advanced_predictions = self._generate_advanced_predictions(game_context)

        return ComprehensiveExpertPrediction(
            expert_id=self.expert_id,
            expert_name=self.name,
            game_context=game_context,

            # Core predictions
            game_winner=core_predictions['game_winner'],
            point_spread=core_predictions['point_spread'],
            total_points=core_predictions['total_points'],
            moneyline=core_predictions['moneyline'],
            exact_score=core_predictions['exact_score'],
            margin_of_victory=core_predictions['margin_of_victory'],

            # Quarter predictions
            q1_score=quarter_predictions['q1'],
            q2_score=quarter_predictions['q2'],
            q3_score=quarter_predictions['q3'],
            q4_score=quarter_predictions['q4'],
            first_half_winner=core_predictions['first_half_winner'],
            highest_scoring_quarter=core_predictions['highest_scoring_quarter'],

            # Player props
            qb_passing_yards=player_props['qb_passing_yards'],
            qb_touchdowns=player_props['qb_touchdowns'],
            qb_completions=player_props['qb_completions'],
            qb_interceptions=player_props['qb_interceptions'],
            rb_rushing_yards=player_props['rb_rushing_yards'],
            rb_attempts=player_props['rb_attempts'],
            rb_touchdowns=player_props['rb_touchdowns'],
            wr_receiving_yards=player_props['wr_receiving_yards'],
            wr_receptions=player_props['wr_receptions'],
            wr_touchdowns=player_props['wr_touchdowns'],

            # Situational predictions
            turnover_differential=situational_predictions['turnover_differential'],
            red_zone_efficiency=situational_predictions['red_zone_efficiency'],
            third_down_conversion=situational_predictions['third_down_conversion'],
            time_of_possession=situational_predictions['time_of_possession'],
            sacks=situational_predictions['sacks'],
            penalties=situational_predictions['penalties'],

            # Environmental/advanced
            weather_impact=advanced_predictions['weather_impact'],
            injury_impact=advanced_predictions['injury_impact'],
            momentum_analysis=advanced_predictions['momentum_analysis'],
            special_teams=advanced_predictions['special_teams'],
            coaching_matchup=advanced_predictions['coaching_matchup'],

            # Meta
            confidence_overall=self._calculate_overall_confidence(game_context, memory_influences),
            reasoning=self._generate_reasoning(game_context, memory_influences),
            key_factors=self._identify_key_factors(game_context),
            prediction_timestamp=datetime.now(),
            memory_influences=memory_influences,
            specialty_confidence=self._calculate_specialty_confidence()
        )

    def _generate_core_predictions(self, game_context: GameContext) -> Dict[str, PredictionWithConfidence]:
        """Generate comprehensive core game predictions with advanced analysis"""

        # Extract betting lines and context
        spread = game_context.current_spread or 0
        total = game_context.total_line or 45.5
        opening_spread = game_context.opening_spread or spread

        # Perform comprehensive game analysis
        game_analysis = self._analyze_game_fundamentals(game_context)
        margin_analysis = self._analyze_margin_potential(game_context, game_analysis)
        scoring_analysis = self._analyze_scoring_patterns(game_context, game_analysis)
        value_analysis = self._analyze_moneyline_value(game_context, game_analysis)

        # Generate winner prediction with confidence and reasoning
        winner_prediction = self._predict_game_winner(game_context, game_analysis)

        # Generate point spread prediction with margin analysis
        spread_prediction = self._predict_point_spread(game_context, game_analysis, margin_analysis)

        # Generate total points prediction with scoring pattern analysis
        total_prediction = self._predict_total_points(game_context, scoring_analysis)

        # Generate moneyline value assessment
        moneyline_prediction = self._assess_moneyline_value(game_context, value_analysis)

        # Generate exact score prediction
        exact_score_prediction = self._predict_exact_score(game_context, scoring_analysis)

        # Generate margin of victory prediction
        margin_prediction = self._predict_margin_of_victory(game_context, margin_analysis)

        # Generate first half winner prediction
        first_half_prediction = self._predict_first_half_winner(game_context, game_analysis)

        # Generate highest scoring quarter prediction
        quarter_prediction = self._predict_highest_scoring_quarter(game_context, scoring_analysis)

        return {
            'game_winner': winner_prediction,
            'point_spread': spread_prediction,
            'total_points': total_prediction,
            'moneyline': moneyline_prediction,
            'exact_score': exact_score_prediction,
            'margin_of_victory': margin_prediction,
            'first_half_winner': first_half_prediction,
            'highest_scoring_quarter': quarter_prediction
        }

    def _analyze_game_fundamentals(self, game_context: GameContext) -> Dict[str, Any]:
        """Analyze fundamental game factors for prediction basis"""
        analysis = {
            'home_advantage': 2.5,  # Standard home field advantage
            'weather_impact': 0.0,
            'injury_impact': 0.0,
            'rest_advantage': 0.0,
            'motivation_factor': 0.0,
            'coaching_edge': 0.0,
            'matchup_advantages': {},
            'key_trends': []
        }

        # Weather impact analysis
        if game_context.weather_conditions:
            weather = game_context.weather_conditions
            if weather.get('wind_speed', 0) > 15:
                analysis['weather_impact'] -= 1.5  # Reduces scoring
                analysis['key_trends'].append("High wind conditions")
            if weather.get('temperature', 70) < 32:
                analysis['weather_impact'] -= 1.0  # Cold weather impact
                analysis['key_trends'].append("Cold weather conditions")
            if weather.get('precipitation', 0) > 0.1:
                analysis['weather_impact'] -= 2.0  # Rain/snow impact
                analysis['key_trends'].append("Precipitation expected")

        # Injury impact analysis
        if game_context.has_significant_injuries():
            key_injuries = 0
            for injury_list in [game_context.home_injuries, game_context.away_injuries]:
                for injury in injury_list:
                    if injury.get('position') in ['QB', 'RB', 'WR1', 'LT', 'C'] and injury.get('status') in ['OUT', 'DOUBTFUL']:
                        key_injuries += 1
            analysis['injury_impact'] = -key_injuries * 1.5
            analysis['key_trends'].append(f"{key_injuries} key injuries")

        # Divisional game factors
        if game_context.is_divisional:
            analysis['home_advantage'] += 0.5  # Slight boost for divisional home games
            analysis['key_trends'].append("Divisional rivalry")

        # Primetime game factors
        if game_context.is_primetime:
            analysis['motivation_factor'] += 1.0  # Teams play harder on primetime
            analysis['key_trends'].append("Primetime spotlight")

        # Playoff implications
        if game_context.playoff_implications:
            analysis['motivation_factor'] += 1.5  # High stakes motivation
            analysis['key_trends'].append("Playoff implications")

        return analysis

    def _analyze_margin_potential(self, game_context: GameContext, game_analysis: Dict) -> Dict[str, Any]:
        """Analyze potential margin of victory scenarios"""
        base_margin = abs(game_context.current_spread or 3.0)

        # Adjust margin based on game factors
        adjusted_margin = base_margin
        adjusted_margin += game_analysis['home_advantage'] if game_context.current_spread and game_context.current_spread < 0 else -game_analysis['home_advantage']
        adjusted_margin += game_analysis['weather_impact']
        adjusted_margin += game_analysis['injury_impact']
        adjusted_margin += game_analysis['motivation_factor']

        # Determine blowout potential
        blowout_threshold = 14.0
        close_game_threshold = 7.0

        margin_scenarios = {
            'expected_margin': max(0.5, adjusted_margin),
            'blowout_probability': 0.15 if adjusted_margin > blowout_threshold else 0.05,
            'close_game_probability': 0.65 if adjusted_margin < close_game_threshold else 0.35,
            'overtime_probability': 0.08 if adjusted_margin < 3.0 else 0.02,
            'margin_confidence': 0.60 if abs(adjusted_margin - base_margin) < 2.0 else 0.45
        }

        return margin_scenarios

    def _analyze_scoring_patterns(self, game_context: GameContext, game_analysis: Dict) -> Dict[str, Any]:
        """Analyze expected scoring patterns and totals"""
        base_total = game_context.total_line or 45.5

        # Adjust total based on conditions
        adjusted_total = base_total
        adjusted_total += game_analysis['weather_impact']  # Weather reduces scoring
        adjusted_total += game_analysis['motivation_factor'] * 0.5  # High stakes can increase scoring

        # Team-specific scoring analysis (simplified - would use real team stats)
        home_expected = adjusted_total * 0.52  # Home team slight advantage
        away_expected = adjusted_total * 0.48

        scoring_analysis = {
            'projected_total': adjusted_total,
            'home_projected_score': home_expected,
            'away_projected_score': away_expected,
            'over_probability': 0.52 if adjusted_total > base_total else 0.48,
            'scoring_pace': 'average',  # Would analyze team pace stats
            'red_zone_efficiency': {'home': 0.58, 'away': 0.55},  # Would use real stats
            'turnover_impact': -2.5 if 'turnover_prone' in game_analysis.get('key_trends', []) else 0
        }

        # Determine scoring pace
        if adjusted_total > 50:
            scoring_analysis['scoring_pace'] = 'high'
        elif adjusted_total < 42:
            scoring_analysis['scoring_pace'] = 'low'

        return scoring_analysis

    def _analyze_moneyline_value(self, game_context: GameContext, game_analysis: Dict) -> Dict[str, Any]:
        """Analyze moneyline betting value"""
        spread = game_context.current_spread or 0

        # Convert spread to implied win probability
        if spread == 0:
            home_win_prob = 0.52  # Slight home advantage
            away_win_prob = 0.48
        else:
            # Simplified spread to probability conversion
            spread_advantage = abs(spread) * 0.03  # Each point ≈ 3% win probability
            if spread < 0:  # Home favored
                home_win_prob = 0.52 + spread_advantage
                away_win_prob = 0.48 - spread_advantage
            else:  # Away favored
                home_win_prob = 0.52 - spread_advantage
                away_win_prob = 0.48 + spread_advantage

        # Adjust probabilities based on analysis
        total_adjustment = (game_analysis['home_advantage'] + game_analysis['weather_impact'] +
                          game_analysis['injury_impact'] + game_analysis['motivation_factor']) * 0.02

        home_win_prob = max(0.15, min(0.85, home_win_prob + total_adjustment))
        away_win_prob = 1.0 - home_win_prob

        return {
            'home_win_probability': home_win_prob,
            'away_win_probability': away_win_prob,
            'expected_value_home': 0.05 if home_win_prob > 0.55 else -0.02,
            'expected_value_away': 0.05 if away_win_prob > 0.55 else -0.02,
            'value_confidence': 0.65 if abs(home_win_prob - 0.5) > 0.1 else 0.45
        }

    def _predict_game_winner(self, game_context: GameContext, game_analysis: Dict) -> PredictionWithConfidence:
        """Predict game winner with confidence and reasoning"""
        spread = game_context.current_spread or 0

        # Determine favorite and underdog
        if spread < 0:
            favorite = game_context.home_team
            underdog = game_context.away_team
            favorite_advantage = abs(spread)
        elif spread > 0:
            favorite = game_context.away_team
            underdog = game_context.home_team
            favorite_advantage = abs(spread)
        else:
            favorite = game_context.home_team  # Home advantage in pick'em
            underdog = game_context.away_team
            favorite_advantage = 2.5  # Standard home advantage

        # Calculate total advantage
        total_advantage = favorite_advantage
        total_advantage += game_analysis['home_advantage'] if favorite == game_context.home_team else -game_analysis['home_advantage']
        total_advantage += game_analysis['motivation_factor']
        total_advantage -= abs(game_analysis['weather_impact'])  # Weather creates uncertainty
        total_advantage -= abs(game_analysis['injury_impact'])  # Injuries create uncertainty

        # Determine prediction and confidence
        if total_advantage > 7.0:
            prediction = favorite
            confidence = 0.75
            reasoning = f"{favorite} has significant advantages with {total_advantage:.1f} point edge"
        elif total_advantage > 3.0:
            prediction = favorite
            confidence = 0.65
            reasoning = f"{favorite} favored with {total_advantage:.1f} point advantage"
        elif total_advantage > 0.5:
            prediction = favorite
            confidence = 0.55
            reasoning = f"{favorite} slight edge in close matchup"
        else:
            prediction = underdog
            confidence = 0.52
            reasoning = f"Upset potential with {underdog} getting value"

        # Build key factors
        key_factors = []
        if abs(game_analysis['home_advantage']) > 1.0:
            key_factors.append("Home field advantage")
        if abs(game_analysis['weather_impact']) > 1.0:
            key_factors.append("Weather conditions")
        if abs(game_analysis['injury_impact']) > 1.0:
            key_factors.append("Key injuries")
        if game_analysis['motivation_factor'] > 1.0:
            key_factors.append("Motivation factors")
        key_factors.extend(game_analysis['key_trends'][:2])  # Add top trends

        return PredictionWithConfidence(
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors[:5]
        )

    def _predict_point_spread(self, game_context: GameContext, game_analysis: Dict, margin_analysis: Dict) -> PredictionWithConfidence:
        """Predict point spread with margin analysis"""
        spread = game_context.current_spread or 0
        expected_margin = margin_analysis['expected_margin']

        # Determine spread pick
        if spread < 0:  # Home favored
            if expected_margin > abs(spread):
                pick = "home"
                reasoning = f"Home team expected to win by {expected_margin:.1f}, covering {abs(spread)} point spread"
            else:
                pick = "away"
                reasoning = f"Away team expected to keep it closer than {abs(spread)} point spread"
        elif spread > 0:  # Away favored
            if expected_margin > spread:
                pick = "away"
                reasoning = f"Away team expected to win by {expected_margin:.1f}, covering {spread} point spread"
            else:
                pick = "home"
                reasoning = f"Home team expected to keep it closer than {spread} point spread"
        else:  # Pick'em
            pick = "home" if expected_margin > 0 else "away"
            reasoning = f"Pick'em game with slight edge to {pick} team"

        # Calculate confidence based on margin differential
        margin_differential = abs(expected_margin - abs(spread))
        if margin_differential > 4.0:
            confidence = 0.70
        elif margin_differential > 2.0:
            confidence = 0.60
        elif margin_differential > 1.0:
            confidence = 0.55
        else:
            confidence = 0.50

        # Adjust confidence based on game factors
        confidence += margin_analysis['margin_confidence'] * 0.1
        confidence = max(0.35, min(0.85, confidence))

        key_factors = [
            f"Expected margin: {expected_margin:.1f}",
            f"Spread line: {spread}",
            f"Margin differential: {margin_differential:.1f}"
        ]

        if margin_analysis['blowout_probability'] > 0.15:
            key_factors.append("Blowout potential")
        if margin_analysis['close_game_probability'] > 0.60:
            key_factors.append("Close game expected")

        return PredictionWithConfidence(
            prediction=pick,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors[:5]
        )

    def _predict_total_points(self, game_context: GameContext, scoring_analysis: Dict) -> PredictionWithConfidence:
        """Predict total points with scoring pattern analysis"""
        total_line = game_context.total_line or 45.5
        projected_total = scoring_analysis['projected_total']

        # Determine over/under pick
        if projected_total > total_line + 1.0:
            pick = "over"
            reasoning = f"Projected total of {projected_total:.1f} exceeds line of {total_line}"
        elif projected_total < total_line - 1.0:
            pick = "under"
            reasoning = f"Projected total of {projected_total:.1f} falls short of line of {total_line}"
        else:
            # Close to line - use other factors
            if scoring_analysis['over_probability'] > 0.52:
                pick = "over"
                reasoning = f"Slight lean over with {scoring_analysis['over_probability']:.1%} probability"
            else:
                pick = "under"
                reasoning = f"Slight lean under with {1-scoring_analysis['over_probability']:.1%} probability"

        # Calculate confidence
        total_differential = abs(projected_total - total_line)
        if total_differential > 4.0:
            confidence = 0.68
        elif total_differential > 2.0:
            confidence = 0.58
        elif total_differential > 1.0:
            confidence = 0.52
        else:
            confidence = 0.48

        # Build key factors
        key_factors = [
            f"Projected total: {projected_total:.1f}",
            f"Total line: {total_line}",
            f"Scoring pace: {scoring_analysis['scoring_pace']}"
        ]

        if abs(scoring_analysis['turnover_impact']) > 1.0:
            key_factors.append("Turnover impact")

        weather_impact = game_context.weather_conditions
        if weather_impact and weather_impact.get('impact_level') != 'low':
            key_factors.append("Weather conditions")

        return PredictionWithConfidence(
            prediction=pick,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors[:5]
        )

    def _assess_moneyline_value(self, game_context: GameContext, value_analysis: Dict) -> PredictionWithConfidence:
        """Assess moneyline value with expected value calculation"""
        home_prob = value_analysis['home_win_probability']
        away_prob = value_analysis['away_win_probability']

        # Determine best value pick
        home_ev = value_analysis['expected_value_home']
        away_ev = value_analysis['expected_value_away']

        if home_ev > away_ev and home_ev > 0.02:
            pick = game_context.home_team
            confidence = value_analysis['value_confidence']
            reasoning = f"Home team offers value with {home_prob:.1%} win probability and +{home_ev:.1%} expected value"
        elif away_ev > home_ev and away_ev > 0.02:
            pick = game_context.away_team
            confidence = value_analysis['value_confidence']
            reasoning = f"Away team offers value with {away_prob:.1%} win probability and +{away_ev:.1%} expected value"
        else:
            # Pick higher probability team if no clear value
            if home_prob > away_prob:
                pick = game_context.home_team
                confidence = 0.55
                reasoning = f"Home team favored with {home_prob:.1%} win probability"
            else:
                pick = game_context.away_team
                confidence = 0.55
                reasoning = f"Away team favored with {away_prob:.1%} win probability"

        key_factors = [
            f"Win probability: {max(home_prob, away_prob):.1%}",
            f"Expected value: {max(home_ev, away_ev):+.1%}",
            "Line shopping recommended"
        ]

        return PredictionWithConfidence(
            prediction=pick,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors
        )

    def _predict_exact_score(self, game_context: GameContext, scoring_analysis: Dict) -> PredictionWithConfidence:
        """Predict exact score based on scoring analysis"""
        home_score = int(round(scoring_analysis['home_projected_score']))
        away_score = int(round(scoring_analysis['away_projected_score']))

        # Adjust scores to realistic NFL ranges
        home_score = max(7, min(45, home_score))
        away_score = max(7, min(45, away_score))

        # Ensure scores make sense with spread
        spread = game_context.current_spread or 0
        if spread != 0:
            expected_diff = home_score - away_score
            spread_diff = -spread  # Negative spread means home favored

            # Adjust if scores don't align with spread
            if abs(expected_diff - spread_diff) > 3:
                if spread < 0:  # Home favored
                    home_score = away_score + int(abs(spread))
                else:  # Away favored
                    away_score = home_score + int(spread)

        exact_score = f"{home_score}-{away_score}"

        # Confidence is always low for exact scores
        confidence = 0.25 + (0.1 if abs(home_score - away_score) > 7 else 0)  # Slightly higher for blowouts

        reasoning = f"Score projection based on offensive/defensive efficiency and game conditions"

        key_factors = [
            f"Home projected: {home_score}",
            f"Away projected: {away_score}",
            "Red zone efficiency",
            "Turnover differential",
            "Field position"
        ]

        return PredictionWithConfidence(
            prediction=exact_score,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors
        )

    def _predict_margin_of_victory(self, game_context: GameContext, margin_analysis: Dict) -> PredictionWithConfidence:
        """Predict margin of victory with blowout/close game analysis"""
        expected_margin = margin_analysis['expected_margin']

        # Round to nearest 0.5 for betting purposes
        predicted_margin = round(expected_margin * 2) / 2

        # Determine confidence based on margin scenarios
        if margin_analysis['blowout_probability'] > 0.15:
            confidence = 0.60
            reasoning = f"Blowout potential suggests {predicted_margin:.1f} point margin"
        elif margin_analysis['close_game_probability'] > 0.60:
            confidence = 0.45
            reasoning = f"Close game expected with {predicted_margin:.1f} point margin"
        else:
            confidence = 0.50
            reasoning = f"Standard margin projection of {predicted_margin:.1f} points"

        key_factors = [
            f"Expected margin: {predicted_margin:.1f}",
            f"Blowout probability: {margin_analysis['blowout_probability']:.1%}",
            f"Close game probability: {margin_analysis['close_game_probability']:.1%}"
        ]

        if margin_analysis['overtime_probability'] > 0.05:
            key_factors.append(f"Overtime probability: {margin_analysis['overtime_probability']:.1%}")

        return PredictionWithConfidence(
            prediction=predicted_margin,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors[:5]
        )

    def _predict_first_half_winner(self, game_context: GameContext, game_analysis: Dict) -> PredictionWithConfidence:
        """Predict first half winner based on game script analysis"""
        spread = game_context.current_spread or 0

        # Teams often start conservatively, so first half margins are typically smaller
        first_half_advantage = abs(spread) * 0.6  # First half spreads typically 60% of full game

        if spread < 0:  # Home favored
            if first_half_advantage > 2.0:
                pick = game_context.home_team
                confidence = 0.58
                reasoning = f"Home team expected to establish early lead"
            else:
                pick = game_context.home_team
                confidence = 0.52
                reasoning = f"Slight first half edge to home team"
        elif spread > 0:  # Away favored
            if first_half_advantage > 2.0:
                pick = game_context.away_team
                confidence = 0.58
                reasoning = f"Away team expected to establish early lead"
            else:
                pick = game_context.away_team
                confidence = 0.52
                reasoning = f"Slight first half edge to away team"
        else:  # Pick'em
            pick = game_context.home_team  # Home advantage
            confidence = 0.51
            reasoning = f"Home field advantage in first half"

        # Adjust for game factors
        if game_context.is_primetime:
            confidence += 0.03  # Teams more prepared for primetime starts

        if 'fast_start' in self.specializations:
            confidence += 0.05  # This expert specializes in first half analysis

        key_factors = [
            "Game script analysis",
            "First half trends",
            "Opening drive importance"
        ]

        if game_context.is_primetime:
            key_factors.append("Primetime preparation")

        return PredictionWithConfidence(
            prediction=pick,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors[:5]
        )

    def _predict_highest_scoring_quarter(self, game_context: GameContext, scoring_analysis: Dict) -> PredictionWithConfidence:
        """Predict highest scoring quarter based on game flow analysis"""

        # Historical NFL scoring patterns:
        # Q1: Lower scoring (teams feeling out, conservative)
        # Q2: Higher scoring (two-minute drill, established rhythm)
        # Q3: Moderate scoring (halftime adjustments)
        # Q4: Highest scoring (urgency, prevent defense, garbage time)

        quarter_probabilities = {
            1: 0.15,  # Q1 rarely highest
            2: 0.25,  # Q2 solid chance
            3: 0.20,  # Q3 moderate chance
            4: 0.40   # Q4 most likely
        }

        # Adjust based on game factors
        if scoring_analysis['scoring_pace'] == 'high':
            quarter_probabilities[2] += 0.05  # High-scoring games often peak in Q2
            quarter_probabilities[4] += 0.05  # And continue in Q4
        elif scoring_analysis['scoring_pace'] == 'low':
            quarter_probabilities[4] += 0.10  # Low-scoring games often decided late

        # Weather impact
        if game_context.weather_conditions and game_context.weather_conditions.get('impact_level') == 'high':
            quarter_probabilities[1] += 0.05  # Teams more prepared early in bad weather
            quarter_probabilities[4] -= 0.05

        # Find highest probability quarter
        predicted_quarter = max(quarter_probabilities, key=quarter_probabilities.get)
        confidence = quarter_probabilities[predicted_quarter]

        quarter_names = {1: "First", 2: "Second", 3: "Third", 4: "Fourth"}

        reasoning = f"{quarter_names[predicted_quarter]} quarter expected to be highest scoring based on game flow analysis"

        if predicted_quarter == 4:
            reasoning += " - late game urgency and prevent defense typically increase scoring"
        elif predicted_quarter == 2:
            reasoning += " - two-minute drill and established offensive rhythm"
        elif predicted_quarter == 3:
            reasoning += " - halftime adjustments creating offensive opportunities"

        key_factors = [
            "Historical scoring patterns",
            "Game flow analysis",
            f"Scoring pace: {scoring_analysis['scoring_pace']}"
        ]

        if game_context.weather_conditions:
            key_factors.append("Weather impact")

        return PredictionWithConfidence(
            prediction=predicted_quarter,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors[:5]
        )

    def _generate_quarter_predictions(self, game_context: GameContext) -> Dict[str, QuarterPrediction]:
        """Generate comprehensive quarter-by-quarter predictions with game flow analysis"""

        # Get overall game analysis for context
        game_analysis = self._analyze_game_fundamentals(game_context)
        scoring_analysis = self._analyze_scoring_patterns(game_context, game_analysis)

        # Analyze quarter-specific factors
        quarter_analysis = self._analyze_quarter_patterns(game_context, scoring_analysis)

        quarters = {}
        for q in range(1, 5):
            quarter_pred = self._predict_quarter_score(q, game_context, quarter_analysis)
            quarters[f'q{q}'] = quarter_pred

        return quarters

    def _analyze_quarter_patterns(self, game_context: GameContext, scoring_analysis: Dict) -> Dict[str, Any]:
        """Analyze quarter-specific scoring patterns and game flow"""

        total_projected = scoring_analysis['projected_total']
        home_projected = scoring_analysis['home_projected_score']
        away_projected = scoring_analysis['away_projected_score']

        # Historical NFL quarter scoring distributions
        quarter_distributions = {
            1: 0.22,  # ~22% of total scoring in Q1
            2: 0.28,  # ~28% of total scoring in Q2 (two-minute drill)
            3: 0.24,  # ~24% of total scoring in Q3 (adjustments)
            4: 0.26   # ~26% of total scoring in Q4 (urgency)
        }

        # Adjust distributions based on game factors
        if scoring_analysis['scoring_pace'] == 'high':
            # High-scoring games tend to have more even distribution
            quarter_distributions[1] += 0.02
            quarter_distributions[2] += 0.03
            quarter_distributions[3] -= 0.02
            quarter_distributions[4] -= 0.03
        elif scoring_analysis['scoring_pace'] == 'low':
            # Low-scoring games often have late scoring
            quarter_distributions[1] -= 0.03
            quarter_distributions[2] -= 0.02
            quarter_distributions[3] += 0.01
            quarter_distributions[4] += 0.04

        # Weather impact on quarter distribution
        if game_context.weather_conditions and game_context.weather_conditions.get('impact_level') == 'high':
            # Bad weather favors early scoring when teams are fresh
            quarter_distributions[1] += 0.03
            quarter_distributions[2] += 0.02
            quarter_distributions[3] -= 0.02
            quarter_distributions[4] -= 0.03

        # Divisional games tend to be more conservative early
        if game_context.is_divisional:
            quarter_distributions[1] -= 0.02
            quarter_distributions[2] -= 0.01
            quarter_distributions[3] += 0.01
            quarter_distributions[4] += 0.02

        # Primetime games often start slower but finish strong
        if game_context.is_primetime:
            quarter_distributions[1] -= 0.01
            quarter_distributions[2] += 0.01
            quarter_distributions[3] += 0.01
            quarter_distributions[4] -= 0.01

        return {
            'quarter_distributions': quarter_distributions,
            'total_projected': total_projected,
            'home_projected': home_projected,
            'away_projected': away_projected,
            'game_script_factors': self._analyze_game_script(game_context)
        }

    def _analyze_game_script(self, game_context: GameContext) -> Dict[str, Any]:
        """Analyze expected game script and flow"""
        spread = game_context.current_spread or 0

        script_analysis = {
            'expected_leader': game_context.home_team if spread < 0 else game_context.away_team,
            'blowout_potential': abs(spread) > 7.0,
            'close_game_expected': abs(spread) < 3.0,
            'comeback_potential': 0.25,  # Base comeback probability
            'garbage_time_likely': abs(spread) > 10.0
        }

        # Adjust comeback potential based on teams and context
        if game_context.playoff_implications:
            script_analysis['comeback_potential'] += 0.10  # Teams fight harder

        if game_context.is_divisional:
            script_analysis['comeback_potential'] += 0.05  # Rivalry games

        return script_analysis

    def _predict_quarter_score(self, quarter: int, game_context: GameContext, quarter_analysis: Dict) -> QuarterPrediction:
        """Predict individual quarter score with detailed analysis"""

        quarter_dist = quarter_analysis['quarter_distributions'][quarter]
        total_projected = quarter_analysis['total_projected']
        home_projected = quarter_analysis['home_projected']
        away_projected = quarter_analysis['away_projected']
        script_factors = quarter_analysis['game_script_factors']

        # Calculate base quarter totals
        quarter_total = total_projected * quarter_dist
        home_quarter_base = home_projected * quarter_dist
        away_quarter_base = away_projected * quarter_dist

        # Apply quarter-specific adjustments
        if quarter == 1:
            # Q1: Conservative start, feeling out period
            home_quarter, away_quarter = self._adjust_q1_scoring(
                home_quarter_base, away_quarter_base, game_context, script_factors
            )
            confidence = 0.45
            key_factors = ["Opening game script", "Conservative play calling", "Field position"]

        elif quarter == 2:
            # Q2: Two-minute drill, established rhythm
            home_quarter, away_quarter = self._adjust_q2_scoring(
                home_quarter_base, away_quarter_base, game_context, script_factors
            )
            confidence = 0.50
            key_factors = ["Two-minute drill", "Red zone efficiency", "Rhythm established"]

        elif quarter == 3:
            # Q3: Halftime adjustments, fresh start
            home_quarter, away_quarter = self._adjust_q3_scoring(
                home_quarter_base, away_quarter_base, game_context, script_factors
            )
            confidence = 0.48
            key_factors = ["Halftime adjustments", "Second half script", "Coaching impact"]

        else:  # quarter == 4
            # Q4: Urgency, prevent defense, garbage time
            home_quarter, away_quarter = self._adjust_q4_scoring(
                home_quarter_base, away_quarter_base, game_context, script_factors
            )
            confidence = 0.42
            key_factors = ["Fourth quarter urgency", "Prevent defense", "Game situation"]

        # Round to realistic NFL quarter scores
        home_quarter = max(0, int(round(home_quarter)))
        away_quarter = max(0, int(round(away_quarter)))

        # Ensure at least some scoring variety
        if home_quarter == 0 and away_quarter == 0 and quarter_total > 2:
            if random.random() > 0.5:
                home_quarter = 3  # Field goal
            else:
                away_quarter = 3

        return QuarterPrediction(
            quarter=quarter,
            home_score=home_quarter,
            away_score=away_quarter,
            total_points=home_quarter + away_quarter,
            confidence=confidence,
            key_factors=key_factors
        )

    def _adjust_q1_scoring(self, home_base: float, away_base: float, game_context: GameContext, script_factors: Dict) -> Tuple[float, float]:
        """Adjust Q1 scoring for opening game dynamics"""
        # Q1 is typically lower scoring - teams feeling each other out
        home_adj = home_base * 0.9  # Slightly conservative
        away_adj = away_base * 0.9

        # Weather has bigger impact early when teams aren't warmed up
        if game_context.weather_conditions and game_context.weather_conditions.get('temperature', 70) < 32:
            home_adj *= 0.85
            away_adj *= 0.85

        # Primetime games often start slower
        if game_context.is_primetime:
            home_adj *= 0.95
            away_adj *= 0.95

        # Home teams often start stronger
        home_adj *= 1.05

        return home_adj, away_adj

    def _adjust_q2_scoring(self, home_base: float, away_base: float, game_context: GameContext, script_factors: Dict) -> Tuple[float, float]:
        """Adjust Q2 scoring for two-minute drill and rhythm"""
        # Q2 often highest scoring due to two-minute drill
        home_adj = home_base * 1.1
        away_adj = away_base * 1.1

        # Teams with good two-minute offense get boost
        # (In real implementation, would use team stats)
        if script_factors['expected_leader'] == game_context.home_team:
            home_adj *= 1.05  # Leader often scores before half
        else:
            away_adj *= 1.05

        # Close games have more urgency before half
        if script_factors['close_game_expected']:
            home_adj *= 1.08
            away_adj *= 1.08

        return home_adj, away_adj

    def _adjust_q3_scoring(self, home_base: float, away_base: float, game_context: GameContext, script_factors: Dict) -> Tuple[float, float]:
        """Adjust Q3 scoring for halftime adjustments"""
        # Q3 scoring depends heavily on halftime adjustments
        home_adj = home_base
        away_adj = away_base

        # Team that was trailing often comes out stronger
        if script_factors['comeback_potential'] > 0.3:
            # Boost the expected underdog
            if game_context.current_spread and game_context.current_spread > 0:
                home_adj *= 1.1  # Home team trailing
            else:
                away_adj *= 1.1  # Away team trailing

        # Coaching matchup can matter more in Q3
        if 'coaching_advantage' in game_context.__dict__:
            # Would implement coaching edge logic
            pass

        return home_adj, away_adj

    def _adjust_q4_scoring(self, home_base: float, away_base: float, game_context: GameContext, script_factors: Dict) -> Tuple[float, float]:
        """Adjust Q4 scoring for urgency and game situation"""
        # Q4 scoring highly dependent on game situation
        home_adj = home_base
        away_adj = away_base

        # Blowouts often have garbage time scoring
        if script_factors['garbage_time_likely']:
            home_adj *= 1.15
            away_adj *= 1.15

        # Close games have more urgency and prevent defense
        elif script_factors['close_game_expected']:
            home_adj *= 1.2  # Urgency increases scoring
            away_adj *= 1.2

        # Comeback potential affects trailing team
        if script_factors['comeback_potential'] > 0.3:
            # Trailing team gets boost, leading team might play prevent
            if game_context.current_spread and game_context.current_spread > 0:
                home_adj *= 1.15  # Home trailing, more urgency
                away_adj *= 1.05  # Away leading, prevent defense
            else:
                away_adj *= 1.15  # Away trailing, more urgency
                home_adj *= 1.05  # Home leading, prevent defense

        return home_adj, away_adj

    def _generate_player_props(self, game_context: GameContext) -> Dict[str, List[PlayerPropPrediction]]:
        """Generate comprehensive player prop predictions with detailed analysis"""

        # Analyze player matchups and game conditions
        player_analysis = self._analyze_player_matchups(game_context)

        return {
            'qb_passing_yards': self._predict_qb_passing_yards(game_context, player_analysis),
            'qb_touchdowns': self._predict_qb_touchdowns(game_context, player_analysis),
            'qb_completions': self._predict_qb_completions(game_context, player_analysis),
            'qb_interceptions': self._predict_qb_interceptions(game_context, player_analysis),
            'rb_rushing_yards': self._predict_rb_rushing_yards(game_context, player_analysis),
            'rb_attempts': self._predict_rb_attempts(game_context, player_analysis),
            'rb_touchdowns': self._predict_rb_touchdowns(game_context, player_analysis),
            'wr_receiving_yards': self._predict_wr_receiving_yards(game_context, player_analysis),
            'wr_receptions': self._predict_wr_receptions(game_context, player_analysis),
            'wr_touchdowns': self._predict_wr_touchdowns(game_context, player_analysis)
        }

    def _analyze_player_matchups(self, game_context: GameContext) -> Dict[str, Any]:
        """Analyze player matchups and conditions affecting props"""

        analysis = {
            # QB Analysis
            'qb_matchups': {
                'home': {
                    'pass_defense_rank': 15,  # Would use real defensive rankings
                    'pressure_rate_allowed': 0.25,  # Would use real O-line stats
                    'red_zone_td_rate': 0.58,  # Would use real red zone stats
                    'weather_impact': 0.0,
                    'injury_impact': 0.0
                },
                'away': {
                    'pass_defense_rank': 18,
                    'pressure_rate_allowed': 0.28,
                    'red_zone_td_rate': 0.55,
                    'weather_impact': 0.0,
                    'injury_impact': 0.0
                }
            },

            # RB Analysis
            'rb_matchups': {
                'home': {
                    'run_defense_rank': 12,
                    'yards_per_carry_allowed': 4.3,
                    'goal_line_td_rate': 0.65,
                    'game_script_boost': 0.0
                },
                'away': {
                    'run_defense_rank': 20,
                    'yards_per_carry_allowed': 4.7,
                    'goal_line_td_rate': 0.58,
                    'game_script_boost': 0.0
                }
            },

            # WR Analysis
            'wr_matchups': {
                'home': {
                    'target_share': {'wr1': 0.28, 'wr2': 0.18, 'wr3': 0.12},
                    'coverage_difficulty': 'average',
                    'separation_advantage': 0.0
                },
                'away': {
                    'target_share': {'wr1': 0.25, 'wr2': 0.20, 'wr3': 0.15},
                    'coverage_difficulty': 'average',
                    'separation_advantage': 0.0
                }
            },

            # Game conditions
            'game_conditions': {
                'total_plays_projected': 130,  # Average NFL game
                'pass_play_percentage': 0.60,
                'weather_passing_impact': 0.0,
                'pace_factor': 1.0
            }
        }

        # Weather impact analysis
        if game_context.weather_conditions:
            weather = game_context.weather_conditions

            # Wind affects passing significantly
            if weather.get('wind_speed', 0) > 15:
                analysis['qb_matchups']['home']['weather_impact'] = -0.15
                analysis['qb_matchups']['away']['weather_impact'] = -0.15
                analysis['game_conditions']['weather_passing_impact'] = -0.15

            # Cold weather affects ball handling
            if weather.get('temperature', 70) < 32:
                analysis['qb_matchups']['home']['weather_impact'] -= 0.08
                analysis['qb_matchups']['away']['weather_impact'] -= 0.08

            # Precipitation heavily impacts passing
            if weather.get('precipitation', 0) > 0.1:
                analysis['qb_matchups']['home']['weather_impact'] -= 0.20
                analysis['qb_matchups']['away']['weather_impact'] -= 0.20
                analysis['game_conditions']['pass_play_percentage'] -= 0.10  # More running

        # Game script analysis
        spread = game_context.current_spread or 0
        if abs(spread) > 7:  # Likely blowout
            if spread < 0:  # Home favored
                analysis['rb_matchups']['home']['game_script_boost'] = 0.15  # More running when leading
                analysis['qb_matchups']['away']['weather_impact'] += 0.10  # Trailing team passes more
            else:  # Away favored
                analysis['rb_matchups']['away']['game_script_boost'] = 0.15
                analysis['qb_matchups']['home']['weather_impact'] += 0.10

        # Injury impact
        if game_context.has_significant_injuries():
            for injury_list, team in [(game_context.home_injuries, 'home'), (game_context.away_injuries, 'away')]:
                for injury in injury_list:
                    pos = injury.get('position', '')
                    status = injury.get('status', '')

                    if status in ['OUT', 'DOUBTFUL']:
                        if pos == 'QB':
                            # Backup QB significantly impacts all passing props
                            analysis['qb_matchups'][team]['injury_impact'] = -0.25
                        elif pos in ['WR1', 'WR']:
                            # Top WR injury boosts other receivers
                            analysis['wr_matchups'][team]['target_share']['wr2'] += 0.08
                            analysis['wr_matchups'][team]['target_share']['wr3'] += 0.05
                        elif pos in ['RB', 'RB1']:
                            # RB injury affects rushing props significantly
                            analysis['rb_matchups'][team]['game_script_boost'] -= 0.20

        return analysis

    def _predict_qb_passing_yards(self, game_context: GameContext, player_analysis: Dict) -> List[PlayerPropPrediction]:
        """Predict QB passing yards props"""
        predictions = []

        for team, qb_name in [('home', 'Home QB'), ('away', 'Away QB')]:
            matchup = player_analysis['qb_matchups'][team]

            # Base projection (NFL average ~250 yards)
            base_yards = 250.0

            # Adjust for matchup quality
            defense_rank = matchup['pass_defense_rank']
            if defense_rank <= 10:  # Top 10 defense
                base_yards -= 25
            elif defense_rank >= 25:  # Bottom 8 defense
                base_yards += 30

            # Adjust for pressure
            pressure_impact = matchup['pressure_rate_allowed'] * -100  # More pressure = fewer yards
            base_yards += pressure_impact

            # Weather impact
            base_yards += matchup['weather_impact'] * 150

            # Injury impact
            base_yards += matchup['injury_impact'] * 100

            # Game script impact
            spread = game_context.current_spread or 0
            if (team == 'home' and spread > 3) or (team == 'away' and spread < -3):
                base_yards += 20  # Trailing teams pass more

            projected_yards = max(180, min(350, base_yards))  # Reasonable bounds

            # Common betting lines
            if projected_yards > 280:
                line = 279.5
            elif projected_yards > 260:
                line = 267.5
            elif projected_yards > 240:
                line = 249.5
            else:
                line = 229.5

            # Determine prediction
            if projected_yards > line + 15:
                prediction = "over"
                confidence = 0.65
            elif projected_yards > line + 5:
                prediction = "over"
                confidence = 0.58
            elif projected_yards < line - 15:
                prediction = "under"
                confidence = 0.65
            elif projected_yards < line - 5:
                prediction = "under"
                confidence = 0.58
            else:
                prediction = "over" if projected_yards > line else "under"
                confidence = 0.52

            # Build reasoning
            reasoning_factors = []
            if defense_rank <= 10:
                reasoning_factors.append("tough pass defense")
            elif defense_rank >= 25:
                reasoning_factors.append("weak pass defense")

            if matchup['pressure_rate_allowed'] > 0.30:
                reasoning_factors.append("poor pass protection")
            elif matchup['pressure_rate_allowed'] < 0.20:
                reasoning_factors.append("strong pass protection")

            if abs(matchup['weather_impact']) > 0.1:
                reasoning_factors.append("weather conditions")

            if matchup['injury_impact'] < -0.1:
                reasoning_factors.append("key injuries")

            reasoning = f"Projected {projected_yards:.0f} yards based on " + ", ".join(reasoning_factors[:3])

            predictions.append(PlayerPropPrediction(
                player_name=qb_name,
                position="QB",
                team=game_context.home_team if team == 'home' else game_context.away_team,
                prop_type="passing_yards",
                over_under_line=line,
                prediction=prediction,
                projected_value=projected_yards,
                confidence=confidence,
                reasoning=reasoning
            ))

        return predictions

    def _predict_qb_touchdowns(self, game_context: GameContext, player_analysis: Dict) -> List[PlayerPropPrediction]:
        """Predict QB passing touchdown props"""
        predictions = []

        for team, qb_name in [('home', 'Home QB'), ('away', 'Away QB')]:
            matchup = player_analysis['qb_matchups'][team]

            # Base projection (NFL average ~1.8 passing TDs)
            base_tds = 1.8

            # Adjust for red zone efficiency
            rz_rate = matchup['red_zone_td_rate']
            if rz_rate > 0.60:
                base_tds += 0.4
            elif rz_rate < 0.50:
                base_tds -= 0.3

            # Weather impact (cold/wind reduces passing TDs)
            base_tds += matchup['weather_impact'] * 2

            # Injury impact
            base_tds += matchup['injury_impact'] * 2

            # Game script (trailing teams throw more in red zone)
            spread = game_context.current_spread or 0
            if (team == 'home' and spread > 3) or (team == 'away' and spread < -3):
                base_tds += 0.2

            projected_tds = max(0.5, min(4.0, base_tds))

            # Common betting lines
            if projected_tds > 2.2:
                line = 2.5
            elif projected_tds > 1.8:
                line = 1.5
            else:
                line = 1.5

            # Determine prediction
            if projected_tds > line + 0.3:
                prediction = "over"
                confidence = 0.62
            elif projected_tds > line + 0.1:
                prediction = "over"
                confidence = 0.55
            elif projected_tds < line - 0.3:
                prediction = "under"
                confidence = 0.62
            elif projected_tds < line - 0.1:
                prediction = "under"
                confidence = 0.55
            else:
                prediction = "over" if projected_tds > line else "under"
                confidence = 0.50

            reasoning = f"Projected {projected_tds:.1f} TDs based on red zone efficiency ({rz_rate:.1%})"

            predictions.append(PlayerPropPrediction(
                player_name=qb_name,
                position="QB",
                team=game_context.home_team if team == 'home' else game_context.away_team,
                prop_type="passing_touchdowns",
                over_under_line=line,
                prediction=prediction,
                projected_value=projected_tds,
                confidence=confidence,
                reasoning=reasoning
            ))

        return predictions

    def _predict_qb_completions(self, game_context: GameContext, player_analysis: Dict) -> List[PlayerPropPrediction]:
        """Predict QB completion props"""
        predictions = []

        for team, qb_name in [('home', 'Home QB'), ('away', 'Away QB')]:
            matchup = player_analysis['qb_matchups'][team]

            # Base completions (NFL average ~22)
            base_completions = 22.0

            # Adjust for pressure (more pressure = fewer completions)
            pressure_impact = matchup['pressure_rate_allowed'] * -15
            base_completions += pressure_impact

            # Weather impact
            base_completions += matchup['weather_impact'] * 20

            # Game script
            spread = game_context.current_spread or 0
            if (team == 'home' and spread > 3) or (team == 'away' and spread < -3):
                base_completions += 3  # Trailing teams attempt more passes

            projected_completions = max(15, min(35, base_completions))

            # Common lines
            if projected_completions > 25:
                line = 24.5
            elif projected_completions > 22:
                line = 22.5
            else:
                line = 20.5

            prediction = "over" if projected_completions > line else "under"
            confidence = 0.55 if abs(projected_completions - line) > 2 else 0.50

            reasoning = f"Projected {projected_completions:.0f} completions based on game conditions"

            predictions.append(PlayerPropPrediction(
                player_name=qb_name,
                position="QB",
                team=game_context.home_team if team == 'home' else game_context.away_team,
                prop_type="completions",
                over_under_line=line,
                prediction=prediction,
                projected_value=projected_completions,
                confidence=confidence,
                reasoning=reasoning
            ))

        return predictions

    def _predict_qb_interceptions(self, game_context: GameContext, player_analysis: Dict) -> List[PlayerPropPrediction]:
        """Predict QB interception props"""
        predictions = []

        for team, qb_name in [('home', 'Home QB'), ('away', 'Away QB')]:
            matchup = player_analysis['qb_matchups'][team]

            # Base interceptions (NFL average ~0.8)
            base_ints = 0.8

            # Weather increases interceptions
            if matchup['weather_impact'] < -0.1:
                base_ints += 0.3

            # Pressure increases interceptions
            if matchup['pressure_rate_allowed'] > 0.30:
                base_ints += 0.2

            # Injury impact (backup QBs throw more INTs)
            if matchup['injury_impact'] < -0.1:
                base_ints += 0.4

            projected_ints = max(0.2, min(2.5, base_ints))

            # Most common line
            line = 0.5

            prediction = "over" if projected_ints > 0.7 else "under"
            confidence = 0.58 if projected_ints > 1.0 or projected_ints < 0.5 else 0.52

            reasoning = f"Projected {projected_ints:.1f} interceptions based on conditions"

            predictions.append(PlayerPropPrediction(
                player_name=qb_name,
                position="QB",
                team=game_context.home_team if team == 'home' else game_context.away_team,
                prop_type="interceptions",
                over_under_line=line,
                prediction=prediction,
                projected_value=projected_ints,
                confidence=confidence,
                reasoning=reasoning
            ))

        return predictions

    def _predict_rb_rushing_yards(self, game_context: GameContext, player_analysis: Dict) -> List[PlayerPropPrediction]:
        """Predict RB rushing yards props"""
        predictions = []

        for team, rb_name in [('home', 'Home RB1'), ('away', 'Away RB1')]:
            matchup = player_analysis['rb_matchups'][team]

            # Base rushing yards (NFL RB1 average ~85)
            base_yards = 85.0

            # Adjust for run defense quality
            ypc_allowed = matchup['yards_per_carry_allowed']
            if ypc_allowed > 4.5:
                base_yards += 20  # Weak run defense
            elif ypc_allowed < 4.0:
                base_yards -= 15  # Strong run defense

            # Game script boost
            base_yards += matchup['game_script_boost'] * 100

            # Weather can favor running
            if game_context.weather_conditions and game_context.weather_conditions.get('precipitation', 0) > 0.1:
                base_yards += 15  # More running in bad weather

            projected_yards = max(40, min(150, base_yards))

            # Common lines
            if projected_yards > 90:
                line = 89.5
            elif projected_yards > 75:
                line = 74.5
            else:
                line = 59.5

            prediction = "over" if projected_yards > line + 8 else "under" if projected_yards < line - 8 else ("over" if projected_yards > line else "under")
            confidence = 0.60 if abs(projected_yards - line) > 12 else 0.52

            reasoning = f"Projected {projected_yards:.0f} yards vs {matchup['run_defense_rank']} ranked run defense"

            predictions.append(PlayerPropPrediction(
                player_name=rb_name,
                position="RB",
                team=game_context.home_team if team == 'home' else game_context.away_team,
                prop_type="rushing_yards",
                over_under_line=line,
                prediction=prediction,
                projected_value=projected_yards,
                confidence=confidence,
                reasoning=reasoning
            ))

        return predictions

    def _predict_rb_attempts(self, game_context: GameContext, player_analysis: Dict) -> List[PlayerPropPrediction]:
        """Predict RB rushing attempts props"""
        predictions = []

        for team, rb_name in [('home', 'Home RB1'), ('away', 'Away RB1')]:
            matchup = player_analysis['rb_matchups'][team]

            # Base attempts (NFL RB1 average ~18)
            base_attempts = 18.0

            # Game script heavily affects attempts
            base_attempts += matchup['game_script_boost'] * 25

            # Weather increases running
            if game_context.weather_conditions and game_context.weather_conditions.get('precipitation', 0) > 0.1:
                base_attempts += 3

            projected_attempts = max(10, min(30, base_attempts))

            # Common lines
            if projected_attempts > 20:
                line = 19.5
            elif projected_attempts > 16:
                line = 16.5
            else:
                line = 14.5

            prediction = "over" if projected_attempts > line else "under"
            confidence = 0.58 if abs(projected_attempts - line) > 3 else 0.52

            reasoning = f"Projected {projected_attempts:.0f} attempts based on game script"

            predictions.append(PlayerPropPrediction(
                player_name=rb_name,
                position="RB",
                team=game_context.home_team if team == 'home' else game_context.away_team,
                prop_type="rushing_attempts",
                over_under_line=line,
                prediction=prediction,
                projected_value=projected_attempts,
                confidence=confidence,
                reasoning=reasoning
            ))

        return predictions

    def _predict_rb_touchdowns(self, game_context: GameContext, player_analysis: Dict) -> List[PlayerPropPrediction]:
        """Predict RB rushing touchdown props"""
        predictions = []

        for team, rb_name in [('home', 'Home RB1'), ('away', 'Away RB1')]:
            matchup = player_analysis['rb_matchups'][team]

            # Base TDs (NFL RB1 average ~0.7)
            base_tds = 0.7

            # Goal line efficiency
            gl_rate = matchup['goal_line_td_rate']
            if gl_rate > 0.65:
                base_tds += 0.2
            elif gl_rate < 0.55:
                base_tds -= 0.15

            # Game script boost
            base_tds += matchup['game_script_boost'] * 0.8

            projected_tds = max(0.2, min(2.0, base_tds))

            # Most common line
            line = 0.5

            prediction = "over" if projected_tds > 0.65 else "under"
            confidence = 0.55 if projected_tds > 0.8 or projected_tds < 0.4 else 0.50

            reasoning = f"Projected {projected_tds:.1f} TDs with {gl_rate:.1%} goal line rate"

            predictions.append(PlayerPropPrediction(
                player_name=rb_name,
                position="RB",
                team=game_context.home_team if team == 'home' else game_context.away_team,
                prop_type="rushing_touchdowns",
                over_under_line=line,
                prediction=prediction,
                projected_value=projected_tds,
                confidence=confidence,
                reasoning=reasoning
            ))

        return predictions

    def _predict_wr_receiving_yards(self, game_context: GameContext, player_analysis: Dict) -> List[PlayerPropPrediction]:
        """Predict WR receiving yards props"""
        predictions = []

        for team in ['home', 'away']:
            matchup = player_analysis['wr_matchups'][team]
            team_name = game_context.home_team if team == 'home' else game_context.away_team

            # Predict for WR1 and WR2
            for wr_num in ['wr1', 'wr2']:
                wr_name = f"{team.title()} {wr_num.upper()}"

                # Base yards based on target share
                target_share = matchup['target_share'][wr_num]
                base_yards = target_share * 400  # Rough conversion from target share to yards

                # Adjust for coverage difficulty
                if matchup['coverage_difficulty'] == 'tough':
                    base_yards *= 0.85
                elif matchup['coverage_difficulty'] == 'favorable':
                    base_yards *= 1.15

                # Weather impact
                qb_weather_impact = player_analysis['qb_matchups'][team]['weather_impact']
                base_yards += qb_weather_impact * 100

                projected_yards = max(30, min(150, base_yards))

                # Common lines based on WR tier
                if wr_num == 'wr1':
                    if projected_yards > 85:
                        line = 84.5
                    elif projected_yards > 70:
                        line = 69.5
                    else:
                        line = 54.5
                else:  # wr2
                    if projected_yards > 60:
                        line = 59.5
                    elif projected_yards > 45:
                        line = 44.5
                    else:
                        line = 34.5

                prediction = "over" if projected_yards > line + 8 else "under" if projected_yards < line - 8 else ("over" if projected_yards > line else "under")
                confidence = 0.58 if abs(projected_yards - line) > 10 else 0.52

                reasoning = f"Projected {projected_yards:.0f} yards with {target_share:.1%} target share"

                predictions.append(PlayerPropPrediction(
                    player_name=wr_name,
                    position="WR",
                    team=team_name,
                    prop_type="receiving_yards",
                    over_under_line=line,
                    prediction=prediction,
                    projected_value=projected_yards,
                    confidence=confidence,
                    reasoning=reasoning
                ))

        return predictions

    def _predict_wr_receptions(self, game_context: GameContext, player_analysis: Dict) -> List[PlayerPropPrediction]:
        """Predict WR reception props"""
        predictions = []

        for team in ['home', 'away']:
            matchup = player_analysis['wr_matchups'][team]
            team_name = game_context.home_team if team == 'home' else game_context.away_team

            for wr_num in ['wr1', 'wr2']:
                wr_name = f"{team.title()} {wr_num.upper()}"

                # Base receptions from target share
                target_share = matchup['target_share'][wr_num]
                base_receptions = target_share * 35  # Rough conversion

                # Weather reduces completion rate
                qb_weather_impact = player_analysis['qb_matchups'][team]['weather_impact']
                base_receptions += qb_weather_impact * 10

                projected_receptions = max(2, min(12, base_receptions))

                # Common lines
                if wr_num == 'wr1':
                    if projected_receptions > 6.5:
                        line = 6.5
                    elif projected_receptions > 5:
                        line = 5.5
                    else:
                        line = 4.5
                else:  # wr2
                    if projected_receptions > 5:
                        line = 4.5
                    elif projected_receptions > 3.5:
                        line = 3.5
                    else:
                        line = 2.5

                prediction = "over" if projected_receptions > line else "under"
                confidence = 0.55 if abs(projected_receptions - line) > 1 else 0.50

                reasoning = f"Projected {projected_receptions:.1f} receptions with {target_share:.1%} target share"

                predictions.append(PlayerPropPrediction(
                    player_name=wr_name,
                    position="WR",
                    team=team_name,
                    prop_type="receptions",
                    over_under_line=line,
                    prediction=prediction,
                    projected_value=projected_receptions,
                    confidence=confidence,
                    reasoning=reasoning
                ))

        return predictions

    def _predict_wr_touchdowns(self, game_context: GameContext, player_analysis: Dict) -> List[PlayerPropPrediction]:
        """Predict WR touchdown props"""
        predictions = []

        for team in ['home', 'away']:
            matchup = player_analysis['wr_matchups'][team]
            team_name = game_context.home_team if team == 'home' else game_context.away_team

            # Only predict for WR1 (most common prop)
            wr_name = f"{team.title()} WR1"

            # Base TD probability
            target_share = matchup['target_share']['wr1']
            base_tds = target_share * 2.5  # Rough conversion

            # Red zone target share typically higher for WR1
            rz_rate = player_analysis['qb_matchups'][team]['red_zone_td_rate']
            base_tds *= rz_rate / 0.58  # Adjust for team's red zone efficiency

            projected_tds = max(0.2, min(1.5, base_tds))

            # Most common line
            line = 0.5

            prediction = "over" if projected_tds > 0.6 else "under"
            confidence = 0.52 if projected_tds > 0.7 or projected_tds < 0.4 else 0.48

            reasoning = f"Projected {projected_tds:.1f} TDs with {target_share:.1%} target share"

            predictions.append(PlayerPropPrediction(
                player_name=wr_name,
                position="WR",
                team=team_name,
                prop_type="receiving_touchdowns",
                over_under_line=line,
                prediction=prediction,
                projected_value=projected_tds,
                confidence=confidence,
                reasoning=reasoning
            ))

        return predictions

    def _generate_situational_predictions(self, game_context: GameContext) -> Dict[str, PredictionWithConfidence]:
        """Generate comprehensive situational predictions with detailed analysis"""

        # Analyze situational factors
        situational_analysis = self._analyze_situational_factors(game_context)

        return {
            'turnover_differential': self._predict_turnover_differential(game_context, situational_analysis),
            'red_zone_efficiency': self._predict_red_zone_efficiency(game_context, situational_analysis),
            'third_down_conversion': self._predict_third_down_conversion(game_context, situational_analysis),
            'time_of_possession': self._predict_time_of_possession(game_context, situational_analysis),
            'sacks': self._predict_sack_total(game_context, situational_analysis),
            'penalties': self._predict_penalty_total(game_context, situational_analysis)
        }

    def _analyze_situational_factors(self, game_context: GameContext) -> Dict[str, Any]:
        """Analyze situational factors that affect game outcomes"""

        analysis = {
            # Turnover factors
            'weather_turnover_impact': 0.0,
            'pressure_differential': 0.0,
            'ball_security_edge': 'even',

            # Red zone factors
            'red_zone_advantage': 'even',
            'goal_line_strength': {'home': 0.58, 'away': 0.55},  # Default NFL averages

            # Third down factors
            'pass_rush_advantage': 'even',
            'coverage_advantage': 'even',
            'third_down_edge': 'even',

            # Time of possession factors
            'running_game_edge': 'even',
            'game_script_control': 'even',
            'pace_preference': 'average',

            # Sack factors
            'pass_rush_quality': {'home': 0.5, 'away': 0.5},
            'oline_protection': {'home': 0.5, 'away': 0.5},
            'sack_rate_projection': 6.5,  # NFL average per game

            # Penalty factors
            'discipline_edge': 'even',
            'referee_tendency': 'average',
            'penalty_rate_projection': 12.0  # NFL average per game
        }

        # Weather impact on turnovers
        if game_context.weather_conditions:
            weather = game_context.weather_conditions
            if weather.get('wind_speed', 0) > 15:
                analysis['weather_turnover_impact'] += 1.0  # Wind causes fumbles/INTs
            if weather.get('precipitation', 0) > 0.1:
                analysis['weather_turnover_impact'] += 1.5  # Rain/snow increases turnovers
            if weather.get('temperature', 70) < 32:
                analysis['weather_turnover_impact'] += 0.5  # Cold affects ball handling

        # Injury impact on situational factors
        if game_context.has_significant_injuries():
            for injury_list, team in [(game_context.home_injuries, 'home'), (game_context.away_injuries, 'away')]:
                for injury in injury_list:
                    pos = injury.get('position', '')
                    status = injury.get('status', '')

                    if status in ['OUT', 'DOUBTFUL']:
                        if pos == 'QB':
                            # Backup QB affects all situational factors
                            analysis['red_zone_advantage'] = 'away' if team == 'home' else 'home'
                            analysis['third_down_edge'] = 'away' if team == 'home' else 'home'
                            analysis['ball_security_edge'] = 'away' if team == 'home' else 'home'
                        elif pos in ['LT', 'C', 'RT']:
                            # O-line injuries affect pass protection
                            analysis['oline_protection'][team] -= 0.15
                        elif pos in ['DE', 'OLB', 'DT']:
                            # Pass rush injuries
                            analysis['pass_rush_quality'][team] -= 0.1

        # Game context adjustments
        if game_context.is_divisional:
            # Divisional games tend to be more physical and penalty-prone
            analysis['penalty_rate_projection'] += 1.5
            analysis['discipline_edge'] = 'deteriorates'

        if game_context.is_primetime:
            # Primetime games often have fewer penalties (more preparation)
            analysis['penalty_rate_projection'] -= 1.0
            analysis['discipline_edge'] = 'improves'

        return analysis

    def _predict_turnover_differential(self, game_context: GameContext, situational_analysis: Dict) -> PredictionWithConfidence:
        """Predict turnover differential with detailed analysis"""

        # Base turnover expectation (NFL average ~2.3 turnovers per team per game)
        base_turnovers = 2.3
        weather_impact = situational_analysis['weather_turnover_impact']

        # Calculate expected turnovers for each team
        home_turnovers = base_turnovers + (weather_impact * 0.3)
        away_turnovers = base_turnovers + (weather_impact * 0.3)

        # Adjust based on ball security edge
        if situational_analysis['ball_security_edge'] == 'home':
            home_turnovers -= 0.5
            away_turnovers += 0.3
        elif situational_analysis['ball_security_edge'] == 'away':
            away_turnovers -= 0.5
            home_turnovers += 0.3

        # Calculate differential
        differential = home_turnovers - away_turnovers

        if differential > 0.5:
            prediction = f"{game_context.away_team} +{abs(differential):.0f}"
            confidence = 0.55
            reasoning = f"Away team expected to win turnover battle by {abs(differential):.1f}"
        elif differential < -0.5:
            prediction = f"{game_context.home_team} +{abs(differential):.0f}"
            confidence = 0.55
            reasoning = f"Home team expected to win turnover battle by {abs(differential):.1f}"
        else:
            prediction = "Even"
            confidence = 0.45
            reasoning = "Turnover differential expected to be minimal"

        key_factors = ["Ball security", "Defensive pressure"]

        if weather_impact > 0.5:
            key_factors.append("Weather conditions")
        if situational_analysis['ball_security_edge'] != 'even':
            key_factors.append("Ball handling edge")

        return PredictionWithConfidence(
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors[:5]
        )

    def _predict_red_zone_efficiency(self, game_context: GameContext, situational_analysis: Dict) -> PredictionWithConfidence:
        """Predict red zone efficiency comparison"""

        home_rz_rate = situational_analysis['goal_line_strength']['home']
        away_rz_rate = situational_analysis['goal_line_strength']['away']

        # Determine which team has red zone advantage
        if home_rz_rate > away_rz_rate + 0.05:
            prediction = f"{game_context.home_team} advantage"
            confidence = 0.60
            reasoning = f"Home team red zone efficiency edge ({home_rz_rate:.1%} vs {away_rz_rate:.1%})"
        elif away_rz_rate > home_rz_rate + 0.05:
            prediction = f"{game_context.away_team} advantage"
            confidence = 0.60
            reasoning = f"Away team red zone efficiency edge ({away_rz_rate:.1%} vs {home_rz_rate:.1%})"
        else:
            prediction = "Even matchup"
            confidence = 0.50
            reasoning = f"Red zone efficiency closely matched ({home_rz_rate:.1%} vs {away_rz_rate:.1%})"

        key_factors = [
            "Goal line offense vs defense",
            "Red zone play calling",
            "Short yardage situations"
        ]

        # Add injury impact if relevant
        if game_context.has_significant_injuries():
            key_factors.append("Key injury impact")

        return PredictionWithConfidence(
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors
        )

    def _predict_third_down_conversion(self, game_context: GameContext, situational_analysis: Dict) -> PredictionWithConfidence:
        """Predict third down conversion advantage"""

        pass_rush_adv = situational_analysis['pass_rush_advantage']
        coverage_adv = situational_analysis['coverage_advantage']

        # Determine third down edge
        if pass_rush_adv == 'home' or coverage_adv == 'home':
            prediction = f"{game_context.home_team} defensive edge"
            confidence = 0.58
            reasoning = "Home team pass rush/coverage advantage on third downs"
        elif pass_rush_adv == 'away' or coverage_adv == 'away':
            prediction = f"{game_context.away_team} defensive edge"
            confidence = 0.58
            reasoning = "Away team pass rush/coverage advantage on third downs"
        else:
            prediction = "Even matchup"
            confidence = 0.50
            reasoning = "Third down conversion rates expected to be similar"

        key_factors = [
            "Pass rush effectiveness",
            "Coverage quality",
            "Third down play calling"
        ]

        # Weather can affect third down passing
        if game_context.weather_conditions and game_context.weather_conditions.get('wind_speed', 0) > 15:
            key_factors.append("Wind impact on passing")
            confidence -= 0.05  # More uncertainty

        return PredictionWithConfidence(
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors
        )

    def _predict_time_of_possession(self, game_context: GameContext, situational_analysis: Dict) -> PredictionWithConfidence:
        """Predict time of possession with game script analysis"""

        spread = game_context.current_spread or 0
        running_edge = situational_analysis['running_game_edge']

        # Base time split (30 minutes each)
        base_minutes = 30.0

        # Adjust based on expected game script
        if abs(spread) > 7:  # Likely blowout
            if spread < 0:  # Home favored
                home_minutes = base_minutes + 2.5  # Favorites control clock
                away_minutes = base_minutes - 2.5
                prediction = f"{game_context.home_team} {int(home_minutes)}:{int((home_minutes % 1) * 60):02d}"
            else:  # Away favored
                away_minutes = base_minutes + 2.5
                home_minutes = base_minutes - 2.5
                prediction = f"{game_context.away_team} {int(away_minutes)}:{int((away_minutes % 1) * 60):02d}"
            confidence = 0.62
            reasoning = "Favorite expected to control game clock"
        else:  # Close game
            # Slight edge to team with running game advantage
            if running_edge == 'home':
                home_minutes = base_minutes + 1.0
                away_minutes = base_minutes - 1.0
                prediction = f"{game_context.home_team} {int(home_minutes)}:{int((home_minutes % 1) * 60):02d}"
            elif running_edge == 'away':
                away_minutes = base_minutes + 1.0
                home_minutes = base_minutes - 1.0
                prediction = f"{game_context.away_team} {int(away_minutes)}:{int((away_minutes % 1) * 60):02d}"
            else:
                prediction = "Even split (30:00 each)"
            confidence = 0.48
            reasoning = "Close game expected with balanced time of possession"

        key_factors = [
            "Running game effectiveness",
            "Game script expectations",
            "Clock management"
        ]

        if abs(spread) > 7:
            key_factors.append("Blowout potential")

        return PredictionWithConfidence(
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors
        )

    def _predict_sack_total(self, game_context: GameContext, situational_analysis: Dict) -> PredictionWithConfidence:
        """Predict total sacks in game"""

        home_pass_rush = situational_analysis['pass_rush_quality']['home']
        away_pass_rush = situational_analysis['pass_rush_quality']['away']
        home_oline = situational_analysis['oline_protection']['home']
        away_oline = situational_analysis['oline_protection']['away']

        # Calculate expected sacks for each team
        home_sacks = (1.0 - away_oline) * home_pass_rush * 3.5  # Base sack rate
        away_sacks = (1.0 - home_oline) * away_pass_rush * 3.5

        total_sacks = home_sacks + away_sacks

        # Common sack totals for betting
        if total_sacks > 5.5:
            prediction = "Over 5.5"
            confidence = 0.58
            reasoning = f"Strong pass rush matchups project {total_sacks:.1f} total sacks"
        elif total_sacks > 4.5:
            prediction = "Over 4.5"
            confidence = 0.55
            reasoning = f"Moderate pass rush advantage projects {total_sacks:.1f} sacks"
        elif total_sacks < 3.5:
            prediction = "Under 3.5"
            confidence = 0.55
            reasoning = f"Strong O-line protection limits sacks to {total_sacks:.1f}"
        else:
            prediction = "Over 4.5"  # NFL average
            confidence = 0.50
            reasoning = f"Average pass rush/protection matchup projects {total_sacks:.1f} sacks"

        key_factors = [
            "Pass rush quality",
            "O-line protection",
            "QB mobility"
        ]

        # Injury impact
        if game_context.has_significant_injuries():
            for injury_list in [game_context.home_injuries, game_context.away_injuries]:
                for injury in injury_list:
                    if injury.get('position') in ['LT', 'C', 'RT'] and injury.get('status') in ['OUT', 'DOUBTFUL']:
                        key_factors.append("O-line injuries")
                        break

        return PredictionWithConfidence(
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors[:5]
        )

    def _predict_penalty_total(self, game_context: GameContext, situational_analysis: Dict) -> PredictionWithConfidence:
        """Predict total penalties in game"""

        projected_penalties = situational_analysis['penalty_rate_projection']
        discipline_edge = situational_analysis['discipline_edge']

        # Adjust for game factors
        if game_context.is_divisional:
            projected_penalties += 1.0  # Divisional games more chippy

        if game_context.is_primetime:
            projected_penalties -= 0.5  # Better preparation

        if game_context.playoff_implications:
            projected_penalties += 0.5  # Higher stakes, more emotion

        # Common penalty totals for betting
        if projected_penalties > 13.5:
            prediction = "Over 13.5"
            confidence = 0.55
            reasoning = f"Physical game conditions project {projected_penalties:.1f} penalties"
        elif projected_penalties > 11.5:
            prediction = "Over 11.5"
            confidence = 0.52
            reasoning = f"Average penalty conditions project {projected_penalties:.1f} penalties"
        elif projected_penalties < 10.5:
            prediction = "Under 10.5"
            confidence = 0.55
            reasoning = f"Disciplined teams project {projected_penalties:.1f} penalties"
        else:
            prediction = "Under 12.5"  # Slight under bias
            confidence = 0.50
            reasoning = f"Standard penalty rate projects {projected_penalties:.1f} penalties"

        key_factors = [
            "Team discipline",
            "Referee crew tendencies",
            "Game intensity"
        ]

        if game_context.is_divisional:
            key_factors.append("Divisional rivalry")
        if game_context.playoff_implications:
            key_factors.append("High stakes emotion")

        return PredictionWithConfidence(
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors[:5]
        )

    def _generate_advanced_predictions(self, game_context: GameContext) -> Dict[str, PredictionWithConfidence]:
        """Generate environmental and advanced predictions"""
        return {
            'weather_impact': PredictionWithConfidence(
                prediction="minimal",
                confidence=0.70,
                reasoning="Weather impact assessment",
                key_factors=["Wind", "Temperature", "Precipitation"]
            ),
            'injury_impact': PredictionWithConfidence(
                prediction="moderate" if game_context.has_significant_injuries() else "low",
                confidence=0.65,
                reasoning="Injury impact analysis",
                key_factors=["Key players", "Depth chart"]
            ),
            'momentum_analysis': PredictionWithConfidence(
                prediction="positive",
                confidence=0.55,
                reasoning="Momentum and trend analysis",
                key_factors=["Recent performance", "Confidence"]
            ),
            'special_teams': PredictionWithConfidence(
                prediction="even",
                confidence=0.50,
                reasoning="Special teams comparison",
                key_factors=["Kicking game", "Return units"]
            ),
            'coaching_matchup': PredictionWithConfidence(
                prediction=game_context.home_team,
                confidence=0.52,
                reasoning="Coaching matchup analysis",
                key_factors=["Play calling", "Adjustments"]
            )
        }

    def _analyze_core_game(self, home_team: str, away_team: str, game_data: Dict) -> Dict:
        """Analyze core game predictions - to be overridden by each expert"""
        spread = game_data.get('spread', 0)
        total = game_data.get('total', 45.5)

        # Basic implementation - each expert will override with their specialty
        winner = home_team if spread < 0 else away_team
        home_score = random.randint(17, 31)
        away_score = random.randint(14, 28)

        return {
            'game_outcome': {
                'winner': winner,
                'home_win_prob': 0.55 if winner == home_team else 0.45,
                'away_win_prob': 0.45 if winner == home_team else 0.55,
                'confidence': 0.65,
                'reasoning': f"Based on {self.name}'s analysis methodology"
            },
            'exact_score': {
                'home_score': home_score,
                'away_score': away_score,
                'confidence': 0.35,
                'reasoning': 'Score prediction based on offensive/defensive efficiency'
            },
            'margin': {
                'margin': abs(home_score - away_score),
                'winner': winner,
                'confidence': 0.45
            },
            'ats': {
                'pick': winner,
                'spread_line': spread,
                'confidence': 0.58,
                'edge': round(random.uniform(-2.5, 2.5), 1)
            },
            'totals': {
                'pick': 'over' if (home_score + away_score) > total else 'under',
                'total_line': total,
                'predicted_total': home_score + away_score,
                'confidence': 0.52
            },
            'moneyline': {
                'pick': winner,
                'expected_value': round(random.uniform(-0.05, 0.15), 3),
                'confidence': 0.60
            },
            'first_half': {
                'pick': winner,
                'confidence': 0.48,
                'reasoning': 'First half trends analysis'
            },
            'highest_quarter': {
                'pick': random.choice([2, 3, 4]),
                'confidence': 0.25,
                'reasoning': 'Historical scoring pattern analysis'
            }
        }

    def _predict_player_props(self, home_team: str, away_team: str, game_data: Dict) -> Dict:
        """Predict player props across all categories"""
        return {
            'passing': {
                'qb_yards': {
                    'home_qb': {'over_under': 267.5, 'pick': 'over', 'confidence': 0.55},
                    'away_qb': {'over_under': 245.5, 'pick': 'under', 'confidence': 0.52}
                },
                'qb_touchdowns': {
                    'home_qb': {'over_under': 1.5, 'pick': 'over', 'confidence': 0.60},
                    'away_qb': {'over_under': 1.5, 'pick': 'under', 'confidence': 0.48}
                },
                'completions': {
                    'home_qb': {'over_under': 22.5, 'pick': 'over', 'confidence': 0.58},
                    'away_qb': {'over_under': 21.5, 'pick': 'over', 'confidence': 0.55}
                },
                'interceptions': {
                    'home_qb': {'over_under': 0.5, 'pick': 'under', 'confidence': 0.65},
                    'away_qb': {'over_under': 0.5, 'pick': 'over', 'confidence': 0.52}
                }
            },
            'rushing': {
                'rb_yards': {
                    'home_rb1': {'over_under': 75.5, 'pick': 'over', 'confidence': 0.62},
                    'away_rb1': {'over_under': 68.5, 'pick': 'under', 'confidence': 0.58}
                },
                'rb_attempts': {
                    'home_rb1': {'over_under': 18.5, 'pick': 'over', 'confidence': 0.55},
                    'away_rb1': {'over_under': 16.5, 'pick': 'under', 'confidence': 0.52}
                },
                'rb_touchdowns': {
                    'home_rb1': {'over_under': 0.5, 'pick': 'over', 'confidence': 0.48},
                    'away_rb1': {'over_under': 0.5, 'pick': 'under', 'confidence': 0.45}
                },
                'longest_rush': {
                    'game_longest': {'over_under': 18.5, 'pick': 'over', 'confidence': 0.50}
                }
            },
            'receiving': {
                'wr_yards': {
                    'home_wr1': {'over_under': 82.5, 'pick': 'over', 'confidence': 0.58},
                    'away_wr1': {'over_under': 75.5, 'pick': 'under', 'confidence': 0.55}
                },
                'receptions': {
                    'home_wr1': {'over_under': 5.5, 'pick': 'over', 'confidence': 0.60},
                    'away_wr1': {'over_under': 5.5, 'pick': 'over', 'confidence': 0.52}
                },
                'rec_touchdowns': {
                    'home_wr1': {'over_under': 0.5, 'pick': 'over', 'confidence': 0.45},
                    'away_wr1': {'over_under': 0.5, 'pick': 'under', 'confidence': 0.42}
                },
                'targets': {
                    'home_wr1': {'over_under': 8.5, 'pick': 'over', 'confidence': 0.55},
                    'away_wr1': {'over_under': 7.5, 'pick': 'over', 'confidence': 0.50}
                }
            },
            'fantasy': {
                'qb_points': {
                    'home_qb': {'projected': 18.7, 'confidence': 0.65},
                    'away_qb': {'projected': 16.2, 'confidence': 0.62}
                },
                'rb_points': {
                    'home_rb1': {'projected': 14.3, 'confidence': 0.58},
                    'away_rb1': {'projected': 12.1, 'confidence': 0.55}
                },
                'wr_points': {
                    'home_wr1': {'projected': 15.8, 'confidence': 0.60},
                    'away_wr1': {'projected': 13.4, 'confidence': 0.57}
                }
            }
        }

    def _predict_live_scenarios(self, home_team: str, away_team: str, game_data: Dict) -> Dict:
        """Predict live game scenarios"""
        return {
            'win_prob': {
                'opening_drive': {'home': 0.52, 'away': 0.48},
                'end_first_quarter': {'home': 0.55, 'away': 0.45},
                'halftime': {'home': 0.58, 'away': 0.42},
                'end_third_quarter': {'home': 0.62, 'away': 0.38},
                'two_minute_warning': {'home': 0.65, 'away': 0.35}
            },
            'next_score': {
                'opening_drive': {
                    'team': home_team,
                    'score_type': 'touchdown',
                    'probability': 0.35,
                    'expected_points': 6.2
                },
                'first_score_method': {
                    'touchdown': 0.65,
                    'field_goal': 0.30,
                    'safety': 0.02,
                    'none': 0.03
                }
            },
            'drive_outcomes': {
                'touchdown_prob': 0.28,
                'field_goal_prob': 0.22,
                'punt_prob': 0.35,
                'turnover_prob': 0.12,
                'turnover_on_downs_prob': 0.03
            },
            'fourth_down': {
                'go_for_it_situations': {
                    'red_zone': {'recommendation': 'go_for_it', 'success_prob': 0.65},
                    'midfield': {'recommendation': 'punt', 'success_prob': 0.45},
                    'own_territory': {'recommendation': 'punt', 'success_prob': 0.35}
                },
                'expected_value': {
                    'go_for_it': 2.1,
                    'field_goal': 1.8,
                    'punt': 0.3
                }
            }
        }

    def _analyze_weather_impact(self, game_data: Dict) -> Dict:
        """Analyze weather impact on game"""
        weather = game_data.get('weather', {})
        return {
            'conditions': weather,
            'impact_level': 'low',  # low, medium, high
            'affected_areas': ['passing_accuracy', 'kicking_accuracy'],
            'total_adjustment': -2.5,  # Points adjustment
            'confidence': 0.70
        }

    def _analyze_injury_impact(self, game_data: Dict) -> Dict:
        """Analyze injury impact"""
        injuries = game_data.get('injuries', {})
        return {
            'key_injuries': injuries,
            'impact_rating': 'medium',  # low, medium, high
            'affected_positions': ['QB', 'RB'],
            'team_adjustments': {
                'home': -1.5,
                'away': -0.5
            },
            'confidence': 0.65
        }



    def _calculate_overall_confidence(self, game_context: GameContext, memory_influences: List[MemoryInfluence]) -> float:
        """Calculate overall prediction confidence"""
        base_confidence = 0.65

        # Adjust based on data quality and specialty match
        if any(spec in ['weather_impact', 'environmental'] for spec in self.specializations):
            if game_context.weather_conditions and game_context.weather_conditions.get('impact_level') == 'high':
                base_confidence += 0.1

        if any(spec in ['injury_impact', 'player_availability'] for spec in self.specializations):
            if game_context.has_significant_injuries():
                base_confidence += 0.08

        # Adjust based on memory influences
        strong_memories = [mem for mem in memory_influences if mem.is_strong_influence()]
        if len(strong_memories) > 3:
            base_confidence += 0.05  # More relevant memories = higher confidence

        # Adjust based on game context
        if game_context.is_divisional:
            base_confidence += 0.03  # More familiar matchups

        if game_context.playoff_implications:
            base_confidence -= 0.02  # Higher stakes = more uncertainty

        return min(0.95, max(0.35, base_confidence))

    def _generate_reasoning(self, game_context: GameContext, memory_influences: List[MemoryInfluence]) -> str:
        """Generate expert's reasoning"""
        factors = []

        # Weather factors
        if game_context.weather_conditions and game_context.weather_conditions.get('impact_level') != 'low':
            factors.append(f"weather conditions {game_context.weather_conditions.get('impact_level')} impact")

        # Injury factors
        if game_context.has_significant_injuries():
            factors.append("key injuries affecting game dynamics")

        # Memory influences
        strong_memories = [mem for mem in memory_influences if mem.is_strong_influence()]
        if strong_memories:
            factors.append(f"{len(strong_memories)} relevant past experiences")

        # Game context factors
        if game_context.is_divisional:
            factors.append("divisional rivalry dynamics")

        if game_context.playoff_implications:
            factors.append("playoff implications adding pressure")

        # Default reasoning
        factors.append(f"favor {game_context.home_team} based on {self.name} methodology")

        return f"Analysis shows {', '.join(factors)}"

    def _identify_key_factors(self, game_context: GameContext) -> List[str]:
        """Identify key factors for this prediction"""
        factors = []

        # Add specialty-based factors
        if 'weather_impact' in self.specializations:
            factors.append("Weather conditions")
        if 'injury_impact' in self.specializations:
            factors.append("Injury reports")
        if 'sharp_money' in self.specializations:
            factors.append("Line movement")

        # Add context-based factors
        if game_context.is_divisional:
            factors.append("Divisional familiarity")

        if game_context.is_primetime:
            factors.append("Primetime performance")

        if game_context.playoff_implications:
            factors.append("Playoff implications")

        # Add general factors
        factors.extend(["Team form", "Matchup analysis", "Historical trends"])

        return factors[:5]  # Limit to top 5

    def _calculate_specialty_confidence(self) -> Dict[str, float]:
        """Calculate confidence in specialty areas"""
        return {spec: random.uniform(0.6, 0.9) for spec in self.specializations}
