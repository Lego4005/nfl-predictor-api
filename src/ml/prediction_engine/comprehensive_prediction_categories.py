"""
Comprehensive Prediction Categories System
Defines all 25+ prediction categories for expert models as specified in the design document
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class PredictionCategoryGroup(Enum):
    """Main groups of prediction categories"""
    GAME_OUTCOME = "game_outcome"
    BETTING_MARKET = "betting_market"
    LIVE_SCENARIO = "live_scenario"
    PLAYER_PROPS = "player_props"
    SITUATIONAL = "situational"
    QUARTER_PROPS = "quarter_props"
    TEAM_PROPS = "team_props"
    GAME_PROPS = "game_props"
    ADVANCED_PROPS = "advanced_props"

class AccessTier(Enum):
    """Access tiers for monetization"""
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"

class DataType(Enum):
    """Data types for prediction values"""
    BOOLEAN = "boolean"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    PERCENTAGE = "percentage"

@dataclass
class ValidationRule:
    """Validation rule for prediction values"""
    rule_type: str  # min, max, choices, range
    value: Any
    error_message: str

@dataclass
class PredictionCategory:
    """Definition of a single prediction category"""
    category_id: str
    category_name: str
    group: PredictionCategoryGroup
    data_type: DataType
    description: str
    validation_rules: List[ValidationRule] = field(default_factory=list)
    scoring_weight: float = 1.0
    difficulty_level: str = "medium"  # easy, medium, hard
    requires_live_data: bool = False
    access_tier: AccessTier = AccessTier.FREE
    popularity_score: int = 5  # 1-10, higher = more popular betting line

    def validate_value(self, value: Any) -> bool:
        """Validate a prediction value against the rules"""
        for rule in self.validation_rules:
            if not self._apply_validation_rule(value, rule):
                return False
        return True

    def _apply_validation_rule(self, value: Any, rule: ValidationRule) -> bool:
        """Apply a single validation rule"""
        try:
            if rule.rule_type == "min" and value < rule.value:
                return False
            elif rule.rule_type == "max" and value > rule.value:
                return False
            elif rule.rule_type == "choices" and value not in rule.value:
                return False
            elif rule.rule_type == "range" and not (rule.value[0] <= value <= rule.value[1]):
                return False
            return True
        except (TypeError, ValueError):
            return False

@dataclass
class ExpertPrediction:
    """Complete prediction from a single expert across all categories"""
    expert_id: str
    expert_name: str
    game_id: str
    prediction_timestamp: datetime

    # Game Outcome Predictions (4 categories)
    winner_prediction: Optional[str] = None  # home, away
    exact_score_home: Optional[int] = None
    exact_score_away: Optional[int] = None
    margin_of_victory: Optional[float] = None

    # Betting Market Predictions (4 categories)
    against_the_spread: Optional[str] = None  # home, away, push
    totals_over_under: Optional[str] = None  # over, under, push
    first_half_winner: Optional[str] = None  # home, away, tie
    highest_scoring_quarter: Optional[str] = None  # Q1, Q2, Q3, Q4

    # Live Game Scenarios (4 categories)
    live_win_probability: Optional[float] = None  # 0.0-1.0
    next_score_probability: Optional[str] = None  # touchdown, field_goal, safety, none
    drive_outcome_prediction: Optional[str] = None  # touchdown, field_goal, punt, turnover
    fourth_down_decision: Optional[str] = None  # punt, field_goal, go_for_it

    # Player Performance Props (8 categories)
    qb_passing_yards: Optional[float] = None
    qb_touchdowns: Optional[int] = None
    qb_interceptions: Optional[int] = None
    rb_rushing_yards: Optional[float] = None
    rb_touchdowns: Optional[int] = None
    wr_receiving_yards: Optional[float] = None
    wr_receptions: Optional[int] = None
    fantasy_points_projection: Optional[float] = None

    # Situational Analysis (7 categories)
    weather_impact_score: Optional[float] = None  # 0.0-1.0
    injury_impact_score: Optional[float] = None  # 0.0-1.0
    travel_rest_factor: Optional[float] = None  # -0.5 to 0.5
    divisional_rivalry_factor: Optional[float] = None  # 0.0-1.0
    coaching_advantage: Optional[str] = None  # home, away, neutral
    home_field_advantage: Optional[float] = None  # points
    momentum_factor: Optional[float] = None  # -1.0 to 1.0

    # Confidence and Meta Information
    confidence_overall: float = 0.5
    confidence_by_category: Dict[str, float] = field(default_factory=dict)
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert prediction to dictionary format"""
        return {
            'expert_id': self.expert_id,
            'expert_name': self.expert_name,
            'game_id': self.game_id,
            'prediction_timestamp': self.prediction_timestamp.isoformat(),
            'game_outcome': {
                'winner_prediction': self.winner_prediction,
                'exact_score_home': self.exact_score_home,
                'exact_score_away': self.exact_score_away,
                'margin_of_victory': self.margin_of_victory
            },
            'betting_markets': {
                'against_the_spread': self.against_the_spread,
                'totals_over_under': self.totals_over_under,
                'first_half_winner': self.first_half_winner,
                'highest_scoring_quarter': self.highest_scoring_quarter
            },
            'live_scenarios': {
                'live_win_probability': self.live_win_probability,
                'next_score_probability': self.next_score_probability,
                'drive_outcome_prediction': self.drive_outcome_prediction,
                'fourth_down_decision': self.fourth_down_decision
            },
            'player_props': {
                'qb_passing_yards': self.qb_passing_yards,
                'qb_touchdowns': self.qb_touchdowns,
                'qb_interceptions': self.qb_interceptions,
                'rb_rushing_yards': self.rb_rushing_yards,
                'rb_touchdowns': self.rb_touchdowns,
                'wr_receiving_yards': self.wr_receiving_yards,
                'wr_receptions': self.wr_receptions,
                'fantasy_points_projection': self.fantasy_points_projection
            },
            'situational_analysis': {
                'weather_impact_score': self.weather_impact_score,
                'injury_impact_score': self.injury_impact_score,
                'travel_rest_factor': self.travel_rest_factor,
                'divisional_rivalry_factor': self.divisional_rivalry_factor,
                'coaching_advantage': self.coaching_advantage,
                'home_field_advantage': self.home_field_advantage,
                'momentum_factor': self.momentum_factor
            },
            'confidence_overall': self.confidence_overall,
            'confidence_by_category': self.confidence_by_category,
            'reasoning': self.reasoning,
            'key_factors': self.key_factors
        }

