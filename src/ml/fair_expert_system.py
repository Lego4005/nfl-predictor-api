"""
Fair Expert Differentiation System for NFL Predictions
Eliminates structural advantages while maintaining unique expert methodologies

Core Principles:
1. Equal Foundation: All experts get same data, same base confidence, same validation
2. Methodological Differentiation: Unique analytical lenses, not privileges
3. Dynamic Contextual Weighting: Weights earned based on game relevance
4. Shared Reality: Consensus on objective facts, personal interpretation of implications
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
import math
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class GameContext:
    """Shared reality layer: objective facts all experts agree on"""
    home_team: str
    away_team: str
    spread: float
    total: float
    weather: Dict[str, Any]
    injuries: Dict[str, List[Dict]]
    line_movement: float
    public_percentage: float
    sharp_action: str
    game_time: str

    # Derived context metrics (calculated, not subjective)
    injury_severity_score: float = 0.0
    weather_impact_score: float = 0.0
    market_stability_score: float = 0.0

    def calculate_context_scores(self):
        """Calculate objective context scores that determine expert relevance"""

        # Injury severity (objective calculation)
        total_injuries = len(self.injuries.get('home', [])) + len(self.injuries.get('away', []))
        qb_injuries = sum(1 for inj in self.injuries.get('home', []) + self.injuries.get('away', [])
                         if inj.get('position') == 'QB')
        self.injury_severity_score = min(1.0, (total_injuries * 0.1) + (qb_injuries * 0.4))

        # Weather impact (objective calculation)
        wind = self.weather.get('wind_speed', 0)
        temp = abs(self.weather.get('temperature', 70) - 70)  # Distance from ideal temp
        precipitation = 1 if 'rain' in self.weather.get('conditions', '').lower() else 0
        self.weather_impact_score = min(1.0, (wind * 0.05) + (temp * 0.01) + (precipitation * 0.3))

        # Market instability (objective calculation)
        line_volatility = abs(self.line_movement)
        public_extremity = abs(self.public_percentage - 50) / 50
        self.market_stability_score = min(1.0, (line_volatility * 0.2) + (public_extremity * 0.5))

@dataclass
class ExpertRelevance:
    """Dynamic relevance scoring for fair competition"""
    expert_name: str
    base_relevance: float = 0.5  # All experts start equal
    context_multipliers: Dict[str, float] = field(default_factory=dict)
    final_relevance: float = 0.5

    def calculate_relevance(self, context: GameContext):
        """Calculate expert's relevance for this specific game context"""
        self.final_relevance = self.base_relevance

        # Apply context multipliers (but keep bounded)
        for factor, multiplier in self.context_multipliers.items():
            if factor == 'injury_specialist' and context.injury_severity_score > 0.3:
                self.final_relevance *= (1 + (context.injury_severity_score * multiplier))
            elif factor == 'weather_specialist' and context.weather_impact_score > 0.3:
                self.final_relevance *= (1 + (context.weather_impact_score * multiplier))
            elif factor == 'market_specialist' and context.market_stability_score > 0.3:
                self.final_relevance *= (1 + (context.market_stability_score * multiplier))

        # Normalize to prevent any expert from having >80% relevance
        self.final_relevance = min(0.8, max(0.2, self.final_relevance))

@dataclass
class ConsistentPrediction:
    """Logically consistent prediction set"""
    # Primary decisions (must be consistent)
    winner: str
    win_probability: float  # 0.0 to 1.0
    exact_score: Dict[str, int]  # Must align with winner
    margin_of_victory: float  # Must align with exact_score

    # Secondary decisions (derived from primary)
    point_spread_pick: str    # Derived from winner + margin
    total_pick: str           # Derived from exact_score total
    first_half_winner: str    # Derived from game flow
    highest_scoring_quarter: str  # Derived from total + flow

    # Meta information
    confidence: float = 0.5   # Adjusted by relevance, not base capability
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)

    def validate_consistency(self) -> bool:
        """Ensure all predictions are logically consistent"""

        # Check 1: Winner matches exact score
        home_score = list(self.exact_score.values())[0]
        away_score = list(self.exact_score.values())[1]
        score_winner = list(self.exact_score.keys())[0] if home_score > away_score else list(self.exact_score.keys())[1]

        if score_winner != self.winner:
            logger.error(f"Inconsistency: Winner {self.winner} != Score winner {score_winner}")
            return False

        # Check 2: Margin matches score difference (allow 2-point tolerance for rounding)
        predicted_margin = abs(home_score - away_score)
        if abs(predicted_margin - self.margin_of_victory) > 2:
            logger.error(f"Inconsistency: Margin {self.margin_of_victory} != Score margin {predicted_margin}")
            return False

        # Check 3: Total pick aligns with total score
        total_score = home_score + away_score
        if self.total_pick == 'over' and total_score < 40:
            logger.error(f"Inconsistency: Over pick but low total score {total_score}")
            return False
        if self.total_pick == 'under' and total_score > 50:
            logger.error(f"Inconsistency: Under pick but high total score {total_score}")
            return False

        return True

