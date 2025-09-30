"""
Supabase-Compatible Episodic Memory Manager

Stores expert experiences using Supabase client (no direct DB connection needed).
Replaces asyncpg-based implementation with REST API calls.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class EpisodicMemory:
    """A memorable game experience"""
    expert_id: str
    game_id: str
    predicted_winner: str
    actual_winner: str
    confidence: float
    was_correct: bool
    surprise_level: float  # 0.0 = expected, 1.0 = shocking
    emotional_impact: str  # 'triumph', 'disappointment', 'neutral', 'vindication'
    key_factors: List[str]
    lesson_learned: str
    created_at: str


class SupabaseEpisodicMemory:
    """
    Stores and retrieves episodic memories using Supabase client.

    Advantages over asyncpg version:
    - Works with Supabase connection pooling
    - No direct database credentials needed
    - Automatic row-level security
    - Easy to query and analyze
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def store_memory(
        self,
        expert_id: str,
        game_id: str,
        prediction: Dict[str, Any],
        actual_outcome: Dict[str, Any],
        factors: List[str]
    ) -> str:
        """Store a game experience as episodic memory"""

        predicted_winner = prediction.get('winner')
        actual_winner = actual_outcome.get('winner')
        confidence = prediction.get('confidence', 0.5)

        was_correct = predicted_winner == actual_winner

        # Calculate surprise level (high confidence + wrong = high surprise)
        if not was_correct:
            surprise = confidence  # More confident mistakes are more surprising
        else:
            surprise = 1.0 - confidence  # Low confidence correct picks are surprising

        # Determine emotional impact
        if was_correct and confidence > 0.7:
            emotional_impact = 'triumph'
        elif was_correct and confidence < 0.4:
            emotional_impact = 'vindication'  # Upset pick was right!
        elif not was_correct and confidence > 0.7:
            emotional_impact = 'disappointment'
        else:
            emotional_impact = 'neutral'

        # Generate lesson
        if was_correct:
            lesson = f"Trust {', '.join(factors[:2])} when predicting {actual_winner}"
        else:
            lesson = f"Reconsider {', '.join(factors[:2])} - led to incorrect pick"

        # Store in Supabase
        memory_data = {
            'expert_id': expert_id,
            'game_id': game_id,
            'predicted_winner': predicted_winner,
            'actual_winner': actual_winner,
            'confidence': confidence,
            'was_correct': was_correct,
            'surprise_level': surprise,
            'emotional_impact': emotional_impact,
            'key_factors': factors,
            'lesson_learned': lesson,
            'created_at': datetime.utcnow().isoformat()
        }

        result = self.supabase.table('expert_episodic_memories').insert(memory_data).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]['id']

        return None

    async def get_similar_memories(
        self,
        expert_id: str,
        current_factors: List[str],
        limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve similar past experiences to inform current prediction.

        Similarity based on factor overlap.
        """
        # Get recent memories for this expert
        result = self.supabase.table('expert_episodic_memories') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .order('created_at', desc=True) \
            .limit(50) \
            .execute()

        if not result.data:
            return []

        # Calculate similarity scores
        memories_with_scores = []
        for memory in result.data:
            memory_factors = set(memory.get('key_factors', []))
            current_factors_set = set(current_factors)

            # Jaccard similarity
            intersection = len(memory_factors & current_factors_set)
            union = len(memory_factors | current_factors_set)
            similarity = intersection / union if union > 0 else 0.0

            memories_with_scores.append({
                'memory': memory,
                'similarity': similarity
            })

        # Sort by similarity and return top matches
        memories_with_scores.sort(key=lambda x: x['similarity'], reverse=True)
        return [m['memory'] for m in memories_with_scores[:limit]]

    async def get_high_impact_memories(
        self,
        expert_id: str,
        emotion: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get most memorable (high surprise) experiences"""
        query = self.supabase.table('expert_episodic_memories') \
            .select('*') \
            .eq('expert_id', expert_id)

        if emotion:
            query = query.eq('emotional_impact', emotion)

        result = query.order('surprise_level', desc=True).limit(limit).execute()

        return result.data if result.data else []

    async def get_accuracy_by_factors(
        self,
        expert_id: str
    ) -> Dict[str, float]:
        """
        Analyze which factors lead to correct predictions.

        Returns: {factor_name: accuracy_rate}
        """
        result = self.supabase.table('expert_episodic_memories') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .execute()

        if not result.data:
            return {}

        # Count correct/total for each factor
        factor_stats = {}

        for memory in result.data:
            factors = memory.get('key_factors', [])
            was_correct = memory.get('was_correct', False)

            for factor in factors:
                if factor not in factor_stats:
                    factor_stats[factor] = {'correct': 0, 'total': 0}

                factor_stats[factor]['total'] += 1
                if was_correct:
                    factor_stats[factor]['correct'] += 1

        # Calculate accuracy rates
        factor_accuracy = {}
        for factor, stats in factor_stats.items():
            if stats['total'] > 0:
                factor_accuracy[factor] = stats['correct'] / stats['total']

        return factor_accuracy

    async def get_memory_stats(self, expert_id: str) -> Dict:
        """Get summary statistics for expert's memory"""
        result = self.supabase.table('expert_episodic_memories') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .execute()

        if not result.data:
            return {
                'total_memories': 0,
                'accuracy': 0.0,
                'avg_surprise': 0.0,
                'emotional_distribution': {}
            }

        memories = result.data
        total = len(memories)
        correct = sum(1 for m in memories if m.get('was_correct'))
        avg_surprise = sum(m.get('surprise_level', 0) for m in memories) / total

        emotions = {}
        for m in memories:
            emotion = m.get('emotional_impact', 'neutral')
            emotions[emotion] = emotions.get(emotion, 0) + 1

        return {
            'total_memories': total,
            'accuracy': correct / total if total > 0 else 0.0,
            'avg_surprise': avg_surprise,
            'emotional_distribution': emotions
        }