class ComprehensivePredictionCategories:
    """Registry and manager for all prediction categories"""

    def __init__(self):
        self.categories: Dict[str, PredictionCategory] = {}
        self._initialize_categories()

    def _initialize_categories(self):
        """Initialize all 27 prediction categories"""

        # Game Outcome Predictions (4 categories)
        self.categories["winner_prediction"] = PredictionCategory(
            category_id="winner_prediction",
            category_name="Winner Prediction",
            group=PredictionCategoryGroup.GAME_OUTCOME,
            data_type=DataType.CATEGORICAL,
            description="Predicted game winner",
            validation_rules=[ValidationRule("choices", ["home", "away"], "Must be 'home' or 'away'")],
            scoring_weight=1.5,
            difficulty_level="medium"
        )

        self.categories["exact_score_home"] = PredictionCategory(
            category_id="exact_score_home",
            category_name="Exact Score - Home Team",
            group=PredictionCategoryGroup.GAME_OUTCOME,
            data_type=DataType.NUMERIC,
            description="Predicted home team final score",
            validation_rules=[
                ValidationRule("min", 0, "Score cannot be negative"),
                ValidationRule("max", 70, "Score cannot exceed 70")
            ],
            scoring_weight=0.8,
            difficulty_level="hard"
        )

        self.categories["exact_score_away"] = PredictionCategory(
            category_id="exact_score_away",
            category_name="Exact Score - Away Team",
            group=PredictionCategoryGroup.GAME_OUTCOME,
            data_type=DataType.NUMERIC,
            description="Predicted away team final score",
            validation_rules=[
                ValidationRule("min", 0, "Score cannot be negative"),
                ValidationRule("max", 70, "Score cannot exceed 70")
            ],
            scoring_weight=0.8,
            difficulty_level="hard"
        )

        self.categories["margin_of_victory"] = PredictionCategory(
            category_id="margin_of_victory",
            category_name="Margin of Victory",
            group=PredictionCategoryGroup.GAME_OUTCOME,
            data_type=DataType.NUMERIC,
            description="Predicted point margin",
            validation_rules=[
                ValidationRule("min", 0, "Margin cannot be negative"),
                ValidationRule("max", 50, "Margin cannot exceed 50")
            ],
            scoring_weight=1.2,
            difficulty_level="medium"
        )

        # Continue with other categories
        self._add_betting_market_categories()
        self._add_quarter_props_categories()
        self._add_team_props_categories()
        self._add_game_props_categories()
        self._add_live_scenario_categories()
        self._add_player_props_categories()
        self._add_advanced_player_props()
        self._add_situational_categories()

    def _add_betting_market_categories(self):
        """Add betting market categories"""
        betting_categories = [
            ("against_the_spread", "Against the Spread", ["home", "away", "push"], 1.4),
            ("totals_over_under", "Totals Over/Under", ["over", "under", "push"], 1.3),
            ("first_half_winner", "First Half Winner", ["home", "away", "tie"], 1.0),
            ("highest_scoring_quarter", "Highest Scoring Quarter", ["Q1", "Q2", "Q3", "Q4"], 0.7)
        ]

        for cat_id, name, choices, weight in betting_categories:
            self.categories[cat_id] = PredictionCategory(
                category_id=cat_id,
                category_name=name,
                group=PredictionCategoryGroup.BETTING_MARKET,
                data_type=DataType.CATEGORICAL,
                description=f"{name} prediction",
                validation_rules=[ValidationRule("choices", choices, f"Must be one of {choices}")],
                scoring_weight=weight,
                difficulty_level="medium"
            )

    def _add_live_scenario_categories(self):
        """Add live scenario categories"""
        self.categories["live_win_probability"] = PredictionCategory(
            category_id="live_win_probability",
            category_name="Live Win Probability",
            group=PredictionCategoryGroup.LIVE_SCENARIO,
            data_type=DataType.PERCENTAGE,
            description="Real-time win probability",
            validation_rules=[ValidationRule("range", [0.0, 1.0], "Must be between 0 and 1")],
            scoring_weight=0.9,
            difficulty_level="medium",
            requires_live_data=True
        )

        live_categories = [
            ("next_score_probability", "Next Score Probability", ["touchdown", "field_goal", "safety", "none"]),
            ("drive_outcome_prediction", "Drive Outcome", ["touchdown", "field_goal", "punt", "turnover"]),
            ("fourth_down_decision", "Fourth Down Decision", ["punt", "field_goal", "go_for_it"])
        ]

        for cat_id, name, choices in live_categories:
            self.categories[cat_id] = PredictionCategory(
                category_id=cat_id,
                category_name=name,
                group=PredictionCategoryGroup.LIVE_SCENARIO,
                data_type=DataType.CATEGORICAL,
                description=f"{name} prediction",
                validation_rules=[ValidationRule("choices", choices, f"Must be one of {choices}")],
                scoring_weight=0.8,
                difficulty_level="hard",
                requires_live_data=True
            )

    def _add_player_props_categories(self):
        """Add player performance categories"""
        numeric_props = [
            ("qb_passing_yards", "QB Passing Yards", 0, 600, 1.1),
            ("qb_touchdowns", "QB Touchdowns", 0, 8, 1.0),
            ("qb_interceptions", "QB Interceptions", 0, 6, 0.9),
            ("rb_rushing_yards", "RB Rushing Yards", 0, 300, 1.0),
            ("rb_touchdowns", "RB Touchdowns", 0, 5, 0.9),
            ("wr_receiving_yards", "WR Receiving Yards", 0, 250, 0.9),
            ("wr_receptions", "WR Receptions", 0, 20, 0.8),
            ("fantasy_points_projection", "Fantasy Points", 0, 50, 0.7)
        ]

        for cat_id, name, min_val, max_val, weight in numeric_props:
            self.categories[cat_id] = PredictionCategory(
                category_id=cat_id,
                category_name=name,
                group=PredictionCategoryGroup.PLAYER_PROPS,
                data_type=DataType.NUMERIC,
                description=f"{name} prediction",
                validation_rules=[
                    ValidationRule("min", min_val, f"Cannot be less than {min_val}"),
                    ValidationRule("max", max_val, f"Cannot exceed {max_val}")
                ],
                scoring_weight=weight,
                difficulty_level="medium"
            )

    def _add_situational_categories(self):
        """Add situational analysis categories"""
        percentage_categories = [
            ("weather_impact_score", "Weather Impact", 0.8),
            ("injury_impact_score", "Injury Impact", 0.9),
            ("divisional_rivalry_factor", "Divisional Dynamics", 0.7)
        ]

        for cat_id, name, weight in percentage_categories:
            self.categories[cat_id] = PredictionCategory(
                category_id=cat_id,
                category_name=name,
                group=PredictionCategoryGroup.SITUATIONAL,
                data_type=DataType.PERCENTAGE,
                description=f"{name} assessment",
                validation_rules=[ValidationRule("range", [0.0, 1.0], "Must be between 0 and 1")],
                scoring_weight=weight,
                difficulty_level="medium"
            )

        # Special situational categories
        self.categories["travel_rest_factor"] = PredictionCategory(
            category_id="travel_rest_factor",
            category_name="Travel/Rest Factor",
            group=PredictionCategoryGroup.SITUATIONAL,
            data_type=DataType.NUMERIC,
            description="Travel and rest impact",
            validation_rules=[ValidationRule("range", [-0.5, 0.5], "Must be between -0.5 and 0.5")],
            scoring_weight=0.6,
            difficulty_level="medium"
        )

        self.categories["coaching_advantage"] = PredictionCategory(
            category_id="coaching_advantage",
            category_name="Coaching Advantage",
            group=PredictionCategoryGroup.SITUATIONAL,
            data_type=DataType.CATEGORICAL,
            description="Coaching matchup advantage",
            validation_rules=[ValidationRule("choices", ["home", "away", "neutral"], "Must be home, away, or neutral")],
            scoring_weight=0.8,
            difficulty_level="hard"
        )

        self.categories["home_field_advantage"] = PredictionCategory(
            category_id="home_field_advantage",
            category_name="Home Field Advantage",
            group=PredictionCategoryGroup.SITUATIONAL,
            data_type=DataType.NUMERIC,
            description="Home field advantage in points",
            validation_rules=[ValidationRule("range", [0, 10], "Must be between 0 and 10")],
            scoring_weight=0.9,
            difficulty_level="medium"
        )

        self.categories["momentum_factor"] = PredictionCategory(
            category_id="momentum_factor",
            category_name="Momentum Factor",
            group=PredictionCategoryGroup.SITUATIONAL,
            data_type=DataType.NUMERIC,
            description="Team momentum indicator",
            validation_rules=[ValidationRule("range", [-1.0, 1.0], "Must be between -1 and 1")],
            scoring_weight=0.7,
            difficulty_level="medium"
        )

    def get_category(self, category_id: str) -> Optional[PredictionCategory]:
        """Get category by ID"""
        return self.categories.get(category_id)

    def get_categories_by_group(self, group: PredictionCategoryGroup) -> List[PredictionCategory]:
        """Get all categories in a specific group"""
        return [cat for cat in self.categories.values() if cat.group == group]

    def get_all_categories(self) -> List[PredictionCategory]:
        """Get all categories"""
        return list(self.categories.values())

    def get_category_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all categories"""
        total_categories = len(self.categories)
        groups = {}
        difficulties = {}

        for category in self.categories.values():
            group_key = category.group.value
            groups[group_key] = groups.get(group_key, 0) + 1
            difficulties[category.difficulty_level] = difficulties.get(category.difficulty_level, 0) + 1

        live_categories = len([cat for cat in self.categories.values() if cat.requires_live_data])

        return {
            'total_categories': total_categories,
            'categories_by_group': groups,
            'categories_by_difficulty': difficulties,
            'live_data_categories': live_categories
        }

# Global instance
prediction_categories = ComprehensivePredictionCategories()

def get_prediction_categories() -> ComprehensivePredictionCategories:
    """Get the global prediction categories instance"""
    return prediction_categories