class FairExpertBase(ABC):
    """Base class ensuring all experts have equal foundation"""

    def __init__(self, expert_id: str, name: str, specializations: List[str]):
        self.expert_id = expert_id
        self.name = name
        self.specializations = specializations

        # EQUAL FOUNDATION PRINCIPLES
        self.base_confidence = 0.5  # ALL experts start with same confidence
        self.data_access_level = "full"  # ALL experts get same data
        self.prediction_categories = self._get_standard_categories()  # ALL predict same categories

        # Unique methodology (THIS is where experts differ)
        self.analytical_lens = self._define_analytical_lens()
        self.relevance_factors = self._define_relevance_factors()

        # Performance tracking (fair evaluation)
        self.performance_by_relevance = {"high": [], "medium": [], "low": []}

        # Weekly Learning/Adaptation System
        self.weekly_weights = {}  # Each expert can modify their own weights
        self.adaptation_history = []  # Track what changes were made
        self.performance_trends = []  # Track improvement/decline
        self.learning_rate = 0.1  # How aggressively to adapt
        self.weeks_active = 0

    def _get_standard_categories(self) -> List[str]:
        """Standard prediction categories ALL experts must predict"""
        return [
            'game_winner', 'exact_score', 'margin_of_victory', 'point_spread',
            'total_over_under', 'first_half_winner', 'highest_scoring_quarter',
            'passing_props', 'rushing_props', 'receiving_props', 'fantasy_points',
            'weather_impact', 'injury_impact', 'momentum_analysis', 'situational_predictions',
            'special_teams', 'coaching_matchup', 'home_field_advantage', 'travel_rest_impact'
        ]

    @abstractmethod
    def _define_analytical_lens(self) -> str:
        """Define how this expert interprets data (METHODOLOGY differentiation)"""
        pass

    @abstractmethod
    def _define_relevance_factors(self) -> Dict[str, float]:
        """Define what game contexts make this expert more relevant"""
        pass

    def make_fair_prediction(self, context: GameContext) -> ConsistentPrediction:
        """Generate consistent prediction using fair methodology"""

        # Step 1: Calculate expert's relevance for this game
        relevance = ExpertRelevance(
            expert_name=self.name,
            context_multipliers=self.relevance_factors
        )
        relevance.calculate_relevance(context)

        # Step 2: Apply analytical lens to shared reality
        analysis = self._apply_analytical_lens(context)

        # Step 3: Make primary decisions using methodology
        primary_decisions = self._make_primary_decisions(context, analysis, relevance)

        # Step 4: Generate consistent secondary predictions
        prediction = self._generate_consistent_prediction(context, primary_decisions, relevance)

        # Step 5: Validate consistency (SAME rules for ALL experts)
        if not prediction.validate_consistency():
            raise ValueError(f"{self.name}: Generated inconsistent predictions")

        # Step 6: Record performance for fair evaluation
        self._record_performance(relevance.final_relevance, prediction)

        return prediction

    def weekly_adaptation(self, week_results: List[Dict]) -> Dict[str, Any]:
        """Weekly learning where expert adapts their own weights/methodology"""

        self.weeks_active += 1
        adaptation_log = {
            'week': self.weeks_active,
            'previous_performance': self._calculate_weekly_performance(week_results),
            'adaptations_made': [],
            'reasoning': []
        }

        # Each expert can implement their own learning strategy
        adaptations = self._analyze_performance_and_adapt(week_results)

        for adaptation in adaptations:
            # Apply the adaptation
            if adaptation['type'] == 'weight_adjustment':
                old_weight = self.weekly_weights.get(adaptation['factor'], 1.0)
                new_weight = max(0.1, min(2.0, old_weight + adaptation['change']))  # Bounded
                self.weekly_weights[adaptation['factor']] = new_weight

                adaptation_log['adaptations_made'].append({
                    'factor': adaptation['factor'],
                    'old_weight': old_weight,
                    'new_weight': new_weight,
                    'change': adaptation['change']
                })

            elif adaptation['type'] == 'methodology_tweak':
                # Each expert can implement custom methodology changes
                self._apply_methodology_tweak(adaptation)
                adaptation_log['adaptations_made'].append(adaptation)

            adaptation_log['reasoning'].append(adaptation['reasoning'])

        # Record this week's adaptation
        self.adaptation_history.append(adaptation_log)

        return adaptation_log

    @abstractmethod
    def _analyze_performance_and_adapt(self, week_results: List[Dict]) -> List[Dict]:
        """Each expert implements their own learning strategy"""
        pass

    def _apply_methodology_tweak(self, adaptation: Dict):
        """Apply methodology changes (can be overridden by each expert)"""
        # Base implementation - experts can override for custom changes
        pass

    def _calculate_weekly_performance(self, week_results: List[Dict]) -> Dict:
        """Calculate performance metrics for the week"""
        if not week_results:
            return {'accuracy': 0.0, 'total_games': 0}

        correct_predictions = sum(1 for result in week_results if result.get('correct', False))
        total_games = len(week_results)
        accuracy = correct_predictions / total_games if total_games > 0 else 0.0

        return {
            'accuracy': accuracy,
            'total_games': total_games,
            'correct_predictions': correct_predictions,
            'by_category': self._performance_by_category(week_results)
        }

    def _performance_by_category(self, week_results: List[Dict]) -> Dict:
        """Break down performance by prediction category"""
        category_performance = {}
        for result in week_results:
            for category, correct in result.get('category_results', {}).items():
                if category not in category_performance:
                    category_performance[category] = {'correct': 0, 'total': 0}
                category_performance[category]['total'] += 1
                if correct:
                    category_performance[category]['correct'] += 1

        # Calculate accuracy for each category
        for category in category_performance:
            stats = category_performance[category]
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0.0

        return category_performance

