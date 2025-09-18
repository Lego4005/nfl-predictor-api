"""
Pydantic Models for NFL Prediction API
Comprehensive data validation and serialization for 375+ predictions
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class PredictionCategory(str, Enum):
    """Prediction category enumeration"""
    CORE_GAME = "core_game"
    LIVE_GAME = "live_game"
    PLAYER_PROPS = "player_props"
    GAME_SEGMENTS = "game_segments"
    ENVIRONMENTAL = "environmental"
    ADVANCED = "advanced"

class ExpertSpecialty(str, Enum):
    """Expert specialty areas"""
    SHARP_MONEY = "sharp_money"
    WEATHER_IMPACT = "weather_impact"
    INJURY_ANALYSIS = "injury_analysis"
    ANALYTICS = "analytics"
    ROAD_WARRIOR = "road_warrior"
    SITUATIONAL = "situational"
    PLAYER_PROPS = "player_props"
    LIVE_BETTING = "live_betting"

class ConfidenceLevel(str, Enum):
    """Confidence level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

# Core Prediction Models
class GameOutcomePrediction(BaseModel):
    """Game outcome prediction model"""
    winner: str = Field(..., description="Predicted winner team")
    home_win_prob: float = Field(..., ge=0, le=1, description="Home team win probability")
    away_win_prob: float = Field(..., ge=0, le=1, description="Away team win probability")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")
    reasoning: str = Field(..., description="Prediction reasoning")

    @validator('home_win_prob', 'away_win_prob')
    def validate_probabilities(cls, v, values):
        if 'home_win_prob' in values and 'away_win_prob' in values:
            if abs((values.get('home_win_prob', 0) + v) - 1.0) > 0.01:
                raise ValueError('Probabilities must sum to 1.0')
        return v

class ScorePrediction(BaseModel):
    """Score prediction model"""
    home_score: int = Field(..., ge=0, description="Predicted home team score")
    away_score: int = Field(..., ge=0, description="Predicted away team score")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")
    reasoning: str = Field(..., description="Prediction reasoning")

class MarginPrediction(BaseModel):
    """Margin of victory prediction"""
    margin: int = Field(..., ge=0, description="Predicted margin of victory")
    winner: str = Field(..., description="Team predicted to win")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")

class SpreadPrediction(BaseModel):
    """Against the spread prediction"""
    pick: str = Field(..., description="ATS pick")
    spread_line: float = Field(..., description="Current spread line")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")
    edge: float = Field(..., description="Perceived edge in points")

class TotalsPrediction(BaseModel):
    """Totals (Over/Under) prediction"""
    pick: str = Field(..., regex="^(over|under)$", description="Totals pick")
    total_line: float = Field(..., description="Current total line")
    predicted_total: int = Field(..., ge=0, description="Predicted total points")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")

class MoneylinePrediction(BaseModel):
    """Moneyline value prediction"""
    pick: str = Field(..., description="Moneyline pick")
    expected_value: float = Field(..., description="Expected value")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")

# Player Props Models
class PlayerPropPrediction(BaseModel):
    """Individual player prop prediction"""
    over_under: float = Field(..., description="Prop line")
    pick: str = Field(..., regex="^(over|under)$", description="Prop pick")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")

class PassingProps(BaseModel):
    """Passing props predictions"""
    qb_yards: Dict[str, PlayerPropPrediction] = Field(..., description="QB passing yards")
    qb_touchdowns: Dict[str, PlayerPropPrediction] = Field(..., description="QB passing TDs")
    completions: Dict[str, PlayerPropPrediction] = Field(..., description="QB completions")
    interceptions: Dict[str, PlayerPropPrediction] = Field(..., description="QB interceptions")

class RushingProps(BaseModel):
    """Rushing props predictions"""
    rb_yards: Dict[str, PlayerPropPrediction] = Field(..., description="RB rushing yards")
    rb_attempts: Dict[str, PlayerPropPrediction] = Field(..., description="RB attempts")
    rb_touchdowns: Dict[str, PlayerPropPrediction] = Field(..., description="RB TDs")
    longest_rush: Dict[str, PlayerPropPrediction] = Field(..., description="Longest rush")

