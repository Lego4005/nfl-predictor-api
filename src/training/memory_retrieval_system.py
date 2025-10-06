"""
Memory Retrieval System for NFrediction Training

This module implements the memory retrieval system that connects to vector databases
and retrieves relevant historical memories using expert-specific temporal decay and
similarity scoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

from training.expert_configuration import ExpertType, ExpertConfiguration, ExpertConfigurationManager
from training.temporal_decay_calculator import TemporalDecayCalculator, DecayScore


@dataclass
class GameMemory:
    """Represents a stored memory from a historical game"""
    memory_id: str
    memory_type: str  # 'reasoning', 'contextual', 'market', 'learning'
    content: str
    game_context: Dict[str, Any]
    outcome_data: Optional[Dict[str, Any]]
    created_date: datetime
    expert_source: Optional[ExpertType] = None
    confidence_level: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'memory_id': self.memory_id,
            'memory_type': self.memory_type,
            'content': self.content,
            'game_context': self.game_context,
            'outcome_data': self.outcome_data,
            'created_date': self.created_date.isoformat(),
            'expert_source': self.expert_source.value if self.expert_source else None,
            'confidence_level': self.confidence_level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameMemory':
        """Create from dictionary"""
        return cls(
            memory_id=data['memory_id'],
            memory_type=data['memory_type'],
            content=data['content'],
            game_context=data['game_context'],
            outcome_data=data.get('outcome_data'),
            created_date=datetime.fromisoformat(data['created_date']),
            expert_source=ExpertType(data['expert_source']) if data.get('expert_source') else None,
            confidence_level=data.get('confidence_level', 0.0)
        )


@dataclass
class RetrievedMemory:
    """A memory retrieved for expert analysis with scoring"""
    memory: GameMemory
    decay_score: DecayScore
    similarity_explanation: str
    relevance_rank: int

    def __str__(self) -> str:
        return (f"Memory {self.memory.memory_id} (Rank {self.relevance_rank}): "
                f"Score {self.decay_score.final_weighted_score:.3f}, "
                f"Age {self.decay_score.age_days}d")


@dataclass
class MemoryRetrievalResult:
    """Complete result of memory retrieval for an expert"""
    expert_type: ExpertType
    game_context: Dict[str, Any]
    retrieved_memories: List[RetrievedMemory]
    total_candidates_evaluated: int
    retrieval_time_ms: float
    retrieval_summary: str


class MemoryRetrievalSystem:
    """
    Memory retrieval system that fetches relevant historical memories
    using expert-specific temporal decay and similarity scoring
    """

    def __init__(
        self,
        config_manager: ExpertConfigurationManager,
        temporal_calculator: TemporalDecayCalculator,
        learning_memory_system=None
    ):
        self.config_manager = config_manager
        self.temporal_calculator = temporal_calculator
        self.learning_memory_system = learning_memory_system
        self.logger = logging.getLogger(__name__)

        # Mock memory storage - in production this would be vector DB
        self.memory_storage: Dict[str, List[GameMemory]] = {
            'reasoning': [],
            'contextual': [],
            'market': [],
            'learning': []
        }

        # Initialize with some sample memories for testing
        self._initialize_sample_memories()

    def _initialize_sample_memories(self):
        """Initialize with sample memories for testing"""

        # Sample reasoning memories
        reasoning_memories = [
            GameMemory(
                memory_id="reasoning_001",
                memory_type="reasoning",
                content="Cold weather games historically favor teams with strong running attacks and conservative passing",
                game_context={
                    'home_team': 'GB',
                    'away_team': 'CHI',
                    'weather': {'temperature': 22, 'wind_speed': 18, 'conditions': 'snow'},
                    'week': 15,
                    'season': 2023
                },
                outcome_data={'home_score': 24, 'away_score': 17, 'total': 41},
                created_date=datetime.now() - timedelta(days=45),
                expert_source=ExpertType.FUNDAMENTALIST_SCHOLAR,
                confidence_level=0.85
            ),
            GameMemory(
                memory_id="reasoning_002",
                memory_type="reasoning",
                content="Teams coming off bye weeks show improved performance in first two quarters",
                game_context={
                    'home_team': 'KC',
                    'away_team': 'DEN',
                    'rest_advantage': {'home': 7, 'away': 14},
                    'week': 8,
                    'season': 2023
                },
                outcome_data={'home_score': 31, 'away_score': 17, 'total': 48},
                created_date=datetime.now() - timedelta(days=120),
                expert_source=ExpertType.GUT_INSTINCT_EXPERT,
                confidence_level=0.72
            )
        ]

        # Sample contextual memories
        contextual_memories = [
            GameMemory(
                memory_id="contextual_001",
                memory_type="contextual",
                content="Divisional games in December tend to be lower-scoring due to familiarity and weather",
                game_context={
                    'home_team': 'NE',
                    'away_team': 'BUF',
                    'division_game': True,
                    'weather': {'temperature': 28, 'wind_speed': 12, 'conditions': 'clear'},
                    'week': 16,
                    'season': 2023
                },
                outcome_data={'home_score': 21, 'away_score': 14, 'total': 35},
                created_date=datetime.now() - timedelta(days=30),
                expert_source=ExpertType.VALUE_HUNTER,
                confidence_level=0.78
            )
        ]

        # Sample market memories
        market_memories = [
            GameMemory(
                memory_id="market_001",
                memory_type="market",
                content="Heavy public betting on favorites often creates value on underdogs in primetime games",
                game_context={
                    'home_team': 'DAL',
                    'away_team': 'PHI',
                    'primetime': True,
                    'public_betting': {'home': 78, 'away': 22},
                    'line_movement': {'opening': -7.0, 'current': -4.5},
                    'week': 14,
                    'season': 2023
                },
                outcome_data={'home_score': 20, 'away_score': 26, 'total': 46},
                created_date=datetime.now() - timedelta(days=60),
                expert_source=ExpertType.CONTRARIAN_REBEL,
                confidence_level=0.81
            )
        ]

        # Sample learning memories
        learning_memories = [
            GameMemory(
                memory_id="learning_001",
                memory_type="learning",
                content="Overconfidence in momentum teams led to poor predictions - need to weight recent performance more carefully",
                game_context={
                    'home_team': 'MIA',
                    'away_team': 'BUF',
                    'momentum': {'home': 'hot_4_game_win_streak', 'away': 'cold_2_losses'},
                    'week': 11,
                    'season': 2023
                },
                outcome_data={'home_score': 14, 'away_score': 31, 'total': 45},
                created_date=datetime.now() - timedelta(days=90),
                expert_source=ExpertType.MOMENTUM_RIDER,
                confidence_level=0.65
            )
        ]

        # Store sample memories
        self.memory_storage['reasoning'] = reasoning_memories
        self.memory_storage['contextual'] = contextual_memories
        self.memory_storage['market'] = market_memories
        self.memory_storage['learning'] = learning_memories

    async def retrieve_memories_for_expert(
        self,
        expert_type: ExpertType,
        current_game_context: Dict[str, Any],
        current_date: datetime = None,
        max_memories: int = None
    ) -> MemoryRetrievalResult:
        """
        Retrieve relevant memories for an expert making a prediction

        Args:
            expert_type: Type of expert requesting memories
            current_game_context: Context of the game being predicted
            current_date: Current date for temporal decay calculation
            max_memories: Maximum memories to retrieve (uses expert config if None)

        Returns:
            MemoryRetrievalResult with scored and ranked memories
        """
        start_time = datetime.now()

        if current_date is None:
            current_date = datetime.now()

        config = self.config_manager.get_configuration(expert_type)
        if not config:
            raise ValueError(f"No configuration found for expert type: {expert_type}")

        # Determine memory limits
        if max_memories is None:
            max_memories = (
                config.max_reasoning_memories +
                config.max_contextual_memories +
                config.max_market_memories +
                config.max_learning_memories
            )

        # Retrieve and score memories from all types
        all_retrieved_memories = []
        total_candidates = 0

        # Get memories from sample storage
        for memory_type, memories in self.memory_storage.items():
            if not memories:
                continue

            total_candidates += len(memories)

            for memory in memories:
                # Calculate similarity score
                similarity_score = self._calculate_similarity_score(
                    current_game_context, memory, expert_type
                )

                # Calculate temporal decay and weighted score
                age_days = (current_date - memory.created_date).days
                decay_score = self.temporal_calculator.calculate_weighted_score(
                    expert_type, age_days, similarity_score
                )

                # Generate similarity explanation
                similarity_explanation = self._generate_similarity_explanation(
                    current_game_context, memory, similarity_score, expert_type
                )

                all_retrieved_memories.append(RetrievedMemory(
                    memory=memory,
                    decay_score=decay_score,
                    similarity_explanation=similarity_explanation,
                    relevance_rank=0  # Will be set after sorting
                ))

        # ALSO get memories from learning system if available
        if self.learning_memory_system and hasattr(self.learning_memory_system, 'game_memories'):
            expert_id = expert_type.value
            if expert_id in self.learning_memory_system.game_memories:
                learned_memories = self.learning_memory_system.game_memories[expert_id]
                total_candidates += len(learned_memories)

                for memory in learned_memories:
                    # Calculate similarity score
                    similarity_score = self._calculate_similarity_score(
                        current_game_context, memory, expert_type
                    )

                    # Calculate temporal decay and weighted score
                    age_days = (current_date - memory.created_date).days
                    decay_score = self.temporal_calculator.calculate_weighted_score(
                        expert_type, age_days, similarity_score
                    )

                    # Generate similarity explanation
                    similarity_explanation = self._generate_similarity_explanation(
                        current_game_context, memory, similarity_score, expert_type
                    )

                    all_retrieved_memories.append(RetrievedMemory(
                        memory=memory,
                        decay_score=decay_score,
                        similarity_explanation=similarity_explanation
                    ))

                # Generate similarity explanation
                similarity_explanation = self._generate_similarity_explanation(
                    current_game_context, memory, similarity_score, expert_type
                )

                retrieved_memory = RetrievedMemory(
                    memory=memory,
                    decay_score=decay_score,
                    similarity_explanation=similarity_explanation,
                    relevance_rank=0  # Will be set after sorting
                )

                all_retrieved_memories.append(retrieved_memory)

        # Sort by final weighted score and assign ranks
        all_retrieved_memories.sort(
            key=lambda x: x.decay_score.final_weighted_score,
            reverse=True
        )

        # Assign relevance ranks
        for i, retrieved_memory in enumerate(all_retrieved_memories):
            retrieved_memory.relevance_rank = i + 1

        # Take top memories up to limit
        top_memories = all_retrieved_memories[:max_memories]

        # Calculate retrieval time
        end_time = datetime.now()
        retrieval_time_ms = (end_time - start_time).total_seconds() * 1000

        # Generate retrieval summary
        retrieval_summary = self._generate_retrieval_summary(
            expert_type, top_memories, total_candidates, current_game_context
        )

        return MemoryRetrievalResult(
            expert_type=expert_type,
            game_context=current_game_context,
            retrieved_memories=top_memories,
            total_candidates_evaluated=total_candidates,
            retrieval_time_ms=retrieval_time_ms,
            retrieval_summary=retrieval_summary
        )

    def _calculate_similarity_score(
        self,
        current_context: Dict[str, Any],
        memory: GameMemory,
        expert_type: ExpertType
    ) -> float:
        """
        Calculate similarity score between current game and memory
        based on expert's analytical focus
        """
        config = self.config_manager.get_configuration(expert_type)
        similarity_components = []

        # Team matchup similarity - FIXED to ensure it works
        current_teams = {
            current_context.get('home_team', '').upper(),
            current_context.get('away_team', '').upper()
        }
        memory_teams = {
            memory.game_context.get('home_team', '').upper(),
            memory.game_context.get('away_team', '').upper()
        }

        # Remove empty strings
        current_teams.discard('')
        memory_teams.discard('')

        if current_teams and memory_teams:
            team_overlap = len(current_teams & memory_teams)
            team_similarity = team_overlap / 2.0  # 0, 0.5, or 1.0
            similarity_components.append(('teams', team_similarity, 0.5))

            # Debug logging
            if team_similarity > 0:
                self.logger.debug(f"🎯 Team similarity: {team_similarity:.2f} (current: {current_teams}, memory: {memory_teams})")
        else:
            # Fallback: if no team data, give some base similarity
            similarity_components.append(('teams', 0.3, 0.5))

        # Weather similarity (important for Weather Specialist)
        weather_weight = config.analytical_focus.get('weather_temperature', 0) + \
                        config.analytical_focus.get('wind_speed_direction', 0) + \
                        config.analytical_focus.get('precipitation_conditions', 0)

        if weather_weight > 1.5:  # Weather specialist
            weather_sim = self._calculate_weather_similarity(
                current_context.get('weather', {}),
                memory.game_context.get('weather', {})
            )
            similarity_components.append(('weather', weather_sim, 0.4))

        # Market similarity (important for Market Reader, Contrarian Expert)
        market_weight = config.analytical_focus.get('line_movement_patterns', 0) + \
                       config.analytical_focus.get('public_betting_percentages', 0)

        if market_weight > 1.0:  # Market-focused expert
            market_sim = self._calculate_market_similarity(
                current_context.get('line_movement', {}),
                memory.game_context.get('line_movement', {}),
                current_context.get('public_betting', {}),
                memory.game_context.get('public_betting', {})
            )
            similarity_components.append(('market', market_sim, 0.3))

        # Situational similarity (important for Situational Expert, Divisional Specialist)
        situational_weight = config.analytical_focus.get('divisional_rivalry_history', 0) + \
                           config.analytical_focus.get('playoff_implication_motivation', 0)

        if situational_weight > 1.0:  # Situational expert
            situational_sim = self._calculate_situational_similarity(
                current_context, memory.game_context
            )
            similarity_components.append(('situational', situational_sim, 0.3))

        # Calculate weighted similarity
        if not similarity_components:
            return 0.5  # Default similarity

        total_weight = sum(weight for _, _, weight in similarity_components)
        weighted_similarity = sum(
            score * weight for _, score, weight in similarity_components
        ) / total_weight

        return max(0.0, min(1.0, weighted_similarity))

    def _calculate_weather_similarity(
        self,
        current_weather: Dict[str, Any],
        memory_weather: Dict[str, Any]
    ) -> float:
        """Calculate weather condition similarity"""
        if not current_weather or not memory_weather:
            return 0.5

        # Temperature similarity
        current_temp = current_weather.get('temperature', 70)
        memory_temp = memory_weather.get('temperature', 70)
        temp_diff = abs(current_temp - memory_temp)
        temp_similarity = max(0.0, 1.0 - temp_diff / 50.0)

        # Wind similarity
        current_wind = current_weather.get('wind_speed', 0)
        memory_wind = memory_weather.get('wind_speed', 0)
        wind_diff = abs(current_wind - memory_wind)
        wind_similarity = max(0.0, 1.0 - wind_diff / 25.0)

        # Conditions similarity
        current_conditions = current_weather.get('conditions', 'clear').lower()
        memory_conditions = memory_weather.get('conditions', 'clear').lower()
        conditions_similarity = 1.0 if current_conditions == memory_conditions else 0.3

        # Weighted average
        return (temp_similarity * 0.4 + wind_similarity * 0.4 + conditions_similarity * 0.2)

    def _calculate_market_similarity(
        self,
        current_line: Dict[str, Any],
        memory_line: Dict[str, Any],
        current_public: Dict[str, Any],
        memory_public: Dict[str, Any]
    ) -> float:
        """Calculate market dynamics similarity"""
        similarities = []

        # Line movement similarity
        if current_line and memory_line:
            current_movement = current_line.get('current', 0) - current_line.get('opening', 0)
            memory_movement = memory_line.get('current', 0) - memory_line.get('opening', 0)

            # Similar direction and magnitude of movement
            if (current_movement * memory_movement) > 0:  # Same direction
                movement_similarity = max(0.0, 1.0 - abs(current_movement - memory_movement) / 7.0)
            else:
                movement_similarity = 0.2  # Opposite directions

            similarities.append(movement_similarity)

        # Public betting similarity
        if current_public and memory_public:
            current_home_pct = current_public.get('home', 50)
            memory_home_pct = memory_public.get('home', 50)

            public_diff = abs(current_home_pct - memory_home_pct)
            public_similarity = max(0.0, 1.0 - public_diff / 50.0)
            similarities.append(public_similarity)

        return sum(similarities) / len(similarities) if similarities else 0.5

    def _calculate_situational_similarity(
        self,
        current_context: Dict[str, Any],
        memory_context: Dict[str, Any]
    ) -> float:
        """Calculate situational factors similarity"""
        similarities = []

        # Division game similarity
        current_division = current_context.get('division_game', False)
        memory_division = memory_context.get('division_game', False)
        if current_division == memory_division:
            similarities.append(1.0 if current_division else 0.7)
        else:
            similarities.append(0.3)

        # Primetime game similarity
        current_primetime = current_context.get('primetime', False)
        memory_primetime = memory_context.get('primetime', False)
        if current_primetime == memory_primetime:
            similarities.append(1.0 if current_primetime else 0.8)
        else:
            similarities.append(0.4)

        # Week similarity (late season vs early season)
        current_week = current_context.get('week', 10)
        memory_week = memory_context.get('week', 10)
        week_diff = abs(current_week - memory_week)
        week_similarity = max(0.0, 1.0 - week_diff / 9.0)  # Within 9 weeks = similar
        similarities.append(week_similarity)

        return sum(similarities) / len(similarities) if similarities else 0.5

    def _generate_similarity_explanation(
        self,
        current_context: Dict[str, Any],
        memory: GameMemory,
        similarity_score: float,
        expert_type: ExpertType
    ) -> str:
        """Generate human-readable explanation of similarity"""

        explanations = []

        # Team overlap
        current_teams = {current_context.get('home_team'), current_context.get('away_team')}
        memory_teams = {memory.game_context.get('home_team'), memory.game_context.get('away_team')}
        team_overlap = current_teams & memory_teams

        if len(team_overlap) == 2:
            explanations.append("exact team matchup")
        elif len(team_overlap) == 1:
            explanations.append(f"involves {list(team_overlap)[0]}")

        # Expert-specific explanations
        config = self.config_manager.get_configuration(expert_type)

        if expert_type == ExpertType.FUNDAMENTALIST_SCHOLAR:
            # Scholar focuses on deep analytical patterns
            explanations.append("analytical pattern match")

        elif expert_type == ExpertType.CONTRARIAN_REBEL:
            # Rebel looks for contrarian opportunities
            explanations.append("contrarian opportunity identified")

        elif expert_type == ExpertType.SHARP_MONEY_FOLLOWER:
            current_line = current_context.get('line_movement', {})
            memory_line = memory.game_context.get('line_movement', {})
            if current_line and memory_line:
                explanations.append("similar sharp money pattern")

        # Similarity level description
        if similarity_score >= 0.8:
            level = "highly similar"
        elif similarity_score >= 0.6:
            level = "moderately similar"
        elif similarity_score >= 0.4:
            level = "somewhat similar"
        else:
            level = "loosely similar"

        if explanations:
            return f"{level}: {', '.join(explanations)}"
        else:
            return f"{level} game situation"

    def _generate_retrieval_summary(
        self,
        expert_type: ExpertType,
        retrieved_memories: List[RetrievedMemory],
        total_candidates: int,
        game_context: Dict[str, Any]
    ) -> str:
        """Generate summary of memory retrieval"""

        config = self.config_manager.get_configuration(expert_type)

        summary_parts = [
            f"{config.name} retrieved {len(retrieved_memories)} memories from {total_candidates} candidates"
        ]

        if retrieved_memories:
            # Memory type breakdown
            type_counts = {}
            for mem in retrieved_memories:
                mem_type = mem.memory.memory_type
                type_counts[mem_type] = type_counts.get(mem_type, 0) + 1

            type_breakdown = ", ".join([f"{count} {mem_type}" for mem_type, count in type_counts.items()])
            summary_parts.append(f"Types: {type_breakdown}")

            # Age range
            ages = [mem.decay_score.age_days for mem in retrieved_memories]
            min_age, max_age = min(ages), max(ages)
            avg_age = sum(ages) / len(ages)
            summary_parts.append(f"Age range: {min_age}-{max_age} days (avg {avg_age:.0f})")

            # Score range
            scores = [mem.decay_score.final_weighted_score for mem in retrieved_memories]
            min_score, max_score = min(scores), max(scores)
            avg_score = sum(scores) / len(scores)
            summary_parts.append(f"Scores: {min_score:.3f}-{max_score:.3f} (avg {avg_score:.3f})")

        return " | ".join(summary_parts)

    def add_memory(self, memory: GameMemory):
        """Add a new memory to storage"""
        if memory.memory_type not in self.memory_storage:
            self.memory_storage[memory.memory_type] = []

        self.memory_storage[memory.memory_type].append(memory)

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about memory storage"""
        stats = {
            'total_memories': 0,
            'by_type': {},
            'by_expert': {},
            'age_distribution': {}
        }

        current_date = datetime.now()

        for memory_type, memories in self.memory_storage.items():
            stats['by_type'][memory_type] = len(memories)
            stats['total_memories'] += len(memories)

            for memory in memories:
                # Expert source stats
                if memory.expert_source:
                    expert_key = memory.expert_source.value
                    stats['by_expert'][expert_key] = stats['by_expert'].get(expert_key, 0) + 1

                # Age distribution
                age_days = (current_date - memory.created_date).days
                if age_days <= 30:
                    age_bucket = '0-30d'
                elif age_days <= 90:
                    age_bucket = '31-90d'
                elif age_days <= 180:
                    age_bucket = '91-180d'
                else:
                    age_bucket = '180d+'

                stats['age_distribution'][age_bucket] = stats['age_distribution'].get(age_bucket, 0) + 1

        return stats


