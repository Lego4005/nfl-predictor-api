#!/usr/bin/env python3
"""
Improved Vector Memory Design for NFL Expert Learning

This shows how vector memories should be structured to capture
rich factor-based learning from NFL game data.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import json

@dataclass
class FactorImpactMemory:
    """Memory about how specific factors affected game outcomes"""
    factor_type: str  # 'weather', 'rest', 'injury', 'betting_line', etc.
    factor_values: Dict[str, Any]  # Specific factor measurements
    team_context: Dict[str, Any]  # Team characteristics relevant to this factor
    impact_observed: Dict[str, float]  # Quantified impact on various metrics
    confidence: float  # How confident the expert is in this learning
    sample_size: int  # How many similar situations this is based on

@dataclass
class PatternRecognitionMemory:
    """Memory about recurring patterns across similar situations"""
    pattern_description: str  # Human-readable pattern description
    trigger_conditions: Dict[str, Any]  # When this pattern applies
    expected_outcomes: Dict[str, float]  # What typically happens
    exceptions: List[Dict[str, Any]]  # When the pattern doesn't hold
    strength: float  # How reliable this pattern is

@dataclass
class PredictionAccuracyMemory:
    """Memory about prediction accuracy in specific contexts"""
    context_factors: Dict[str, Any]  # The situation context
    prediction_made: Dict[str, float]  # What was predicted
    actual_outcome: Dict[str, float]  # What actually happened
    accuracy_metrics: Dict[str, float]  # Various accuracy measures
    contributing_factors: List[str]  # What factors influenced accuracy
    lessons_learned: str  # What the expert learned from this

def create_weather_impact_memory(game_data: Dict, prediction_data: Dict, outcome_data: Dict) -> str:
    """
    Create a properly structured weather impact memory

    Instead of: "Chiefs struggled in cold weather"
    Create: Detailed factor analysis with quantified relationships
    """

    # Extract relevant data
    weather = {
        'temperature': game_data.get('weather_temperature'),
        'wind_mph': game_data.get('weather_wind_mph'),
        'humidity': game_data.get('weather_humidity'),
        'description': game_data.get('weather_description')
    }

    home_team = game_data.get('home_team')
    away_team = game_data.get('away_team')

    # Team context (would come from team stats)
    team_context = {
        'home_passing_ypg': 285,  # Would be actual data
        'home_rushing_ypg': 120,
        'away_passing_ypg': 240,
        'away_rushing_ypg': 145,
        'home_dome_team': False,
        'away_dome_team': False
    }

    # Observed impacts
    impact_observed = {
        'passing_efficiency_drop': 0.25,  # 25% drop from normal
        'rushing_efficiency_change': 0.10,  # 10% increase
        'scoring_variance': 1.8,  # Higher variance in scoring
        'turnover_increase': 0.4  # 40% more turnovers than expected
    }

    # Create structured content for embedding
    content_parts = [
        f"Weather Impact Analysis: {home_team} vs {away_team}",
        f"Conditions: {weather['temperature']}°F, {weather['wind_mph']}mph wind, {weather['description']}",
        f"Team Context: {home_team} passing offense {team_context['home_passing_ypg']} ypg, {away_team} {team_context['away_passing_ypg']} ypg",
        f"Observed Impact: Passing efficiency dropped {impact_observed['passing_efficiency_drop']*100:.0f}%, rushing up {impact_observed['rushing_efficiency_change']*100:.0f}%",
        f"Key Learning: High-volume passing teams underperform significantly in {weather['wind_mph']}+ mph winds",
        f"Quantified Relationship: Every 5mph wind above 15mph reduces passing efficiency by ~8%"
    ]

    return " | ".join(content_parts)

def create_betting_line_memory(game_data: Dict, prediction_data: Dict, outcome_data: Dict) -> str:
    """Create memory about betting line accuracy and market efficiency"""

    spread_line = game_data.get('spread_line', 0)
    actual_margin = outcome_data.get('actual_margin', 0)
    predicted_margin = prediction_data.get('predicted_margin', 0)

    line_accuracy = abs(spread_line - actual_margin)
    expert_accuracy = abs(predicted_margin - actual_margin)

    content_parts = [
        f"Betting Line Analysis: {game_data.get('home_team')} vs {game_data.get('away_team')}",
        f"Market Line: {spread_line}, Expert Prediction: {predicted_margin}, Actual: {actual_margin}",
        f"Market Error: {line_accuracy:.1f} points, Expert Error: {expert_accuracy:.1f} points",
        f"Market Efficiency: {'High' if line_accuracy < 3 else 'Medium' if line_accuracy < 7 else 'Low'}",
        f"Expert Performance: {'Beat Market' if expert_accuracy < line_accuracy else 'Underperformed Market'}",
        f"Context Factors: Week {game_data.get('week')}, {game_data.get('weather_description', 'Normal conditions')}"
    ]

    return " | ".join(content_parts)

def create_rest_advantage_memory(game_data: Dict, prediction_data: Dict, outcome_data: Dict) -> str:
    """Create memory about rest day advantages"""

    home_rest = game_data.get('home_rest', 7)
    away_rest = game_data.get('away_rest', 7)
    rest_differential = home_rest - away_rest

    actual_margin = outcome_data.get('actual_margin', 0)
    expected_margin = prediction_data.get('predicted_margin', 0)

    # Calculate if rest advantage materialized
    rest_impact = 0
    if rest_differential > 0:
        # Home team had more rest
        rest_impact = actual_margin - expected_margin
    elif rest_differential < 0:
        # Away team had more rest
        rest_impact = expected_margin - actual_margin

    content_parts = [
        f"Rest Advantage Analysis: {game_data.get('home_team')} vs {game_data.get('away_team')}",
        f"Rest Days: Home {home_rest}, Away {away_rest}, Differential: {rest_differential}",
        f"Expected Impact: {abs(rest_differential) * 1.5:.1f} points for {'home' if rest_differential > 0 else 'away'} team",
        f"Observed Impact: {rest_impact:.1f} points {'materialized' if abs(rest_impact) > 1 else 'minimal'}",
        f"Rest Efficiency: {rest_impact / max(abs(rest_differential), 1):.2f} points per rest day advantage",
        f"Context: Week {game_data.get('week')}, {'Divisional' if game_data.get('div_game') else 'Non-divisional'} game"
    ]

    return " | ".join(content_parts)

def create_qb_impact_memory(game_data: Dict, prediction_data: Dict, outcome_data: Dict) -> str:
    """Create memory about quarterback impact on game outcomes"""

    home_qb = game_data.get('home_qb_name', 'Unknown')
    away_qb = game_data.get('away_qb_name', 'Unknown')

    # Would include QB stats, injury status, etc.
    content_parts = [
        f"QB Impact Analysis: {home_qb} ({game_data.get('home_team')}) vs {away_qb} ({game_data.get('away_team')})",
        f"Weather Context: {game_data.get('weather_temperature', 'N/A')}°F, {game_data.get('weather_wind_mph', 0)}mph wind",
        f"Performance vs Expectation: Home QB {'exceeded' if outcome_data.get('home_qb_performance', 0) > 0 else 'underperformed'} by {abs(outcome_data.get('home_qb_performance', 0)):.1f} points",
        f"Key Factors: {', '.join(outcome_data.get('qb_impact_factors', ['Standard conditions']))}",
        f"Learning: QB performance correlation with {game_data.get('weather_description', 'normal conditions')}"
    ]

    return " | ".join(content_parts)

# Example of improved metadata structure
def create_enhanced_metadata(game_data: Dict, prediction_data: Dict, outcome_data: Dict) -> Dict[str, Any]:
    """Create rich metadata for vector search and analysis"""

    return {
        # Game identifiers
        'game_id': game_data.get('game_id'),
        'season': game_data.get('season'),
        'week': game_data.get('week'),
        'home_team': game_data.get('home_team'),
        'away_team': game_data.get('away_team'),

        # Environmental factors
        'weather': {
            'temperature': game_data.get('weather_temperature'),
            'wind_mph': game_data.get('weather_wind_mph'),
            'humidity': game_data.get('weather_humidity'),
            'description': game_data.get('weather_description'),
            'impact_category': 'high' if game_data.get('weather_wind_mph', 0) > 15 else 'low'
        },

        # Situational factors
        'rest_differential': game_data.get('home_rest', 7) - game_data.get('away_rest', 7),
        'is_divisional': game_data.get('div_game', False),
        'is_primetime': game_data.get('weekday') in ['Thursday', 'Sunday Night', 'Monday'],

        # Betting context
        'market_data': {
            'spread': game_data.get('spread_line'),
            'total': game_data.get('total_line'),
            'home_ml': game_data.get('home_moneyline'),
            'away_ml': game_data.get('away_moneyline')
        },

        # Performance metrics
        'accuracy_metrics': {
            'spread_accuracy': outcome_data.get('spread_accuracy', 0),
            'total_accuracy': outcome_data.get('total_accuracy', 0),
            'margin_error': outcome_data.get('margin_error', 0)
        },

        # Factor impacts (quantified)
        'factor_impacts': {
            'weather_impact': outcome_data.get('weather_impact', 0),
            'rest_impact': outcome_data.get('rest_impact', 0),
            'qb_impact': outcome_data.get('qb_impact', 0),
            'coaching_impact': outcome_data.get('coaching_impact', 0)
        },

        # Learning classification
        'memory_category': prediction_data.get('memory_category', 'general'),
        'confidence_level': prediction_data.get('confidence', 0.5),
        'sample_size': prediction_data.get('sample_size', 1),

        # Expert-specific
        'expert_reasoning': prediction_data.get('reasoning_chain', []),
        'key_insights': prediction_data.get('key_insights', []),
        'pattern_matches': prediction_data.get('pattern_matches', [])
    }

if __name__ == "__main__":
    print("🧠 Improved Vector Memory Design for NFL Expert Learning")
    print("\nKey Improvements:")
    print("1. Factor-specific learning with quantified relationships")
    print("2. Rich metadata capturing all relevant context")
    print("3. Structured content that enables semantic similarity")
    print("4. Expert reasoning chains and confidence tracking")
    print("5. Pattern recognition and exception handling")

    # Example of improved memory content
    sample_game = {
        'game_id': '2024_12_KC_DEN',
        'home_team': 'KC', 'away_team': 'DEN',
        'weather_temperature': 25, 'weather_wind_mph': 20,
        'weather_description': 'Cold with strong winds',
        'week': 12, 'div_game': True
    }

    sample_prediction = {'predicted_margin': 7, 'confidence': 0.8}
    sample_outcome = {'actual_margin': 3, 'weather_impact': -4}

    improved_content = create_weather_impact_memory(sample_game, sample_prediction, sample_outcome)
    print(f"\nExample Improved Content:\n{improved_content}")

    improved_metadata = create_enhanced_metadata(sample_game, sample_prediction, sample_outcome)
    print(f"\nExample Improved Metadata:\n{json.dumps(improved_metadata, indent=2)}")