class ReceivingProps(BaseModel):
    """Receiving props predictions"""
    wr_yards: Dict[str, PlayerPropPrediction] = Field(..., description="WR receiving yards")
    receptions: Dict[str, PlayerPropPrediction] = Field(..., description="Receptions")
    rec_touchdowns: Dict[str, PlayerPropPrediction] = Field(..., description="Receiving TDs")
    targets: Dict[str, PlayerPropPrediction] = Field(..., description="Targets")

class FantasyPoints(BaseModel):
    """Fantasy points predictions"""
    qb_points: Dict[str, Dict[str, float]] = Field(..., description="QB fantasy points")
    rb_points: Dict[str, Dict[str, float]] = Field(..., description="RB fantasy points")
    wr_points: Dict[str, Dict[str, float]] = Field(..., description="WR fantasy points")

# Live Game Models
class WinProbabilityTimeline(BaseModel):
    """Real-time win probability timeline"""
    opening_drive: Dict[str, float] = Field(..., description="Opening drive probabilities")
    end_first_quarter: Dict[str, float] = Field(..., description="End Q1 probabilities")
    halftime: Dict[str, float] = Field(..., description="Halftime probabilities")
    end_third_quarter: Dict[str, float] = Field(..., description="End Q3 probabilities")
    two_minute_warning: Dict[str, float] = Field(..., description="Two minute warning probabilities")

class NextScorePrediction(BaseModel):
    """Next score prediction"""
    team: str = Field(..., description="Team predicted to score next")
    score_type: str = Field(..., description="Type of score")
    probability: float = Field(..., ge=0, le=1, description="Probability")
    expected_points: float = Field(..., description="Expected points")

class DriveOutcomePrediction(BaseModel):
    """Drive outcome predictions"""
    touchdown_prob: float = Field(..., ge=0, le=1, description="Touchdown probability")
    field_goal_prob: float = Field(..., ge=0, le=1, description="Field goal probability")
    punt_prob: float = Field(..., ge=0, le=1, description="Punt probability")
    turnover_prob: float = Field(..., ge=0, le=1, description="Turnover probability")
    turnover_on_downs_prob: float = Field(..., ge=0, le=1, description="Turnover on downs probability")

class FourthDownDecision(BaseModel):
    """Fourth down decision recommendations"""
    go_for_it_situations: Dict[str, Dict[str, Union[str, float]]] = Field(..., description="Go for it scenarios")
    expected_value: Dict[str, float] = Field(..., description="Expected value by decision")

# Environmental Models
class WeatherImpact(BaseModel):
    """Weather impact analysis"""
    conditions: Dict[str, Any] = Field(..., description="Weather conditions")
    impact_level: str = Field(..., regex="^(low|medium|high)$", description="Impact level")
    affected_areas: List[str] = Field(..., description="Affected game areas")
    total_adjustment: float = Field(..., description="Total points adjustment")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in analysis")

class InjuryImpact(BaseModel):
    """Injury impact analysis"""
    key_injuries: List[str] = Field(..., description="Key injuries")
    impact_rating: str = Field(..., regex="^(low|medium|high)$", description="Impact rating")
    affected_positions: List[str] = Field(..., description="Affected positions")
    team_adjustments: Dict[str, float] = Field(..., description="Team point adjustments")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in analysis")

# Expert Performance Models
class ExpertPerformance(BaseModel):
    """Expert performance tracking"""
    expert_id: str = Field(..., description="Expert identifier")
    expert_name: str = Field(..., description="Expert name")
    overall_accuracy: float = Field(..., ge=0, le=1, description="Overall accuracy")
    category_accuracy: Dict[str, float] = Field(..., description="Accuracy by category")
    recent_form: str = Field(..., description="Recent performance form")
    total_predictions: int = Field(..., ge=0, description="Total predictions made")
    correct_predictions: int = Field(..., ge=0, description="Correct predictions")
    specialty_confidence: Dict[str, float] = Field(..., description="Confidence in specialties")
    last_updated: datetime = Field(..., description="Last update timestamp")

