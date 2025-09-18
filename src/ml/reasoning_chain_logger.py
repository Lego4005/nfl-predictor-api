"""
Reasoning Chain Logger Service for NFL Personality-Driven Experts

Captures and stores detailed reasoning behind expert predictions, including
factors, weights, confidence levels, and personality-influenced internal monologue.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import json
import asyncio
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)

@dataclass
class ReasoningFactor:
    """Represents a single decision factor in expert reasoning"""
    factor: str  # e.g., "road_performance", "divisional_history"
    value: str  # e.g., "Buffalo 5-1 on road", "Jets 2-8 in primetime"
    weight: float  # 0.0 to 1.0 - importance in decision
    confidence: float  # 0.0 to 1.0 - confidence in this factor
    source: str  # "season_stats", "historical_pattern", "learned_principle"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return asdict(self)

@dataclass
class ConfidenceBreakdown:
    """Detailed confidence scores for different prediction aspects"""
    overall: float
    winner: float
    spread: float
    total: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return asdict(self)

@dataclass
class PredictionData:
    """Structured prediction data"""
    winner: str
    spread: float
    total: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return asdict(self)


class PersonalityMonologueGenerator:
    """Generates personality-driven internal monologue for experts"""

    PERSONALITY_PATTERNS = {
        "analytical": [
            "The data strongly suggests {prediction}, with {top_factor} being the key driver.",
            "Statistical analysis points to {prediction}. {top_factor} has {confidence}% historical accuracy.",
            "Multiple regression factors converge on {prediction}. Primary signal: {top_factor}."
        ],
        "intuitive": [
            "My gut tells me {prediction}, especially considering {top_factor}.",
            "Something about this matchup screams {prediction}. Can't ignore {top_factor}.",
            "I've seen this pattern before - {prediction} feels right. {top_factor} seals it."
        ],
        "contrarian": [
            "Everyone's missing {top_factor}, which makes {prediction} the smart play.",
            "The market's wrong here. {top_factor} means {prediction} is the value.",
            "Going against the grain with {prediction} because {top_factor}."
        ],
        "momentum": [
            "Riding the wave with {prediction}. {top_factor} shows clear momentum.",
            "The trend is your friend - {prediction} based on {top_factor}.",
            "Hot teams stay hot. {top_factor} confirms {prediction}."
        ],
        "conservative": [
            "Taking the safe route with {prediction}. {top_factor} provides solid foundation.",
            "No need to overthink - {prediction} backed by {top_factor}.",
            "Sticking to fundamentals: {prediction} because of {top_factor}."
        ]
    }

    @classmethod
    def generate_monologue(cls, personality_type: str, prediction: Dict,
                           top_factors: List[ReasoningFactor],
                           confidence: ConfidenceBreakdown) -> str:
        """Generate personality-appropriate internal monologue"""

        # Get patterns for personality type
        patterns = cls.PERSONALITY_PATTERNS.get(
            personality_type,
            cls.PERSONALITY_PATTERNS["analytical"]
        )

        # Select pattern based on confidence
        import random
        if confidence.overall > 0.8:
            pattern = random.choice(patterns)
        else:
            pattern = patterns[0]  # Use more measured language when less confident

        # Extract top factor
        if top_factors:
            top_factor = top_factors[0]
            factor_desc = f"{top_factor.factor}: {top_factor.value}"
        else:
            factor_desc = "multiple converging signals"

        # Format prediction description
        prediction_desc = f"{prediction.get('winner', 'Unknown')} to win"
        if 'spread' in prediction and prediction['spread']:
            prediction_desc += f" by {abs(prediction['spread'])} points"

        # Generate monologue
        monologue = pattern.format(
            prediction=prediction_desc,
            top_factor=factor_desc,
            confidence=int(confidence.overall * 100)
        )

        # Add confidence qualifier if uncertain
        if confidence.overall < 0.6:
            monologue += " Still some uncertainty here, but that's my lean."
        elif confidence.overall < 0.7:
            monologue += " Not my strongest pick, but the edge is there."

        return monologue


class ReasoningChainLogger:
    """Service for logging and analyzing expert reasoning chains"""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.monologue_generator = PersonalityMonologueGenerator()
        self.factor_cache = defaultdict(list)
        logger.info("🧠 Reasoning Chain Logger initialized")

    async def log_reasoning_chain(
        self,
        expert_id: str,
        game_id: str,
        prediction: Dict[str, Any],
        factors: List[Dict[str, Any]],
        monologue: Optional[str] = None,
        confidence: Optional[Dict[str, float]] = None,
        expert_personality: str = "analytical"
    ) -> str:
        """
        Log complete reasoning chain for an expert's prediction

        Args:
            expert_id: Unique identifier for the expert
            game_id: Unique identifier for the game
            prediction: Dict with winner, spread, total
            factors: List of reasoning factors
            monologue: Optional internal monologue (auto-generated if not provided)
            confidence: Optional confidence breakdown (auto-calculated if not provided)
            expert_personality: Personality type for monologue generation

        Returns:
            ID of the logged reasoning chain
        """
        try:
            # Convert factors to ReasoningFactor objects
            reasoning_factors = [
                ReasoningFactor(**f) if isinstance(f, dict) else f
                for f in factors
            ]

            # Sort factors by weight * confidence for importance
            reasoning_factors.sort(
                key=lambda f: f.weight * f.confidence,
                reverse=True
            )

            # Auto-calculate confidence if not provided
            if not confidence:
                confidence = self._calculate_confidence(reasoning_factors)

            confidence_obj = ConfidenceBreakdown(**confidence) if isinstance(confidence, dict) else confidence

            # Generate monologue if not provided
            if not monologue:
                monologue = self.monologue_generator.generate_monologue(
                    expert_personality,
                    prediction,
                    reasoning_factors[:3],  # Top 3 factors
                    confidence_obj
                )

            # Prepare data for database
            chain_data = {
                'id': str(uuid.uuid4()),
                'expert_id': expert_id,
                'game_id': game_id,
                'prediction': json.dumps(prediction),
                'confidence_scores': json.dumps(confidence_obj.to_dict()),
                'reasoning_factors': json.dumps([f.to_dict() for f in reasoning_factors]),
                'internal_monologue': monologue,
                'prediction_timestamp': datetime.utcnow().isoformat(),
                'model_version': 'v1.0'
            }

            # Store in database if available
            if self.supabase:
                result = await self._store_in_database(chain_data)
                chain_id = result.get('id', chain_data['id'])
            else:
                # Fallback to local cache
                self.factor_cache[expert_id].append(chain_data)
                chain_id = chain_data['id']

            logger.info(f"✅ Logged reasoning chain for {expert_id} on game {game_id}")
            return chain_id

        except Exception as e:
            logger.error(f"❌ Failed to log reasoning chain: {e}")
            raise

    async def get_recent_reasoning(
        self,
        expert_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent reasoning chains for an expert

        Args:
            expert_id: Expert identifier
            limit: Maximum number of records to return

        Returns:
            List of recent reasoning chains
        """
        try:
            if self.supabase:
                result = self.supabase.table('expert_reasoning_chains') \
                    .select('*') \
                    .eq('expert_id', expert_id) \
                    .order('prediction_timestamp', desc=True) \
                    .limit(limit) \
                    .execute()

                return result.data
            else:
                # Return from cache
                expert_chains = self.factor_cache.get(expert_id, [])
                return sorted(
                    expert_chains,
                    key=lambda x: x['prediction_timestamp'],
                    reverse=True
                )[:limit]

        except Exception as e:
            logger.error(f"❌ Failed to get recent reasoning: {e}")
            return []

    async def analyze_factor_success_rates(
        self,
        expert_id: str,
        min_occurrences: int = 5
    ) -> Dict[str, Dict]:
        """
        Analyze success rates of different reasoning factors

        Args:
            expert_id: Expert identifier
            min_occurrences: Minimum times a factor must appear

        Returns:
            Dictionary mapping factors to their success metrics
        """
        try:
            # Get reasoning chains with outcomes
            if self.supabase:
                query = """
                    SELECT
                        rc.reasoning_factors,
                        rc.prediction,
                        em.accuracy_scores
                    FROM expert_reasoning_chains rc
                    JOIN expert_episodic_memories em ON rc.game_id = em.game_id
                    WHERE rc.expert_id = %s
                    AND em.expert_id = %s
                """
                result = self.supabase.rpc('analyze_factor_success', {
                    'p_expert_id': expert_id,
                    'p_min_occurrences': min_occurrences
                }).execute()

                return self._process_factor_analysis(result.data)
            else:
                # Simple analysis from cache
                return self._analyze_cached_factors(expert_id)

        except Exception as e:
            logger.error(f"❌ Failed to analyze factor success: {e}")
            return {}

    async def extract_dominant_factors(
        self,
        expert_id: str,
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Extract the most influential factors for an expert

        Args:
            expert_id: Expert identifier
            top_n: Number of top factors to return

        Returns:
            List of (factor_name, average_weight) tuples
        """
        try:
            factor_weights = defaultdict(list)

            # Get all reasoning chains
            chains = await self.get_recent_reasoning(expert_id, limit=100)

            for chain in chains:
                factors = json.loads(chain.get('reasoning_factors', '[]'))
                for factor in factors:
                    factor_weights[factor['factor']].append(
                        factor['weight'] * factor['confidence']
                    )

            # Calculate average importance
            factor_importance = [
                (factor, sum(weights) / len(weights))
                for factor, weights in factor_weights.items()
                if len(weights) >= 3  # Minimum occurrences
            ]

            # Sort by importance
            factor_importance.sort(key=lambda x: x[1], reverse=True)

            return factor_importance[:top_n]

        except Exception as e:
            logger.error(f"❌ Failed to extract dominant factors: {e}")
            return []

    async def update_reasoning_with_outcome(
        self,
        expert_id: str,
        game_id: str,
        actual_outcome: Dict,
        create_episodic_memory: bool = True
    ) -> Optional[str]:
        """
        Update reasoning chain with actual game outcome for learning

        Args:
            expert_id: Expert identifier
            game_id: Game identifier
            actual_outcome: Actual game results
            create_episodic_memory: Whether to create episodic memory

        Returns:
            Episodic memory ID if created
        """
        try:
            # Get the reasoning chain for this game
            if self.supabase:
                chain = self.supabase.table('expert_reasoning_chains') \
                    .select('*') \
                    .eq('expert_id', expert_id) \
                    .eq('game_id', game_id) \
                    .single() \
                    .execute()

                if not chain.data:
                    logger.warning(f"No reasoning chain found for {expert_id} on {game_id}")
                    return None

                prediction = json.loads(chain.data['prediction'])
                confidence = json.loads(chain.data['confidence_scores'])

                # Calculate accuracy
                accuracy = self._calculate_accuracy(prediction, actual_outcome)

                if create_episodic_memory:
                    # Create episodic memory entry
                    memory_data = {
                        'expert_id': expert_id,
                        'game_id': game_id,
                        'prediction_summary': prediction,
                        'actual_outcome': actual_outcome,
                        'accuracy_scores': accuracy,
                        'lesson_learned': self._generate_lesson(
                            prediction, actual_outcome, accuracy
                        ),
                        'emotional_weight': self._calculate_emotional_weight(accuracy),
                        'surprise_factor': self._calculate_surprise(confidence, accuracy)
                    }

                    memory_result = self.supabase.table('expert_episodic_memories') \
                        .insert(memory_data) \
                        .execute()

                    return memory_result.data[0]['id'] if memory_result.data else None

            return None

        except Exception as e:
            logger.error(f"❌ Failed to update reasoning with outcome: {e}")
            return None

    # Helper methods

    def _calculate_confidence(self, factors: List[ReasoningFactor]) -> ConfidenceBreakdown:
        """Calculate confidence breakdown from factors"""
        if not factors:
            return ConfidenceBreakdown(0.5, 0.5, 0.5, 0.5)

        # Weight factors by importance
        total_weight = sum(f.weight for f in factors)
        if total_weight == 0:
            total_weight = 1

        weighted_confidence = sum(
            f.weight * f.confidence for f in factors
        ) / total_weight

        # Slight variations for different bet types
        return ConfidenceBreakdown(
            overall=weighted_confidence,
            winner=min(weighted_confidence * 1.1, 1.0),
            spread=weighted_confidence * 0.9,
            total=weighted_confidence * 0.85
        )

    def _calculate_accuracy(self, prediction: Dict, outcome: Dict) -> Dict:
        """Calculate accuracy scores for prediction vs outcome"""
        scores = {}

        # Winner accuracy (binary)
        scores['winner'] = 1.0 if prediction.get('winner') == outcome.get('winner') else 0.0

        # Spread accuracy (scaled by closeness)
        if 'spread' in prediction and 'margin' in outcome:
            spread_diff = abs(prediction['spread'] - outcome['margin'])
            scores['spread'] = max(0, 1 - (spread_diff / 10))  # 10 point scale
        else:
            scores['spread'] = 0.5

        # Total accuracy (scaled by closeness)
        if 'total' in prediction and 'total_points' in outcome:
            total_diff = abs(prediction['total'] - outcome['total_points'])
            scores['total'] = max(0, 1 - (total_diff / 10))  # 10 point scale
        else:
            scores['total'] = 0.5

        # Overall accuracy
        scores['overall'] = sum(scores.values()) / len(scores)

        return scores

    def _generate_lesson(self, prediction: Dict, outcome: Dict, accuracy: Dict) -> str:
        """Generate lesson learned from prediction outcome"""
        if accuracy['overall'] > 0.8:
            return f"Strong prediction validated. {prediction['winner']} won as expected."
        elif accuracy['overall'] < 0.3:
            return f"Major miss. Underestimated {outcome['winner']}. Need to reconsider approach."
        elif accuracy['winner'] == 1.0 and accuracy['spread'] < 0.5:
            return f"Right winner but wrong margin. {outcome['winner']} won by {outcome.get('margin', 0)}, not {prediction.get('spread', 0)}."
        else:
            return "Mixed results. Some factors were correct, others need adjustment."

    def _calculate_emotional_weight(self, accuracy: Dict) -> float:
        """Calculate emotional weight based on accuracy"""
        # More emotional weight for extreme outcomes
        if accuracy['overall'] > 0.9 or accuracy['overall'] < 0.2:
            return 0.8
        else:
            return 0.5

    def _calculate_surprise(self, confidence: Dict, accuracy: Dict) -> float:
        """Calculate surprise factor"""
        # High confidence but low accuracy = high surprise
        confidence_val = confidence.get('overall', 0.5)
        accuracy_val = accuracy.get('overall', 0.5)
        return abs(confidence_val - accuracy_val)

    def _process_factor_analysis(self, data: List[Dict]) -> Dict:
        """Process factor analysis results"""
        factor_stats = defaultdict(lambda: {'success': 0, 'total': 0})

        for row in data:
            factors = json.loads(row['reasoning_factors'])
            accuracy = row['accuracy_scores']['overall']

            for factor in factors:
                factor_name = factor['factor']
                factor_stats[factor_name]['total'] += 1
                if accuracy > 0.6:  # Success threshold
                    factor_stats[factor_name]['success'] += 1

        # Calculate success rates
        result = {}
        for factor, stats in factor_stats.items():
            if stats['total'] >= 5:  # Minimum occurrences
                result[factor] = {
                    'success_rate': stats['success'] / stats['total'],
                    'occurrences': stats['total'],
                    'successful_uses': stats['success']
                }

        return result

    def _analyze_cached_factors(self, expert_id: str) -> Dict:
        """Simple factor analysis from cache"""
        # This is a simplified version for when database is not available
        factor_stats = defaultdict(lambda: {'count': 0, 'total_weight': 0})

        for chain in self.factor_cache.get(expert_id, []):
            factors = json.loads(chain.get('reasoning_factors', '[]'))
            for factor in factors:
                factor_name = factor['factor']
                factor_stats[factor_name]['count'] += 1
                factor_stats[factor_name]['total_weight'] += factor['weight']

        result = {}
        for factor, stats in factor_stats.items():
            if stats['count'] > 0:
                result[factor] = {
                    'average_weight': stats['total_weight'] / stats['count'],
                    'occurrences': stats['count']
                }

        return result

    async def _store_in_database(self, chain_data: Dict) -> Dict:
        """Store reasoning chain in database"""
        result = self.supabase.table('expert_reasoning_chains') \
            .insert(chain_data) \
            .execute()

        return result.data[0] if result.data else chain_data