"""
Personality-Driven Autonomous Expert System for NFL Predictions

This system creates experts based on decision-making personalities rather than
domain specializations, ensuring fair competition where all experts have equal
access to data but different interpretation styles.

Key Principles:
- Universal Data Access: All experts see the same weather, injuries, stats, market data
- Personality-Driven Processing: Different decision-making styles, not different data sources
- Fair Competition: No structural advantages based on specialization
- Autonomous Evolution: Each personality can evolve their algorithms while preserving core traits
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import sqlite3
from abc import ABC, abstractmethod
import math
import random
import asyncio
import time

logger = logging.getLogger(__name__)

@dataclass
class PersonalityTrait:
    """Individual personality dimension that affects decision making"""
    name: str                           # e.g., "risk_tolerance", "contrarian_tendency"
    value: float                        # 0.0 to 1.0 scale
    stability: float                    # How resistant to change (0.0 = highly adaptable, 1.0 = fixed)
    influence_weight: float             # How much this trait affects decisions (0.0 to 1.0)

@dataclass
class PersonalityProfile:
    """Complete personality profile for an expert"""
    traits: Dict[str, PersonalityTrait] = field(default_factory=dict)
    decision_style: str = "balanced"    # "analytical", "intuitive", "mixed"
    confidence_level: float = 0.5       # Base confidence in predictions
    learning_rate: float = 0.1          # How quickly personality adapts

@dataclass
class UniversalGameData:
    """All available data that every expert can access equally"""
    # Team and game basics
    home_team: str
    away_team: str
    game_time: str
    location: str

    # Weather conditions
    weather: Dict[str, Any] = field(default_factory=dict)

    # Injury reports
    injuries: Dict[str, List[Dict]] = field(default_factory=dict)

    # Team statistics
    team_stats: Dict[str, Dict] = field(default_factory=dict)

    # Market data
    line_movement: Dict[str, Any] = field(default_factory=dict)
    public_betting: Dict[str, Any] = field(default_factory=dict)

    # News and updates
    recent_news: List[Dict] = field(default_factory=list)

    # Historical matchups
    head_to_head: Dict[str, Any] = field(default_factory=dict)

    # Coaching data
    coaching_info: Dict[str, Any] = field(default_factory=dict)

class PersonalityDrivenExpert(ABC):
    """Base class for personality-driven autonomous experts"""

    def __init__(self, expert_id: str, name: str, personality_profile: PersonalityProfile,
                 memory_service=None):
        self.expert_id = expert_id
        self.name = name
        self.personality = personality_profile

        # Memory system with Supabase integration
        self.memory = ExpertMemoryDatabase(name)  # Local cache
        self.memory_service = memory_service  # Supabase persistent storage
        self.tools_cache = {}  # Cache for external data
        self.loaded_weights = None  # Weights loaded from database

        # Performance tracking
        self.weekly_performance = []
        self.decision_history = []

    @abstractmethod
    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Process universal data through this expert's personality lens"""
        pass

    def retrieve_relevant_memories(self, game_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for the current game context (sync wrapper)"""
        if not self.memory_service:
            return []

        try:
            import asyncio
            # Try to get existing event loop or create new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, return empty for now
                    # (proper async version should be used in async context)
                    logger.warning(f"{self.name}: Cannot retrieve memories in running event loop - use async version")
                    return []
                memories = loop.run_until_complete(
                    self.memory_service.retrieve_memories(self.expert_id, game_context, limit=5)
                )
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    memories = loop.run_until_complete(
                        self.memory_service.retrieve_memories(self.expert_id, game_context, limit=5)
                    )
                finally:
                    loop.close()

            logger.info(f"🧠 {self.name}: Retrieved {len(memories)} relevant memories")
            return memories
        except Exception as e:
            logger.warning(f"⚠️ {self.name}: Could not retrieve memories: {e}")
            return []

    def apply_memory_insights(self, prediction: Dict[str, Any], memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply memory insights to adjust prediction"""
        if not memories:
            return prediction

        adjusted_prediction = prediction.copy()

        # Analyze memory patterns for success rate
        total_memories = len(memories)
        successful_memories = 0
        similar_confidence_levels = []

        for memory in memories:
            try:
                # Check if this memory represents a successful prediction
                prediction_data = memory.get('prediction_data', {})
                if isinstance(prediction_data, str):
                    import json
                    prediction_data = json.loads(prediction_data)

                actual_outcome = memory.get('actual_outcome', {})
                if isinstance(actual_outcome, str):
                    import json
                    actual_outcome = json.loads(actual_outcome)

                # Check if prediction was correct
                if prediction_data.get('winner') == actual_outcome.get('winner'):
                    successful_memories += 1

                # Track confidence levels from similar situations
                similar_confidence_levels.append(prediction_data.get('confidence', 0.5))
            except Exception as e:
                logger.debug(f"Error parsing memory: {e}")
                continue

        success_rate = successful_memories / total_memories if total_memories > 0 else 0.5

        # Calculate confidence adjustment
        confidence_adjustment = self.calculate_memory_influenced_confidence(
            prediction.get('winner_confidence', 0.5),
            memories
        )

        # Apply adjustment
        adjusted_prediction['winner_confidence'] = max(0.1, min(0.95,
            prediction['winner_confidence'] + confidence_adjustment))

        # Add memory metadata
        adjusted_prediction['memory_enhanced'] = True
        adjusted_prediction['memories_consulted'] = total_memories
        adjusted_prediction['memory_success_rate'] = success_rate
        adjusted_prediction['confidence_adjustment'] = confidence_adjustment

        # Add learned principles
        learned_principles = []
        if success_rate > 0.7:
            learned_principles.append(f"High success rate ({success_rate:.0%}) in similar situations")
        elif success_rate < 0.3:
            learned_principles.append(f"Low success rate ({success_rate:.0%}) - exercising caution")

        adjusted_prediction['learned_principles'] = learned_principles

        logger.info(f"🎯 {self.name}: Applied memory insights - confidence adjusted by {confidence_adjustment:+.3f}")

        return adjusted_prediction

    def calculate_memory_influenced_confidence(self, base_confidence: float, memories: List[Dict[str, Any]]) -> float:
        """Calculate confidence adjustment based on memory patterns"""
        if not memories:
            return 0.0

        total_memories = len(memories)
        successful_predictions = 0
        high_confidence_successes = 0
        high_confidence_failures = 0

        for memory in memories:
            try:
                prediction_data = memory.get('prediction_data', {})
                if isinstance(prediction_data, str):
                    import json
                    prediction_data = json.loads(prediction_data)

                actual_outcome = memory.get('actual_outcome', {})
                if isinstance(actual_outcome, str):
                    import json
                    actual_outcome = json.loads(actual_outcome)

                was_successful = prediction_data.get('winner') == actual_outcome.get('winner')
                memory_confidence = prediction_data.get('confidence', 0.5)

                if was_successful:
                    successful_predictions += 1
                    if memory_confidence > 0.7:
                        high_confidence_successes += 1
                else:
                    if memory_confidence > 0.7:
                        high_confidence_failures += 1
            except Exception as e:
                logger.debug(f"Error analyzing memory: {e}")
                continue

        # Calculate success rate
        success_rate = successful_predictions / total_memories if total_memories > 0 else 0.5

        # Conservative adjustment based on historical performance
        adjustment = 0.0

        # Pattern 1: Overall success rate
        if success_rate > 0.7:
            adjustment += 0.05  # Boost confidence
        elif success_rate < 0.3:
            adjustment -= 0.05  # Reduce confidence

        # Pattern 2: High confidence track record
        if base_confidence > 0.7:
            if high_confidence_successes > high_confidence_failures:
                adjustment += 0.03  # Validated high confidence
            elif high_confidence_failures > high_confidence_successes:
                adjustment -= 0.03  # Overconfidence in past

        # Pattern 3: Consistency check
        if total_memories >= 5:
            recent_success = successful_predictions / total_memories
            if recent_success > 0.8:
                adjustment += 0.02  # Consistent success
            elif recent_success < 0.2:
                adjustment -= 0.02  # Consistent failure pattern

        # Limit total adjustment to maintain stability
        return max(-0.15, min(0.15, adjustment))

    def make_personality_driven_prediction(self, universal_data: UniversalGameData) -> Dict[str, Any]:
        """Make prediction based on personality-driven interpretation of universal data"""

        # Step 1: Retrieve relevant memories before prediction (if memory service available)
        memories = []
        if self.memory_service:
            game_context = {
                'home_team': universal_data.home_team,
                'away_team': universal_data.away_team,
                'weather': universal_data.weather,
                'injuries': universal_data.injuries,
                'line_movement': universal_data.line_movement
            }
            memories = self.retrieve_relevant_memories(game_context)

        # Step 2: Process all data through personality lens
        personality_weights = self.process_through_personality_lens(universal_data)

        # Step 3: Apply personality-specific decision making
        prediction_components = self._generate_personality_predictions(universal_data, personality_weights)

        # Step 4: Synthesize final outcome
        final_prediction = self._synthesize_personality_outcome(prediction_components)

        # Step 5: Apply memory insights to adjust prediction (if memories available)
        if memories:
            final_prediction = self.apply_memory_insights(final_prediction, memories)

        # Step 6: Record decision in memory
        self._record_personality_decision(universal_data, prediction_components, final_prediction)

        return final_prediction

    def _generate_personality_predictions(self, data: UniversalGameData, weights: Dict[str, float]) -> Dict[str, float]:
        """Generate predictions using personality-weighted data interpretation"""

        predictions = {}

        # Weather impact (everyone sees same weather, different interpretation)
        weather_impact = self._interpret_weather_through_personality(data.weather, weights)
        predictions['weather_factor'] = weather_impact

        # Injury impact (everyone sees same injuries, different interpretation)
        injury_impact = self._interpret_injuries_through_personality(data.injuries, weights)
        predictions['injury_factor'] = injury_impact

        # Market sentiment (everyone sees same lines, different interpretation)
        market_impact = self._interpret_market_through_personality(data.line_movement, weights)
        predictions['market_factor'] = market_impact

        # Team performance (everyone sees same stats, different interpretation)
        team_impact = self._interpret_team_stats_through_personality(data.team_stats, weights)
        predictions['team_factor'] = team_impact

        # Coaching impact (everyone sees same coaching data, different interpretation)
        coaching_impact = self._interpret_coaching_through_personality(data.coaching_info, weights)
        predictions['coaching_factor'] = coaching_impact

        # Final game outcome synthesis
        predictions['game_winner'] = self._synthesize_winner_prediction(predictions, weights)
        predictions['spread_prediction'] = self._synthesize_spread_prediction(predictions, weights)
        predictions['total_prediction'] = self._synthesize_total_prediction(predictions, weights)

        return predictions

    def _interpret_weather_through_personality(self, weather: Dict, weights: Dict[str, float]) -> float:
        """Interpret weather data through personality lens"""
        if not weather:
            return 0.5

        temp = weather.get('temperature', 70)
        wind = weather.get('wind_speed', 0)
        conditions = weather.get('conditions', 'Clear').lower()

        # Base weather impact
        base_impact = 0.0
        if temp < 40 or temp > 85:
            base_impact += 0.3
        if wind > 15:
            base_impact += 0.2
        if any(condition in conditions for condition in ['rain', 'snow']):
            base_impact += 0.4

        # Apply personality interpretation
        risk_tolerance = self.personality.traits.get('risk_tolerance', PersonalityTrait('risk_tolerance', 0.5, 0.5, 0.5)).value
        chaos_comfort = self.personality.traits.get('chaos_comfort', PersonalityTrait('chaos_comfort', 0.5, 0.5, 0.5)).value

        # Risk takers see weather as opportunity, conservatives see it as threat
        if risk_tolerance > 0.6:
            # Risk taker: "Weather creates chaos, chaos creates opportunity"
            personality_modifier = 1.2 if base_impact > 0.3 else 0.8
        else:
            # Conservative: "Weather adds uncertainty, avoid uncertainty"
            personality_modifier = 1.5 if base_impact > 0.3 else 0.9

        return min(1.0, base_impact * personality_modifier * chaos_comfort)

    def _interpret_injuries_through_personality(self, injuries: Dict, weights: Dict[str, float]) -> float:
        """Interpret injury data through personality lens"""
        if not injuries:
            return 0.5

        total_injury_impact = 0.0

        for team, team_injuries in injuries.items():
            for injury in team_injuries:
                # Handle both dict and string injury formats
                if isinstance(injury, str):
                    # Parse string format like "WR2-Doubtful"
                    if '-' in injury:
                        pos_info, severity = injury.split('-', 1)
                        position = pos_info[:2] if len(pos_info) >= 2 else 'UNKNOWN'
                        severity = severity.lower()
                    else:
                        position = 'UNKNOWN'
                        severity = 'medium'
                    probability_play = {'doubtful': 0.2, 'questionable': 0.5, 'probable': 0.8}.get(severity, 0.5)
                else:
                    # Parse dict format
                    position = injury.get('position', 'UNKNOWN')
                    severity = injury.get('severity', 'medium')
                    probability_play = injury.get('probability_play', 0.5)

                # Base impact calculation
                position_importance = {
                    'QB': 0.9, 'RB': 0.6, 'WR': 0.5, 'TE': 0.4, 'OL': 0.7,
                    'DE': 0.6, 'LB': 0.5, 'CB': 0.6, 'S': 0.5
                }.get(position, 0.4)

                severity_multiplier = {'minor': 0.3, 'medium': 0.6, 'major': 1.0}.get(severity, 0.6)
                availability_impact = 1.0 - probability_play

                base_impact = position_importance * severity_multiplier * availability_impact

                # Apply personality interpretation
                optimism = self.personality.traits.get('optimism', PersonalityTrait('optimism', 0.5, 0.5, 0.5)).value

                if optimism > 0.6:
                    # Optimist: "Players overcome adversity, next man up mentality"
                    personality_modifier = 0.7
                else:
                    # Pessimist: "Injuries have ripple effects, depth is exposed"
                    personality_modifier = 1.3

                total_injury_impact += base_impact * personality_modifier

        return min(1.0, total_injury_impact)

    def _interpret_market_through_personality(self, line_movement: Dict, weights: Dict[str, float]) -> float:
        """Interpret market data through personality lens"""
        if not line_movement:
            return 0.5

        opening_line = line_movement.get('opening_line', 0)
        current_line = line_movement.get('current_line', 0)
        public_percentage = line_movement.get('public_percentage', 50)

        line_move = abs(current_line - opening_line)
        public_heavy_side = public_percentage > 65 or public_percentage < 35

        # Apply personality interpretation
        contrarian_tendency = self.personality.traits.get('contrarian_tendency', PersonalityTrait('contrarian_tendency', 0.5, 0.5, 0.5)).value
        market_trust = self.personality.traits.get('market_trust', PersonalityTrait('market_trust', 0.5, 0.5, 0.5)).value

        if contrarian_tendency > 0.7:
            # Contrarian: "When everyone zigs, I zag"
            market_factor = 0.3 if public_heavy_side else 0.7
        elif market_trust > 0.7:
            # Market follower: "The market is usually right"
            market_factor = 0.8 if line_move > 1 else 0.5
        else:
            # Balanced approach
            market_factor = 0.5 + (line_move * 0.1)

        return min(1.0, market_factor)

    def _interpret_team_stats_through_personality(self, team_stats: Dict, weights: Dict[str, float]) -> float:
        """Interpret team statistics through personality lens"""
        if not team_stats:
            return 0.5

        # Base statistical analysis (same for everyone)
        home_stats = team_stats.get('home', {})
        away_stats = team_stats.get('away', {})

        home_strength = (
            home_stats.get('offensive_yards_per_game', 350) / 450 +
            (450 - home_stats.get('defensive_yards_allowed', 350)) / 450
        ) / 2

        away_strength = (
            away_stats.get('offensive_yards_per_game', 350) / 450 +
            (450 - away_stats.get('defensive_yards_allowed', 350)) / 450
        ) / 2

        stat_edge = abs(home_strength - away_strength)

        # Apply personality interpretation
        analytics_trust = self.personality.traits.get('analytics_trust', PersonalityTrait('analytics_trust', 0.5, 0.5, 0.5)).value
        recent_bias = self.personality.traits.get('recent_bias', PersonalityTrait('recent_bias', 0.5, 0.5, 0.5)).value

        if analytics_trust > 0.7:
            # Analytics lover: "Numbers don't lie"
            return min(1.0, stat_edge * 1.5)
        elif recent_bias > 0.7:
            # Recency bias: "What have you done for me lately?"
            # Would weight recent games more heavily
            return min(1.0, stat_edge * 1.2)
        else:
            return min(1.0, stat_edge)

    def _interpret_coaching_through_personality(self, coaching_info: Dict, weights: Dict[str, float]) -> float:
        """Interpret coaching data through personality lens"""
        if not coaching_info:
            return 0.5

        # Base coaching analysis
        home_coaching_quality = coaching_info.get('home_coaching_quality', 0.5)
        away_coaching_quality = coaching_info.get('away_coaching_quality', 0.5)

        coaching_edge = abs(home_coaching_quality - away_coaching_quality)

        # Apply personality interpretation
        authority_respect = self.personality.traits.get('authority_respect', PersonalityTrait('authority_respect', 0.5, 0.5, 0.5)).value

        if authority_respect > 0.7:
            # "Coaching matters tremendously"
            return min(1.0, coaching_edge * 1.4)
        else:
            # "Players play the game, not coaches"
            return min(1.0, coaching_edge * 0.6)

    def _synthesize_winner_prediction(self, predictions: Dict[str, float], weights: Dict[str, float]) -> float:
        """Synthesize winner prediction based on personality"""

        # Weighted combination based on personality
        confidence_boost = self.personality.traits.get('confidence_level', PersonalityTrait('confidence_level', 0.5, 0.5, 0.5)).value

        base_prediction = (
            predictions.get('weather_factor', 0.5) * 0.15 +
            predictions.get('injury_factor', 0.5) * 0.25 +
            predictions.get('market_factor', 0.5) * 0.20 +
            predictions.get('team_factor', 0.5) * 0.30 +
            predictions.get('coaching_factor', 0.5) * 0.10
        )

        # Apply confidence adjustment
        if confidence_boost > 0.6:
            # Overconfident: Push predictions toward extremes
            base_prediction = 0.5 + (base_prediction - 0.5) * 1.3
        elif confidence_boost < 0.4:
            # Underconfident: Pull predictions toward center
            base_prediction = 0.5 + (base_prediction - 0.5) * 0.7

        return max(0.1, min(0.9, base_prediction))

    def _synthesize_spread_prediction(self, predictions: Dict[str, float], weights: Dict[str, float]) -> float:
        """Synthesize spread prediction based on personality"""

        winner_confidence = predictions.get('game_winner', 0.5)

        # Convert winner confidence to spread prediction
        # 0.5 = pick'em, 0.7 = -3, 0.8 = -7, 0.9 = -14
        if winner_confidence > 0.5:
            spread = -((winner_confidence - 0.5) * 28)  # Max spread of -14
        else:
            spread = ((0.5 - winner_confidence) * 28)   # Max spread of +14

        return spread

    def _synthesize_total_prediction(self, predictions: Dict[str, float], weights: Dict[str, float]) -> float:
        """Synthesize total points prediction based on personality"""

        # Base total around 45 points
        base_total = 45.0

        # Weather reduces scoring
        weather_impact = predictions.get('weather_factor', 0.5)
        weather_adjustment = (weather_impact - 0.5) * -10  # Bad weather = lower total

        # Injuries can reduce scoring
        injury_impact = predictions.get('injury_factor', 0.5)
        injury_adjustment = (injury_impact - 0.5) * -8

        # Team strength affects scoring
        team_impact = predictions.get('team_factor', 0.5)
        team_adjustment = (team_impact - 0.5) * 12  # Better teams = higher scoring

        total_prediction = base_total + weather_adjustment + injury_adjustment + team_adjustment

        return max(30.0, min(65.0, total_prediction))

    def _synthesize_personality_outcome(self, predictions: Dict[str, float]) -> Dict[str, Any]:
        """Create final prediction outcome"""

        winner_pred = predictions.get('game_winner', 0.5)
        spread_pred = predictions.get('spread_prediction', 0.0)
        total_pred = predictions.get('total_prediction', 45.0)

        return {
            'expert_name': self.name,
            'personality_profile': {trait: t.value for trait, t in self.personality.traits.items()},
            'winner_prediction': 'home' if winner_pred > 0.5 else 'away',
            'winner_confidence': abs(winner_pred - 0.5) * 2,  # 0-1 scale
            'spread_prediction': round(spread_pred, 1),
            'total_prediction': round(total_pred, 1),
            'key_factors': self._identify_key_personality_factors(predictions),
            'reasoning': self._generate_personality_reasoning(predictions)
        }

    def _identify_key_personality_factors(self, predictions: Dict[str, float]) -> List[str]:
        """Identify which factors this personality weighted most heavily"""

        factors = []

        # Find dominant personality traits
        dominant_traits = sorted(
            self.personality.traits.items(),
            key=lambda x: x[1].influence_weight,
            reverse=True
        )[:3]

        for trait_name, trait in dominant_traits:
            if trait.value > 0.6:
                factors.append(f"High {trait_name.replace('_', ' ')}")
            elif trait.value < 0.4:
                factors.append(f"Low {trait_name.replace('_', ' ')}")

        return factors

    def _generate_personality_reasoning(self, predictions: Dict[str, float]) -> str:
        """Generate reasoning based on personality"""

        reasoning_parts = []

        # Risk tolerance reasoning
        risk_tolerance = self.personality.traits.get('risk_tolerance', PersonalityTrait('risk_tolerance', 0.5, 0.5, 0.5)).value
        if risk_tolerance > 0.7:
            reasoning_parts.append("High-risk approach: Embracing uncertainty and chaos as opportunity")
        elif risk_tolerance < 0.3:
            reasoning_parts.append("Conservative approach: Avoiding uncertainty and seeking safe plays")

        # Contrarian reasoning
        contrarian = self.personality.traits.get('contrarian_tendency', PersonalityTrait('contrarian_tendency', 0.5, 0.5, 0.5)).value
        if contrarian > 0.7:
            reasoning_parts.append("Contrarian stance: Fading public opinion and popular narratives")
        elif contrarian < 0.3:
            reasoning_parts.append("Consensus approach: Following market wisdom and popular opinion")

        return "; ".join(reasoning_parts) if reasoning_parts else "Balanced analytical approach"

    def _record_personality_decision(self, data: UniversalGameData, predictions: Dict[str, float], final: Dict[str, Any]):
        """Record decision for personality evolution tracking"""

        decision_record = {
            'timestamp': datetime.now().isoformat(),
            'game': f"{data.away_team}@{data.home_team}",
            'personality_state': {trait: t.value for trait, t in self.personality.traits.items()},
            'prediction_components': predictions,
            'final_prediction': final,
            'key_personality_factors': final.get('key_factors', [])
        }

        self.decision_history.append(decision_record)

    def evolve_personality(self, results: List[Dict]):
        """Evolve personality based on performance feedback"""

        # Calculate recent performance
        recent_accuracy = sum(r.get('correct', False) for r in results[-5:]) / min(5, len(results))

        # Evolve traits based on performance
        for trait_name, trait in self.personality.traits.items():
            if trait.stability < 0.8:  # Only evolve non-stable traits
                if recent_accuracy < 0.4:  # Poor performance
                    # Adjust trait toward opposite direction
                    adjustment = (0.5 - trait.value) * self.personality.learning_rate
                    trait.value = max(0.0, min(1.0, trait.value + adjustment))
                elif recent_accuracy > 0.7:  # Good performance
                    # Reinforce current trait direction
                    if trait.value > 0.5:
                        trait.value = min(1.0, trait.value + 0.05)
                    else:
                        trait.value = max(0.0, trait.value - 0.05)

        logger.info(f"{self.name}: Personality evolution completed - {recent_accuracy:.1%} accuracy")


class ExpertMemoryDatabase:
    """Personal historical database for each expert (reused from original)"""

    def __init__(self, expert_name: str):
        self.expert_name = expert_name
        self.db_path = f"memory/{expert_name.lower().replace(' ', '_')}_memory.db"
        self._initialize_database()

    def _initialize_database(self):
        """Create expert's personal database"""
        import os
        os.makedirs("memory", exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Prediction history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY,
                game_id TEXT,
                prediction_date TEXT,
                personality_state TEXT,
                prediction_data TEXT,
                actual_outcome TEXT,
                was_correct BOOLEAN
            )
        ''')

        conn.commit()
        conn.close()


# Concrete Personality Implementations

class ConservativeAnalyzer(PersonalityDrivenExpert):
    """The Conservative Analyzer: Risk-averse, analytical, prefers proven patterns
    
    Now powered by LLM reasoning instead of deterministic calculations.
    """

    def __init__(self, memory_service=None, llm_service=None):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.2, 0.8, 0.9),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.9, 0.7, 0.8),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.3, 0.6, 0.6),
                'recent_bias': PersonalityTrait('recent_bias', 0.2, 0.5, 0.7),
                'confidence_level': PersonalityTrait('confidence_level', 0.4, 0.8, 0.7),
                'optimism': PersonalityTrait('optimism', 0.3, 0.6, 0.6),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.1, 0.9, 0.8),
                'market_trust': PersonalityTrait('market_trust', 0.8, 0.7, 0.7),
                'authority_respect': PersonalityTrait('authority_respect', 0.8, 0.8, 0.6)
            },
            decision_style="analytical",
            confidence_level=0.4,
            learning_rate=0.05
        )

        super().__init__(
            expert_id="conservative_analyzer",
            name="The Analyst",
            personality_profile=personality,
            memory_service=memory_service
        )
        
        # LLM integration for AI reasoning
        self.llm_service = llm_service
        self.use_llm_reasoning = llm_service is not None
        
    async def make_llm_powered_prediction(self, universal_data) -> Dict[str, Any]:
        """Make LLM-powered prediction with conversational reasoning"""
        if not self.llm_service:
            logger.warning(f"{self.name}: No LLM service available, falling back to deterministic prediction")
            return self.make_personality_driven_prediction(universal_data)
            
        start_time = time.perf_counter()
        
        try:
            # Step 1: Retrieve relevant episodic memories
            logger.info(f"{self.name}: Retrieving relevant memories for LLM prediction")
            game_context = {
                'home_team': universal_data.home_team,
                'away_team': universal_data.away_team,
                'weather': universal_data.weather,
                'injuries': universal_data.injuries,
                'line_movement': universal_data.line_movement
            }
            
            memories = []
            if self.memory_service:
                try:
                    memories = await self.memory_service.retrieve_memories(
                        self.expert_id, game_context, limit=5
                    )
                    logger.info(f"{self.name}: Retrieved {len(memories)} relevant memories")
                except Exception as e:
                    logger.warning(f"{self.name}: Error retrieving memories: {e}")
                    memories = []
            
            # Step 2: Build expert personality description
            personality_description = self._build_personality_description()
            
            # Step 3: Build prediction prompt using templates
            from ..prompts.nfl_prediction_prompts import build_prediction_prompt
            system_message, user_message = build_prediction_prompt(
                expert_personality=personality_description,
                game_data=universal_data,
                episodic_memories=memories
            )
            
            logger.info(f"{self.name}: Built prediction prompt with {len(memories)} memories")
            logger.debug(f"{self.name}: System message length: {len(system_message)} chars")
            logger.debug(f"{self.name}: User message length: {len(user_message)} chars")
            
            # Step 4: Call LLM for prediction generation
            logger.info(f"{self.name}: Making LLM call for prediction generation")
            llm_start = time.perf_counter()
            
            llm_response = await self.llm_service.generate_completion(
                system_message=system_message,
                user_message=user_message,
                temperature=0.7,
                max_tokens=-1,
                model="openai/gpt-oss-20b"
            )
            
            llm_duration = time.perf_counter() - llm_start
            logger.info(f"{self.name}: LLM call completed in {llm_duration:.2f}s")
            logger.info(f"{self.name}: Response length: {len(llm_response.content)} chars, tokens: {llm_response.total_tokens}")
            
            # Step 5: Parse JSON response
            try:
                parsed_predictions = json.loads(llm_response.content)
                logger.info(f"{self.name}: Successfully parsed LLM JSON response")
                logger.debug(f"{self.name}: Parsed predictions: {json.dumps(parsed_predictions, indent=2)}")
            except json.JSONDecodeError as e:
                logger.error(f"{self.name}: Failed to parse LLM JSON response: {e}")
                logger.error(f"{self.name}: Raw response: {llm_response.content[:500]}...")
                # Fallback to deterministic prediction
                return self.make_personality_driven_prediction(universal_data)
            
            # Step 6: Convert to structured prediction format
            structured_prediction = self._convert_llm_to_structured_prediction(parsed_predictions, universal_data)
            
            # Step 7: Store complete reasoning chain in database
            await self._store_reasoning_chain(
                universal_data, 
                parsed_predictions, 
                structured_prediction,
                llm_response,
                memories
            )
            
            total_duration = time.perf_counter() - start_time
            logger.info(f"{self.name}: Complete LLM prediction pipeline finished in {total_duration:.2f}s")
            
            return structured_prediction
            
        except Exception as e:
            logger.error(f"{self.name}: Error in LLM prediction pipeline: {e}")
            logger.exception("Full exception details:")
            # Fallback to deterministic prediction
            return self.make_personality_driven_prediction(universal_data)
    
    def make_personality_driven_prediction(self, universal_data) -> Dict[str, Any]:
        """Enhanced to use LLM when available, fallback to deterministic"""
        if self.use_llm_reasoning:
            # For sync calls, we need to handle async properly
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, log warning and use deterministic
                    logger.warning(f"{self.name}: Event loop running, using deterministic prediction. Use async version for LLM.")
                    return super().make_personality_driven_prediction(universal_data)
                else:
                    return loop.run_until_complete(self.make_llm_powered_prediction(universal_data))
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.make_llm_powered_prediction(universal_data))
                finally:
                    loop.close()
        else:
            # Use original deterministic prediction
            return super().make_personality_driven_prediction(universal_data)
            
    def _build_personality_description(self) -> str:
        """Build comprehensive personality description for LLM prompt"""
        return f"""You are The Conservative Analyzer, a risk-averse NFL prediction expert who values:

**Core Personality Traits:**
- Risk Tolerance: Very Low (20%) - You avoid uncertainty and prefer safe, proven approaches
- Analytics Trust: Very High (90%) - You heavily weight statistical data and historical patterns  
- Contrarian Tendency: Low (30%) - You generally follow consensus and established wisdom
- Recent Bias: Very Low (20%) - You prefer season-long trends over recent game results
- Confidence Level: Moderate-Low (40%) - You express measured confidence, avoiding overconfidence
- Optimism: Low (30%) - You tend toward pessimistic assessments and conservative projections
- Chaos Comfort: Very Low (10%) - You strongly prefer predictable, stable conditions
- Market Trust: High (80%) - You respect betting market consensus as collective wisdom
- Authority Respect: High (80%) - You value expert opinion and established coaching/management

**Decision-Making Philosophy:**
"I believe in proven patterns over speculation. My approach emphasizes historical data, established trends, and conservative risk management. I'm skeptical of flashy narratives and prefer the safety of consensus wisdom. When uncertainty exists, I default to the historically reliable choice rather than chasing upside potential."

**Typical Reasoning Patterns:**
- "Let me look at what the data has consistently shown over multiple seasons..."
- "I'm wary of overreacting to recent results when season-long patterns suggest..."
- "The market consensus typically reflects smart money, so I need strong evidence to go against it..."
- "Weather and chaos factors make me nervous - I'll weight them heavily as negative factors..."
- "My experience has taught me that flashy offensive performances often regress to the mean..."

You think through problems methodically, referencing your past experiences, and explain your reasoning with measured confidence while acknowledging uncertainties."""
    
    def _convert_llm_to_structured_prediction(self, llm_predictions: Dict, universal_data) -> Dict[str, Any]:
        """Convert LLM JSON response to structured prediction format"""
        try:
            # Extract core predictions from LLM response
            predictions_list = llm_predictions.get('predictions', [])
            
            # Initialize structured prediction
            structured = {
                'expert_name': self.name,
                'expert_id': self.expert_id,
                'llm_powered': True,
                'reasoning_discussion': llm_predictions.get('reasoning_discussion', ''),
                'overall_analysis': llm_predictions.get('overall_analysis', ''),
                'memories_applied': llm_predictions.get('memories_applied', []),
                'prediction_relationships': llm_predictions.get('prediction_relationships', ''),
                'all_predictions': {},
                'confidence_scores': {}
            }
            
            # Process each prediction
            for pred in predictions_list:
                pred_type = pred.get('prediction_type', '')
                pred_value = pred.get('predicted_value', '')
                confidence = pred.get('confidence', 50)
                reasoning = pred.get('reasoning', '')
                
                structured['all_predictions'][pred_type] = pred_value
                structured['confidence_scores'][pred_type] = confidence
                
                # Map to legacy format for compatibility
                if pred_type == 'game_winner_spread':
                    if 'home' in str(pred_value).lower():
                        structured['winner_prediction'] = 'home'
                    else:
                        structured['winner_prediction'] = 'away'
                    structured['winner_confidence'] = confidence / 100.0
                elif pred_type == 'total_points':
                    try:
                        structured['total_prediction'] = float(pred_value)
                    except (ValueError, TypeError):
                        structured['total_prediction'] = 45.0
                elif pred_type == 'point_spread':
                    try:
                        structured['spread_prediction'] = float(pred_value)
                    except (ValueError, TypeError):
                        structured['spread_prediction'] = 0.0
            
            # Set defaults if not found
            if 'winner_prediction' not in structured:
                structured['winner_prediction'] = 'home'
                structured['winner_confidence'] = 0.5
            if 'total_prediction' not in structured:
                structured['total_prediction'] = 45.0
            if 'spread_prediction' not in structured:
                structured['spread_prediction'] = 0.0
                
            # Add personality profile for compatibility
            structured['personality_profile'] = {
                trait_name: trait.value for trait_name, trait in self.personality.traits.items()
            }
            
            return structured
            
        except Exception as e:
            logger.error(f"{self.name}: Error converting LLM predictions: {e}")
            # Return minimal structured prediction
            return {
                'expert_name': self.name,
                'expert_id': self.expert_id,
                'llm_powered': True,
                'winner_prediction': 'home',
                'winner_confidence': 0.5,
                'total_prediction': 45.0,
                'spread_prediction': 0.0,
                'reasoning_discussion': llm_predictions.get('reasoning_discussion', 'Error in prediction processing'),
                'error': str(e)
            }
    
    async def _store_reasoning_chain(self, universal_data, llm_predictions: Dict, 
                                   structured_prediction: Dict, llm_response, memories: List):
        """Store complete reasoning chain in database"""
        try:
            if not self.memory_service:
                return
                
            reasoning_data = {
                'expert_id': self.expert_id,
                'game_context': {
                    'home_team': universal_data.home_team,
                    'away_team': universal_data.away_team,
                    'game_date': getattr(universal_data, 'game_date', None),
                    'week': getattr(universal_data, 'week', None),
                    'season': getattr(universal_data, 'season', None)
                },
                'llm_request': {
                    'model': llm_response.model,
                    'total_tokens': llm_response.total_tokens,
                    'prompt_tokens': llm_response.prompt_tokens,
                    'completion_tokens': llm_response.completion_tokens
                },
                'raw_llm_response': llm_response.content,
                'parsed_predictions': llm_predictions,
                'structured_prediction': structured_prediction,
                'memories_used': len(memories),
                'reasoning_discussion': llm_predictions.get('reasoning_discussion', ''),
                'prediction_relationships': llm_predictions.get('prediction_relationships', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in expert_reasoning_chains table
            await self.memory_service.store_reasoning_chain(reasoning_data)
            logger.info(f"{self.name}: Stored complete reasoning chain in database")
            
        except Exception as e:
            logger.error(f"{self.name}: Error storing reasoning chain: {e}")
    
    async def process_game_outcome(self, original_prediction: Dict, actual_outcome: Dict):
        """Process game outcome for belief revision and learning"""
        if not self.llm_service or not self.memory_service:
            logger.warning(f"{self.name}: Cannot process game outcome - missing LLM or memory service")
            return
            
        start_time = time.perf_counter()
        
        try:
            logger.info(f"{self.name}: Starting belief revision process")
            
            # Build belief revision prompt
            from ..prompts.nfl_prediction_prompts import build_belief_revision_prompt
            personality_description = self._build_personality_description()
            
            system_message, user_message = build_belief_revision_prompt(
                prediction_data=original_prediction,
                actual_outcome=actual_outcome,
                expert_personality=personality_description
            )
            
            logger.info(f"{self.name}: Built belief revision prompt")
            
            # Call LLM for belief revision
            llm_start = time.perf_counter()
            belief_response = await self.llm_service.generate_completion(
                system_message=system_message,
                user_message=user_message,
                temperature=0.6,
                max_tokens=1000,
                model="openai/gpt-oss-20b"
            )
            
            llm_duration = time.perf_counter() - llm_start
            logger.info(f"{self.name}: Belief revision LLM call completed in {llm_duration:.2f}s")
            
            # Parse belief revision response
            try:
                belief_analysis = json.loads(belief_response.content)
                logger.info(f"{self.name}: Successfully parsed belief revision response")
            except json.JSONDecodeError as e:
                logger.warning(f"{self.name}: Failed to parse belief revision JSON: {e}")
                belief_analysis = {
                    'reflection_discussion': belief_response.content,
                    'lessons_learned': [],
                    'belief_updates': [],
                    'performance_assessment': 'Unable to parse structured response'
                }
            
            # Store episodic memory
            await self._store_episodic_memory(
                original_prediction, actual_outcome, belief_analysis, belief_response
            )
            
            # Update personality traits based on learning (if applicable)
            await self._update_personality_from_learning(belief_analysis)
            
            total_duration = time.perf_counter() - start_time
            logger.info(f"{self.name}: Complete belief revision process finished in {total_duration:.2f}s")
            
            return belief_analysis
            
        except Exception as e:
            logger.error(f"{self.name}: Error in belief revision process: {e}")
            logger.exception("Full exception details:")
            return None
    
    async def _store_episodic_memory(self, prediction: Dict, outcome: Dict, belief_analysis: Dict, llm_response):
        """Store episodic memory in Supabase database"""
        try:
            if not self.memory_service:
                return
                
            memory_data = {
                'expert_id': self.expert_id,
                'game_context': {
                    'teams': f"{prediction.get('away_team', 'Unknown')} @ {prediction.get('home_team', 'Unknown')}",
                    'prediction_winner': prediction.get('winner_prediction', 'unknown'),
                    'actual_winner': outcome.get('winner', 'unknown')
                },
                'prediction_summary': json.dumps({
                    'winner': prediction.get('winner_prediction'),
                    'confidence': prediction.get('winner_confidence'),
                    'spread': prediction.get('spread_prediction'),
                    'total': prediction.get('total_prediction'),
                    'reasoning': prediction.get('reasoning_discussion', '')[:200]
                }),
                'actual_outcome': json.dumps(outcome),
                'was_correct': prediction.get('winner_prediction') == outcome.get('winner'),
                'reasoning_chain': json.dumps({
                    'original_reasoning': prediction.get('reasoning_discussion', ''),
                    'belief_revision': belief_analysis.get('reflection_discussion', ''),
                    'lessons_learned': belief_analysis.get('lessons_learned', [])
                }),
                'post_game_insights': belief_analysis.get('reflection_discussion', ''),
                'lessons_extracted': json.dumps(belief_analysis.get('lessons_learned', [])),
                'causal_analysis': belief_analysis.get('causal_analysis', ''),
                'pattern_insights': json.dumps(belief_analysis.get('pattern_insights', [])),
                'memory_type': 'prediction_outcome',
                'timestamp': datetime.now().isoformat()
            }
            
            await self.memory_service.store_episodic_memory(memory_data)
            logger.info(f"{self.name}: Stored episodic memory in Supabase")
            
        except Exception as e:
            logger.error(f"{self.name}: Error storing episodic memory: {e}")
    
    async def _update_personality_from_learning(self, belief_analysis: Dict):
        """Update personality traits based on learning insights"""
        try:
            belief_updates = belief_analysis.get('belief_updates', [])
            
            for update in belief_updates:
                if isinstance(update, dict):
                    trait_name = update.get('trait_affected')
                    direction = update.get('adjustment_direction', 'none')
                    magnitude = update.get('adjustment_magnitude', 0.0)
                    
                    if trait_name in self.personality.traits:
                        trait = self.personality.traits[trait_name]
                        if trait.stability < 0.8:  # Only adjust non-stable traits
                            if direction == 'increase':
                                trait.value = min(1.0, trait.value + magnitude * self.personality.learning_rate)
                            elif direction == 'decrease':
                                trait.value = max(0.0, trait.value - magnitude * self.personality.learning_rate)
                            
                            logger.info(f"{self.name}: Updated {trait_name} to {trait.value:.3f}")
            
        except Exception as e:
            logger.error(f"{self.name}: Error updating personality from learning: {e}")
            
            system_message, user_message = build_belief_revision_prompt(
                original_prediction=original_prediction,
                actual_outcome=actual_outcome,
                expert_personality=personality_description
            )
            
            logger.info(f"{self.name}: Built belief revision prompt")
            
            # Call LLM for belief revision analysis
            llm_response = await self.llm_service.generate_completion(
                system_message=system_message,
                user_message=user_message,
                temperature=0.6,  # Slightly more focused for learning
                max_tokens=-1,
                model="openai/gpt-oss-20b"
            )
            
            logger.info(f"{self.name}: LLM belief revision completed")
            
            # Parse belief revision response
            try:
                belief_revision = json.loads(llm_response.content)
                logger.info(f"{self.name}: Successfully parsed belief revision JSON")
            except json.JSONDecodeError as e:
                logger.error(f"{self.name}: Failed to parse belief revision JSON: {e}")
                return
            
            # Store belief revision in database
            await self._store_belief_revision(original_prediction, actual_outcome, belief_revision, llm_response)
            
            # Extract and apply learned weight adjustments
            await self._apply_learned_weights(belief_revision)
            
            # Create enriched episodic memory
            await self._create_enriched_memory(original_prediction, actual_outcome, belief_revision)
            
            total_duration = time.perf_counter() - start_time
            logger.info(f"{self.name}: Belief revision process completed in {total_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"{self.name}: Error in belief revision process: {e}")
            logger.exception("Full exception details:")
    
    async def _store_belief_revision(self, original_prediction: Dict, actual_outcome: Dict, 
                                   belief_revision: Dict, llm_response):
        """Store belief revision analysis in database"""
        try:
            revision_data = {
                'expert_id': self.expert_id,
                'original_prediction': original_prediction,
                'actual_outcome': actual_outcome,
                'belief_revision_analysis': belief_revision,
                'reflection_discussion': belief_revision.get('reflection_discussion', ''),
                'correct_predictions_analysis': belief_revision.get('correct_predictions_analysis', []),
                'incorrect_predictions_analysis': belief_revision.get('incorrect_predictions_analysis', []),
                'causal_reasoning_evaluation': belief_revision.get('causal_reasoning_evaluation', ''),
                'pattern_recognition': belief_revision.get('pattern_recognition', ''),
                'lessons_learned': belief_revision.get('lessons_learned', []),
                'memory_updates': belief_revision.get('memory_updates', ''),
                'llm_response_metadata': {
                    'model': llm_response.model,
                    'total_tokens': llm_response.total_tokens
                },
                'timestamp': datetime.now().isoformat()
            }
            
            await self.memory_service.store_belief_revision(revision_data)
            logger.info(f"{self.name}: Stored belief revision in database")
            
        except Exception as e:
            logger.error(f"{self.name}: Error storing belief revision: {e}")
    
    async def _apply_learned_weights(self, belief_revision: Dict):
        """Extract and apply learned weight adjustments"""
        try:
            lessons = belief_revision.get('lessons_learned', [])
            
            for lesson in lessons:
                lesson_text = lesson.get('lesson', '')
                application = lesson.get('application', '')
                confidence_adjustment = lesson.get('confidence_adjustment', '')
                
                # Extract weight adjustments and store in expert_learned_weights table
                weight_data = {
                    'expert_id': self.expert_id,
                    'lesson_description': lesson_text,
                    'application_method': application,
                    'confidence_impact': confidence_adjustment,
                    'timestamp': datetime.now().isoformat()
                }
                
                await self.memory_service.store_learned_weight(weight_data)
            
            logger.info(f"{self.name}: Applied {len(lessons)} learned weight adjustments")
            
        except Exception as e:
            logger.error(f"{self.name}: Error applying learned weights: {e}")
    
    async def _create_enriched_memory(self, original_prediction: Dict, actual_outcome: Dict, 
                                    belief_revision: Dict):
        """Create enriched episodic memory with post-game insights"""
        try:
            memory_data = {
                'expert_id': self.expert_id,
                'game_context': original_prediction.get('game_context', {}),
                'prediction_summary': self._summarize_prediction(original_prediction),
                'actual_outcome': actual_outcome,
                'was_correct': self._evaluate_prediction_accuracy(original_prediction, actual_outcome),
                'reasoning_chain': original_prediction.get('reasoning_discussion', ''),
                'post_game_insights': belief_revision.get('reflection_discussion', ''),
                'lessons_extracted': belief_revision.get('lessons_learned', []),
                'causal_analysis': belief_revision.get('causal_reasoning_evaluation', ''),
                'pattern_insights': belief_revision.get('pattern_recognition', ''),
                'memory_type': 'enriched_episodic',
                'timestamp': datetime.now().isoformat()
            }
            
            await self.memory_service.store_episodic_memory(memory_data)
            logger.info(f"{self.name}: Created enriched episodic memory")
            
        except Exception as e:
            logger.error(f"{self.name}: Error creating enriched memory: {e}")
    
    def _summarize_prediction(self, prediction: Dict) -> str:
        """Create concise summary of prediction for memory storage"""
        winner = prediction.get('winner_prediction', 'unknown')
        confidence = prediction.get('winner_confidence', 0.5)
        spread = prediction.get('spread_prediction', 0)
        total = prediction.get('total_prediction', 45)
        
        return f"Predicted {winner} to win (confidence: {confidence:.0%}), spread: {spread:+.1f}, total: {total:.1f}"
    
    def _evaluate_prediction_accuracy(self, prediction: Dict, outcome: Dict) -> bool:
        """Evaluate if the main prediction was correct"""
        predicted_winner = prediction.get('winner_prediction', '')
        actual_winner = outcome.get('winner', '')
        
        return predicted_winner.lower() == actual_winner.lower()

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Conservative processing: Emphasizes proven patterns, avoids uncertainty"""

        weights = {}

        # Heavily weight historical data and proven metrics
        weights['historical_emphasis'] = 0.9
        weights['uncertainty_avoidance'] = 0.8
        weights['proven_patterns_only'] = 0.85

        # De-emphasize volatile factors
        weights['weather_discount'] = 0.3  # "Weather is unpredictable"
        weights['news_discount'] = 0.4     # "News is often hype"
        weights['market_trust'] = 0.8      # "Market reflects consensus wisdom"

        return weights


class RiskTakingGambler(PersonalityDrivenExpert):
    """The Risk-Taking Gambler: High-risk, opportunity-seeking, embraces chaos"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.9, 0.8, 0.9),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.4, 0.6, 0.7),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.7, 0.5, 0.8),
                'recent_bias': PersonalityTrait('recent_bias', 0.8, 0.4, 0.8),
                'confidence_level': PersonalityTrait('confidence_level', 0.8, 0.7, 0.9),
                'optimism': PersonalityTrait('optimism', 0.8, 0.6, 0.7),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.9, 0.8, 0.9),
                'market_trust': PersonalityTrait('market_trust', 0.3, 0.5, 0.8),
                'authority_respect': PersonalityTrait('authority_respect', 0.2, 0.6, 0.6)
            },
            decision_style="intuitive",
            confidence_level=0.8,
            learning_rate=0.15
        )

        super().__init__(
            expert_id="risk_taking_gambler",
            name="The Gambler",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Aggressive processing: Seeks opportunity in chaos and uncertainty"""

        weights = {}

        # Emphasize volatile, opportunity-creating factors
        weights['chaos_opportunity'] = 0.9
        weights['underdog_bias'] = 0.8      # "Love a good upset"
        weights['momentum_emphasis'] = 0.85  # "Ride the hot hand"

        # Embrace uncertainty as opportunity
        weights['weather_amplify'] = 0.9     # "Weather creates chaos = opportunity"
        weights['injury_opportunity'] = 0.8  # "Next man up stories"
        weights['market_fade'] = 0.7         # "Fade the public when possible"

        return weights


class ContrarianRebel(PersonalityDrivenExpert):
    """The Contrarian Rebel: Anti-consensus, narrative-fading, market contrarian"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.7, 0.6, 0.8),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.6, 0.7, 0.7),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.95, 0.9, 1.0),
                'recent_bias': PersonalityTrait('recent_bias', 0.3, 0.5, 0.6),
                'confidence_level': PersonalityTrait('confidence_level', 0.7, 0.7, 0.8),
                'optimism': PersonalityTrait('optimism', 0.5, 0.6, 0.5),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.8, 0.7, 0.7),
                'market_trust': PersonalityTrait('market_trust', 0.1, 0.8, 0.9),
                'authority_respect': PersonalityTrait('authority_respect', 0.2, 0.7, 0.8)
            },
            decision_style="contrarian",
            confidence_level=0.7,
            learning_rate=0.08
        )

        super().__init__(
            expert_id="contrarian_rebel",
            name="The Rebel",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Contrarian processing: Systematically opposes popular opinion"""

        weights = {}

        # Anti-public sentiment weights
        weights['public_fade_emphasis'] = 0.95  # "When everyone agrees, disagree"
        weights['narrative_skepticism'] = 0.9   # "Popular stories are usually wrong"
        weights['media_discount'] = 0.8         # "Media creates false narratives"

        # Look for overlooked factors
        weights['overlooked_factor_boost'] = 0.85
        weights['unpopular_truth_seeking'] = 0.9
        weights['consensus_avoidance'] = 0.95

        return weights


class ValueHunter(PersonalityDrivenExpert):
    """The Value Hunter: Market inefficiency seeker, value-focused, patient opportunist"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.6, 0.7, 0.8),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.8, 0.8, 0.9),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.6, 0.6, 0.7),
                'recent_bias': PersonalityTrait('recent_bias', 0.3, 0.7, 0.6),
                'confidence_level': PersonalityTrait('confidence_level', 0.6, 0.8, 0.7),
                'optimism': PersonalityTrait('optimism', 0.5, 0.6, 0.5),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.4, 0.6, 0.6),
                'market_trust': PersonalityTrait('market_trust', 0.4, 0.5, 0.9),
                'authority_respect': PersonalityTrait('authority_respect', 0.5, 0.6, 0.5),
                'patience_level': PersonalityTrait('patience_level', 0.9, 0.8, 0.9)
            },
            decision_style="value_seeking",
            confidence_level=0.6,
            learning_rate=0.07
        )

        super().__init__(
            expert_id="value_hunter",
            name="The Hunter",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Value-focused processing: Seeks market inefficiencies and true odds"""

        weights = {}

        # Market inefficiency detection
        weights['line_value_assessment'] = 0.95     # "Where's the value?"
        weights['market_overreaction'] = 0.85       # "Market overreacting to news?"
        weights['true_probability_vs_implied'] = 0.9 # "What should the real odds be?"

        # Patient value seeking
        weights['long_term_value'] = 0.8            # "Not chasing immediate action"
        weights['disciplined_selection'] = 0.9      # "Only bet when there's clear value"
        weights['noise_filtering'] = 0.85           # "Ignore market noise"

        return weights


class MomentumRider(PersonalityDrivenExpert):
    """The Momentum Rider: Trend follower, recency-biased, hot hand believer"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.7, 0.5, 0.8),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.5, 0.6, 0.6),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.2, 0.7, 0.8),
                'recent_bias': PersonalityTrait('recent_bias', 0.95, 0.8, 1.0),
                'confidence_level': PersonalityTrait('confidence_level', 0.7, 0.6, 0.8),
                'optimism': PersonalityTrait('optimism', 0.7, 0.5, 0.7),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.6, 0.5, 0.6),
                'market_trust': PersonalityTrait('market_trust', 0.6, 0.5, 0.7),
                'authority_respect': PersonalityTrait('authority_respect', 0.4, 0.5, 0.5),
                'momentum_belief': PersonalityTrait('momentum_belief', 0.95, 0.9, 1.0)
            },
            decision_style="momentum_following",
            confidence_level=0.7,
            learning_rate=0.12
        )

        super().__init__(
            expert_id="momentum_rider",
            name="The Rider",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Momentum-focused processing: Follows trends and recent patterns"""

        weights = {}

        # Momentum detection and following
        weights['recent_form_emphasis'] = 0.95      # "What have you done lately?"
        weights['streak_continuation'] = 0.9        # "Hot streaks continue"
        weights['trend_following'] = 0.85           # "Ride the wave"

        # Recency bias amplification
        weights['last_game_weight'] = 0.8           # "Last game tells the story"
        weights['current_season_focus'] = 0.9       # "This year matters most"
        weights['historical_discount'] = 0.3        # "Ancient history doesn't matter"

        return weights


class FundamentalistScholar(PersonalityDrivenExpert):
    """The Fundamentalist Scholar: Long-term focused, data-driven, historically grounded"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.4, 0.8, 0.7),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.95, 0.9, 1.0),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.4, 0.7, 0.6),
                'recent_bias': PersonalityTrait('recent_bias', 0.1, 0.9, 0.9),
                'confidence_level': PersonalityTrait('confidence_level', 0.6, 0.8, 0.7),
                'optimism': PersonalityTrait('optimism', 0.5, 0.7, 0.5),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.2, 0.8, 0.7),
                'market_trust': PersonalityTrait('market_trust', 0.5, 0.6, 0.6),
                'authority_respect': PersonalityTrait('authority_respect', 0.8, 0.8, 0.7),
                'historical_reverence': PersonalityTrait('historical_reverence', 0.95, 0.9, 1.0)
            },
            decision_style="fundamental_analysis",
            confidence_level=0.6,
            learning_rate=0.04
        )

        super().__init__(
            expert_id="fundamentalist_scholar",
            name="The Scholar",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Fundamental processing: Deep historical analysis and long-term patterns"""

        weights = {}

        # Historical analysis emphasis
        weights['historical_pattern_weight'] = 0.95  # "History repeats itself"
        weights['long_term_trend_analysis'] = 0.9    # "Look at the big picture"
        weights['fundamental_metrics'] = 0.9         # "Core statistics matter most"

        # Noise filtering
        weights['short_term_noise_discount'] = 0.9   # "Ignore temporary fluctuations"
        weights['media_hype_discount'] = 0.8         # "Facts over narratives"
        weights['proven_indicator_focus'] = 0.85     # "Stick to what works long-term"

        return weights


class ChaosTheoryBeliever(PersonalityDrivenExpert):
    """The Chaos Theory Believer: Embraces randomness, seeks edge cases, butterfly effect focused"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.8, 0.6, 0.9),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.3, 0.5, 0.7),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.8, 0.6, 0.8),
                'recent_bias': PersonalityTrait('recent_bias', 0.6, 0.4, 0.6),
                'confidence_level': PersonalityTrait('confidence_level', 0.5, 0.7, 0.8),
                'optimism': PersonalityTrait('optimism', 0.6, 0.5, 0.6),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.95, 0.9, 1.0),
                'market_trust': PersonalityTrait('market_trust', 0.2, 0.6, 0.8),
                'authority_respect': PersonalityTrait('authority_respect', 0.1, 0.5, 0.7),
                'randomness_acceptance': PersonalityTrait('randomness_acceptance', 0.9, 0.8, 0.9)
            },
            decision_style="chaos_embracing",
            confidence_level=0.5,
            learning_rate=0.2
        )

        super().__init__(
            expert_id="chaos_theory_believer",
            name="The Chaos",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Chaos processing: Looks for butterfly effects and random outcomes"""

        weights = {}

        # Chaos and randomness emphasis
        weights['butterfly_effect_search'] = 0.9     # "Small things create big changes"
        weights['edge_case_focus'] = 0.85            # "Look for the unusual"
        weights['randomness_exploitation'] = 0.8     # "Chaos creates opportunity"

        # Anti-predictability
        weights['model_skepticism'] = 0.9            # "Models miss the chaos"
        weights['unexpected_outcome_bias'] = 0.8     # "Expect the unexpected"
        weights['conventional_wisdom_doubt'] = 0.85  # "Common sense is usually wrong"

        return weights


class GutInstinctExpert(PersonalityDrivenExpert):
    """The Gut Instinct Expert: Intuition-driven, feel-based, anti-analytical"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.6, 0.5, 0.7),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.1, 0.8, 0.9),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.5, 0.4, 0.6),
                'recent_bias': PersonalityTrait('recent_bias', 0.7, 0.3, 0.7),
                'confidence_level': PersonalityTrait('confidence_level', 0.8, 0.6, 0.9),
                'optimism': PersonalityTrait('optimism', 0.6, 0.4, 0.6),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.7, 0.5, 0.7),
                'market_trust': PersonalityTrait('market_trust', 0.3, 0.4, 0.6),
                'authority_respect': PersonalityTrait('authority_respect', 0.3, 0.5, 0.5),
                'intuition_trust': PersonalityTrait('intuition_trust', 0.95, 0.9, 1.0)
            },
            decision_style="pure_intuition",
            confidence_level=0.8,
            learning_rate=0.18
        )

        super().__init__(
            expert_id="gut_instinct_expert",
            name="The Intuition",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Intuitive processing: Feels the game rather than analyzing it"""

        weights = {}

        # Intuition and feel emphasis
        weights['gut_feeling_primary'] = 0.95        # "Trust your instincts"
        weights['vibe_assessment'] = 0.9             # "What's the vibe?"
        weights['emotional_intelligence'] = 0.85     # "Read between the lines"

        # Anti-analytical approach
        weights['analysis_paralysis_avoidance'] = 0.9 # "Don't overthink it"
        weights['simplicity_preference'] = 0.8        # "Keep it simple"
        weights['first_impression_trust'] = 0.85      # "First thought, best thought"

        return weights


class StatisticsPurist(PersonalityDrivenExpert):
    """The Statistics Purist: Pure numbers, regression analysis, model-driven"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.3, 0.9, 0.8),
                'analytics_trust': PersonalityTrait('analytics_trust', 1.0, 0.95, 1.0),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.3, 0.8, 0.6),
                'recent_bias': PersonalityTrait('recent_bias', 0.2, 0.8, 0.7),
                'confidence_level': PersonalityTrait('confidence_level', 0.8, 0.9, 0.8),
                'optimism': PersonalityTrait('optimism', 0.5, 0.8, 0.4),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.1, 0.95, 0.9),
                'market_trust': PersonalityTrait('market_trust', 0.3, 0.7, 0.6),
                'authority_respect': PersonalityTrait('authority_respect', 0.9, 0.9, 0.7),
                'model_trust': PersonalityTrait('model_trust', 0.98, 0.95, 1.0)
            },
            decision_style="pure_mathematical",
            confidence_level=0.8,
            learning_rate=0.03
        )

        super().__init__(
            expert_id="statistics_purist",
            name="The Quant",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Pure statistical processing: Only numbers matter"""

        weights = {
            'regression_model_primary': 0.98,      # "Models are truth"
            'statistical_significance': 0.95,      # "Only significant results matter"
            'sample_size_obsession': 0.9,          # "Need large sample sizes"
            'noise_elimination': 0.95,             # "Eliminate all noise"
            'mathematical_precision': 0.98,        # "Precise calculations only"
            'human_emotion_discount': 0.95         # "Emotions are irrelevant"
        }
        return weights


class TrendReversalSpecialist(PersonalityDrivenExpert):
    """The Trend Reversal Specialist: Seeks turning points, mean reversion believer"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.8, 0.6, 0.8),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.7, 0.7, 0.7),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.9, 0.7, 0.9),
                'recent_bias': PersonalityTrait('recent_bias', 0.4, 0.6, 0.6),
                'confidence_level': PersonalityTrait('confidence_level', 0.7, 0.7, 0.8),
                'optimism': PersonalityTrait('optimism', 0.5, 0.6, 0.5),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.8, 0.6, 0.7),
                'market_trust': PersonalityTrait('market_trust', 0.4, 0.6, 0.7),
                'authority_respect': PersonalityTrait('authority_respect', 0.4, 0.6, 0.5),
                'mean_reversion_belief': PersonalityTrait('mean_reversion_belief', 0.95, 0.9, 1.0)
            },
            decision_style="reversal_seeking",
            confidence_level=0.7,
            learning_rate=0.1
        )

        super().__init__(
            expert_id="trend_reversal_specialist",
            name="The Reversal",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Reversal processing: Looks for trend exhaustion and turning points"""

        weights = {
            'trend_exhaustion_detection': 0.95,    # "Trends always end"
            'mean_reversion_emphasis': 0.9,        # "Everything returns to average"
            'overextension_identification': 0.85,  # "Find the breaking point"
            'contrarian_timing': 0.9,              # "Time the turn"
            'momentum_fade_signals': 0.8,          # "When momentum dies"
            'cycle_pattern_recognition': 0.85      # "Patterns repeat in cycles"
        }
        return weights


class PopularNarrativeFader(PersonalityDrivenExpert):
    """The Popular Narrative Fader: Anti-media, story skeptic, hype fader"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.7, 0.6, 0.8),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.6, 0.7, 0.7),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.9, 0.8, 0.9),
                'recent_bias': PersonalityTrait('recent_bias', 0.3, 0.7, 0.7),
                'confidence_level': PersonalityTrait('confidence_level', 0.8, 0.7, 0.8),
                'optimism': PersonalityTrait('optimism', 0.4, 0.6, 0.6),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.7, 0.6, 0.7),
                'market_trust': PersonalityTrait('market_trust', 0.3, 0.7, 0.8),
                'authority_respect': PersonalityTrait('authority_respect', 0.2, 0.7, 0.8),
                'media_skepticism': PersonalityTrait('media_skepticism', 0.98, 0.9, 1.0)
            },
            decision_style="narrative_skeptical",
            confidence_level=0.8,
            learning_rate=0.09
        )

        super().__init__(
            expert_id="popular_narrative_fader",
            name="The Fader",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Anti-narrative processing: Fades popular stories and media hype"""

        weights = {
            'media_hype_inverse': 0.95,            # "Fade the hype"
            'popular_story_skepticism': 0.9,       # "Popular stories are wrong"
            'narrative_contrarian': 0.85,          # "Go against the story"
            'hype_train_avoidance': 0.9,           # "Don't ride the hype"
            'underreported_factor_seek': 0.8,      # "Find what's not talked about"
            'mainstream_media_discount': 0.95      # "Media creates false narratives"
        }
        return weights


class SharpMoneyFollower(PersonalityDrivenExpert):
    """The Sharp Money Follower: Follows smart money, respects syndicate action"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.6, 0.7, 0.7),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.7, 0.7, 0.8),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.3, 0.6, 0.6),
                'recent_bias': PersonalityTrait('recent_bias', 0.6, 0.5, 0.6),
                'confidence_level': PersonalityTrait('confidence_level', 0.7, 0.8, 0.7),
                'optimism': PersonalityTrait('optimism', 0.6, 0.6, 0.5),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.4, 0.6, 0.6),
                'market_trust': PersonalityTrait('market_trust', 0.9, 0.8, 0.9),
                'authority_respect': PersonalityTrait('authority_respect', 0.8, 0.8, 0.8),
                'sharp_money_reverence': PersonalityTrait('sharp_money_reverence', 0.95, 0.9, 1.0)
            },
            decision_style="smart_money_following",
            confidence_level=0.7,
            learning_rate=0.06
        )

        super().__init__(
            expert_id="sharp_money_follower",
            name="The Sharp",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Sharp money processing: Follows professional betting patterns"""

        weights = {
            'sharp_action_detection': 0.95,        # "Follow the smart money"
            'syndicate_pattern_recognition': 0.9,  # "Recognize professional action"
            'steam_move_following': 0.85,          # "Follow the steam"
            'closing_line_value_respect': 0.9,     # "Closing line is truth"
            'market_maker_respect': 0.8,           # "Market makers are smart"
            'public_money_fade': 0.7               # "Fade when public heavy"
        }
        return weights


class UnderdogChampion(PersonalityDrivenExpert):
    """The Underdog Champion: David vs Goliath believer, upset seeker"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.9, 0.6, 0.9),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.4, 0.6, 0.6),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.8, 0.7, 0.8),
                'recent_bias': PersonalityTrait('recent_bias', 0.5, 0.5, 0.6),
                'confidence_level': PersonalityTrait('confidence_level', 0.8, 0.6, 0.8),
                'optimism': PersonalityTrait('optimism', 0.8, 0.5, 0.7),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.9, 0.7, 0.9),
                'market_trust': PersonalityTrait('market_trust', 0.2, 0.6, 0.8),
                'authority_respect': PersonalityTrait('authority_respect', 0.2, 0.6, 0.7),
                'underdog_belief': PersonalityTrait('underdog_belief', 0.95, 0.9, 1.0)
            },
            decision_style="underdog_championing",
            confidence_level=0.8,
            learning_rate=0.15
        )

        super().__init__(
            expert_id="underdog_champion",
            name="The Underdog",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Underdog processing: Seeks upset opportunities and David vs Goliath spots"""

        weights = {
            'upset_potential_identification': 0.95, # "Find the upset"
            'motivational_edge_seeking': 0.9,       # "Motivation matters"
            'parity_emphasis': 0.85,                 # "Anyone can beat anyone"
            'desperation_advantage': 0.8,            # "Desperate teams are dangerous"
            'public_underestimation': 0.9,           # "Public underrates underdogs"
            'intangible_factor_boost': 0.85          # "Intangibles favor underdogs"
        }
        return weights


class ConsensusFollower(PersonalityDrivenExpert):
    """The Consensus Follower: Wisdom of crowds believer, safety in numbers"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.3, 0.8, 0.7),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.6, 0.7, 0.7),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.1, 0.9, 0.9),
                'recent_bias': PersonalityTrait('recent_bias', 0.5, 0.6, 0.5),
                'confidence_level': PersonalityTrait('confidence_level', 0.5, 0.8, 0.6),
                'optimism': PersonalityTrait('optimism', 0.6, 0.6, 0.5),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.2, 0.8, 0.8),
                'market_trust': PersonalityTrait('market_trust', 0.9, 0.8, 0.9),
                'authority_respect': PersonalityTrait('authority_respect', 0.9, 0.9, 0.8),
                'consensus_reverence': PersonalityTrait('consensus_reverence', 0.95, 0.9, 1.0)
            },
            decision_style="consensus_following",
            confidence_level=0.5,
            learning_rate=0.04
        )

        super().__init__(
            expert_id="consensus_follower",
            name="The Consensus",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Consensus processing: Follows crowd wisdom and expert opinion"""

        weights = {
            'expert_consensus_following': 0.95,     # "Experts know best"
            'crowd_wisdom_trust': 0.9,              # "Wisdom of crowds"
            'popular_opinion_validation': 0.85,     # "Popular = probably right"
            'majority_rule_belief': 0.9,            # "Majority is usually right"
            'contrarian_avoidance': 0.95,           # "Don't go against the grain"
            'safety_in_numbers': 0.9                # "Follow the herd for safety"
        }
        return weights


class MarketInefficiencyExploiter(PersonalityDrivenExpert):
    """The Market Inefficiency Exploiter: Arbitrage seeker, edge finder, systematic advantage hunter"""

    def __init__(self):
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.7, 0.7, 0.8),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.9, 0.8, 0.9),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.6, 0.6, 0.7),
                'recent_bias': PersonalityTrait('recent_bias', 0.4, 0.7, 0.6),
                'confidence_level': PersonalityTrait('confidence_level', 0.8, 0.8, 0.8),
                'optimism': PersonalityTrait('optimism', 0.6, 0.6, 0.5),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.5, 0.6, 0.6),
                'market_trust': PersonalityTrait('market_trust', 0.3, 0.6, 0.8),
                'authority_respect': PersonalityTrait('authority_respect', 0.5, 0.6, 0.6),
                'inefficiency_detection': PersonalityTrait('inefficiency_detection', 0.98, 0.9, 1.0)
            },
            decision_style="systematic_exploitation",
            confidence_level=0.8,
            learning_rate=0.06
        )

        super().__init__(
            expert_id="market_inefficiency_exploiter",
            name="The Exploiter",
            personality_profile=personality
        )

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Inefficiency processing: Systematically finds and exploits market edges"""

        weights = {
            'arbitrage_opportunity_detection': 0.98, # "Find the arbitrage"
            'market_pricing_error_identification': 0.95, # "Spot pricing mistakes"
            'information_asymmetry_exploitation': 0.9,   # "Use information advantage"
            'systematic_edge_development': 0.95,         # "Build systematic edges"
            'model_vs_market_comparison': 0.9,           # "Model vs market price"
            'inefficiency_pattern_recognition': 0.85     # "Recognize recurring inefficiencies"
        }
        return weights


def test_personality_driven_experts():
    """Test the personality-driven expert system"""

    print("🎭 Testing Personality-Driven Expert System")
    print("=" * 60)

    # Create universal game data (same for all experts)
    universal_data = UniversalGameData(
        home_team="LV",
        away_team="LAC",
        game_time="2024-01-15 22:00:00",
        location="Las Vegas",
        weather={
            'temperature': 45,
            'wind_speed': 18,
            'conditions': 'Clear',
            'humidity': 40
        },
        injuries={
            'home': [
                {'position': 'QB', 'injury_type': 'ankle', 'severity': 'minor', 'probability_play': 0.8}
            ],
            'away': [
                {'position': 'RB', 'injury_type': 'hamstring', 'severity': 'medium', 'probability_play': 0.6}
            ]
        },
        line_movement={
            'opening_line': -3.0,
            'current_line': -1.5,
            'public_percentage': 72
        },
        team_stats={
            'home': {'offensive_yards_per_game': 380, 'defensive_yards_allowed': 320},
            'away': {'offensive_yards_per_game': 360, 'defensive_yards_allowed': 340}
        }
    )

    # Create all 15 personality-driven experts
    experts = [
        ConservativeAnalyzer(),     # The Analyst
        RiskTakingGambler(),        # The Gambler
        ContrarianRebel(),          # The Rebel
        ValueHunter(),              # The Hunter
        MomentumRider(),            # The Rider
        FundamentalistScholar(),    # The Scholar
        ChaosTheoryBeliever(),      # The Chaos
        GutInstinctExpert(),        # The Intuition
        StatisticsPurist(),         # The Quant
        TrendReversalSpecialist(),  # The Reversal
        PopularNarrativeFader(),    # The Fader
        SharpMoneyFollower(),       # The Sharp
        UnderdogChampion(),         # The Underdog
        ConsensusFollower(),        # The Consensus
        MarketInefficiencyExploiter() # The Exploiter
    ]

    print(f"📊 Universal Data Available to All Experts:")
    print(f"   🏈 Game: {universal_data.away_team} @ {universal_data.home_team}")
    print(f"   🌡️ Weather: {universal_data.weather['temperature']}°F, {universal_data.weather['wind_speed']}mph wind")
    print(f"   🏥 Injuries: {len(universal_data.injuries.get('home', []))} home, {len(universal_data.injuries.get('away', []))} away")
    print(f"   📈 Line Movement: {universal_data.line_movement['opening_line']} → {universal_data.line_movement['current_line']}")
    print(f"   👥 Public: {universal_data.line_movement['public_percentage']}% on favorite")

    print(f"\n🎭 All 15 Personality Experts (Same Data, Different Interpretations):")
    print("-" * 80)

    predictions = []
    for expert in experts:
        prediction = expert.make_personality_driven_prediction(universal_data)
        predictions.append((expert.name, prediction))

        print(f"🤖 {expert.name:12} | Winner: {prediction['winner_prediction']:4} | "
              f"Confidence: {prediction['winner_confidence']:4.0%} | "
              f"Spread: {prediction['spread_prediction']:5.1f} | "
              f"Total: {prediction['total_prediction']:4.1f}")

    print(f"\n📊 PERSONALITY DIVERSITY ANALYSIS:")
    home_picks = sum(1 for _, p in predictions if p['winner_prediction'] == 'home')
    away_picks = sum(1 for _, p in predictions if p['winner_prediction'] == 'away')
    avg_confidence = sum(p['winner_confidence'] for _, p in predictions) / len(predictions)
    spread_range = max(p['spread_prediction'] for _, p in predictions) - min(p['spread_prediction'] for _, p in predictions)

    print(f"   🏠 Home Picks: {home_picks}/15 experts ({home_picks/15:.0%})")
    print(f"   ✈️ Away Picks: {away_picks}/15 experts ({away_picks/15:.0%})")
    print(f"   🎯 Average Confidence: {avg_confidence:.1%}")
    print(f"   📊 Spread Range: {spread_range:.1f} points")

    print(f"\n✅ SUCCESS: Complete 15-Expert Personality Ensemble")
    print(f"   🎭 Fair competition: All see identical data")
    print(f"   🧠 Personality-driven differences: No domain bias")
    print(f"   📈 Diverse opinions: Range of interpretations")
    print(f"   🔄 Autonomous evolution: Each preserves core personality")

    print(f"\n🚀 READY: Full autonomous expert system operational!")


if __name__ == "__main__":
    test_personality_driven_experts()