async def test_memory_retrieval_system():
    """Test the memory retrieval system"""

    print("Testing Memory Retrieval System")
    print("=" * 50)

    # Initialize components
    config_manager = ExpertConfigurationManager()
    temporal_calculator = TemporalDecayCalculator(config_manager)
    retrieval_system = MemoryRetrievalSystem(config_manager, temporal_calculator)

    # Test game context
    test_game_context = {
        'home_team': 'KC',
        'away_team': 'DEN',
        'week': 12,
        'season': 2024,
        'weather': {
            'temperature': 25,
            'wind_speed': 15,
            'conditions': 'snow'
        },
        'division_game': True,
        'line_movement': {
            'opening': -7.0,
            'current': -4.5
        },
        'public_betting': {
            'home': 72,
            'away': 28
        }
    }

    # Test different expert types
    test_experts = [
        ExpertType.FUNDAMENTALIST_SCHOLAR,
        ExpertType.CONTRARIAN_REBEL,
        ExpertType.SHARP_MONEY_FOLLOWER,
        ExpertType.MOMENTUM_RIDER
    ]

    print(f"Test Game: {test_game_context['away_team']} @ {test_game_context['home_team']}")
    print(f"Conditions: {test_game_context['weather']['temperature']}°F, {test_game_context['weather']['conditions']}")
    print()

    for expert_type in test_experts:
        print(f"Testing {expert_type.value.replace('_', ' ').title()}:")

        result = await retrieval_system.retrieve_memories_for_expert(
            expert_type, test_game_context, max_memories=3
        )

        print(f"  {result.retrieval_summary}")

        for i, retrieved_mem in enumerate(result.retrieved_memories, 1):
            print(f"  {i}. {retrieved_mem}")
            print(f"     {retrieved_mem.similarity_explanation}")
            print(f"     Content: {retrieved_mem.memory.content[:80]}...")

        print()

    # Storage stats
    stats = retrieval_system.get_storage_stats()
    print("Memory Storage Statistics:")
    print(f"  Total memories: {stats['total_memories']}")
    print(f"  By type: {stats['by_type']}")
    print(f"  By expert: {stats['by_expert']}")
    print(f"  Age distribution: {stats['age_distribution']}")


if __name__ == "__main__":
    asyncio.run(test_memory_retrieval_system())
