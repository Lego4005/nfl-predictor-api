#!/usr/bin/env python3
"""
Expert Learning Memory System

This system handles the post-game reflection and learning process where experts:
1. Analyze their prediction vs actual outcome
2. Generate thoughts on what they got right/wrong
3. Store structured memorteam, matchup, and personal patterns
4. Learn from mistakes to improve future predictions
"""

import sys
import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
sys.path.append('src')

from training.expert_configuration import ExpertType, ExpertConfigurationManager
from training.prediction_generator import GamePrediction, PredictionType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """Types of memories experts can form"""
    TEAM_PATTERN = "team_pattern"  # e.g., "Chiefs struggle in cold weather"
    MATCHUP_HISTORY = "matchup_history"  # e.g., "Patriots vs Bills always close"
    PERSONAL_SUCCESS = "personal_success"  # e.g., "I'm good at predicting underdogs"
    PERSONAL_FAILURE = "personal_failure"  # e.g., "I overvalue momentum in divisional games"
    CONTEXTUAL_INSIGHT = "contextual_insight"  # e.g., "Weather matters more in December"
    MARKET_PATTERN = "market_pattern"  # e.g., "Public always overvalues home teams"

@dataclass
class LearningReflection:
    """Expert's reflection on their prediction vs outcome"""
    expert_id: str
    game_id: str
    prediction: GamePrediction
    actual_outcome: Dict[str, Any]

    # Reflection analysis
    was_correct: bool
    confidence_calibration: float  # How well calibrated was confidence
    key_factors_validated: List[str]
    key_factors_contradicted: List[str]

    # Learning insights
    what_went_right: List[str]
    what_went_wrong: List[str]
    lessons_learned: List[str]
    confidence_adjustment: float  # How to adjust confidence for similar situations

    # Generated thoughts (from LLM)
    reflection_thoughts: str
    future_adjustments: str

    # Memory formation results
    personal_memories_formed: List[str] = None
    team_memories_formed: List[str] = None
    matchup_memories_formed: List[str] = None

    def __post_init__(self):
        if self.personal_memories_formed is None:
            self.personal_memories_formed = []
        if self.team_memories_formed is None:
            self.team_memories_formed = []
        if self.matchup_memories_formed is None:
            self.matchup_memories_formed = []

@dataclass
class StructuredMemory:
    """A structured memory that experts form from experiences"""
    memory_id: str
    expert_id: str
    memory_type: MemoryType

    # Core content
    memory_title: str
    memory_content: str
    confidence_level: float

    # Context tags for retrieval
    teams_involved: List[str]
    game_context_tags: List[str]  # e.g., ["cold_weather", "divisional", "primetime"]

    # Supporting data
    supporting_games: List[str]  # Game IDs that support this memory
    contradicting_games: List[str]  # Game IDs that contradict this memory

    # Metadata
    created_date: datetime
    last_reinforced: datetime
    reinforcement_count: int
    memory_strength: float  # 0.0 to 1.0

@dataclass
class TeamMemoryBank:
    """Memory bank for a specific team"""
    team_name: str
    expert_id: str

    # Team-specific patterns
    strengths: List[StructuredMemory]
    weaknesses: List[StructuredMemory]
    contextual_patterns: List[StructuredMemory]  # Weather, home/away, etc.

    # Performance tracking
    prediction_accuracy_vs_team: float
    games_analyzed: int
    last_updated: datetime

@dataclass
class MatchupMemoryBank:
    """Memory bank for team vs team matchups"""
    team_a: str
    team_b: str
    expert_id: str

    # Matchup patterns
    historical_patterns: List[StructuredMemory]
    rivalry_factors: List[StructuredMemory]

    # Performance tracking
    prediction_accuracy_in_matchup: float
    games_analyzed: int
    last_updated: datetime