class ExpertPerformanceTracker:
    """Tracks and shares performance data across experts for meta-learning"""

    def __init__(self):
        self.weekly_performances = {}  # {week: {expert_name: performance_data}}
        self.expert_specialties = {}   # Track what each expert excels at
        self.current_week = 0

    def record_weekly_performance(self, week: int, expert_name: str, performance_data: Dict):
        """Record an expert's weekly performance for transparency"""
        if week not in self.weekly_performances:
            self.weekly_performances[week] = {}

        self.weekly_performances[week][expert_name] = {
            'overall_accuracy': performance_data['accuracy'],
            'total_games': performance_data['total_games'],
            'category_performance': performance_data['by_category'],
            'timestamp': datetime.now()
        }

        # Update specialty tracking
        self._update_specialty_tracking(expert_name, performance_data)

    def _update_specialty_tracking(self, expert_name: str, performance_data: Dict):
        """Track what categories each expert excels at"""
        if expert_name not in self.expert_specialties:
            self.expert_specialties[expert_name] = {}

        for category, stats in performance_data['by_category'].items():
            if category not in self.expert_specialties[expert_name]:
                self.expert_specialties[expert_name][category] = []

            self.expert_specialties[expert_name][category].append(stats['accuracy'])

    def get_peer_performance_insights(self, requesting_expert: str, weeks_back: int = 4) -> Dict:
        """Get performance insights about other experts (for meta-learning)"""

        insights = {
            'top_performers': {},
            'category_leaders': {},
            'trending_experts': {},
            'my_relative_performance': {}
        }

        recent_weeks = [w for w in self.weekly_performances.keys() if w >= (self.current_week - weeks_back)]

        if not recent_weeks:
            return insights

        # Calculate overall top performers
        expert_accuracies = {}
        for week in recent_weeks:
            for expert, data in self.weekly_performances[week].items():
                if expert not in expert_accuracies:
                    expert_accuracies[expert] = []
                expert_accuracies[expert].append(data['overall_accuracy'])

        for expert, accuracies in expert_accuracies.items():
            avg_accuracy = sum(accuracies) / len(accuracies)
            insights['top_performers'][expert] = {
                'avg_accuracy': avg_accuracy,
                'games_predicted': sum(self.weekly_performances[w][expert]['total_games']
                                     for w in recent_weeks if expert in self.weekly_performances[w])
            }

        # Find category leaders
        category_leaders = {}
        for expert, categories in self.expert_specialties.items():
            for category, accuracies in categories.items():
                if len(accuracies) >= 3:  # Need minimum data
                    avg_acc = sum(accuracies[-weeks_back:]) / min(len(accuracies), weeks_back)
                    if category not in category_leaders or avg_acc > category_leaders[category]['accuracy']:
                        category_leaders[category] = {'expert': expert, 'accuracy': avg_acc}

        insights['category_leaders'] = category_leaders

        # Calculate requesting expert's relative performance
        if requesting_expert in expert_accuracies:
            my_accuracy = sum(expert_accuracies[requesting_expert]) / len(expert_accuracies[requesting_expert])
            all_accuracies = [sum(accs)/len(accs) for accs in expert_accuracies.values()]
            avg_accuracy = sum(all_accuracies) / len(all_accuracies)

            insights['my_relative_performance'] = {
                'my_accuracy': my_accuracy,
                'peer_average': avg_accuracy,
                'rank': sum(1 for acc in all_accuracies if acc < my_accuracy) + 1,
                'total_experts': len(all_accuracies)
            }

        return insights

    def should_defer_to_peer(self, requesting_expert: str, category: str, confidence_threshold: float = 0.7) -> Optional[str]:
        """Determine if expert should defer to a peer in specific category"""

        insights = self.get_peer_performance_insights(requesting_expert)

        # Check if there's a clear category leader
        if category in insights['category_leaders']:
            leader_data = insights['category_leaders'][category]
            leader_expert = leader_data['expert']
            leader_accuracy = leader_data['accuracy']

            # If leader is significantly better and not the requesting expert
            if leader_expert != requesting_expert and leader_accuracy > confidence_threshold:
                return leader_expert

        return None

# Global performance tracker (shared across all experts)
performance_tracker = ExpertPerformanceTracker()

