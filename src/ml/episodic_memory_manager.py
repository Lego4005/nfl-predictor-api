"""
Episodic Memory Manager - Expert Game Experience Storage
Stores game experiences with emotional encoding and lesson extraction
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import asyncpg
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmotionalState(Enum):
    EUPHORIA = "euphoria"           # Perfect prediction
    SATISFACTION = "satisfaction"   # Good prediction
    NEUTRAL = "neutral"            # Average result
    DISAPPOINTMENT = "disappointment" # Poor prediction
    DEVASTATION = "devastation"    # Completely wrong
    SURPRISE = "surprise"          # Unexpected outcome
    CONFUSION = "confusion"        # Conflicting signals
    VINDICATION = "vindication"    # Contrarian pick was right

class MemoryType(Enum):
    PREDICTION_OUTCOME = "prediction_outcome"
    PATTERN_RECOGNITION = "pattern_recognition"
    UPSET_DETECTION = "upset_detection"
    CONSENSUS_DEVIATION = "consensus_deviation"
    LEARNING_MOMENT = "learning_moment"
    FAILURE_ANALYSIS = "failure_analysis"

class LessonCategory(Enum):
    INJURY_IMPACT = "injury_impact"
    WEATHER_EFFECTS = "weather_effects"
    HOME_FIELD_ADVANTAGE = "home_field_advantage"
    MOMENTUM_SHIFTS = "momentum_shifts"
    COACHING_DECISIONS = "coaching_decisions"
    ROSTER_CHANGES = "roster_changes"
    MOTIVATION_FACTORS = "motivation_factors"
    STATISTICAL_PATTERNS = "statistical_patterns"

@dataclass
class EpisodicMemory:
    expert_id: str
    game_id: str
    memory_type: MemoryType
    emotional_state: EmotionalState
    prediction_data: Dict[str, Any]
    actual_outcome: Dict[str, Any]
    contextual_factors: List[Dict[str, Any]]
    lessons_learned: List[Dict[str, Any]]
    emotional_intensity: float  # 0-1 scale
    memory_vividness: float     # 0-1 scale
    experience_timestamp: datetime
    retrieval_count: int = 0
    memory_decay: float = 1.0

class EpisodicMemoryManager:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.db_pool = None
        self.expert_personalities = self._load_expert_personalities()
        self.memory_consolidation_threshold = 0.7

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(**self.db_config)
            logger.info("✅ Episodic Memory Manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Episodic Memory Manager: {e}")
            raise

    def _load_expert_personalities(self) -> Dict[str, Dict[str, Any]]:
        """Load expert personality profiles for memory encoding"""
        return {
            "1": {"name": "The Analyst", "memory_style": "analytical", "emotion_intensity": 0.6},
            "2": {"name": "The Gambler", "memory_style": "outcome_focused", "emotion_intensity": 0.9},
            "3": {"name": "The Rebel", "memory_style": "contrarian", "emotion_intensity": 0.8},
            "4": {"name": "The Hunter", "memory_style": "opportunity_seeking", "emotion_intensity": 0.7},
            "5": {"name": "The Rider", "memory_style": "momentum_based", "emotion_intensity": 0.8},
            "6": {"name": "The Scholar", "memory_style": "systematic", "emotion_intensity": 0.5},
            "7": {"name": "The Chaos", "memory_style": "random", "emotion_intensity": 1.0},
            "8": {"name": "The Intuition", "memory_style": "feeling_based", "emotion_intensity": 0.9},
            "9": {"name": "The Quant", "memory_style": "data_driven", "emotion_intensity": 0.4},
            "10": {"name": "The Reversal", "memory_style": "pattern_seeking", "emotion_intensity": 0.7},
            "11": {"name": "The Fader", "memory_style": "narrative_resistant", "emotion_intensity": 0.6},
            "12": {"name": "The Sharp", "memory_style": "professional", "emotion_intensity": 0.5},
            "13": {"name": "The Underdog", "memory_style": "upset_focused", "emotion_intensity": 0.8},
            "14": {"name": "The Consensus", "memory_style": "group_oriented", "emotion_intensity": 0.6},
            "15": {"name": "The Exploiter", "memory_style": "edge_seeking", "emotion_intensity": 0.7}
        }

    async def create_episodic_memory(self, expert_id: str, game_id: str,
                                   prediction_data: Dict[str, Any],
                                   actual_outcome: Dict[str, Any],
                                   contextual_factors: Optional[List[Dict[str, Any]]] = None) -> EpisodicMemory:
        """Create and store an episodic memory from game experience"""

        # Determine memory type
        memory_type = self._classify_memory_type(prediction_data, actual_outcome)

        # Calculate emotional state and intensity
        emotional_state, emotional_intensity = self._assess_emotional_response(
            expert_id, prediction_data, actual_outcome
        )

        # Extract lessons learned
        lessons_learned = await self._extract_lessons(
            expert_id, prediction_data, actual_outcome, contextual_factors or []
        )

        # Calculate memory vividness
        memory_vividness = self._calculate_vividness(
            emotional_intensity, memory_type, lessons_learned
        )

        # Generate contextual factors if not provided
        if not contextual_factors:
            contextual_factors = await self._extract_contextual_factors(game_id, prediction_data)

        memory = EpisodicMemory(
            expert_id=expert_id,
            game_id=game_id,
            memory_type=memory_type,
            emotional_state=emotional_state,
            prediction_data=prediction_data,
            actual_outcome=actual_outcome,
            contextual_factors=contextual_factors,
            lessons_learned=lessons_learned,
            emotional_intensity=emotional_intensity,
            memory_vividness=memory_vividness,
            experience_timestamp=datetime.utcnow()
        )

        # Store in database
        await self._store_memory(memory)

        return memory

    def _classify_memory_type(self, prediction: Dict[str, Any], outcome: Dict[str, Any]) -> MemoryType:
        """Classify the type of episodic memory"""

        predicted_winner = prediction.get("winner")
        actual_winner = outcome.get("winner")
        predicted_confidence = prediction.get("confidence", 0.5)

        # Check for major upset
        if predicted_confidence > 0.8 and predicted_winner != actual_winner:
            return MemoryType.UPSET_DETECTION

        # Check for pattern recognition opportunity
        predicted_score_diff = abs(prediction.get("home_score", 20) - prediction.get("away_score", 20))
        actual_score_diff = abs(outcome.get("home_score", 20) - outcome.get("away_score", 20))

        if abs(predicted_score_diff - actual_score_diff) <= 3:
            return MemoryType.PATTERN_RECOGNITION

        # Check for learning moment (significant miss)
        if predicted_winner != actual_winner and predicted_confidence > 0.7:
            return MemoryType.LEARNING_MOMENT

        # Check for failure analysis (complete miss)
        if (predicted_winner != actual_winner and
            abs(predicted_score_diff - actual_score_diff) > 10):
            return MemoryType.FAILURE_ANALYSIS

        # Default to prediction outcome
        return MemoryType.PREDICTION_OUTCOME

    def _assess_emotional_response(self, expert_id: str, prediction: Dict[str, Any],
                                 outcome: Dict[str, Any]) -> Tuple[EmotionalState, float]:
        """Assess emotional state and intensity of the experience"""

        personality = self.expert_personalities.get(expert_id, {})
        base_emotion_intensity = personality.get("emotion_intensity", 0.6)

        predicted_winner = prediction.get("winner")
        actual_winner = outcome.get("winner")
        predicted_confidence = prediction.get("confidence", 0.5)

        # Perfect prediction with high confidence
        if (predicted_winner == actual_winner and predicted_confidence > 0.8):
            emotion_state = EmotionalState.EUPHORIA
            intensity = base_emotion_intensity * 1.0

        # Good prediction
        elif predicted_winner == actual_winner:
            emotion_state = EmotionalState.SATISFACTION
            intensity = base_emotion_intensity * 0.7

        # Wrong prediction with high confidence
        elif predicted_winner != actual_winner and predicted_confidence > 0.8:
            emotion_state = EmotionalState.DEVASTATION
            intensity = base_emotion_intensity * 1.0

        # Wrong prediction with medium confidence
        elif predicted_winner != actual_winner and predicted_confidence > 0.6:
            emotion_state = EmotionalState.DISAPPOINTMENT
            intensity = base_emotion_intensity * 0.8

        # Unexpected outcome (low confidence but right)
        elif predicted_winner == actual_winner and predicted_confidence < 0.6:
            emotion_state = EmotionalState.SURPRISE
            intensity = base_emotion_intensity * 0.6

        # Contrarian vindication (expert went against consensus and was right)
        elif self._was_contrarian_pick(expert_id, prediction) and predicted_winner == actual_winner:
            emotion_state = EmotionalState.VINDICATION
            intensity = base_emotion_intensity * 0.9

        # Confusing outcome
        else:
            emotion_state = EmotionalState.CONFUSION
            intensity = base_emotion_intensity * 0.5

        return emotion_state, min(1.0, intensity)

    def _was_contrarian_pick(self, expert_id: str, prediction: Dict[str, Any]) -> bool:
        """Check if this was a contrarian pick against consensus"""
        personality = self.expert_personalities.get(expert_id, {})
        return personality.get("memory_style") in ["contrarian", "narrative_resistant"]

    async def _extract_lessons(self, expert_id: str, prediction: Dict[str, Any],
                             outcome: Dict[str, Any],
                             contextual_factors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract lessons learned from the experience"""

        lessons = []
        personality = self.expert_personalities.get(expert_id, {})
        memory_style = personality.get("memory_style", "balanced")

        predicted_winner = prediction.get("winner")
        actual_winner = outcome.get("winner")

        # Lesson 1: Prediction accuracy analysis
        if predicted_winner == actual_winner:
            lessons.append({
                "category": LessonCategory.STATISTICAL_PATTERNS.value,
                "content": f"Prediction methodology worked well for this matchup",
                "confidence": 0.8,
                "applicability": "similar_matchups"
            })
        else:
            lessons.append({
                "category": LessonCategory.STATISTICAL_PATTERNS.value,
                "content": f"Missed key factor that influenced {actual_winner} victory",
                "confidence": 0.7,
                "applicability": "future_analysis"
            })

        # Lesson 2: Contextual factor analysis
        for factor in contextual_factors:
            factor_type = factor.get("type", "unknown")

            if factor_type == "injury":
                lessons.append({
                    "category": LessonCategory.INJURY_IMPACT.value,
                    "content": f"Injury to {factor.get('player', 'key player')} had {factor.get('impact', 'significant')} impact",
                    "confidence": 0.9,
                    "applicability": "injury_scenarios"
                })

            elif factor_type == "weather":
                lessons.append({
                    "category": LessonCategory.WEATHER_EFFECTS.value,
                    "content": f"Weather conditions ({factor.get('condition', 'unknown')}) affected game flow",
                    "confidence": 0.6,
                    "applicability": "outdoor_games"
                })

        # Lesson 3: Expert-specific insights based on memory style
        if memory_style == "analytical":
            lessons.append({
                "category": LessonCategory.STATISTICAL_PATTERNS.value,
                "content": "Need to incorporate more advanced metrics for edge cases",
                "confidence": 0.7,
                "applicability": "model_improvement"
            })

        elif memory_style == "outcome_focused":
            lessons.append({
                "category": LessonCategory.MOTIVATION_FACTORS.value,
                "content": "Team motivation and situational factors were undervalued",
                "confidence": 0.6,
                "applicability": "situational_analysis"
            })

        return lessons

    def _calculate_vividness(self, emotional_intensity: float, memory_type: MemoryType,
                           lessons_learned: List[Dict[str, Any]]) -> float:
        """Calculate how vivid and memorable this experience will be"""

        base_vividness = emotional_intensity * 0.6

        # Type-based adjustments
        type_multipliers = {
            MemoryType.UPSET_DETECTION: 1.2,
            MemoryType.LEARNING_MOMENT: 1.1,
            MemoryType.FAILURE_ANALYSIS: 1.3,
            MemoryType.PATTERN_RECOGNITION: 1.0,
            MemoryType.PREDICTION_OUTCOME: 0.8,
            MemoryType.CONSENSUS_DEVIATION: 1.1
        }

        vividness = base_vividness * type_multipliers.get(memory_type, 1.0)

        # Lesson quality boost
        if len(lessons_learned) > 2:
            vividness *= 1.1

        return min(1.0, vividness)

    async def _extract_contextual_factors(self, game_id: str,
                                        prediction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract contextual factors from game data"""

        factors = []

        # Try to get game-specific context from database
        try:
            async with self.db_pool.acquire() as conn:
                # Check for weather data
                weather_query = "SELECT * FROM weather_conditions WHERE game_id = $1"
                weather_row = await conn.fetchrow(weather_query, game_id)

                if weather_row:
                    factors.append({
                        "type": "weather",
                        "condition": weather_row.get("condition"),
                        "temperature": weather_row.get("temperature"),
                        "impact": "moderate"
                    })

                # Check for injury reports
                injury_query = "SELECT * FROM injury_reports WHERE game_id = $1"
                injury_rows = await conn.fetch(injury_query, game_id)

                for injury in injury_rows:
                    factors.append({
                        "type": "injury",
                        "player": injury.get("player_name"),
                        "severity": injury.get("severity"),
                        "impact": "high" if injury.get("severity") == "out" else "moderate"
                    })

        except Exception as e:
            logger.warning(f"Could not fetch contextual factors: {e}")

        # Add reasoning chain as contextual factors
        reasoning_chain = prediction_data.get("reasoning_chain", [])
        for item in reasoning_chain:
            factors.append({
                "type": "reasoning_factor",
                "factor": item.get("factor"),
                "value": item.get("value"),
                "weight": item.get("weight"),
                "impact": "analysis_based"
            })

        return factors

    async def _store_memory(self, memory: EpisodicMemory):
        """Store episodic memory in database"""

        # Generate unique memory hash
        memory_content = f"{memory.expert_id}_{memory.game_id}_{memory.experience_timestamp.isoformat()}"
        memory_hash = hashlib.sha256(memory_content.encode()).hexdigest()[:16]

        query = """
        INSERT INTO expert_episodic_memories (
            memory_id, expert_id, game_id, memory_type, emotional_state,
            prediction_data, actual_outcome, contextual_factors, lessons_learned,
            emotional_intensity, memory_vividness, retrieval_count, memory_decay,
            created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """

        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query,
                    memory_hash,
                    memory.expert_id,
                    memory.game_id,
                    memory.memory_type.value,
                    memory.emotional_state.value,
                    json.dumps(memory.prediction_data),
                    json.dumps(memory.actual_outcome),
                    json.dumps(memory.contextual_factors),
                    json.dumps(memory.lessons_learned),
                    memory.emotional_intensity,
                    memory.memory_vividness,
                    memory.retrieval_count,
                    memory.memory_decay,
                    memory.experience_timestamp
                )

            logger.info(f"✅ Stored episodic memory {memory_hash} for expert {memory.expert_id}")

        except Exception as e:
            logger.error(f"❌ Failed to store episodic memory: {e}")
            raise

    async def retrieve_similar_memories(self, expert_id: str, current_situation: Dict[str, Any],
                                      limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve memories similar to current situation"""

        # Extract key features from current situation
        situation_features = self._extract_situation_features(current_situation)

        query = """
        SELECT
            memory_id, memory_type, emotional_state, prediction_data,
            actual_outcome, contextual_factors, lessons_learned,
            emotional_intensity, memory_vividness, retrieval_count,
            memory_decay, created_at
        FROM expert_episodic_memories
        WHERE expert_id = $1
        ORDER BY memory_vividness * memory_decay DESC
        LIMIT $2
        """

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, expert_id, limit * 2)  # Get more to filter

            # Score memories by similarity to current situation
            scored_memories = []
            for row in rows:
                memory_dict = dict(row)

                # Calculate similarity score
                similarity_score = self._calculate_memory_similarity(
                    situation_features, memory_dict
                )

                memory_dict['similarity_score'] = similarity_score
                scored_memories.append(memory_dict)

            # Sort by similarity and return top matches
            scored_memories.sort(key=lambda x: x['similarity_score'], reverse=True)
            relevant_memories = scored_memories[:limit]

            # Update retrieval counts
            for memory in relevant_memories:
                await self._update_retrieval_count(memory['memory_id'])

            return relevant_memories

        except Exception as e:
            logger.error(f"❌ Failed to retrieve similar memories: {e}")
            return []

    def _extract_situation_features(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key features from current situation for memory matching"""

        features = {
            "teams": [situation.get("home_team"), situation.get("away_team")],
            "confidence_level": situation.get("confidence", 0.5),
            "predicted_winner": situation.get("predicted_winner"),
            "reasoning_factors": []
        }

        # Extract reasoning factors
        reasoning_chain = situation.get("reasoning_chain", [])
        for item in reasoning_chain:
            features["reasoning_factors"].append(item.get("factor", "unknown"))

        return features

    def _calculate_memory_similarity(self, situation_features: Dict[str, Any],
                                   memory: Dict[str, Any]) -> float:
        """Calculate similarity between current situation and stored memory"""

        similarity_score = 0.0

        # Team similarity (30% weight)
        memory_prediction = json.loads(memory.get("prediction_data", "{}"))
        memory_teams = [memory_prediction.get("home_team"), memory_prediction.get("away_team")]

        team_overlap = len(set(situation_features["teams"]) & set(memory_teams))
        similarity_score += (team_overlap / 2.0) * 0.3

        # Confidence level similarity (20% weight)
        memory_confidence = memory_prediction.get("confidence", 0.5)
        situation_confidence = situation_features.get("confidence_level", 0.5)
        confidence_similarity = 1.0 - abs(memory_confidence - situation_confidence)
        similarity_score += confidence_similarity * 0.2

        # Reasoning factor similarity (30% weight)
        memory_factors = []
        for factor in json.loads(memory.get("contextual_factors", "[]")):
            if factor.get("type") == "reasoning_factor":
                memory_factors.append(factor.get("factor", ""))

        situation_factors = situation_features.get("reasoning_factors", [])
        if memory_factors and situation_factors:
            factor_overlap = len(set(memory_factors) & set(situation_factors))
            max_factors = max(len(memory_factors), len(situation_factors))
            factor_similarity = factor_overlap / max_factors if max_factors > 0 else 0
            similarity_score += factor_similarity * 0.3

        # Memory vividness bonus (20% weight)
        vividness_bonus = memory.get("memory_vividness", 0.5) * 0.2
        similarity_score += vividness_bonus

        return min(1.0, similarity_score)

    async def _update_retrieval_count(self, memory_id: str):
        """Update retrieval count and adjust memory decay"""

        query = """
        UPDATE expert_episodic_memories
        SET retrieval_count = retrieval_count + 1,
            memory_decay = LEAST(1.0, memory_decay + 0.1)
        WHERE memory_id = $1
        """

        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(query, memory_id)

        except Exception as e:
            logger.warning(f"Failed to update retrieval count: {e}")

    async def consolidate_memories(self, expert_id: str):
        """Consolidate and strengthen frequently accessed memories"""

        query = """
        SELECT memory_id, retrieval_count, memory_vividness, emotional_intensity
        FROM expert_episodic_memories
        WHERE expert_id = $1 AND retrieval_count >= 3
        """

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, expert_id)

            for row in rows:
                # Strengthen memories that are frequently retrieved
                new_vividness = min(1.0, row['memory_vividness'] * 1.1)
                new_decay = min(1.0, row['memory_decay'] * 1.05)

                update_query = """
                UPDATE expert_episodic_memories
                SET memory_vividness = $1, memory_decay = $2
                WHERE memory_id = $3
                """

                await conn.execute(update_query, new_vividness, new_decay, row['memory_id'])

            logger.info(f"✅ Consolidated {len(rows)} memories for expert {expert_id}")

        except Exception as e:
            logger.error(f"❌ Failed to consolidate memories: {e}")

    async def get_memory_stats(self, expert_id: str) -> Dict[str, Any]:
        """Get memory statistics for an expert"""

        query = """
        SELECT
            COUNT(*) as total_memories,
            AVG(emotional_intensity) as avg_emotional_intensity,
            AVG(memory_vividness) as avg_vividness,
            SUM(retrieval_count) as total_retrievals,
            memory_type,
            emotional_state,
            COUNT(*) as type_count
        FROM expert_episodic_memories
        WHERE expert_id = $1
        GROUP BY memory_type, emotional_state
        """

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, expert_id)

            stats = {
                "total_memories": 0,
                "avg_emotional_intensity": 0,
                "avg_vividness": 0,
                "total_retrievals": 0,
                "memory_types": {},
                "emotional_states": {}
            }

            for row in rows:
                stats["total_memories"] += row["type_count"]
                stats["memory_types"][row["memory_type"]] = row["type_count"]
                stats["emotional_states"][row["emotional_state"]] = row["type_count"]

            if stats["total_memories"] > 0:
                # Get overall averages
                avg_query = """
                SELECT
                    AVG(emotional_intensity) as avg_emotional_intensity,
                    AVG(memory_vividness) as avg_vividness,
                    SUM(retrieval_count) as total_retrievals
                FROM expert_episodic_memories
                WHERE expert_id = $1
                """

                avg_row = await conn.fetchrow(avg_query, expert_id)
                stats["avg_emotional_intensity"] = float(avg_row["avg_emotional_intensity"])
                stats["avg_vividness"] = float(avg_row["avg_vividness"])
                stats["total_retrievals"] = int(avg_row["total_retrievals"])

            return stats

        except Exception as e:
            logger.error(f"❌ Failed to get memory stats: {e}")
            return {}

    async def close(self):
        """Close database connections"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("✅ Episodic Memory Manager closed")

# Example usage
async def main():
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'your_user',
        'password': 'your_password',
        'database': 'nfl_predictor'
    }

    manager = EpisodicMemoryManager(db_config)
    await manager.initialize()

    # Example memory creation
    prediction_data = {
        "winner": "Chiefs",
        "confidence": 0.85,
        "home_score": 28,
        "away_score": 21,
        "reasoning_chain": [
            {"factor": "Offensive EPA", "value": "+0.35", "weight": 0.4},
            {"factor": "Home Field", "value": "Strong", "weight": 0.3}
        ]
    }

    actual_outcome = {
        "winner": "Bills",
        "home_score": 24,
        "away_score": 31
    }

    memory = await manager.create_episodic_memory(
        expert_id="2",
        game_id="game_456",
        prediction_data=prediction_data,
        actual_outcome=actual_outcome
    )

    print(f"Created memory with emotional state: {memory.emotional_state.value}")
    print(f"Memory vividness: {memory.memory_vividness:.2f}")

    # Retrieve similar memories for future prediction
    similar_memories = await manager.retrieve_similar_memories(
        expert_id="2",
        current_situation={
            "home_team": "Chiefs",
            "away_team": "Bills",
            "confidence": 0.8,
            "predicted_winner": "Chiefs"
        }
    )

    print(f"Found {len(similar_memories)} similar memories")

    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())