class ExpertLearningMemorySystem:
    """Manages expert learning and memory formation after each game"""

    def __init__(self, config_manager: ExpertConfigurationManager):
        """Initialize the learning memory system"""
        self.config_manager = config_manager

        # Memory storage (in production, this would be a database)
        self.team_memories: Dict[str, Dict[str, TeamMemoryBank]] = {}  # expert_id -> team -> memories
        self.matchup_memories: Dict[str, Dict[str, MatchupMemoryBank]] = {}  # expert_id -> matchup_key -> memories
        self.personal_memories: Dict[str, List[StructuredMemory]] = {}  # expert_id -> memories

        logger.info("✅ Expert Learning Memory System initialized")

    async def process_post_game_learning(self, expert_id: str, game_context: Dict[str, Any],
                                       prediction: GamePrediction, actual_outcome: Dict[str, Any]) -> LearningReflection:
        """Process post-game learning for an expert"""
        logger.info(f"🧠 Processing post-game learning for {expert_id}")

        # Validate inputs
        if actual_outcome is None:
            logger.error(f"❌ actual_outcome is None for {expert_id}")
            raise ValueError(f"actual_outcome cannot be None for expert {expert_id}")

        if not isinstance(actual_outcome, dict):
            logger.error(f"❌ actual_outcome is not a dict for {expert_id}: {type(actual_outcome)}")
            raise ValueError(f"actual_outcome must be a dict for expert {expert_id}")

        # Ensure required keys exist
        required_keys = ['home_score', 'away_score']
        for key in required_keys:
            if key not in actual_outcome:
                logger.error(f"❌ Missing required key '{key}' in actual_outcome for {expert_id}")
                raise ValueError(f"actual_outcome missing required key '{key}' for expert {expert_id}")

        try:
            # 1. Generate expert's reflection on their prediction
            reflection = await self._generate_expert_reflection(expert_id, game_context, prediction, actual_outcome)

            # 2. Form structured memories from the experience
            await self._form_structured_memories(reflection, game_context)

            # 3. Update team and matchup memory banks
            await self._update_memory_banks(reflection, game_context)

            # 4. Adjust expert's confidence patterns
            await self._adjust_confidence_patterns(reflection)

            # Log detailed post-game analysis (after memories are formed)
            await self._log_detailed_post_game_analysis(expert_id, game_context, prediction, actual_outcome, reflection)

            logger.info(f"✅ Post-game learning completed for {expert_id}")
            return reflection

        except Exception as e:
            logger.error(f"❌ Post-game learning failed for {expert_id}: {e}")
            raise

    async def _generate_expert_reflection(self, expert_id: str, game_context: Dict[str, Any],
                                        prediction: GamePrediction, actual_outcome: Dict[str, Any]) -> LearningReflection:
        """Generate expert's reflection using their personality"""

        # Determine if prediction was correct
        home_score = actual_outcome.get('home_score', 0)
        away_score = actual_outcome.get('away_score', 0)
        actual_winner = 'home' if home_score > away_score else 'away'
        predicted_winner = 'home' if prediction.win_probability > 0.5 else 'away'
        was_correct = (actual_winner == predicted_winner)

        # Calculate confidence calibration
        confidence_calibration = self._calculate_confidence_calibration(prediction.confidence_level, was_correct)

        # Analyze factors that were validated or contradicted
        validated_factors, contradicted_factors = self._analyze_prediction_factors(
            prediction, game_context, actual_outcome
        )

        # Generate expert-specific reflection thoughts (this would be an LLM call in production)
        reflection_thoughts = await self._generate_reflection_thoughts(
            expert_id, prediction, actual_outcome, was_correct, game_context
        )

        # Generate future adjustment thoughts
        future_adjustments = await self._generate_future_adjustments(
            expert_id, prediction, actual_outcome, was_correct, validated_factors, contradicted_factors
        )

        # Determine what went right/wrong
        what_went_right, what_went_wrong = self._analyze_prediction_accuracy(
            prediction, actual_outcome, validated_factors, contradicted_factors
        )

        # Generate lessons learned
        lessons_learned = self._extract_lessons_learned(
            expert_id, what_went_right, what_went_wrong, game_context
        )

        # Calculate confidence adjustment for similar situations
        confidence_adjustment = self._calculate_confidence_adjustment(
            was_correct, confidence_calibration, prediction.confidence_level
        )

        return LearningReflection(
            expert_id=expert_id,
            game_id=game_context.get('game_id', 'unknown'),
            prediction=prediction,
            actual_outcome=actual_outcome,
            was_correct=was_correct,
            confidence_calibration=confidence_calibration,
            key_factors_validated=validated_factors,
            key_factors_contradicted=contradicted_factors,
            what_went_right=what_went_right,
            what_went_wrong=what_went_wrong,
            lessons_learned=lessons_learned,
            confidence_adjustment=confidence_adjustment,
            reflection_thoughts=reflection_thoughts,
            future_adjustments=future_adjustments
        )

    async def _generate_reflection_thoughts(self, expert_id: str, prediction: GamePrediction,
                                          actual_outcome: Dict[str, Any], was_correct: bool,
                                          game_context: Dict[str, Any]) -> str:
        """Generate expert's reflection thoughts (would be LLM call in production)"""

        # This is a simplified version - in production this would be an LLM call
        # with the expert's personality prompt

        expert_type = ExpertType(expert_id)
        config = self.config_manager.get_configuration(expert_type)

        home_team = game_context.get('home_team', 'HOME')
        away_team = game_context.get('away_team', 'AWAY')
        final_score = f"{actual_outcome.get('away_score', 0)}-{actual_outcome.get('home_score', 0)}"

        if was_correct:
            if expert_type == ExpertType.CHAOS_THEORY_BELIEVER:
                return f"Even a broken clock is right twice a day. The chaos of {away_team} @ {home_team} ({final_score}) aligned with my low-confidence prediction. But this doesn't validate any system - it's just random chance working in my favor."

            elif expert_type == ExpertType.CONTRARIAN_REBEL:
                return f"BOOM! Faded the public on {away_team} @ {home_team} and it paid off ({final_score}). The sheep followed the obvious narrative while I saw the contrarian value. This is why you always bet against the crowd."

            elif expert_type == ExpertType.MOMENTUM_RIDER:
                return f"Momentum never lies! Rode the hot streak in {away_team} @ {home_team} to victory ({final_score}). When you see momentum building, you jump on the train. The trend was clear and I trusted it."

            else:
                return f"My analysis of {away_team} @ {home_team} proved correct ({final_score}). The factors I identified played out as expected, validating my analytical approach."

        else:
            if expert_type == ExpertType.CHAOS_THEORY_BELIEVER:
                return f"As expected, chaos reigned in {away_team} @ {home_team} ({final_score}). My prediction was wrong, but that's the point - NFL games are inherently unpredictable. The butterfly effect struck again."

            elif expert_type == ExpertType.CONTRARIAN_REBEL:
                return f"Sometimes the public gets lucky. My contrarian play on {away_team} @ {home_team} didn't hit ({final_score}), but that doesn't mean the approach is wrong. You can't fade every game - need to pick spots better."

            elif expert_type == ExpertType.MOMENTUM_RIDER:
                return f"Momentum shifted unexpectedly in {away_team} @ {home_team} ({final_score}). What looked like a clear trend broke down. Need to better identify when momentum is fragile vs sustainable."

            else:
                return f"My analysis of {away_team} @ {home_team} was flawed ({final_score}). Need to examine what factors I missed or overweighted in my prediction model."

    async def _generate_future_adjustments(self, expert_id: str, prediction: GamePrediction,
                                         actual_outcome: Dict[str, Any], was_correct: bool,
                                         validated_factors: List[str], contradicted_factors: List[str]) -> str:
        """Generate expert's thoughts on future adjustments"""

        expert_type = ExpertType(expert_id)

        if was_correct:
            if validated_factors:
                return f"Continue emphasizing {', '.join(validated_factors[:2])} in similar situations. These factors proved predictive and should maintain high weight in my analysis."
            else:
                return "While I was correct, need to better understand which specific factors drove the outcome to improve future confidence calibration."

        else:
            adjustments = []

            if contradicted_factors:
                adjustments.append(f"Reduce weight on {', '.join(contradicted_factors[:2])} in similar contexts")

            if expert_type == ExpertType.MOMENTUM_RIDER and 'momentum' in contradicted_factors:
                adjustments.append("Develop better momentum sustainability indicators")

            elif expert_type == ExpertType.CONTRARIAN_REBEL and 'public_betting' in contradicted_factors:
                adjustments.append("Refine contrarian timing - not every public favorite is a fade")

            # Removed WEATHER_SPECIALIST reference - expert type no longer exists

            if not adjustments:
                adjustments.append("Conduct deeper analysis of missed factors in this game type")

            return "; ".join(adjustments)

    def _calculate_confidence_calibration(self, predicted_confidence: float, was_correct: bool) -> float:
        """Calculate how well calibrated the expert's confidence was"""
        if was_correct:
            return predicted_confidence  # Higher confidence for correct predictions is good
        else:
            return 1.0 - predicted_confidence  # Lower confidence for incorrect predictions is good

    def _analyze_prediction_factors(self, prediction: GamePrediction, game_context: Dict[str, Any],
                                  actual_outcome: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Analyze which factors were validated or contradicted by the outcome"""
        validated = []
        contradicted = []

        # Analyze reasoning chain factors
        reasoning_text = ' '.join(prediction.reasoning_chain).lower()

        # Weather factors
        if 'weather' in reasoning_text or 'temperature' in reasoning_text or 'wind' in reasoning_text:
            weather = game_context.get('weather', {})
            total_points = actual_outcome.get('home_score', 0) + actual_outcome.get('away_score', 0)

            if weather.get('temperature', 70) < 40 or weather.get('wind_speed', 0) > 15:
                if total_points < 45:
                    validated.append('weather_impact')
                else:
                    contradicted.append('weather_impact')

        # Momentum factors
        if 'momentum' in reasoning_text or 'hot' in reasoning_text or 'streak' in reasoning_text:
            # This would need more sophisticated momentum tracking
            validated.append('momentum_analysis')

        # Public betting factors
        if 'public' in reasoning_text or 'contrarian' in reasoning_text:
            validated.append('public_betting_analysis')

        # Home field advantage
        if 'home' in reasoning_text and 'advantage' in reasoning_text:
            home_won = actual_outcome.get('home_score', 0) > actual_outcome.get('away_score', 0)
            if home_won:
                validated.append('home_field_advantage')
            else:
                contradicted.append('home_field_advantage')

        return validated, contradicted

    def _analyze_prediction_accuracy(self, prediction: GamePrediction, actual_outcome: Dict[str, Any],
                                   validated_factors: List[str], contradicted_factors: List[str]) -> Tuple[List[str], List[str]]:
        """Analyze what went right and wrong with the prediction"""
        what_went_right = []
        what_went_wrong = []

        # Winner prediction analysis
        home_score = actual_outcome.get('home_score', 0)
        away_score = actual_outcome.get('away_score', 0)
        actual_winner = 'home' if home_score > away_score else 'away'
        predicted_winner = 'home' if prediction.win_probability > 0.5 else 'away'

        if actual_winner == predicted_winner:
            what_went_right.append(f"Correctly predicted {predicted_winner} team would win")

            # Add validated factors
            for factor in validated_factors:
                what_went_right.append(f"Correctly weighted {factor.replace('_', ' ')}")
        else:
            what_went_wrong.append(f"Incorrectly predicted {predicted_winner} team would win")

            # Add contradicted factors
            for factor in contradicted_factors:
                what_went_wrong.append(f"Overweighted {factor.replace('_', ' ')}")

        # Confidence analysis
        if prediction.confidence_level > 0.7:
            if actual_winner == predicted_winner:
                what_went_right.append("High confidence was justified")
            else:
                what_went_wrong.append("Overconfident in incorrect prediction")
        elif prediction.confidence_level < 0.3:
            if actual_winner != predicted_winner:
                what_went_right.append("Low confidence protected against wrong prediction")
            else:
                what_went_wrong.append("Underconfident in correct prediction")

        return what_went_right, what_went_wrong

    def _extract_lessons_learned(self, expert_id: str, what_went_right: List[str],
                               what_went_wrong: List[str], game_context: Dict[str, Any]) -> List[str]:
        """Extract key lessons from the prediction experience"""
        lessons = []

        expert_type = ExpertType(expert_id)

        # Expert-specific lesson extraction
        if expert_type == ExpertType.MOMENTUM_RIDER:
            if any('momentum' in wrong for wrong in what_went_wrong):
                lessons.append("Momentum can be disrupted by unexpected factors - need better sustainability indicators")
            if any('momentum' in right for right in what_went_right):
                lessons.append("Momentum analysis was on point - continue trusting established trends")

        elif expert_type == ExpertType.CONTRARIAN_REBEL:
            if any('public' in wrong for wrong in what_went_wrong):
                lessons.append("Not every public favorite is a fade - need better contrarian timing")
            if any('contrarian' in right for right in what_went_right):
                lessons.append("Contrarian approach paid off - public was wrong as expected")

        # Removed WEATHER_SPECIALIST reference - expert type no longer exists
            if any('weather' in right for right in what_went_right):
                lessons.append("Weather analysis was accurate - continue emphasizing environmental factors")

        # General lessons
        if len(what_went_wrong) > len(what_went_right):
            lessons.append("Need to reassess analytical approach for this game type")

        if not lessons:
            lessons.append("Continue current analytical approach with minor confidence adjustments")

        return lessons

    def _calculate_confidence_adjustment(self, was_correct: bool, confidence_calibration: float,
                                       original_confidence: float) -> float:
        """Calculate how to adjust confidence for similar future situations"""

        if was_correct:
            if original_confidence < 0.5:
                return 0.1  # Increase confidence for correct low-confidence predictions
            else:
                return 0.0  # Maintain confidence for correct high-confidence predictions
        else:
            if original_confidence > 0.7:
                return -0.15  # Significantly reduce confidence for overconfident wrong predictions
            elif original_confidence > 0.5:
                return -0.05  # Slightly reduce confidence for moderately confident wrong predictions
            else:
                return 0.0  # Don't penalize low-confidence wrong predictions much

    async def _form_structured_memories(self, reflection: LearningReflection, game_context: Dict[str, Any]):
        """Form structured memories from the learning experience"""

        home_team = game_context.get('home_team', 'HOME')
        away_team = game_context.get('away_team', 'AWAY')
        expert_id = reflection.expert_id

        memories_to_create = []

        # Create team-specific memories
        if reflection.what_went_right:
            for insight in reflection.what_went_right[:2]:  # Limit to top insights
                if 'home' in insight.lower():
                    memory = self._create_team_memory(
                        expert_id, home_team, insight, MemoryType.TEAM_PATTERN,
                        game_context, True
                    )
                    memories_to_create.append(memory)
                    reflection.team_memories_formed.append(f"{home_team}: {insight[:50]}...")
                elif 'away' in insight.lower():
                    memory = self._create_team_memory(
                        expert_id, away_team, insight, MemoryType.TEAM_PATTERN,
                        game_context, True
                    )
                    memories_to_create.append(memory)
                    reflection.team_memories_formed.append(f"{away_team}: {insight[:50]}...")

        # Create failure memories for learning
        if reflection.what_went_wrong:
            for mistake in reflection.what_went_wrong[:2]:
                memory = self._create_personal_memory(
                    expert_id, mistake, MemoryType.PERSONAL_FAILURE,
                    game_context, False
                )
                memories_to_create.append(memory)
                reflection.personal_memories_formed.append(f"Failure: {mistake[:50]}...")

        # Create contextual memories
        if reflection.lessons_learned:
            for lesson in reflection.lessons_learned[:1]:  # One key lesson
                memory = self._create_contextual_memory(
                    expert_id, lesson, game_context
                )
                memories_to_create.append(memory)
                reflection.personal_memories_formed.append(f"Lesson: {lesson[:50]}...")

        # Create matchup memory if this was a significant game
        if reflection.was_correct and reflection.confidence_calibration > 0.7:
            matchup_insight = f"Successful prediction in {away_team} @ {home_team} matchup"
            reflection.matchup_memories_formed.append(matchup_insight)

        # Store memories
        for memory in memories_to_create:
            await self._store_memory(memory)

    def _create_team_memory(self, expert_id: str, team: str, insight: str,
                          memory_type: MemoryType, game_context: Dict[str, Any],
                          positive: bool) -> StructuredMemory:
        """Create a team-specific memory"""

        memory_id = f"{expert_id[:8]}_{datetime.now().strftime('%m%d_%H%M%S')}"

        # Generate context tags
        context_tags = []
        if game_context.get('weather', {}).get('temperature', 70) < 40:
            context_tags.append('cold_weather')
        if game_context.get('division_game'):
            context_tags.append('divisional')
        if game_context.get('week', 0) > 14:
            context_tags.append('late_season')

        return StructuredMemory(
            memory_id=memory_id,
            expert_id=expert_id,
            memory_type=memory_type,
            memory_title=f"{team} pattern: {insight[:50]}...",
            memory_content=insight,
            confidence_level=0.7 if positive else 0.3,
            teams_involved=[team],
            game_context_tags=context_tags,
            supporting_games=[game_context.get('game_id', 'unknown')],
            contradicting_games=[],
            created_date=datetime.now(),
            last_reinforced=datetime.now(),
            reinforcement_count=1,
            memory_strength=0.6
        )

    def _create_personal_memory(self, expert_id: str, insight: str, memory_type: MemoryType,
                              game_context: Dict[str, Any], positive: bool) -> StructuredMemory:
        """Create a personal learning memory"""

        memory_id = f"{expert_id[:8]}_p_{datetime.now().strftime('%m%d_%H%M%S')}"

        return StructuredMemory(
            memory_id=memory_id,
            expert_id=expert_id,
            memory_type=memory_type,
            memory_title=f"Personal insight: {insight[:50]}...",
            memory_content=insight,
            confidence_level=0.8 if positive else 0.4,
            teams_involved=[game_context.get('home_team', ''), game_context.get('away_team', '')],
            game_context_tags=['personal_learning'],
            supporting_games=[game_context.get('game_id', 'unknown')],
            contradicting_games=[],
            created_date=datetime.now(),
            last_reinforced=datetime.now(),
            reinforcement_count=1,
            memory_strength=0.7
        )

    def _create_contextual_memory(self, expert_id: str, lesson: str, game_context: Dict[str, Any]) -> StructuredMemory:
        """Create a contextual insight memory"""

        memory_id = f"{expert_id[:8]}_c_{datetime.now().strftime('%m%d_%H%M%S')}"

        return StructuredMemory(
            memory_id=memory_id,
            expert_id=expert_id,
            memory_type=MemoryType.CONTEXTUAL_INSIGHT,
            memory_title=f"Context lesson: {lesson[:50]}...",
            memory_content=lesson,
            confidence_level=0.6,
            teams_involved=[game_context.get('home_team', ''), game_context.get('away_team', '')],
            game_context_tags=['contextual_learning'],
            supporting_games=[game_context.get('game_id', 'unknown')],
            contradicting_games=[],
            created_date=datetime.now(),
            last_reinforced=datetime.now(),
            reinforcement_count=1,
            memory_strength=0.5
        )

    async def _store_memory(self, memory: StructuredMemory):
        """Store a structured memory in database and local cache"""

        # Store in local cache for immediate access
        if memory.expert_id not in self.personal_memories:
            self.personal_memories[memory.expert_id] = []
        self.personal_memories[memory.expert_id].append(memory)

        # Store in database for persistence
        try:
            await self._store_memory_in_database(memory)
            logger.debug(f"💾 Stored {memory.memory_type.value} memory for {memory.expert_id}: {memory.memory_title}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to store memory in database: {e}")

        # Also convert to GameMemory format for retrieval system compatibility
        from training.memory_retrieval_system import GameMemory
        from training.expert_configuration import ExpertType

        try:
            expert_type = ExpertType(memory.expert_id)
            game_memory = GameMemory(
                memory_id=memory.memory_id,
                memory_type=memory.memory_type.value,
                content=memory.memory_content,  # Fixed: use 'content' not 'memory_content'
                game_context={
                    'teams_involved': memory.teams_involved,
                    'context_tags': memory.game_context_tags,
                    'home_team': memory.teams_involved[0] if memory.teams_involved else '',
                    'away_team': memory.teams_involved[1] if len(memory.teams_involved) > 1 else ''
                },
                outcome_data=None,
                created_date=memory.created_date,
                expert_source=expert_type,
                confidence_level=memory.confidence_level
            )

            # Store in format compatible with memory retrieval system
            if not hasattr(self, 'game_memories'):
                self.game_memories = {}
            if memory.expert_id not in self.game_memories:
                self.game_memories[memory.expert_id] = []
            self.game_memories[memory.expert_id].append(game_memory)

        except Exception as e:
            logger.warning(f"⚠️ Failed to create GameMemory format: {e}")

    async def _store_memory_in_database(self, memory: StructuredMemory):
        """Store memory in the database"""

        # Get database connection
        supabase = self._get_supabase_client()
        if not supabase:
            logger.warning("⚠️ No database connection available for memory storage")
            return

        # Prepare memory data for database (using actual column names)
        memory_data = {
            'memory_id': memory.memory_id,
            'expert_id': memory.expert_id,
            'game_id': memory.supporting_games[0] if memory.supporting_games else 'unknown',
            'memory_type': memory.memory_type.value,
            'prediction_summary': memory.memory_title[:100],
            'lesson_learned': memory.memory_content,
            'actual_outcome': {},  # Required field - empty dict for now
            'memory_strength': memory.confidence_level,
            'contextual_factors': {
                'teams_involved': memory.teams_involved,
                'game_context_tags': memory.game_context_tags
            },
            'emotional_weight': memory.memory_strength,
            'memory_vividness': min(memory.reinforcement_count / 10.0, 1.0),
            'surprise_factor': 0.5,
            # New columns added by migration
            'teams_involved': memory.teams_involved,
            'game_context_tags': memory.game_context_tags,
            'supporting_games': memory.supporting_games,
            'contradicting_games': memory.contradicting_games,
            'reinforcement_count': memory.reinforcement_count,
            'last_reinforced': memory.last_reinforced.isoformat()
        }

        # Store in expert_episodic_memories table
        result = supabase.table('expert_episodic_memories').insert(memory_data).execute()

        if result.data:
            logger.debug(f"✅ Memory stored in database: {memory.memory_id}")
        else:
            logger.warning(f"⚠️ Failed to store memory in database: {memory.memory_id}")

    async def _store_team_knowledge_in_database(self, expert_id: str, team: str,
                                              bank: TeamMemoryBank, reflection: LearningReflection):
        """Store team knowledge in database"""

        supabase = self._get_supabase_client()
        if not supabase:
            return

        try:
            # Prepare team knowledge data (using correct column names)
            team_data = {
                'expert_id': expert_id,
                'team_id': team,
                'current_injuries': {},
                'player_stats': {},
                'home_advantage_factors': {},
                'coaching_tendencies': {},
                'pattern_confidence_scores': {
                    'strengths': [s.memory_content for s in bank.strengths] if bank.strengths else [],
                    'weaknesses': [w.memory_content for w in bank.weaknesses] if bank.weaknesses else []
                },
                # New columns added by migration
                'team_trends': {
                    'prediction_accuracy': bank.prediction_accuracy_vs_team,
                    'games_analyzed': bank.games_analyzed
                },
                'weather_preferences': {},
                'recent_performance': {
                    'accuracy': bank.prediction_accuracy_vs_team,
                    'games': bank.games_analyzed,
                    'last_updated': bank.last_updated.isoformat()
                }
            }

            # Upsert team knowledge (update if exists, insert if not)
            result = supabase.table('team_knowledge').upsert(team_data, on_conflict='expert_id,team_id').execute()

            if result.data:
                logger.debug(f"✅ Team knowledge updated for {expert_id} - {team}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to store team knowledge: {e}")

    async def _store_matchup_memory_in_database(self, expert_id: str, team_a: str, team_b: str,
                                              reflection: LearningReflection, game_context: Dict[str, Any]):
        """Store matchup memory in database"""

        supabase = self._get_supabase_client()
        if not supabase:
            return

        try:
            # Create matchup key (consistent ordering)
            from src.utils.team_name_standardizer import create_matchup_key
            matchup_key = create_matchup_key(team_a, team_b)

            # Prepare matchup memory data (using correct column names)
            matchup_data = {
                'expert_id': expert_id,
                'matchup_id': matchup_key,
                'game_date': datetime.now().date().isoformat(),  # Convert date to string
                # Existing columns
                'pre_game_analysis': {
                    'prediction_confidence': reflection.prediction.confidence_level,
                    'reasoning': reflection.prediction.reasoning_chain
                },
                'predictions': {
                    'predicted_winner': reflection.prediction.predicted_winner,
                    'confidence': reflection.prediction.confidence_level
                },
                'actual_results': reflection.actual_outcome,
                'post_game_insights': {
                    'what_went_right': reflection.what_went_right,
                    'what_went_wrong': reflection.what_went_wrong,
                    'lessons_learned': reflection.lessons_learned
                },
                'accuracy_scores': {
                    'correct': reflection.was_correct,
                    'confidence_calibration': reflection.confidence_calibration
                },
                'learning_updates': {
                    'confidence_adjustment': reflection.confidence_adjustment
                },
                # New columns added by migration
                'team_a_id': team_a,
                'team_b_id': team_b,
                'historical_outcomes': {
                    'game_result': reflection.actual_outcome,
                    'prediction_correct': reflection.was_correct
                },
                'pattern_insights': {
                    'prediction_confidence': reflection.prediction.confidence_level,
                    'accuracy': 1.0 if reflection.was_correct else 0.0
                },
                'rivalry_factors': {},
                'weather_impact': {},
                'venue_advantages': {},
                'recent_trends': {
                    'games_analyzed': 1,
                    'last_meeting': datetime.now().isoformat()
                }
            }

            # Insert matchup memory
            result = supabase.table('matchup_memories').insert(matchup_data).execute()

            if result.data:
                logger.debug(f"✅ Matchup memory stored for {expert_id}: {matchup_key}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to store matchup memory: {e}")

    def _get_supabase_client(self):
        """Get Supabase client for database operations"""
        try:
            import os
            from supabase import create_client

            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')

            if not supabase_url or not supabase_key:
                return None

            return create_client(supabase_url, supabase_key)
        except Exception as e:
            logger.warning(f"⚠️ Failed to create Supabase client: {e}")
            return None

    async def _update_memory_banks(self, reflection: LearningReflection, game_context: Dict[str, Any]):
        """Update team and matchup memory banks"""

        home_team = game_context.get('home_team', 'HOME')
        away_team = game_context.get('away_team', 'AWAY')
        expert_id = reflection.expert_id

        # Update team memory banks
        await self._update_team_memory_bank(expert_id, home_team, reflection, game_context)
        await self._update_team_memory_bank(expert_id, away_team, reflection, game_context)

        # Update matchup memory bank
        await self._update_matchup_memory_bank(expert_id, home_team, away_team, reflection, game_context)

    async def _update_team_memory_bank(self, expert_id: str, team: str,
                                     reflection: LearningReflection, game_context: Dict[str, Any]):
        """Update memory bank for a specific team"""

        # Initialize if needed
        if expert_id not in self.team_memories:
            self.team_memories[expert_id] = {}

        if team not in self.team_memories[expert_id]:
            self.team_memories[expert_id][team] = TeamMemoryBank(
                team_name=team,
                expert_id=expert_id,
                strengths=[],
                weaknesses=[],
                contextual_patterns=[],
                prediction_accuracy_vs_team=0.0,
                games_analyzed=0,
                last_updated=datetime.now()
            )

        bank = self.team_memories[expert_id][team]

        # Update accuracy tracking
        bank.games_analyzed += 1
        if reflection.was_correct:
            bank.prediction_accuracy_vs_team = (
                (bank.prediction_accuracy_vs_team * (bank.games_analyzed - 1) + 1.0) / bank.games_analyzed
            )
        else:
            bank.prediction_accuracy_vs_team = (
                (bank.prediction_accuracy_vs_team * (bank.games_analyzed - 1) + 0.0) / bank.games_analyzed
            )

        bank.last_updated = datetime.now()

        # Store team knowledge in database
        await self._store_team_knowledge_in_database(expert_id, team, bank, reflection)

    async def _update_matchup_memory_bank(self, expert_id: str, team_a: str, team_b: str,
                                        reflection: LearningReflection, game_context: Dict[str, Any]):
        """Update memory bank for team vs team matchups"""

        # Create consistent matchup key
        matchup_key = f"{min(team_a, team_b)}_vs_{max(team_a, team_b)}"

        # Initialize if needed
        if expert_id not in self.matchup_memories:
            self.matchup_memories[expert_id] = {}

        if matchup_key not in self.matchup_memories[expert_id]:
            self.matchup_memories[expert_id][matchup_key] = MatchupMemoryBank(
                team_a=team_a,
                team_b=team_b,
                expert_id=expert_id,
                historical_patterns=[],
                rivalry_factors=[],
                prediction_accuracy_in_matchup=0.0,
                games_analyzed=0,
                last_updated=datetime.now()
            )

        bank = self.matchup_memories[expert_id][matchup_key]

        # Update accuracy tracking
        bank.games_analyzed += 1
        if reflection.was_correct:
            bank.prediction_accuracy_in_matchup = (
                (bank.prediction_accuracy_in_matchup * (bank.games_analyzed - 1) + 1.0) / bank.games_analyzed
            )
        else:
            bank.prediction_accuracy_in_matchup = (
                (bank.prediction_accuracy_in_matchup * (bank.games_analyzed - 1) + 0.0) / bank.games_analyzed
            )

        bank.last_updated = datetime.now()

        # Store matchup memory in database
        await self._store_matchup_memory_in_database(expert_id, team_a, team_b, reflection, game_context)

    async def _adjust_confidence_patterns(self, reflection: LearningReflection):
        """Adjust expert's confidence patterns based on learning"""

        # This would update the expert's configuration in production
        # For now, just log the adjustment

        if abs(reflection.confidence_adjustment) > 0.05:
            logger.info(f"📊 {reflection.expert_id} confidence adjustment: {reflection.confidence_adjustment:+.3f}")

    async def _log_detailed_post_game_analysis(self, expert_id: str, game_context: Dict[str, Any],
                                             prediction: GamePrediction, actual_outcome: Dict[str, Any],
                                             reflection: LearningReflection):
        """Log detailed post-game analysis for expert decision-making transparency"""

        home_team = game_context.get('home_team', 'HOME')
        away_team = game_context.get('away_team', 'AWAY')

        # Determine if prediction was correct
        actual_winner = 'home' if actual_outcome['home_score'] > actual_outcome['away_score'] else 'away'

        # Debug logging for prediction analysis
        logger.debug(f"🔍 DEBUG - {expert_id}:")
        logger.debug(f"   prediction.predicted_winner: {prediction.predicted_winner}")
        logger.debug(f"   home_team: {home_team}, away_team: {away_team}")
        logger.debug(f"   actual_winner: {actual_winner}")

        # Handle None prediction case
        if prediction.predicted_winner is None:
            # Fallback to win_probability
            predicted_winner = 'home' if prediction.win_probability and prediction.win_probability > 0.5 else 'away'
            logger.debug(f"   Using win_probability fallback: {predicted_winner} (prob: {prediction.win_probability})")
        else:
            predicted_winner = 'home' if prediction.predicted_winner == home_team else 'away'
            logger.debug(f"   Using predicted_winner: {predicted_winner}")

        was_correct = (actual_winner == predicted_winner)
        logger.debug(f"   Final: predicted={predicted_winner}, actual={actual_winner}, correct={was_correct}")

        logger.info(f"🎯 POST-GAME ANALYSIS - {expert_id} for {away_team} @ {home_team}")
        logger.info(f"   📊 PREDICTION: {prediction.predicted_winner} ({prediction.confidence_level:.1%} confidence)")
        logger.info(f"   🏆 ACTUAL: {home_team if actual_winner == 'home' else away_team} won {actual_outcome['home_score']}-{actual_outcome['away_score']}")
        logger.info(f"   ✅ RESULT: {'CORRECT' if was_correct else 'INCORRECT'}")

        # Log what the expert learned
        if reflection.what_went_right:
            logger.info(f"   💡 WHAT WENT RIGHT:")
            for insight in reflection.what_went_right[:3]:  # Top 3 insights
                logger.info(f"      • {insight}")

        if reflection.what_went_wrong:
            logger.info(f"   ❌ WHAT WENT WRONG:")
            for mistake in reflection.what_went_wrong[:3]:  # Top 3 mistakes
                logger.info(f"      • {mistake}")

        if reflection.lessons_learned:
            logger.info(f"   🧠 LESSONS LEARNED:")
            for lesson in reflection.lessons_learned[:2]:  # Top 2 lessons
                logger.info(f"      • {lesson}")

        # Log confidence adjustment
        if reflection.confidence_adjustment != 0:
            direction = "increased" if reflection.confidence_adjustment > 0 else "decreased"
            logger.info(f"   📈 CONFIDENCE {direction.upper()} by {abs(reflection.confidence_adjustment):.3f}")

        # Log memory formation
        logger.info(f"   💾 MEMORIES FORMED:")
        logger.info(f"      • Personal: {len(reflection.personal_memories_formed)}")
        logger.info(f"      • Team ({home_team}): {len([m for m in reflection.team_memories_formed if home_team.lower() in m.lower()])}")
        logger.info(f"      • Team ({away_team}): {len([m for m in reflection.team_memories_formed if away_team.lower() in m.lower()])}")
        logger.info(f"      • Matchup: {len(reflection.matchup_memories_formed)}")

    def get_expert_memories(self, expert_id: str, memory_type: Optional[MemoryType] = None) -> List[StructuredMemory]:
        """Get all memories for an expert, optionally filtered by type"""

        if expert_id not in self.personal_memories:
            return []

        memories = self.personal_memories[expert_id]

        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]

        return sorted(memories, key=lambda x: x.memory_strength, reverse=True)

    def get_team_memories(self, expert_id: str, team: str) -> Optional[TeamMemoryBank]:
        """Get team memory bank for an expert"""

        if expert_id not in self.team_memories:
            return None

        return self.team_memories[expert_id].get(team)

    def get_matchup_memories(self, expert_id: str, team_a: str, team_b: str) -> Optional[MatchupMemoryBank]:
        """Get matchup memory bank for an expert"""

        matchup_key = f"{min(team_a, team_b)}_vs_{max(team_a, team_b)}"

        if expert_id not in self.matchup_memories:
            return None

        return self.matchup_memories[expert_id].get(matchup_key)