class FairExpertBase(ABC):
    """Base class ensuring all experts have equal foundation"""

    def __init__(self, expert_id: str, name: str, specializations: List[str]):
        self.expert_id = expert_id
        self.name = name
        self.specializations = specializations

        # EQUAL FOUNDATION PRINCIPLES
        self.base_confidence = 0.5  # ALL experts start with same confidence
        self.data_access_level = "full"  # ALL experts get same data
        self.prediction_categories = self._get_standard_categories()  # ALL predict same categories

        # Unique methodology (THIS is where experts differ)
        self.analytical_lens = self._define_analytical_lens()
        self.relevance_factors = self._define_relevance_factors()

        # Performance tracking (fair evaluation)
        self.performance_by_relevance = {"high": [], "medium": [], "low": []}

        # Weekly Learning/Adaptation System
        self.weekly_weights = {}  # Each expert can modify their own weights
        self.adaptation_history = []  # Track what changes were made
        self.performance_trends = []  # Track improvement/decline
        self.learning_rate = 0.1  # How aggressively to adapt
        self.weeks_active = 0

    def _get_standard_categories(self) -> List[str]:
        """Standard prediction categories ALL experts must predict"""
        return [
            'game_winner', 'exact_score', 'margin_of_victory', 'point_spread',
            'total_over_under', 'first_half_winner', 'highest_scoring_quarter',
            'passing_props', 'rushing_props', 'receiving_props', 'fantasy_points',
            'weather_impact', 'injury_impact', 'momentum_analysis', 'situational_predictions',
            'special_teams', 'coaching_matchup', 'home_field_advantage', 'travel_rest_impact'
        ]

    @abstractmethod
    def _define_analytical_lens(self) -> str:
        """Define how this expert interprets data (METHODOLOGY differentiation)"""
        pass

    @abstractmethod
    def _define_relevance_factors(self) -> Dict[str, float]:
        """Define what game contexts make this expert more relevant"""
        pass

    def make_fair_prediction(self, context: GameContext) -> ConsistentPrediction:
        """Generate consistent prediction using fair methodology"""

        # Step 1: Calculate expert's relevance for this game
        relevance = ExpertRelevance(
            expert_name=self.name,
            context_multipliers=self.relevance_factors
        )
        relevance.calculate_relevance(context)

        # Step 2: Apply analytical lens to shared reality
        analysis = self._apply_analytical_lens(context)

        # Step 3: Make primary decisions using methodology
        primary_decisions = self._make_primary_decisions(context, analysis, relevance)

        # Step 4: Generate consistent secondary predictions
        prediction = self._generate_consistent_prediction(context, primary_decisions, relevance)

        # Step 5: Validate consistency (SAME rules for ALL experts)
        if not prediction.validate_consistency():
            raise ValueError(f"{self.name}: Generated inconsistent predictions")

        # Step 6: Record performance for fair evaluation
        self._record_performance(relevance.final_relevance, prediction)

        return prediction

    def weekly_adaptation(self, week_results: List[Dict]) -> Dict[str, Any]:
        """Weekly learning where expert adapts their own weights/methodology"""

        self.weeks_active += 1
        adaptation_log = {
            'week': self.weeks_active,
            'previous_performance': self._calculate_weekly_performance(week_results),
            'adaptations_made': [],
            'reasoning': []
        }

        # Record performance for cross-expert learning
        performance_data = self._calculate_weekly_performance(week_results)
        performance_tracker.record_weekly_performance(self.weeks_active, self.name, performance_data)

        # Get insights from other experts
        peer_insights = performance_tracker.get_peer_performance_insights(self.name)

        # Each expert can implement their own learning strategy
        adaptations = self._analyze_performance_and_adapt(week_results, peer_insights)

        for adaptation in adaptations:
            # Apply the adaptation
            if adaptation['type'] == 'weight_adjustment':
                old_weight = self.weekly_weights.get(adaptation['factor'], 1.0)
                new_weight = max(0.1, min(2.0, old_weight + adaptation['change']))  # Bounded
                self.weekly_weights[adaptation['factor']] = new_weight

                adaptation_log['adaptations_made'].append({
                    'factor': adaptation['factor'],
                    'old_weight': old_weight,
                    'new_weight': new_weight,
                    'change': adaptation['change']
                })

            elif adaptation['type'] == 'methodology_tweak':
                # Each expert can implement custom methodology changes
                self._apply_methodology_tweak(adaptation)
                adaptation_log['adaptations_made'].append(adaptation)

            adaptation_log['reasoning'].append(adaptation['reasoning'])

        # Record this week's adaptation
        self.adaptation_history.append(adaptation_log)

        return adaptation_log

    @abstractmethod
    def _analyze_performance_and_adapt(self, week_results: List[Dict], peer_insights: Dict = None) -> List[Dict]:
        """Each expert implements their own learning strategy with optional peer insights"""
        pass

    @abstractmethod
    def _apply_analytical_lens(self, context: GameContext) -> Dict[str, Any]:
        """Apply expert's unique methodology to interpret shared data"""
        pass

    def _apply_methodology_tweak(self, adaptation: Dict):
        """Apply methodology changes (can be overridden by each expert)"""
        # Base implementation - experts can override for custom changes
        pass

    def _calculate_weekly_performance(self, week_results: List[Dict]) -> Dict:
        """Calculate performance metrics for the week"""
        if not week_results:
            return {'accuracy': 0.0, 'total_games': 0, 'by_category': {}}

        correct_predictions = sum(1 for result in week_results if result.get('correct', False))
        total_games = len(week_results)
        accuracy = correct_predictions / total_games if total_games > 0 else 0.0

        return {
            'accuracy': accuracy,
            'total_games': total_games,
            'correct_predictions': correct_predictions,
            'by_category': self._performance_by_category(week_results)
        }

    def _performance_by_category(self, week_results: List[Dict]) -> Dict:
        """Break down performance by prediction category"""
        category_performance = {}
        for result in week_results:
            for category, correct in result.get('category_results', {}).items():
                if category not in category_performance:
                    category_performance[category] = {'correct': 0, 'total': 0}
                category_performance[category]['total'] += 1
                if correct:
                    category_performance[category]['correct'] += 1

        # Calculate accuracy for each category
        for category in category_performance:
            stats = category_performance[category]
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0.0

        return category_performance

    def _make_primary_decisions(self, context: GameContext, analysis: Dict, relevance: ExpertRelevance) -> Dict:
        """Make primary decisions that drive all other predictions"""

        # All experts use same decision framework but different analysis
        decision_factors = analysis.get('decision_factors', [])

        # Calculate weighted score (methodology differs, framework same)
        home_score = sum(factor.get('home_impact', 0) for factor in decision_factors)
        away_score = sum(factor.get('away_impact', 0) for factor in decision_factors)

        # Determine winner
        if home_score > away_score:
            winner = context.home_team
            win_prob = min(0.95, 0.5 + ((home_score - away_score) / 10))
        else:
            winner = context.away_team
            win_prob = min(0.95, 0.5 + ((away_score - home_score) / 10))

        # Calculate margin and scores
        margin = (win_prob - 0.5) * 20  # Convert probability to points
        total_points = context.total + analysis.get('total_adjustment', 0)

        if winner == context.home_team:
            home_final = int((total_points + margin) / 2)
            away_final = int(total_points - home_final)
        else:
            away_final = int((total_points + margin) / 2)
            home_final = int(total_points - away_final)

        return {
            'winner': winner,
            'win_probability': win_prob,
            'exact_score': {context.home_team: home_final, context.away_team: away_final},
            'margin': abs(margin),
            'confidence': self.base_confidence * relevance.final_relevance,
            'reasoning': analysis.get('reasoning', f"{self.name}'s {self.analytical_lens} analysis")
        }

    def _generate_consistent_prediction(self, context: GameContext, primary: Dict, relevance: ExpertRelevance) -> ConsistentPrediction:
        """Generate all predictions that cascade consistently from primary decisions"""

        # Calculate total score for over/under
        total_score = sum(primary['exact_score'].values())
        total_pick = 'over' if total_score > context.total else 'under'

        # Determine ATS pick
        if primary['winner'] == context.home_team:
            ats_pick = context.home_team if context.spread <= primary['margin'] else context.away_team
        else:
            ats_pick = context.away_team if abs(context.spread) <= primary['margin'] else context.home_team

        # Game flow predictions
        first_half = primary['winner'] if primary['confidence'] > 0.6 else 'close'
        scoring_quarter = '4th' if total_pick == 'over' else '2nd'

        return ConsistentPrediction(
            winner=primary['winner'],
            win_probability=primary['win_probability'],
            exact_score=primary['exact_score'],
            margin_of_victory=primary['margin'],
            point_spread_pick=ats_pick,
            total_pick=total_pick,
            first_half_winner=first_half,
            highest_scoring_quarter=scoring_quarter,
            confidence=primary['confidence'],
            reasoning=primary['reasoning'],
            key_factors=[]
        )

    def _record_performance(self, relevance: float, prediction: ConsistentPrediction):
        """Record performance across different relevance levels for fair evaluation"""

        if relevance >= 0.7:
            category = "high"
        elif relevance >= 0.4:
            category = "medium"
        else:
            category = "low"

        # Store prediction for later accuracy evaluation
        self.performance_by_relevance[category].append({
            'prediction': prediction,
            'timestamp': datetime.now(),
            'relevance_score': relevance
        })