# Comprehensive Expert Prediction Model
class ComprehensiveExpertPrediction(BaseModel):
    """Complete expert prediction covering all categories"""
    expert_id: str = Field(..., description="Expert identifier")
    expert_name: str = Field(..., description="Expert name")
    game_id: str = Field(..., description="Game identifier")

    # Core Game Predictions
    game_outcome: GameOutcomePrediction = Field(..., description="Game outcome prediction")
    exact_score: ScorePrediction = Field(..., description="Exact score prediction")
    margin_of_victory: MarginPrediction = Field(..., description="Margin prediction")
    against_the_spread: SpreadPrediction = Field(..., description="ATS prediction")
    totals: TotalsPrediction = Field(..., description="Totals prediction")
    moneyline_value: MoneylinePrediction = Field(..., description="Moneyline prediction")

    # Live Game Predictions
    real_time_win_probability: WinProbabilityTimeline = Field(..., description="Win probability timeline")
    next_score_probability: NextScorePrediction = Field(..., description="Next score prediction")
    drive_outcome_predictions: DriveOutcomePrediction = Field(..., description="Drive outcomes")
    fourth_down_decisions: FourthDownDecision = Field(..., description="Fourth down decisions")

    # Player Props
    passing_props: PassingProps = Field(..., description="Passing props")
    rushing_props: RushingProps = Field(..., description="Rushing props")
    receiving_props: ReceivingProps = Field(..., description="Receiving props")
    fantasy_points: FantasyPoints = Field(..., description="Fantasy points")

    # Game Segments
    first_half_winner: Dict[str, Any] = Field(..., description="First half winner")
    highest_scoring_quarter: Dict[str, Any] = Field(..., description="Highest scoring quarter")

    # Environmental
    weather_impact: WeatherImpact = Field(..., description="Weather impact")
    injury_impact: InjuryImpact = Field(..., description="Injury impact")
    momentum_analysis: Dict[str, Any] = Field(..., description="Momentum analysis")
    situational_predictions: Dict[str, Any] = Field(..., description="Situational predictions")

    # Advanced Analysis
    special_teams: Dict[str, Any] = Field(..., description="Special teams analysis")
    coaching_matchup: Dict[str, Any] = Field(..., description="Coaching matchup")
    home_field_advantage: Dict[str, Any] = Field(..., description="Home field advantage")
    travel_rest_impact: Dict[str, Any] = Field(..., description="Travel/rest impact")
    divisional_dynamics: Dict[str, Any] = Field(..., description="Divisional dynamics")

    # Meta Information
    confidence_overall: float = Field(..., ge=0, le=1, description="Overall confidence")
    reasoning: str = Field(..., description="Expert reasoning")
    key_factors: List[str] = Field(..., description="Key factors")
    prediction_timestamp: datetime = Field(..., description="Prediction timestamp")

    # Performance Tracking
    historical_accuracy: Optional[float] = Field(None, description="Historical accuracy")
    recent_form: Optional[str] = Field(None, description="Recent form")
    specialty_confidence: Dict[str, float] = Field(default_factory=dict, description="Specialty confidence")

# API Response Models
class PredictionSummary(BaseModel):
    """Prediction summary for API responses"""
    prediction_id: str = Field(..., description="Prediction identifier")
    expert_name: str = Field(..., description="Expert name")
    category: PredictionCategory = Field(..., description="Prediction category")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level")
    key_prediction: str = Field(..., description="Key prediction summary")
    timestamp: datetime = Field(..., description="Prediction timestamp")

class GamePredictionsResponse(BaseModel):
    """Complete game predictions response"""
    game_id: str = Field(..., description="Game identifier")
    home_team: str = Field(..., description="Home team")
    away_team: str = Field(..., description="Away team")
    game_time: datetime = Field(..., description="Game time")
    predictions: List[ComprehensiveExpertPrediction] = Field(..., description="All expert predictions")
    total_predictions: int = Field(..., description="Total prediction count")
    categories_covered: List[PredictionCategory] = Field(..., description="Categories covered")
    consensus_summary: Dict[str, Any] = Field(..., description="Consensus summary")
    last_updated: datetime = Field(..., description="Last update timestamp")