async def main():
    """Test the Expert Learning Memory System"""
    print("🧠 Expert Learning Memory System Test")
    print("=" * 60)

    from training.expert_configuration import ExpertConfigurationManager
    from training.prediction_generator import GamePrediction, PredictionType

    # Initialize system
    config_manager = ExpertConfigurationManager()
    memory_system = ExpertLearningMemorySystem(config_manager)

    # Create test prediction and outcome
    test_prediction = GamePrediction(
        expert_type=ExpertType.MOMENTUM_RIDER,
        prediction_type=PredictionType.WINNER,
        predicted_winner="Chiefs",
        win_probability=0.65,
        confidence_level=0.75,
        reasoning_chain=[
            "Chiefs are riding a 4-game winning streak",
            "Momentum strongly favors Kansas City",
            "Hot teams stay hot in December"
        ]
    )

    test_game_context = {
        'game_id': 'test_game_001',
        'home_team': 'Chiefs',
        'away_team': 'Raiders',
        'week': 15,
        'weather': {'temperature': 35, 'wind_speed': 12},
        'division_game': True
    }

    test_outcome = {
        'home_score': 28,
        'away_score': 21,
        'overtime': False
    }

    # Process learning
    reflection = await memory_system.process_post_game_learning(
        'momentum_rider', test_game_context, test_prediction, test_outcome
    )

    print(f"\n📊 Learning Reflection Results:")
    print(f"   Expert: {reflection.expert_id}")
    print(f"   Prediction Correct: {reflection.was_correct}")
    print(f"   Confidence Calibration: {reflection.confidence_calibration:.3f}")
    print(f"   What Went Right: {reflection.what_went_right}")
    print(f"   What Went Wrong: {reflection.what_went_wrong}")
    print(f"   Lessons Learned: {reflection.lessons_learned}")
    print(f"   Confidence Adjustment: {reflection.confidence_adjustment:+.3f}")

    print(f"\n🧠 Reflection Thoughts:")
    print(f"   {reflection.reflection_thoughts}")

    print(f"\n🔮 Future Adjustments:")
    print(f"   {reflection.future_adjustments}")

    # Check stored memories
    memories = memory_system.get_expert_memories('momentum_rider')
    print(f"\n💾 Stored Memories: {len(memories)}")
    for memory in memories:
        print(f"   • {memory.memory_type.value}: {memory.memory_title}")

    print(f"\n✅ Expert Learning Memory System test completed!")


if __name__ == "__main__":
    asyncio.run(main())