# Example Implementation: Fair Injury Analyst
class FairInjuryAnalyst(FairExpertBase):
    """Injury-focused expert with fair methodology (no structural advantages)"""

    def __init__(self):
        super().__init__(
            expert_id="fair_injury_analyst",
            name="Fair Injury Analyst",
            specializations=["injury_impact", "player_availability", "depth_analysis"]
        )

    def _define_analytical_lens(self) -> str:
        """Injury Analyst's unique methodology"""
        return "medical_impact_analysis"

    def _define_relevance_factors(self) -> Dict[str, float]:
        """Contexts where injury analysis becomes more relevant"""
        return {
            'injury_specialist': 0.6,  # 60% bonus in high-injury games
            'weather_specialist': 0.0,  # No weather bonus
            'market_specialist': 0.1   # Slight market bonus (injury news affects lines)
        }

    def _apply_analytical_lens(self, context: GameContext) -> Dict[str, Any]:
        """Interpret game data through injury impact lens"""

        decision_factors = []
        total_adjustment = 0
        reasoning_parts = []

        # Analyze each injury through medical expertise lens
        for team in ['home', 'away']:
            team_injuries = context.injuries.get(team, [])
            team_name = context.home_team if team == 'home' else context.away_team

            for injury in team_injuries:
                position = injury.get('position', 'UNKNOWN')
                severity = injury.get('severity', 'medium')
                prob_play = injury.get('probability_play', 0.5)

                # Medical impact analysis (METHODOLOGY)
                if position == 'QB':
                    impact = self._analyze_qb_injury_impact(injury, context)
                elif position in ['RB', 'WR', 'TE']:
                    impact = self._analyze_skill_position_impact(injury, context)
                elif position in ['DE', 'LB', 'CB', 'S']:
                    impact = self._analyze_defensive_impact(injury, context)
                else:
                    impact = self._analyze_general_impact(injury, context)

                # Convert medical analysis to decision factor
                if team == 'home':
                    decision_factors.append({
                        'factor': f"{position}_injury_impact",
                        'home_impact': -impact,  # Injury hurts home team
                        'away_impact': 0,
                        'reasoning': f"{team_name} {position} injury reduces performance"
                    })
                else:
                    decision_factors.append({
                        'factor': f"{position}_injury_impact",
                        'home_impact': 0,
                        'away_impact': -impact,  # Injury hurts away team
                        'reasoning': f"{team_name} {position} injury reduces performance"
                    })

                reasoning_parts.append(f"{team_name} {position} {severity} injury")

        return {
            'decision_factors': decision_factors,
            'total_adjustment': total_adjustment,
            'reasoning': f"Medical analysis: {', '.join(reasoning_parts) if reasoning_parts else 'No significant injuries'}"
        }

    def _analyze_qb_injury_impact(self, injury: Dict, context: GameContext) -> float:
        """Specialized QB injury analysis"""
        severity_map = {'minor': 2.0, 'medium': 4.0, 'major': 7.0, 'season_ending': 10.0}
        base_impact = severity_map.get(injury.get('severity', 'medium'), 4.0)
        prob_play = injury.get('probability_play', 0.5)

        # Medical expertise: QB injuries affect passing game significantly
        return base_impact * (1 - prob_play)

    def _analyze_skill_position_impact(self, injury: Dict, context: GameContext) -> float:
        """Skill position injury analysis"""
        severity_map = {'minor': 1.0, 'medium': 2.0, 'major': 3.5, 'season_ending': 5.0}
        return severity_map.get(injury.get('severity', 'medium'), 2.0)

    def _analyze_defensive_impact(self, injury: Dict, context: GameContext) -> float:
        """Defensive player injury analysis"""
        severity_map = {'minor': 0.8, 'medium': 1.5, 'major': 2.5, 'season_ending': 3.5}
        return severity_map.get(injury.get('severity', 'medium'), 1.5)

    def _analyze_general_impact(self, injury: Dict, context: GameContext) -> float:
        """General position injury analysis"""
        severity_map = {'minor': 0.5, 'medium': 1.0, 'major': 1.5, 'season_ending': 2.0}
        return severity_map.get(injury.get('severity', 'medium'), 1.0)

    def _analyze_performance_and_adapt(self, week_results: List[Dict], peer_insights: Dict = None) -> List[Dict]:
        """Injury Analyst's weekly learning strategy with cross-expert insights"""

        adaptations = []
        performance = self._calculate_weekly_performance(week_results)

        # Learn from prediction accuracy by injury type
        if performance['total_games'] >= 3:  # Need minimum data

            # If QB injury predictions were wrong, adjust QB impact weights
            qb_accuracy = performance['by_category'].get('qb_injury_impact', {}).get('accuracy', 0.5)
            if qb_accuracy < 0.4:  # Poor QB injury predictions
                adaptations.append({
                    'type': 'weight_adjustment',
                    'factor': 'qb_injury_weight',
                    'change': -0.1,  # Reduce QB injury weight
                    'reasoning': f"QB injury predictions only {qb_accuracy:.1%} accurate, reducing weight"
                })
            elif qb_accuracy > 0.7:  # Great QB injury predictions
                adaptations.append({
                    'type': 'weight_adjustment',
                    'factor': 'qb_injury_weight',
                    'change': 0.05,  # Increase QB injury weight
                    'reasoning': f"QB injury predictions {qb_accuracy:.1%} accurate, increasing weight"
                })

            # Learn from defensive injury predictions
            def_accuracy = performance['by_category'].get('key_defensive_player', {}).get('accuracy', 0.5)
            if def_accuracy < 0.4:
                adaptations.append({
                    'type': 'weight_adjustment',
                    'factor': 'defense_injury_weight',
                    'change': -0.05,
                    'reasoning': f"Defense injury predictions struggling at {def_accuracy:.1%}"
                })

        # Cross-expert learning: Learn from peer performance
        if peer_insights and peer_insights.get('my_relative_performance'):
            my_rank = peer_insights['my_relative_performance']['rank']
            total_experts = peer_insights['my_relative_performance']['total_experts']

            # If performing poorly compared to peers, become more conservative
            if my_rank > (total_experts * 0.7):  # Bottom 30%
                adaptations.append({
                    'type': 'methodology_tweak',
                    'parameter': 'injury_severity_threshold',
                    'change': 'more_conservative',
                    'reasoning': f"Ranked {my_rank}/{total_experts} among peers, becoming more conservative"
                })

            # Check if weather expert is dominating - maybe weather affects injury outcomes
            if 'category_leaders' in peer_insights:
                for category, leader_data in peer_insights['category_leaders'].items():
                    if 'Weather' in leader_data.get('expert', '') and leader_data.get('accuracy', 0) > 0.75:
                        adaptations.append({
                            'type': 'methodology_tweak',
                            'parameter': 'consider_weather_injury_interaction',
                            'change': 'increase_weather_factor',
                            'reasoning': f"Weather expert leading at {leader_data['accuracy']:.1%}, considering weather-injury interactions"
                        })

        return adaptations