class CategoryPredictionsResponse(BaseModel):
    """Category-filtered predictions response"""
    game_id: str = Field(..., description="Game identifier")
    category: PredictionCategory = Field(..., description="Prediction category")
    predictions: List[Dict[str, Any]] = Field(..., description="Category predictions")
    expert_count: int = Field(..., description="Number of experts")
    consensus: Dict[str, Any] = Field(..., description="Category consensus")
    confidence_range: Dict[str, float] = Field(..., description="Confidence range")

class PlayerPropsResponse(BaseModel):
    """Player props predictions response"""
    game_id: str = Field(..., description="Game identifier")
    passing_props: Dict[str, Any] = Field(..., description="Passing props")
    rushing_props: Dict[str, Any] = Field(..., description="Rushing props")
    receiving_props: Dict[str, Any] = Field(..., description="Receiving props")
    fantasy_props: Dict[str, Any] = Field(..., description="Fantasy props")
    expert_count: int = Field(..., description="Number of experts")
    consensus_confidence: float = Field(..., description="Consensus confidence")

class LivePredictionsResponse(BaseModel):
    """Live predictions response"""
    game_id: str = Field(..., description="Game identifier")
    current_quarter: int = Field(..., description="Current quarter")
    time_remaining: str = Field(..., description="Time remaining")
    current_score: Dict[str, int] = Field(..., description="Current score")
    live_win_probability: Dict[str, float] = Field(..., description="Live win probability")
    next_score_predictions: List[Dict[str, Any]] = Field(..., description="Next score predictions")
    drive_predictions: Dict[str, Any] = Field(..., description="Current drive predictions")
    game_state_analysis: Dict[str, Any] = Field(..., description="Game state analysis")
    last_updated: datetime = Field(..., description="Last update timestamp")

class ConsensusResponse(BaseModel):
    """Top 5 expert consensus response"""
    game_id: str = Field(..., description="Game identifier")
    top_experts: List[str] = Field(..., description="Top 5 expert names")
    consensus_predictions: Dict[str, Any] = Field(..., description="Consensus predictions")
    confidence_score: float = Field(..., ge=0, le=1, description="Consensus confidence")
    prediction_weights: Dict[str, float] = Field(..., description="Expert weights")
    category_consensus: Dict[str, Dict[str, Any]] = Field(..., description="Category-wise consensus")

class ExpertPerformanceResponse(BaseModel):
    """Expert performance tracking response"""
    expert_id: str = Field(..., description="Expert identifier")
    expert_name: str = Field(..., description="Expert name")
    performance_metrics: ExpertPerformance = Field(..., description="Performance metrics")
    recent_predictions: List[PredictionSummary] = Field(..., description="Recent predictions")
    specialty_areas: List[ExpertSpecialty] = Field(..., description="Specialty areas")
    ranking: int = Field(..., description="Overall ranking")
    trend: str = Field(..., description="Performance trend")

# WebSocket Models
class LivePredictionUpdate(BaseModel):
    """Live prediction update for WebSocket"""
    game_id: str = Field(..., description="Game identifier")
    update_type: str = Field(..., description="Update type")
    expert_id: str = Field(..., description="Expert identifier")
    prediction_data: Dict[str, Any] = Field(..., description="Updated prediction data")
    confidence_change: float = Field(..., description="Confidence change")
    timestamp: datetime = Field(..., description="Update timestamp")

class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    message_type: str = Field(..., description="Message type")
    game_id: str = Field(..., description="Game identifier")
    data: Union[LivePredictionUpdate, Dict[str, Any]] = Field(..., description="Message data")
    timestamp: datetime = Field(..., description="Message timestamp")

# Error Models
class APIError(BaseModel):
    """API error response"""
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(..., description="Error timestamp")

class ValidationError(BaseModel):
    """Validation error details"""
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Validation message")
    value: Any = Field(..., description="Invalid value")