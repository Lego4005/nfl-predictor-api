"""
Complete Betting Categories System - All 60+ Prediction Categories
Covers AL betting lines for a comprehensive NFL prediction site
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class PredictionCategoryGroup(Enum):
    """Main groups of prediction categories"""
    GAME_OUTCOME = "game_outcome"
    BETTING_MARKET = "betting_market"
    QUARTER_PROPS = "quarter_props"
    TEAM_PROPS = "team_props"
    GAME_PROPS = "game_props"
    PLAYER_PROPS = "player_props"
    ADVANCED_PROPS = "advanced_props"
    LIVE_SCENARIO = "live_scenario"
    SITUATIONAL = "situational"

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

class CompleteBettingCategories:
    """Complete registry of all 60+ betting categories"""

    def __init__(self):
        self.categories: Dict[str, PredictionCategory] = {}
        self._initialize_all_categories()

    def _initialize_all_categories(self):
        """Initialize all betting categories"""
        self._add_core_game_outcomes()
        self._add_betting_markets()
        self._add_quarter_props()
        self._add_team_props()
        self._add_game_props()
        self._add_player_props()
        self._add_advanced_player_props()
        self._add_live_scenarios()
        self._add_situational_analysis()

    def _add_core_game_outcomes(self):
        """Core game outcome predictions (4 categories)"""
        outcomes = [
            ("winner_prediction", "Game Winner", ["home", "away"], AccessTier.FREE, 10, 1.5),
            ("exact_score_home", "Home Team Score", (0, 70), AccessTier.FREE, 8, 0.8),
            ("exact_score_away", "Away Team Score", (0, 70), AccessTier.FREE, 8, 0.8),
            ("margin_of_victory", "Margin of Victory", (0, 50), AccessTier.FREE, 9, 1.2)
        ]

        for cat_id, name, validation, tier, popularity, weight in outcomes:
            if isinstance(validation, list):
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.GAME_OUTCOME,
                    data_type=DataType.CATEGORICAL,
                    description=f"{name} prediction",
                    validation_rules=[ValidationRule("choices", validation, f"Must be one of {validation}")],
                    scoring_weight=weight,
                    difficulty_level="medium",
                    access_tier=tier,
                    popularity_score=popularity
                )
            else:
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.GAME_OUTCOME,
                    data_type=DataType.NUMERIC,
                    description=f"{name} prediction",
                    validation_rules=[
                        ValidationRule("min", validation[0], f"Cannot be less than {validation[0]}"),
                        ValidationRule("max", validation[1], f"Cannot exceed {validation[1]}")
                    ],
                    scoring_weight=weight,
                    difficulty_level="hard" if "exact_score" in cat_id else "medium",
                    access_tier=tier,
                    popularity_score=popularity
                )

    def _add_betting_markets(self):
        """Main betting market predictions (6 categories)"""
        markets = [
            ("against_the_spread", "Against the Spread", ["home", "away", "push"], AccessTier.FREE, 10, 1.4),
            ("totals_over_under", "Over/Under Total", ["over", "under", "push"], AccessTier.FREE, 10, 1.3),
            ("moneyline", "Moneyline Winner", ["home", "away"], AccessTier.FREE, 9, 1.2),
            ("first_half_winner", "First Half Winner", ["home", "away", "tie"], AccessTier.FREE, 8, 1.0),
            ("first_half_spread", "First Half Spread", ["home", "away", "push"], AccessTier.PRO, 7, 1.1),
            ("first_half_total", "First Half Total", ["over", "under", "push"], AccessTier.PRO, 7, 1.0)
        ]

        for cat_id, name, choices, tier, popularity, weight in markets:
            self.categories[cat_id] = PredictionCategory(
                category_id=cat_id,
                category_name=name,
                group=PredictionCategoryGroup.BETTING_MARKET,
                data_type=DataType.CATEGORICAL,
                description=f"{name} prediction",
                validation_rules=[ValidationRule("choices", choices, f"Must be one of {choices}")],
                scoring_weight=weight,
                difficulty_level="medium",
                access_tier=tier,
                popularity_score=popularity
            )

    def _add_quarter_props(self):
        """Quarter-specific props (12 categories)"""
        quarter_props = [
            # Quarter Winners
            ("q1_winner", "1st Quarter Winner", ["home", "away", "tie"], AccessTier.FREE, 8),
            ("q2_winner", "2nd Quarter Winner", ["home", "away", "tie"], AccessTier.FREE, 7),
            ("q3_winner", "3rd Quarter Winner", ["home", "away", "tie"], AccessTier.PRO, 6),
            ("q4_winner", "4th Quarter Winner", ["home", "away", "tie"], AccessTier.PRO, 7),

            # Quarter Totals
            ("q1_total", "1st Quarter Total", (0, 35), AccessTier.PRO, 6),
            ("q2_total", "2nd Quarter Total", (0, 35), AccessTier.PRO, 5),
            ("q3_total", "3rd Quarter Total", (0, 35), AccessTier.PRO, 5),
            ("q4_total", "4th Quarter Total", (0, 35), AccessTier.PRO, 6),

            # Half Totals
            ("first_half_total_points", "1st Half Total Points", (0, 45), AccessTier.FREE, 8),
            ("second_half_total_points", "2nd Half Total Points", (0, 45), AccessTier.PRO, 7),

            # Scoring Patterns
            ("highest_scoring_quarter", "Highest Scoring Quarter", ["Q1", "Q2", "Q3", "Q4"], AccessTier.PRO, 6),
            ("lowest_scoring_quarter", "Lowest Scoring Quarter", ["Q1", "Q2", "Q3", "Q4"], AccessTier.PRO, 4)
        ]

        for cat_id, name, validation, tier, popularity in quarter_props:
            if isinstance(validation, list):
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.QUARTER_PROPS,
                    data_type=DataType.CATEGORICAL,
                    description=f"{name} prediction",
                    validation_rules=[ValidationRule("choices", validation, f"Must be one of {validation}")],
                    scoring_weight=1.0,
                    difficulty_level="medium",
                    access_tier=tier,
                    popularity_score=popularity
                )
            else:
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.QUARTER_PROPS,
                    data_type=DataType.NUMERIC,
                    description=f"{name} prediction",
                    validation_rules=[
                        ValidationRule("min", validation[0], "Cannot be negative"),
                        ValidationRule("max", validation[1], f"Cannot exceed {validation[1]}")
                    ],
                    scoring_weight=0.9,
                    difficulty_level="medium",
                    access_tier=tier,
                    popularity_score=popularity
                )

    def _add_team_props(self):
        """Team-specific props (10 categories)"""
        team_props = [
            ("home_team_total", "Home Team Total Points", (0, 60), AccessTier.FREE, 9),
            ("away_team_total", "Away Team Total Points", (0, 60), AccessTier.FREE, 9),
            ("first_team_to_score", "First Team to Score", ["home", "away"], AccessTier.FREE, 8),
            ("last_team_to_score", "Last Team to Score", ["home", "away"], AccessTier.PRO, 6),
            ("team_with_longest_td", "Team with Longest TD", ["home", "away"], AccessTier.PRO, 5),
            ("team_most_turnovers", "Team with Most Turnovers", ["home", "away", "tie"], AccessTier.PRO, 6),
            ("team_most_sacks", "Team with Most Sacks", ["home", "away", "tie"], AccessTier.PRO, 5),
            ("team_most_penalties", "Team with Most Penalties", ["home", "away", "tie"], AccessTier.PRO, 4),
            ("largest_lead", "Largest Lead of Game", (0, 35), AccessTier.PRO, 4),
            ("lead_changes", "Number of Lead Changes", (0, 10), AccessTier.PRO, 4)
        ]

        for cat_id, name, validation, tier, popularity in team_props:
            if isinstance(validation, list):
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.TEAM_PROPS,
                    data_type=DataType.CATEGORICAL,
                    description=f"{name} prediction",
                    validation_rules=[ValidationRule("choices", validation, f"Must be one of {validation}")],
                    scoring_weight=1.1,
                    difficulty_level="medium",
                    access_tier=tier,
                    popularity_score=popularity
                )
            else:
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.TEAM_PROPS,
                    data_type=DataType.NUMERIC,
                    description=f"{name} prediction",
                    validation_rules=[
                        ValidationRule("min", validation[0], f"Cannot be less than {validation[0]}"),
                        ValidationRule("max", validation[1], f"Cannot exceed {validation[1]}")
                    ],
                    scoring_weight=1.0,
                    difficulty_level="medium",
                    access_tier=tier,
                    popularity_score=popularity
                )

    def _add_game_props(self):
        """General game props (15 categories)"""
        game_props = [
            # Yes/No Props
            ("will_go_to_overtime", "Will Game Go to Overtime?", ["yes", "no"], AccessTier.FREE, 7),
            ("will_there_be_safety", "Will There Be a Safety?", ["yes", "no"], AccessTier.PRO, 4),
            ("pick_six_scored", "Will There Be a Pick-6?", ["yes", "no"], AccessTier.PRO, 5),
            ("fumble_recovery_td", "Fumble Recovery TD?", ["yes", "no"], AccessTier.PRO, 4),
            ("defensive_td_scored", "Defensive TD Scored?", ["yes", "no"], AccessTier.PRO, 6),
            ("special_teams_td", "Special Teams TD?", ["yes", "no"], AccessTier.PRO, 4),
            ("punt_return_td", "Punt Return TD?", ["yes", "no"], AccessTier.PRO, 3),
            ("kickoff_return_td", "Kickoff Return TD?", ["yes", "no"], AccessTier.PRO, 3),

            # Numeric Props
            ("total_turnovers", "Total Turnovers", (0, 10), AccessTier.FREE, 7),
            ("total_sacks", "Total Sacks", (0, 15), AccessTier.PRO, 6),
            ("total_penalties", "Total Penalties", (0, 25), AccessTier.PRO, 5),
            ("longest_touchdown", "Longest Touchdown", (1, 99), AccessTier.PRO, 6),
            ("longest_field_goal", "Longest Field Goal", (18, 65), AccessTier.PRO, 5),
            ("total_field_goals", "Total Field Goals Made", (0, 8), AccessTier.PRO, 5),
            ("missed_extra_points", "Missed Extra Points", (0, 4), AccessTier.PRO, 3)
        ]

        for cat_id, name, validation, tier, popularity in game_props:
            if isinstance(validation, list):
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.GAME_PROPS,
                    data_type=DataType.CATEGORICAL,
                    description=f"{name} prediction",
                    validation_rules=[ValidationRule("choices", validation, f"Must be one of {validation}")],
                    scoring_weight=0.8,
                    difficulty_level="hard",
                    access_tier=tier,
                    popularity_score=popularity
                )
            else:
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.GAME_PROPS,
                    data_type=DataType.NUMERIC,
                    description=f"{name} prediction",
                    validation_rules=[
                        ValidationRule("min", validation[0], f"Cannot be less than {validation[0]}"),
                        ValidationRule("max", validation[1], f"Cannot exceed {validation[1]}")
                    ],
                    scoring_weight=0.9,
                    difficulty_level="medium",
                    access_tier=tier,
                    popularity_score=popularity
                )

    def _add_player_props(self):
        """Standard player props (10 categories)"""
        player_props = [
            ("qb_passing_yards", "QB Passing Yards", (0, 600), AccessTier.FREE, 9),
            ("qb_touchdowns", "QB Passing TDs", (0, 8), AccessTier.FREE, 8),
            ("qb_interceptions", "QB Interceptions", (0, 6), AccessTier.FREE, 7),
            ("qb_rushing_yards", "QB Rushing Yards", (0, 150), AccessTier.PRO, 7),
            ("rb_rushing_yards", "RB Rushing Yards", (0, 300), AccessTier.FREE, 8),
            ("rb_touchdowns", "RB Rushing TDs", (0, 5), AccessTier.PRO, 7),
            ("wr_receiving_yards", "WR Receiving Yards", (0, 250), AccessTier.FREE, 8),
            ("wr_receptions", "WR Receptions", (0, 20), AccessTier.PRO, 7),
            ("te_receiving_yards", "TE Receiving Yards", (0, 150), AccessTier.PRO, 6),
            ("kicker_total_points", "Kicker Total Points", (0, 20), AccessTier.PRO, 6)
        ]

        for cat_id, name, validation, tier, popularity in player_props:
            self.categories[cat_id] = PredictionCategory(
                category_id=cat_id,
                category_name=name,
                group=PredictionCategoryGroup.PLAYER_PROPS,
                data_type=DataType.NUMERIC,
                description=f"{name} prediction",
                validation_rules=[
                    ValidationRule("min", validation[0], f"Cannot be less than {validation[0]}"),
                    ValidationRule("max", validation[1], f"Cannot exceed {validation[1]}")
                ],
                scoring_weight=1.0,
                difficulty_level="medium",
                access_tier=tier,
                popularity_score=popularity
            )

    def _add_advanced_player_props(self):
        """Advanced player props (12 categories)"""
        advanced_props = [
            # TD Scorer Props
            ("anytime_td_scorer", "Anytime TD Scorer", ["yes", "no"], AccessTier.FREE, 10),
            ("first_td_scorer", "First TD Scorer", ["yes", "no"], AccessTier.PRO, 9),
            ("last_td_scorer", "Last TD Scorer", ["yes", "no"], AccessTier.PRO, 6),

            # Distance Props
            ("qb_longest_completion", "QB Longest Completion", (1, 99), AccessTier.PRO, 5),
            ("rb_longest_rush", "RB Longest Rush", (1, 99), AccessTier.PRO, 5),
            ("wr_longest_reception", "WR Longest Reception", (1, 99), AccessTier.PRO, 5),
            ("kicker_longest_fg", "Kicker Longest FG", (18, 65), AccessTier.PRO, 5),

            # Defense Props
            ("def_interceptions", "Defense Interceptions", (0, 5), AccessTier.PRO, 6),
            ("def_sacks", "Defense Sacks", (0, 8), AccessTier.PRO, 6),
            ("def_forced_fumbles", "Defense Forced Fumbles", (0, 4), AccessTier.PRO, 5),

            # Fantasy Props
            ("qb_fantasy_points", "QB Fantasy Points", (0, 50), AccessTier.PRO, 7),
            ("skill_player_fantasy", "Top Skill Player Fantasy", (0, 40), AccessTier.PRO, 6)
        ]

        for cat_id, name, validation, tier, popularity in advanced_props:
            if isinstance(validation, list):
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.ADVANCED_PROPS,
                    data_type=DataType.CATEGORICAL,
                    description=f"{name} prediction",
                    validation_rules=[ValidationRule("choices", validation, f"Must be one of {validation}")],
                    scoring_weight=0.7,
                    difficulty_level="hard",
                    access_tier=tier,
                    popularity_score=popularity
                )
            else:
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.ADVANCED_PROPS,
                    data_type=DataType.NUMERIC,
                    description=f"{name} prediction",
                    validation_rules=[
                        ValidationRule("min", validation[0], f"Cannot be less than {validation[0]}"),
                        ValidationRule("max", validation[1], f"Cannot exceed {validation[1]}")
                    ],
                    scoring_weight=0.8,
                    difficulty_level="hard",
                    access_tier=tier,
                    popularity_score=popularity
                )

    def _add_live_scenarios(self):
        """Live betting scenarios (6 categories)"""
        live_scenarios = [
            ("live_win_probability", "Live Win Probability", (0.0, 1.0), AccessTier.PRO, 8),
            ("next_score_type", "Next Score Type", ["touchdown", "field_goal", "safety", "none"], AccessTier.PRO, 7),
            ("drive_outcome", "Current Drive Outcome", ["touchdown", "field_goal", "punt", "turnover"], AccessTier.PRO, 6),
            ("fourth_down_decision", "4th Down Decision", ["punt", "field_goal", "go_for_it"], AccessTier.PRO, 5),
            ("next_team_to_score", "Next Team to Score", ["home", "away", "none"], AccessTier.PRO, 8),
            ("time_of_next_score", "Time of Next Score", (0, 900), AccessTier.PREMIUM, 4)  # seconds
        ]

        for cat_id, name, validation, tier, popularity in live_scenarios:
            if isinstance(validation, list):
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.LIVE_SCENARIO,
                    data_type=DataType.CATEGORICAL,
                    description=f"{name} prediction",
                    validation_rules=[ValidationRule("choices", validation, f"Must be one of {validation}")],
                    scoring_weight=0.8,
                    difficulty_level="hard",
                    requires_live_data=True,
                    access_tier=tier,
                    popularity_score=popularity
                )
            else:
                data_type = DataType.PERCENTAGE if validation == (0.0, 1.0) else DataType.NUMERIC
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.LIVE_SCENARIO,
                    data_type=data_type,
                    description=f"{name} prediction",
                    validation_rules=[ValidationRule("range", validation, f"Must be between {validation[0]} and {validation[1]}")],
                    scoring_weight=0.9,
                    difficulty_level="hard",
                    requires_live_data=True,
                    access_tier=tier,
                    popularity_score=popularity
                )

    def _add_situational_analysis(self):
        """Situational analysis factors (8 categories)"""
        situational = [
            ("weather_impact", "Weather Impact Score", (0.0, 1.0), AccessTier.PRO, 5),
            ("injury_impact", "Injury Impact Score", (0.0, 1.0), AccessTier.PRO, 6),
            ("travel_rest_factor", "Travel/Rest Factor", (-0.5, 0.5), AccessTier.PRO, 4),
            ("divisional_rivalry", "Divisional Rivalry Factor", (0.0, 1.0), AccessTier.FREE, 6),
            ("coaching_advantage", "Coaching Advantage", ["home", "away", "neutral"], AccessTier.PRO, 6),
            ("home_field_advantage", "Home Field Advantage", (0, 10), AccessTier.FREE, 7),
            ("momentum_factor", "Momentum Factor", (-1.0, 1.0), AccessTier.FREE, 6),
            ("public_betting_bias", "Public Betting Bias", (-1.0, 1.0), AccessTier.PRO, 5)
        ]

        for cat_id, name, validation, tier, popularity in situational:
            if isinstance(validation, list):
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.SITUATIONAL,
                    data_type=DataType.CATEGORICAL,
                    description=f"{name} assessment",
                    validation_rules=[ValidationRule("choices", validation, f"Must be one of {validation}")],
                    scoring_weight=0.8,
                    difficulty_level="medium",
                    access_tier=tier,
                    popularity_score=popularity
                )
            else:
                data_type = DataType.PERCENTAGE if validation[1] <= 1.0 and validation[0] >= 0.0 else DataType.NUMERIC
                self.categories[cat_id] = PredictionCategory(
                    category_id=cat_id,
                    category_name=name,
                    group=PredictionCategoryGroup.SITUATIONAL,
                    data_type=data_type,
                    description=f"{name} assessment",
                    validation_rules=[ValidationRule("range", validation, f"Must be between {validation[0]} and {validation[1]}")],
                    scoring_weight=0.7,
                    difficulty_level="medium",
                    access_tier=tier,
                    popularity_score=popularity
                )

    # Utility Methods
    def get_category(self, category_id: str) -> Optional[PredictionCategory]:
        """Get category by ID"""
        return self.categories.get(category_id)

    def get_categories_by_group(self, group: PredictionCategoryGroup) -> List[PredictionCategory]:
        """Get all categories in a specific group"""
        return [cat for cat in self.categories.values() if cat.group == group]

    def get_categories_by_tier(self, tier: AccessTier) -> List[PredictionCategory]:
        """Get all categories for a specific access tier"""
        return [cat for cat in self.categories.values() if cat.access_tier == tier]

    def get_popular_categories(self, min_popularity: int = 7) -> List[PredictionCategory]:
        """Get categories above a popularity threshold"""
        return [cat for cat in self.categories.values() if cat.popularity_score >= min_popularity]

    def get_free_categories(self) -> List[PredictionCategory]:
        """Get all free categories"""
        return self.get_categories_by_tier(AccessTier.FREE)

    def get_pro_categories(self) -> List[PredictionCategory]:
        """Get all pro categories"""
        return self.get_categories_by_tier(AccessTier.PRO)

    def get_premium_categories(self) -> List[PredictionCategory]:
        """Get all premium categories"""
        return self.get_categories_by_tier(AccessTier.PREMIUM)

    def get_category_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary statistics"""
        total_categories = len(self.categories)
        groups = {}
        difficulties = {}
        tiers = {}

        for category in self.categories.values():
            group_key = category.group.value
            groups[group_key] = groups.get(group_key, 0) + 1
            difficulties[category.difficulty_level] = difficulties.get(category.difficulty_level, 0) + 1
            tier_key = category.access_tier.value
            tiers[tier_key] = tiers.get(tier_key, 0) + 1

        live_categories = len([cat for cat in self.categories.values() if cat.requires_live_data])
        popular_categories = len([cat for cat in self.categories.values() if cat.popularity_score >= 7])

        return {
            'total_categories': total_categories,
            'categories_by_group': groups,
            'categories_by_difficulty': difficulties,
            'categories_by_tier': tiers,
            'live_data_categories': live_categories,
            'popular_categories': popular_categories,
            'monetization_split': {
                'free': tiers.get('free', 0),
                'pro': tiers.get('pro', 0),
                'premium': tiers.get('premium', 0)
            }
        }

# Global instance
complete_betting_categories = CompleteBettingCategories()

def get_complete_betting_categories() -> CompleteBettingCategories:
    """Get the global complete betting categories instance"""
    return complete_betting_categories