# Example Implementation: Fair Sharp Bettor
class FairSharpBettor(FairExpertBase):
    """Market-focused expert with fair methodology"""

    def __init__(self):
        super().__init__(
            expert_id="fair_sharp_bettor",
            name="Fair Sharp Bettor",
            specializations=["line_movement", "sharp_action", "market_efficiency"]
        )

    def _define_analytical_lens(self) -> str:
        return "market_efficiency_analysis"

    def _define_relevance_factors(self) -> Dict[str, float]:
        return {
            'injury_specialist': 0.1,   # Slight injury bonus (affects lines)
            'weather_specialist': 0.1,  # Slight weather bonus (affects totals)
            'market_specialist': 0.6    # 60% bonus in volatile markets
        }

    def _apply_analytical_lens(self, context: GameContext) -> Dict[str, Any]:
        """Interpret game data through market efficiency lens"""

        decision_factors = []
        reasoning_parts = []

        # Line movement analysis
        if abs(context.line_movement) > 1:
            impact = min(5.0, abs(context.line_movement) * 2)
            if context.line_movement > 0:  # Line moved toward home
                decision_factors.append({
                    'factor': 'line_movement',
                    'home_impact': impact,
                    'away_impact': 0,
                    'reasoning': f"Line moved {context.line_movement} toward home team"
                })
            else:  # Line moved toward away
                decision_factors.append({
                    'factor': 'line_movement',
                    'home_impact': 0,
                    'away_impact': impact,
                    'reasoning': f"Line moved {abs(context.line_movement)} toward away team"
                })
            reasoning_parts.append(f"Line movement: {context.line_movement}")

        # Sharp action analysis
        if context.sharp_action:
            impact = 3.0
            if context.sharp_action == context.home_team:
                decision_factors.append({
                    'factor': 'sharp_action',
                    'home_impact': impact,
                    'away_impact': 0,
                    'reasoning': f"Sharp money on {context.sharp_action}"
                })
            else:
                decision_factors.append({
                    'factor': 'sharp_action',
                    'home_impact': 0,
                    'away_impact': impact,
                    'reasoning': f"Sharp money on {context.sharp_action}"
                })
            reasoning_parts.append(f"Sharp action: {context.sharp_action}")

        # Public fade opportunity
        if abs(context.public_percentage - 50) > 15:
            fade_impact = (abs(context.public_percentage - 50) - 15) / 10
            if context.public_percentage > 65:  # Fade the public (bet away)
                decision_factors.append({
                    'factor': 'public_fade',
                    'home_impact': 0,
                    'away_impact': fade_impact,
                    'reasoning': f"Fade public ({context.public_percentage}% on home)"
                })
            elif context.public_percentage < 35:  # Fade the public (bet home)
                decision_factors.append({
                    'factor': 'public_fade',
                    'home_impact': fade_impact,
                    'away_impact': 0,
                    'reasoning': f"Fade public ({context.public_percentage}% on home)"
                })
            reasoning_parts.append(f"Public: {context.public_percentage}%")

        return {
            'decision_factors': decision_factors,
            'total_adjustment': 0,
            'reasoning': f"Market analysis: {', '.join(reasoning_parts) if reasoning_parts else 'Stable market conditions'}"
        }

    def _analyze_performance_and_adapt(self, week_results: List[Dict], peer_insights: Dict = None) -> List[Dict]:
        """Sharp Bettor's weekly learning strategy with cross-expert insights"""

        adaptations = []
        performance = self._calculate_weekly_performance(week_results)

        if performance['total_games'] >= 3:  # Need minimum data

            # Learn from line movement success
            line_accuracy = performance['by_category'].get('line_movement', {}).get('accuracy', 0.5)
            if line_accuracy < 0.4:  # Line movement not predictive
                adaptations.append({
                    'type': 'weight_adjustment',
                    'factor': 'line_movement_weight',
                    'change': -0.1,
                    'reasoning': f"Line movement predictions only {line_accuracy:.1%} accurate, reducing reliance"
                })
            elif line_accuracy > 0.7:  # Line movement very predictive
                adaptations.append({
                    'type': 'weight_adjustment',
                    'factor': 'line_movement_weight',
                    'change': 0.1,
                    'reasoning': f"Line movement predictions {line_accuracy:.1%} accurate, increasing weight"
                })

            # Learn from public fade strategy
            fade_accuracy = performance['by_category'].get('public_fade', {}).get('accuracy', 0.5)
            if fade_accuracy < 0.4:  # Public fade not working
                adaptations.append({
                    'type': 'weight_adjustment',
                    'factor': 'public_fade_weight',
                    'change': -0.05,
                    'reasoning': f"Public fade strategy only {fade_accuracy:.1%} accurate"
                })

            # Sharp action learning
            sharp_accuracy = performance['by_category'].get('sharp_action', {}).get('accuracy', 0.5)
            if sharp_accuracy > 0.6:  # Sharp action is reliable
                adaptations.append({
                    'type': 'weight_adjustment',
                    'factor': 'sharp_action_weight',
                    'change': 0.05,
                    'reasoning': f"Sharp action signals {sharp_accuracy:.1%} accurate, trusting more"
                })

        # Cross-expert learning: Observe market efficiency patterns
        if peer_insights and peer_insights.get('category_leaders'):
            for category, leader_data in peer_insights['category_leaders'].items():
                expert_name = leader_data.get('expert', '')
                accuracy = leader_data.get('accuracy', 0)

                # If injury expert dominates, maybe injuries move lines more than expected
                if 'Injury' in expert_name and accuracy > 0.75:
                    adaptations.append({
                        'type': 'methodology_tweak',
                        'parameter': 'injury_line_correlation',
                        'change': 'increase_injury_sensitivity',
                        'reasoning': f"Injury expert leading at {accuracy:.1%}, increasing injury-line movement correlation"
                    })

                # If weather expert dominates, maybe weather affects betting patterns
                if 'Weather' in expert_name and accuracy > 0.75:
                    adaptations.append({
                        'type': 'methodology_tweak',
                        'parameter': 'weather_market_reaction',
                        'change': 'track_weather_line_moves',
                        'reasoning': f"Weather expert leading at {accuracy:.1%}, tracking weather-driven line movement"
                    })

            # Market timing: If performing poorly relative to peers, become more selective
            if peer_insights.get('my_relative_performance'):
                my_rank = peer_insights['my_relative_performance']['rank']
                total_experts = peer_insights['my_relative_performance']['total_experts']

                if my_rank > (total_experts * 0.6):  # Bottom 40%
                    adaptations.append({
                        'type': 'methodology_tweak',
                        'parameter': 'market_timing_sensitivity',
                        'change': 'increase_selectivity',
                        'reasoning': f"Ranked {my_rank}/{total_experts}, being more selective with market signals"
                    })

        return adaptations

