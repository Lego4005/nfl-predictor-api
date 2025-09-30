#!/usr/bin/env python3
"""
Supabase-Compatible Memory Services
Adapts episodic memory, belief revision, and reasoning services to use Supabase client
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from supabase import Client

logger = logging.getLogger(__name__)

class SupabaseEpisodicMemoryManager:
    """Supabase-compatible episodic memory manager"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.expert_personalities = {
            "conservative_analyzer": {"name": "The Analyst", "memory_style": "analytical", "emotion_intensity": 0.6}
        }

    async def initialize(self):
        """Initialize (no-op for Supabase client)"""
        logger.info("✅ Supabase Episodic Memory Manager initialized")

    async def close(self):
        """Close (no-op for Supabase client)"""
        logger.info("✅ Supabase Episodic Memory Manager closed")

    async def store_memory(self, expert_id: str, game_id: str, memory_data: Dict[str, Any]) -> bool:
        """Store episodic memory"""
        try:
            import hashlib
            # Generate memory_id from expert+game
            memory_id = hashlib.md5(f"{expert_id}_{game_id}".encode()).hexdigest()[:32]

            memory_record = {
                'memory_id': memory_id,
                'expert_id': expert_id,
                'game_id': game_id,
                'memory_type': memory_data.get('memory_type', 'prediction_outcome'),
                'emotional_state': memory_data.get('emotional_state', 'neutral'),
                'prediction_data': memory_data.get('prediction_data', {}),
                'actual_outcome': memory_data.get('actual_outcome', {}),
                'contextual_factors': memory_data.get('contextual_factors', []),
                'lessons_learned': memory_data.get('lessons_learned', []),
                'emotional_intensity': memory_data.get('emotional_intensity', 0.5),
                'memory_vividness': memory_data.get('memory_vividness', 0.5),
                'retrieval_count': 0,
                'memory_decay': 1.0
            }

            result = self.supabase.table('expert_episodic_memories').insert(memory_record).execute()

            if result.data:
                logger.info(f"✅ Stored episodic memory for {expert_id} game {game_id}")
                return True
            else:
                logger.error(f"❌ Failed to store memory: {result}")
                return False

        except Exception as e:
            logger.error(f"❌ Error storing memory: {e}")
            return False

    async def retrieve_memories(self, expert_id: str, game_context: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve similar memories"""
        try:
            # Simple retrieval by expert_id (similarity search would require pgvector)
            result = self.supabase.table('expert_episodic_memories') \
                .select('*') \
                .eq('expert_id', expert_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()

            memories = []
            if result.data:
                for mem in result.data:
                    mem['similarity_score'] = 0.7  # Mock similarity for now
                    memories.append(mem)

                logger.info(f"✅ Retrieved {len(memories)} memories for {expert_id}")

            return memories

        except Exception as e:
            logger.error(f"❌ Error retrieving memories: {e}")
            return []


class SupabaseBeliefRevisionService:
    """Supabase-compatible belief revision service"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def initialize(self):
        """Initialize (no-op)"""
        logger.info("✅ Supabase Belief Revision Service initialized")

    async def close(self):
        """Close (no-op)"""
        logger.info("✅ Supabase Belief Revision Service closed")

    async def detect_revision(self, expert_id: str, old_prediction: Dict, new_prediction: Dict) -> Optional[Dict[str, Any]]:
        """Detect if beliefs have changed"""
        try:
            # Simple revision detection: confidence change > 15%
            old_conf = old_prediction.get('winner_confidence', 0.5)
            new_conf = new_prediction.get('winner_confidence', 0.5)
            conf_change = abs(new_conf - old_conf)

            if conf_change > 0.15:
                revision_data = {
                    'expert_id': expert_id,
                    'revision_timestamp': datetime.now().isoformat(),
                    'belief_category': 'prediction_confidence',
                    'belief_key': 'confidence_level',
                    'old_belief': json.dumps({'confidence': old_conf}),
                    'new_belief': json.dumps({'confidence': new_conf}),
                    'revision_trigger': 'confidence_adjustment',
                    'supporting_evidence': json.dumps({'change': conf_change}),
                    'causal_reasoning': f"Confidence changed by {conf_change:.1%}",
                    'impact_score': conf_change
                }

                result = self.supabase.table('expert_belief_revisions').insert(revision_data).execute()

                if result.data:
                    logger.info(f"✅ Recorded belief revision for {expert_id}")
                    return revision_data

            return None

        except Exception as e:
            logger.error(f"❌ Error detecting revision: {e}")
            return None


class SupabaseLessonExtractor:
    """Extract lessons from game outcomes"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def extract_lessons(self, prediction: Dict, outcome: Dict, game_data: Dict) -> List[Dict[str, Any]]:
        """Extract lessons learned from game"""
        lessons = []

        was_correct = prediction.get('winner_prediction') == outcome.get('winner')
        confidence = prediction.get('winner_confidence', 0.5)

        # Lesson 1: Confidence calibration
        if was_correct and confidence > 0.7:
            lessons.append({
                'category': 'confidence_calibration',
                'lesson': f"High confidence ({confidence:.1%}) predictions are reliable",
                'confidence': 0.8
            })
        elif not was_correct and confidence > 0.7:
            lessons.append({
                'category': 'confidence_calibration',
                'lesson': f"Overconfidence ({confidence:.1%}) led to error - be more cautious",
                'confidence': 0.9
            })

        # Lesson 2: Home/Away patterns
        home_team = game_data.get('home_team', '')
        away_team = game_data.get('away_team', '')
        winner = outcome.get('winner')

        if winner == home_team:
            lessons.append({
                'category': 'home_field_advantage',
                'lesson': f"{home_team} benefits from home field",
                'confidence': 0.6
            })
        else:
            lessons.append({
                'category': 'road_performance',
                'lesson': f"{away_team} performs well on the road",
                'confidence': 0.6
            })

        return lessons


async def store_learned_principle(supabase: Client, expert_id: str, principle: Dict[str, Any]) -> Optional[str]:
    """Store a learned principle"""
    try:
        principle_record = {
            'expert_id': expert_id,
            'principle_category': principle.get('category', 'general'),
            'principle_statement': principle.get('statement'),
            'supporting_games_count': principle.get('supporting_count', 1),
            'confidence_level': principle.get('confidence', 0.5),
            'effect_size': principle.get('effect_size', 0.0),
            'supporting_evidence': json.dumps(principle.get('evidence', [])),
            'exceptions_noted': json.dumps(principle.get('exceptions', [])),
            'times_applied': 0,
            'success_rate': 0.0,
            'is_active': True
        }

        result = supabase.table('expert_learned_principles').insert(principle_record).execute()

        if result.data and len(result.data) > 0:
            principle_id = result.data[0].get('id')
            logger.info(f"✅ Stored learned principle for {expert_id}: {principle_id}")
            return principle_id
        return None

    except Exception as e:
        logger.error(f"❌ Error storing principle: {e}")
        return False