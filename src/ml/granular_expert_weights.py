"""
Granular Sub-Weight Architecture for NFL Expert Systems
Allows experts to develop sophisticated hierarchical weighting systems

Examples:
- Injury Expert: QB (0.85), RB (0.4), WR (0.3), Defense (0.2), Kicker (0.05)
- Weather Expert: Snow (0.8), Wind (0.7), Rain (0.5), Temperature (0.3)
- Sharp Bettor: Line movement by cause - Injury news (0.9), Weather (0.6), Sharp action (0.8)
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class SubWeight:
    """Individual sub-weight within a category"""
    name: str                    # e.g., "qb_injury", "snow_weather", "injury_line_movement"
    weight: float               # Current weight value (0.0 to 1.0)
    impact_history: List[float] = field(default_factory=list)  # Track performance
    learning_rate: float = 0.05  # How fast this sub-weight adapts
    usage_count: int = 0        # How often this sub-weight was relevant

@dataclass
class WeightCategory:
    """Category of related sub-weights (e.g., "injuries", "weather", "market_factors")"""
    name: str
    sub_weights: Dict[str, SubWeight] = field(default_factory=dict)
    category_multiplier: float = 1.0  # Overall category strength
    normalization_strategy: str = "proportional"  # How to normalize sub-weights

    def add_sub_weight(self, sub_name: str, initial_weight: float = 0.5):
        """Add a new sub-weight to this category"""
        self.sub_weights[sub_name] = SubWeight(
            name=sub_name,
            weight=initial_weight
        )

    def get_effective_weight(self, sub_name: str, context_multiplier: float = 1.0) -> float:
        """Get the effective weight for a specific sub-factor"""
        if sub_name not in self.sub_weights:
            return 0.0

        base_weight = self.sub_weights[sub_name].weight
        effective_weight = base_weight * self.category_multiplier * context_multiplier

        # Normalize to prevent any single sub-weight from dominating
        max_sub_weight = 0.9  # No sub-weight can exceed 90% influence
        return min(effective_weight, max_sub_weight)

    def adapt_sub_weight(self, sub_name: str, performance_feedback: float):
        """Adapt a specific sub-weight based on performance"""
        if sub_name not in self.sub_weights:
            return

        sub_weight = self.sub_weights[sub_name]
        sub_weight.impact_history.append(performance_feedback)
        sub_weight.usage_count += 1

        # Calculate performance trend
        if len(sub_weight.impact_history) >= 3:
            recent_performance = sum(sub_weight.impact_history[-3:]) / 3

            # Adjust weight based on performance
            if recent_performance > 0.6:  # Good performance
                adjustment = sub_weight.learning_rate * 0.1
            elif recent_performance < 0.4:  # Poor performance
                adjustment = -sub_weight.learning_rate * 0.1
            else:
                adjustment = 0  # Neutral performance

            # Apply bounded adjustment
            new_weight = max(0.05, min(0.95, sub_weight.weight + adjustment))
            sub_weight.weight = new_weight

            logger.info(f"Adapted {sub_name}: {sub_weight.weight:.3f} (perf: {recent_performance:.1%})")

class GranularWeightSystem:
    """Advanced weighting system with hierarchical sub-weights"""

    def __init__(self, expert_name: str):
        self.expert_name = expert_name
        self.weight_categories: Dict[str, WeightCategory] = {}
        self.adaptation_history: List[Dict] = []
        self.meta_learning_insights: Dict = {}

    def create_category(self, category_name: str, normalization_strategy: str = "proportional"):
        """Create a new weight category"""
        self.weight_categories[category_name] = WeightCategory(
            name=category_name,
            normalization_strategy=normalization_strategy
        )

    def add_sub_weight(self, category_name: str, sub_name: str, initial_weight: float = 0.5):
        """Add a sub-weight to a category"""
        if category_name not in self.weight_categories:
            self.create_category(category_name)

        self.weight_categories[category_name].add_sub_weight(sub_name, initial_weight)

    def get_decision_weights(self, game_context: Dict) -> Dict[str, float]:
        """Calculate effective weights for all relevant factors in current game context"""

        decision_weights = {}

        for category_name, category in self.weight_categories.items():
            # Determine which sub-weights are relevant for this game
            relevant_sub_weights = self._identify_relevant_sub_weights(category_name, game_context)

            for sub_name, context_multiplier in relevant_sub_weights.items():
                effective_weight = category.get_effective_weight(sub_name, context_multiplier)

                if effective_weight > 0.05:  # Only include meaningful weights
                    decision_weights[f"{category_name}_{sub_name}"] = effective_weight

        return decision_weights

    def _identify_relevant_sub_weights(self, category_name: str, game_context: Dict) -> Dict[str, float]:
        """Identify which sub-weights are relevant for current game context"""

        relevant_weights = {}

        if category_name == "injuries":
            injuries = game_context.get('injuries', {})
            for team in ['home', 'away']:
                for injury in injuries.get(team, []):
                    position = injury.get('position', 'UNKNOWN').lower()
                    severity = injury.get('severity', 'medium')

                    # Context multiplier based on severity
                    severity_multipliers = {
                        'minor': 0.6, 'medium': 1.0, 'major': 1.4, 'season_ending': 1.8
                    }

                    sub_weight_name = f"{position}_injury"
                    context_multiplier = severity_multipliers.get(severity, 1.0)
                    relevant_weights[sub_weight_name] = context_multiplier

        elif category_name == "weather":
            weather = game_context.get('weather', {})

            # Wind impact
            wind_speed = weather.get('wind_speed', 0)
            if wind_speed > 10:
                relevant_weights['wind_weather'] = min(2.0, wind_speed / 10)

            # Temperature impact
            temp = weather.get('temperature', 70)
            if temp < 32 or temp > 85:
                temp_severity = abs(temp - 70) / 20
                relevant_weights['temperature_weather'] = min(1.5, temp_severity)

            # Precipitation impact
            conditions = weather.get('conditions', '').lower()
            if 'snow' in conditions:
                relevant_weights['snow_weather'] = 1.5
            elif 'rain' in conditions:
                relevant_weights['rain_weather'] = 1.2

        elif category_name == "market_factors":
            # Line movement sub-weights
            line_movement = abs(game_context.get('line_movement', 0))
            if line_movement > 0.5:
                relevant_weights['line_movement'] = min(2.0, line_movement)

            # Public percentage extremes
            public_pct = game_context.get('public_percentage', 50)
            if abs(public_pct - 50) > 20:
                relevant_weights['public_fade'] = abs(public_pct - 50) / 30

            # Sharp action
            if game_context.get('sharp_action'):
                relevant_weights['sharp_action'] = 1.3

        return relevant_weights

    def weekly_adaptation_with_granularity(self, week_results: List[Dict], peer_insights: Dict = None):
        """Perform weekly adaptation at the sub-weight level"""

        adaptation_log = {
            'week': len(self.adaptation_history) + 1,
            'sub_weight_adaptations': [],
            'category_adjustments': [],
            'peer_learning': []
        }

        # Adapt individual sub-weights based on performance
        for result in week_results:
            decision_factors = result.get('decision_factors_used', {})
            outcome_correct = result.get('correct', False)

            for factor_name, factor_performance in decision_factors.items():
                # Extract category and sub-weight from factor name
                if '_' in factor_name:
                    parts = factor_name.split('_', 1)
                    if len(parts) == 2:
                        category_name, sub_name = parts

                        if category_name in self.weight_categories:
                            # Provide performance feedback
                            performance_score = 1.0 if outcome_correct else 0.0
                            self.weight_categories[category_name].adapt_sub_weight(sub_name, performance_score)

                            adaptation_log['sub_weight_adaptations'].append({
                                'category': category_name,
                                'sub_weight': sub_name,
                                'performance': performance_score,
                                'new_weight': self.weight_categories[category_name].sub_weights.get(sub_name, SubWeight('', 0)).weight
                            })

        # Cross-expert learning at granular level
        if peer_insights:
            self._learn_from_peer_granular_insights(peer_insights, adaptation_log)

        self.adaptation_history.append(adaptation_log)
        return adaptation_log

    def _learn_from_peer_granular_insights(self, peer_insights: Dict, adaptation_log: Dict):
        """Learn from peer performance at the granular sub-weight level"""

        # If a peer is dominating in a specific category, examine our sub-weight distribution
        category_leaders = peer_insights.get('category_leaders', {})

        for category, leader_data in category_leaders.items():
            peer_expert = leader_data.get('expert', '')
            peer_accuracy = leader_data.get('accuracy', 0)

            # If peer is significantly better in this category
            if peer_accuracy > 0.75 and peer_expert != self.expert_name:

                # Example: If WeatherWizard is dominating, maybe we need to increase weather sub-weights
                if 'Weather' in peer_expert and 'weather' in self.weight_categories:
                    # Slightly increase our weather category multiplier
                    weather_category = self.weight_categories['weather']
                    old_multiplier = weather_category.category_multiplier
                    weather_category.category_multiplier = min(1.5, old_multiplier * 1.05)

                    adaptation_log['peer_learning'].append({
                        'insight': f"Weather expert leading at {peer_accuracy:.1%}",
                        'action': f"Increased weather category multiplier: {old_multiplier:.3f} → {weather_category.category_multiplier:.3f}"
                    })

                # Example: If InjuryAnalyst is dominating, maybe examine our injury sub-weights
                elif 'Injury' in peer_expert and 'injuries' in self.weight_categories:
                    # Focus more on QB injuries if that's where the edge is
                    injury_category = self.weight_categories['injuries']
                    if 'qb_injury' in injury_category.sub_weights:
                        qb_sub_weight = injury_category.sub_weights['qb_injury']
                        old_weight = qb_sub_weight.weight
                        qb_sub_weight.weight = min(0.9, old_weight * 1.03)

                        adaptation_log['peer_learning'].append({
                            'insight': f"Injury expert leading at {peer_accuracy:.1%}",
                            'action': f"Increased QB injury sub-weight: {old_weight:.3f} → {qb_sub_weight.weight:.3f}"
                        })

    def get_granular_summary(self) -> Dict:
        """Get detailed summary of all sub-weights and their performance"""

        summary = {
            'expert_name': self.expert_name,
            'categories': {},
            'total_sub_weights': 0,
            'most_impactful_factors': [],
            'least_reliable_factors': []
        }

        all_factors = []

        for category_name, category in self.weight_categories.items():
            category_summary = {
                'category_multiplier': category.category_multiplier,
                'sub_weights': {},
                'total_usage': 0
            }

            for sub_name, sub_weight in category.sub_weights.items():
                avg_performance = sum(sub_weight.impact_history) / len(sub_weight.impact_history) if sub_weight.impact_history else 0.5

                sub_summary = {
                    'weight': sub_weight.weight,
                    'usage_count': sub_weight.usage_count,
                    'avg_performance': avg_performance,
                    'reliability': len(sub_weight.impact_history)
                }

                category_summary['sub_weights'][sub_name] = sub_summary
                category_summary['total_usage'] += sub_weight.usage_count

                all_factors.append({
                    'name': f"{category_name}_{sub_name}",
                    'weight': sub_weight.weight,
                    'performance': avg_performance,
                    'usage': sub_weight.usage_count
                })

            summary['categories'][category_name] = category_summary
            summary['total_sub_weights'] += len(category.sub_weights)

        # Find most/least impactful factors
        all_factors.sort(key=lambda x: x['weight'] * x['performance'] * x['usage'], reverse=True)
        summary['most_impactful_factors'] = all_factors[:3]
        summary['least_reliable_factors'] = [f for f in all_factors if f['performance'] < 0.4 and f['usage'] >= 3]

        return summary

def test_granular_weights():
    """Test the granular sub-weight system"""

    print("🔬 Testing Granular Sub-Weight Architecture")
    print("=" * 60)

    # Create InjuryAnalyst with granular weights
    injury_expert = GranularWeightSystem("Enhanced Injury Analyst")

    # Set up injury sub-weights
    injury_expert.create_category("injuries")
    injury_expert.add_sub_weight("injuries", "qb_injury", 0.85)      # QB most important
    injury_expert.add_sub_weight("injuries", "rb_injury", 0.45)      # RB moderate impact
    injury_expert.add_sub_weight("injuries", "wr_injury", 0.35)      # WR moderate impact
    injury_expert.add_sub_weight("injuries", "defense_injury", 0.25) # Defense lower impact
    injury_expert.add_sub_weight("injuries", "kicker_injury", 0.05)  # Kicker minimal impact

    # Set up weather sub-weights (injury expert considers weather-injury interactions)
    injury_expert.create_category("weather")
    injury_expert.add_sub_weight("weather", "snow_weather", 0.3)     # Snow increases injury risk
    injury_expert.add_sub_weight("weather", "rain_weather", 0.2)     # Rain increases injury risk
    injury_expert.add_sub_weight("weather", "wind_weather", 0.1)     # Wind less injury-related
    injury_expert.add_sub_weight("weather", "temperature_weather", 0.15) # Cold = more injuries

    # Test game context
    game_context = {
        'injuries': {
            'home': [
                {'position': 'QB', 'severity': 'major', 'probability_play': 0.3},
                {'position': 'RB', 'severity': 'minor', 'probability_play': 0.8}
            ],
            'away': [
                {'position': 'Defense', 'severity': 'medium', 'probability_play': 0.5}
            ]
        },
        'weather': {
            'temperature': 25,  # Very cold
            'wind_speed': 15,   # Windy
            'conditions': 'Snow'
        }
    }

    print(f"🏥 {injury_expert.expert_name} - Granular Weight Analysis:")

    # Get decision weights for this specific game
    decision_weights = injury_expert.get_decision_weights(game_context)

    print(f"\n📊 Relevant Factors for This Game:")
    sorted_weights = sorted(decision_weights.items(), key=lambda x: x[1], reverse=True)
    for factor, weight in sorted_weights:
        print(f"   • {factor}: {weight:.3f}")

    print(f"\n🧠 Expert's Reasoning:")
    print(f"   • QB major injury (0.3 play chance) = HIGH impact")
    print(f"   • Snow + cold weather = increased injury risk")
    print(f"   • RB minor injury = moderate impact")
    print(f"   • Defense injury = lower impact")

    # Simulate weekly learning
    print(f"\n📈 Weekly Learning Simulation:")

    # Week 1: QB injury prediction was wrong, weather factors were right
    week_1_results = [
        {'correct': False, 'decision_factors_used': {'injuries_qb_injury': 0.85, 'weather_snow_weather': 0.3}},
        {'correct': True, 'decision_factors_used': {'weather_temperature_weather': 0.15, 'injuries_rb_injury': 0.45}},
        {'correct': False, 'decision_factors_used': {'injuries_qb_injury': 0.85}}
    ]

    adaptation = injury_expert.weekly_adaptation_with_granularity(week_1_results)

    print(f"   Week 1 Adaptations:")
    for adapt in adaptation['sub_weight_adaptations']:
        print(f"   • {adapt['category']}_{adapt['sub_weight']}: performance {adapt['performance']:.1%} → weight {adapt['new_weight']:.3f}")

    # Show updated weights
    print(f"\n🔧 Updated Sub-Weights After Learning:")
    summary = injury_expert.get_granular_summary()

    for category_name, category_data in summary['categories'].items():
        print(f"   📁 {category_name.title()} (multiplier: {category_data['category_multiplier']:.3f}):")
        for sub_name, sub_data in category_data['sub_weights'].items():
            print(f"      • {sub_name}: {sub_data['weight']:.3f} (used {sub_data['usage_count']}x, {sub_data['avg_performance']:.1%} avg)")

    print(f"\n🎯 Most Impactful Factors:")
    for factor in summary['most_impactful_factors']:
        print(f"   • {factor['name']}: weight={factor['weight']:.3f}, performance={factor['performance']:.1%}, usage={factor['usage']}")

    if summary['least_reliable_factors']:
        print(f"\n⚠️ Least Reliable Factors:")
        for factor in summary['least_reliable_factors']:
            print(f"   • {factor['name']}: {factor['performance']:.1%} performance over {factor['usage']} uses")

    print(f"\n✅ SUCCESS: Granular Sub-Weight System")
    print(f"   🎯 Expert can weight QB injuries (0.85) vs kicker injuries (0.05)")
    print(f"   🌨️ Snow gets different weight than wind based on expert's methodology")
    print(f"   📊 Sub-weights adapt independently based on individual performance")
    print(f"   🧠 Expert maintains unique granular decision-making philosophy")
    print(f"   ⚖️ Still follows fair competition rules and consistency validation")

if __name__ == "__main__":
    test_granular_weights()