def test_fair_expert_system():
    """Test the fair expert system with LAC @ LV game"""

    # Create game context (shared reality)
    context = GameContext(
        home_team='LV',
        away_team='LAC',
        spread=-1.0,
        total=43.5,
        weather={'temperature': 75, 'wind_speed': 5, 'conditions': 'Clear'},
        injuries={
            'home': [{'position': 'QB', 'severity': 'minor', 'probability_play': 0.8}],
            'away': [{'position': 'LB', 'severity': 'major', 'probability_play': 0.2}]
        },
        line_movement=-0.5,
        public_percentage=65,
        sharp_action='LV',
        game_time='10:00 PM ET'
    )

    # Calculate context scores
    context.calculate_context_scores()

    print("🧪 Testing Fair Expert Differentiation System")
    print("=" * 60)
    print(f"📊 Game Context Scores:")
    print(f"   Injury Severity: {context.injury_severity_score:.2f}")
    print(f"   Weather Impact: {context.weather_impact_score:.2f}")
    print(f"   Market Instability: {context.market_stability_score:.2f}")

    # Test Fair Injury Analyst
    injury_analyst = FairInjuryAnalyst()
    injury_prediction = injury_analyst.make_fair_prediction(context)

    print(f"\n🏥 {injury_analyst.name} (Medical Lens):")
    print(f"   🏆 Winner: {injury_prediction.winner} ({injury_prediction.win_probability:.1%})")
    print(f"   📊 ATS: {injury_prediction.point_spread_pick}")
    print(f"   📈 Total: {injury_prediction.total_pick}")
    print(f"   📋 Score: {injury_prediction.exact_score}")
    print(f"   🎯 Confidence: {injury_prediction.confidence:.1%}")
    print(f"   💭 Reasoning: {injury_prediction.reasoning}")

    # Test Fair Sharp Bettor
    sharp_bettor = FairSharpBettor()
    sharp_prediction = sharp_bettor.make_fair_prediction(context)

    print(f"\n💰 {sharp_bettor.name} (Market Lens):")
    print(f"   🏆 Winner: {sharp_prediction.winner} ({sharp_prediction.win_probability:.1%})")
    print(f"   📊 ATS: {sharp_prediction.point_spread_pick}")
    print(f"   📈 Total: {sharp_prediction.total_pick}")
    print(f"   📋 Score: {sharp_prediction.exact_score}")
    print(f"   🎯 Confidence: {sharp_prediction.confidence:.1%}")
    print(f"   💭 Reasoning: {sharp_prediction.reasoning}")

    print(f"\n✅ SUCCESS: Fair Expert System Features:")
    print(f"   🎯 No structural advantages - both use same base confidence")
    print(f"   🔍 Unique methodologies - medical vs market analysis")
    print(f"   📏 Dynamic relevance - context determines expertise value")
    print(f"   🔗 Zero contradictions - all predictions logically consistent")
    print(f"   ⚖️ Fair competition - performance tracked across all game types")

    # Test Weekly Learning System
    print(f"\n🧠 Testing Weekly Learning & Adaptation:")
    print("=" * 60)

    # Simulate weekly results for Injury Analyst
    mock_week_results = [
        {'correct': False, 'category_results': {'qb_injury_impact': False, 'key_defensive_player': True}},
        {'correct': True, 'category_results': {'qb_injury_impact': False, 'key_defensive_player': True}},
        {'correct': False, 'category_results': {'qb_injury_impact': False, 'key_defensive_player': False}},
        {'correct': True, 'category_results': {'qb_injury_impact': True, 'key_defensive_player': True}}
    ]

    # Expert learns from performance
    injury_adaptation = injury_analyst.weekly_adaptation(mock_week_results)

    print(f"🏥 Injury Analyst - Week 1 Learning:")
    print(f"   📊 Performance: {injury_adaptation['previous_performance']['accuracy']:.1%} accuracy")
    print(f"   🔧 Adaptations Made: {len(injury_adaptation['adaptations_made'])}")
    for adaptation in injury_adaptation['adaptations_made']:
        if adaptation.get('factor'):
            print(f"   • {adaptation['factor']}: {adaptation['old_weight']:.2f} → {adaptation['new_weight']:.2f}")
    for reasoning in injury_adaptation['reasoning']:
        print(f"   💭 {reasoning}")

    # Sharp Bettor learning
    sharp_week_results = [
        {'correct': True, 'category_results': {'line_movement': True, 'public_fade': False}},
        {'correct': True, 'category_results': {'line_movement': True, 'sharp_action': True}},
        {'correct': False, 'category_results': {'line_movement': False, 'public_fade': False}}
    ]

    sharp_adaptation = sharp_bettor.weekly_adaptation(sharp_week_results)

    print(f"\n💰 Sharp Bettor - Week 1 Learning:")
    print(f"   📊 Performance: {sharp_adaptation['previous_performance']['accuracy']:.1%} accuracy")
    print(f"   🔧 Adaptations Made: {len(sharp_adaptation['adaptations_made'])}")
    for adaptation in sharp_adaptation['adaptations_made']:
        if adaptation.get('factor'):
            print(f"   • {adaptation['factor']}: {adaptation['old_weight']:.2f} → {adaptation['new_weight']:.2f}")
    for reasoning in sharp_adaptation['reasoning']:
        print(f"   💭 {reasoning}")

    print(f"\n🎯 KEY INSIGHT: Expert Learning System")
    print(f"   📈 Each expert adapts their own weights based on performance")
    print(f"   🔄 No expert has permanent advantages - all can evolve")
    print(f"   🧠 Different learning strategies reflect expert personalities")
    print(f"   ✅ Only rule: Internal consistency (no contradictory predictions)")

    # Test Cross-Expert Learning (Performance Transparency)
    print(f"\n🤝 Testing Cross-Expert Learning & Performance Transparency:")
    print("=" * 60)

    # Simulate multi-week performance with different expert strengths
    performance_tracker.current_week = 4

    # Week 1: Injury analyst dominates
    performance_tracker.record_weekly_performance(1, "Fair Injury Analyst", {
        'accuracy': 0.85, 'total_games': 5, 'by_category': {'qb_injury_impact': {'accuracy': 0.9}}
    })
    performance_tracker.record_weekly_performance(1, "Fair Sharp Bettor", {
        'accuracy': 0.45, 'total_games': 5, 'by_category': {'line_movement': {'accuracy': 0.3}}
    })

    # Week 2: Market conditions favor sharp bettor
    performance_tracker.record_weekly_performance(2, "Fair Injury Analyst", {
        'accuracy': 0.40, 'total_games': 4, 'by_category': {'qb_injury_impact': {'accuracy': 0.5}}
    })
    performance_tracker.record_weekly_performance(2, "Fair Sharp Bettor", {
        'accuracy': 0.80, 'total_games': 4, 'by_category': {'line_movement': {'accuracy': 0.85}}
    })

    # Week 3: Both experts see peer insights and adapt
    performance_tracker.record_weekly_performance(3, "Fair Injury Analyst", {
        'accuracy': 0.65, 'total_games': 3, 'by_category': {'qb_injury_impact': {'accuracy': 0.7}}
    })
    performance_tracker.record_weekly_performance(3, "Fair Sharp Bettor", {
        'accuracy': 0.75, 'total_games': 3, 'by_category': {'line_movement': {'accuracy': 0.8}}
    })

    # Get peer insights for each expert
    injury_insights = performance_tracker.get_peer_performance_insights("Fair Injury Analyst")
    sharp_insights = performance_tracker.get_peer_performance_insights("Fair Sharp Bettor")

    print(f"📊 Injury Analyst sees peer performance:")
    if injury_insights['my_relative_performance']:
        rank = injury_insights['my_relative_performance']['rank']
        total = injury_insights['my_relative_performance']['total_experts']
        print(f"   • My ranking: {rank}/{total} experts")
        print(f"   • My accuracy: {injury_insights['my_relative_performance']['my_accuracy']:.1%}")
        print(f"   • Peer average: {injury_insights['my_relative_performance']['peer_average']:.1%}")

    print(f"\n💰 Sharp Bettor sees peer performance:")
    if sharp_insights['my_relative_performance']:
        rank = sharp_insights['my_relative_performance']['rank']
        total = sharp_insights['my_relative_performance']['total_experts']
        print(f"   • My ranking: {rank}/{total} experts")
        print(f"   • My accuracy: {sharp_insights['my_relative_performance']['my_accuracy']:.1%}")
        print(f"   • Peer average: {sharp_insights['my_relative_performance']['peer_average']:.1%}")

    # Show category leaders
    print(f"\n🏆 Category Leaders Across All Experts:")
    for category, leader_data in injury_insights.get('category_leaders', {}).items():
        print(f"   • {category}: {leader_data['expert']} ({leader_data['accuracy']:.1%})")

    # Test cross-expert adaptation
    cross_expert_week_results = [
        {'correct': True, 'category_results': {'qb_injury_impact': True}},
        {'correct': False, 'category_results': {'qb_injury_impact': False}},
        {'correct': True, 'category_results': {'key_defensive_player': True}}
    ]

    print(f"\n🔄 Cross-Expert Adaptation Example:")
    print(f"📋 Injury Analyst learns from peer insights...")

    cross_adaptation = injury_analyst.weekly_adaptation(cross_expert_week_results)
    print(f"   📊 Week 4 Performance: {cross_adaptation['previous_performance']['accuracy']:.1%}")
    print(f"   🔧 Cross-Expert Adaptations: {len([a for a in cross_adaptation['adaptations_made'] if 'peer' in str(a) or 'Weather' in str(a)])}")
    for reasoning in cross_adaptation['reasoning']:
        if 'Weather' in reasoning or 'ranked' in reasoning.lower():
            print(f"   💭 Cross-learning: {reasoning}")

    print(f"\n🎯 BREAKTHROUGH: Performance Transparency Benefits")
    print(f"   🤝 Experts learn from each other's track records (not weights)")
    print(f"   📈 Competitive pressure drives continuous improvement")
    print(f"   🧠 Meta-learning: 'Who's good at what in which contexts?'")
    print(f"   🔒 Unique methodologies preserved (no weight sharing)")
    print(f"   ⚖️ Fair competition with collaborative intelligence")

if __name__ == "__main__":
    test_fair_expert_system()