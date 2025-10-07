#!/usr/bin/env python3
"""
Supabase-Compatible Memory Services
Adapts episodic memory, belief revision, and reasoning services to use Supabase client
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import json
import math
from enum import Enum
from supabase import Client

logger = logging.getLogger(__name__)


class MemoryBucketType(Enum):
    """Memory bucket types for different retrieval strategies"""
    TEAM_SPECIFIC = "team_specific"
    MATCHUP_SPECIFIC = "matchup_specific"
    SITUATIONAL = "situational"
    PERSONAL_LEARNING = "personal_learning"
    ALL = "all"  # Default behavior - retrieve all relevant memories


class MemoryInfluence:
    """
    Tracks memory influence for explanation and reinforcement.

    Requirements: 3.5, 8.3, 8.4, 5.4
    """
    def __init__(
        self,
        memory_id: str,
        similarity_score: float,
        temporal_weight: float,
        influence_strength: float,
        memory_summary: str,
        why_relevant: str,
        bucket_type: str = None,
        access_timestamp: datetime = None
    ):
        self.memory_id = memory_id
        self.similarity_score = similarity_score
        self.temporal_weight = temporal_weight
        self.influence_strength = influence_strength
        self.memory_summary = memory_summary
        self.why_relevant = why_relevant
        self.bucket_type = bucket_type
        self.access_timestamp = access_timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'memory_id': self.memory_id,
            'similarity_score': self.similarity_score,
            'temporal_weight': self.temporal_weight,
            'influence_strength': self.influence_strength,
            'memory_summary': self.memory_summary,
            'why_relevant': self.why_relevant,
            'bucket_type': self.bucket_type,
            'access_timestamp': self.access_timestamp.isoformat()
        }

    @classmethod
    def from_memory(
        cls,
        memory: Dict[str, Any],
        similarity_score: float,
        temporal_weight: float,
        game_context: Dict[str, Any] = None
    ) -> 'MemoryInfluence':
        """Create MemoryInfluence from memory record"""
        # Calculate influence strength combining similarity and temporal weight
        influence_strength = (similarity_score * 0.7) + (temporal_weight * 0.3)

        # Generate memory summary
        memory_summary = cls._generate_memory_summary(memory)

        # Use existing relevance explanation or generate one
        why_relevant = memory.get('relevance_explanation', 'Relevant past experience')

        return cls(
            memory_id=memory.get('memory_id', ''),
            similarity_score=similarity_score,
            temporal_weight=temporal_weight,
            influence_strength=influence_strength,
            memory_summary=memory_summary,
            why_relevant=why_relevant,
            bucket_type=memory.get('bucket_type', 'unknown')
        )

    @staticmethod
    def _generate_memory_summary(memory: Dict[str, Any]) -> str:
        """Generate a concise summary of the memory"""
        memory_type = memory.get('memory_type', 'experience')
        home_team = memory.get('home_team', 'Unknown')
        away_team = memory.get('away_team', 'Unknown')

        # Get key lessons or outcomes
        lessons = memory.get('lessons_learned', [])
        if lessons and isinstance(lessons, list) and len(lessons) > 0:
            key_lesson = lessons[0] if isinstance(lessons[0], str) else str(lessons[0])
            if len(key_lesson) > 100:
                key_lesson = key_lesson[:97] + "..."
        else:
            key_lesson = "Game experience"

        return f"{memory_type.replace('_', ' ').title()}: {away_team} at {home_team} - {key_lesson}"

class SupabaseEpisodicMemoryManager:
    """Supabase-compatible episodic memory manager with reflection memory support"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.expert_personalities = {
            "conservative_analyzer": {"name": "The Analyst", "memory_style": "analytical", "emotion_intensity": 0.6}
        }

        # Initialize temporal decay service
        try:
            from ...services.temporal_decay_service import TemporalDecayService
            self.temporal_decay_service = TemporalDecayService()
            logger.info("✅ Temporal decay service initialized")
        except ImportError as e:
            logger.warning(f"⚠️ Could not import temporal decay service: {e}")
            self.temporal_decay_service = None

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

            # Extract team data from contextual factors
            home_team = None
            away_team = None
            contextual_factors = memory_data.get('contextual_factors', [])

            for factor in contextual_factors:
                if isinstance(factor, dict):
                    if factor.get('factor') == 'home_team':
                        home_team = factor.get('value')
                    elif factor.get('factor') == 'away_team':
                        away_team = factor.get('value')

            memory_record = {
                'memory_id': memory_id,
                'expert_id': expert_id,
                'game_id': game_id,
                'memory_type': memory_data.get('memory_type', 'prediction_outcome'),
                'emotional_state': memory_data.get('emotional_state', 'neutral'),
                'prediction_data': memory_data.get('prediction_data', {}),
                'actual_outcome': memory_data.get('actual_outcome', {}),
                'contextual_factors': contextual_factors,
                'lessons_learned': memory_data.get('lessons_learned', []),
                'emotional_intensity': memory_data.get('emotional_intensity', 0.5),
                'memory_vividness': memory_data.get('memory_vividness', 0.5),
                'retrieval_count': 0,
                'memory_decay': 1.0,
                # Add team data for vector search
                'home_team': home_team,
                'away_team': away_team
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

    async def retrieve_memories(
        self,
        expert_id: str,
        game_context: Dict[str, Any],
        limit: int = 5,
        team_specific: bool = True,
        bucket_type: MemoryBucketType = MemoryBucketType.ALL
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories using different bucket types for comprehensive context

        Args:
            expert_id: Expert identifier
            game_context: Dict with game context (home_team, away_team, situational factors)
            limit: Max memories to retrieve
            team_specific: Legacy parameter for backward compatibility
            bucket_type: Type of memory bucket to retrieve from

        Returns:
            List of memory dictionaries with similarity scores and relevance explanations
        """
        try:
            # Handle different memory bucket types
            if bucket_type == MemoryBucketType.TEAM_SPECIFIC:
                return await self._retrieve_team_specific_memories(expert_id, game_context, limit)
            elif bucket_type == MemoryBucketType.MATCHUP_SPECIFIC:
                return await self._retrieve_matchup_specific_memories(expert_id, game_context, limit)
            elif bucket_type == MemoryBucketType.SITUATIONAL:
                return await self._retrieve_situational_memories(expert_id, game_context, limit)
            elif bucket_type == MemoryBucketType.PERSONAL_LEARNING:
                return await self._retrieve_personal_learning_memories(expert_id, game_context, limit)
            elif bucket_type == MemoryBucketType.ALL:
                # Retrieve from all bucket types and combine
                return await self._retrieve_comprehensive_memories(expert_id, game_context, limit, team_specific)
            else:
                logger.warning(f"Unknown bucket type: {bucket_type}, falling back to ALL")
                return await self._retrieve_comprehensive_memories(expert_id, game_context, limit, team_specific)

        except Exception as e:
            logger.error(f"❌ Error retrieving memories: {e}")
            return []

    async def _retrieve_team_specific_memories(self, expert_id: str, game_context: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        Retrieve memories involving specific teams for individual team patterns.

        Requirements: 3.1, 3.2, 8.1
        """
        try:
            home_team = game_context.get('home_team')
            away_team = game_context.get('away_team')

            if not home_team and not away_team:
                logger.warning("No team information provided for team-specific memory retrieval")
                return []

            # Build query for memories involving either team with temporal filtering
            base_query = self.supabase.table('expert_episodic_memories').select('*').eq('expert_id', expert_id)
            query = self.apply_temporal_filtering(expert_id, base_query)

            if home_team and away_team:
                # Memories involving either team
                query = query.or_(f'home_team.eq.{home_team},away_team.eq.{home_team},home_team.eq.{away_team},away_team.eq.{away_team}')
            elif home_team:
                query = query.or_(f'home_team.eq.{home_team},away_team.eq.{home_team}')
            elif away_team:
                query = query.or_(f'home_team.eq.{away_team},away_team.eq.{away_team}')

            result = query.order('created_at', desc=True).limit(limit).execute()
            memories = result.data or []

            # Add relevance explanations and similarity scores
            for mem in memories:
                mem['similarity_score'] = self._calculate_team_similarity_score(mem, game_context)
                mem['relevance_explanation'] = self._generate_team_relevance_explanation(mem, game_context)
                mem['bucket_type'] = MemoryBucketType.TEAM_SPECIFIC.value

            logger.info(f"✅ Retrieved {len(memories)} team-specific memories for {expert_id}")
            return memories

        except Exception as e:
            logger.error(f"❌ Error retrieving team-specific memories: {e}")
            return []

    async def _retrieve_matchup_specific_memories(self, expert_id: str, game_context: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        Retrieve memories of head-to-head patterns between specific teams.

        Requirements: 3.2, 8.1
        """
        try:
            home_team = game_context.get('home_team')
            away_team = game_context.get('away_team')

            if not home_team or not away_team:
                logger.warning("Both home_team and away_team required for matchup-specific memory retrieval")
                return []

            # Query for exact matchup memories (both directions) with temporal filtering
            base_query = self.supabase.table('expert_episodic_memories') \
                .select('*') \
                .eq('expert_id', expert_id)

            filtered_query = self.apply_temporal_filtering(expert_id, base_query)

            result = filtered_query \
                .or_(f'and(home_team.eq.{home_team},away_team.eq.{away_team}),and(home_team.eq.{away_team},away_team.eq.{home_team})') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()

            memories = result.data or []

            # Add relevance explanations and similarity scores
            for mem in memories:
                mem['similarity_score'] = 0.95  # High similarity for exact matchups
                mem['relevance_explanation'] = self._generate_matchup_relevance_explanation(mem, game_context)
                mem['bucket_type'] = MemoryBucketType.MATCHUP_SPECIFIC.value

            logger.info(f"✅ Retrieved {len(memories)} matchup-specific memories for {expert_id} ({home_team} vs {away_team})")
            return memories

        except Exception as e:
            logger.error(f"❌ Error retrieving matchup-specific memories: {e}")
            return []

    async def _retrieve_situational_memories(self, expert_id: str, game_context: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        Retrieve memories based on situational contexts (weather, primetime, playoff contexts).

        Requirements: 3.3, 8.1
        """
        try:
            # Extract situational factors from game_context
            situational_factors = []

            if game_context.get('is_primetime'):
                situational_factors.append('is_primetime')
            if game_context.get('is_divisional'):
                situational_factors.append('is_divisional')
            if game_context.get('playoff_implications'):
                situational_factors.append('playoff_implications')
            if game_context.get('weather_conditions'):
                weather = game_context['weather_conditions']
                if isinstance(weather, dict):
                    if weather.get('temperature', 70) < 32:
                        situational_factors.append('cold_weather')
                    if weather.get('precipitation', 0) > 0:
                        situational_factors.append('precipitation')
                    if weather.get('wind_speed', 0) > 15:
                        situational_factors.append('high_wind')

            if not situational_factors:
                logger.info("No situational factors found for situational memory retrieval")
                return []

            # Query memories with matching contextual factors using temporal filtering
            memories = []
            for factor in situational_factors:
                base_query = self.supabase.table('expert_episodic_memories') \
                    .select('*') \
                    .eq('expert_id', expert_id)

                filtered_query = self.apply_temporal_filtering(expert_id, base_query)

                result = filtered_query \
                    .contains('contextual_factors', [{'factor': factor}]) \
                    .order('created_at', desc=True) \
                    .limit(limit // len(situational_factors) + 1) \
                    .execute()

                factor_memories = result.data or []
                for mem in factor_memories:
                    mem['similarity_score'] = self._calculate_situational_similarity_score(mem, game_context)
                    mem['relevance_explanation'] = self._generate_situational_relevance_explanation(mem, game_context, factor)
                    mem['bucket_type'] = MemoryBucketType.SITUATIONAL.value
                    mem['matching_factor'] = factor

                memories.extend(factor_memories)

            # Remove duplicates and sort by similarity
            unique_memories = {mem['memory_id']: mem for mem in memories}.values()
            sorted_memories = sorted(unique_memories, key=lambda x: x['similarity_score'], reverse=True)[:limit]

            logger.info(f"✅ Retrieved {len(sorted_memories)} situational memories for {expert_id} (factors: {situational_factors})")
            return sorted_memories

        except Exception as e:
            logger.error(f"❌ Error retrieving situational memories: {e}")
            return []

    async def _retrieve_personal_learning_memories(self, expert_id: str, game_context: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        Retrieve expert's own pattern recognition and learning memories.

        Requirements: 3.4, 8.2
        """
        try:
            # Query for reflection and learning memory types with temporal filtering
            learning_memory_types = [
                'success_pattern', 'failure_analysis', 'confidence_calibration',
                'factor_weighting', 'pattern_recognition', 'post_game_reflection'
            ]

            base_query = self.supabase.table('expert_episodic_memories') \
                .select('*') \
                .eq('expert_id', expert_id)

            filtered_query = self.apply_temporal_filtering(expert_id, base_query)

            result = filtered_query \
                .in_('memory_type', learning_memory_types) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()

            memories = result.data or []

            # Add relevance explanations and similarity scores
            for mem in memories:
                mem['similarity_score'] = self._calculate_learning_similarity_score(mem, game_context)
                mem['relevance_explanation'] = self._generate_learning_relevance_explanation(mem, game_context)
                mem['bucket_type'] = MemoryBucketType.PERSONAL_LEARNING.value

            logger.info(f"✅ Retrieved {len(memories)} personal learning memories for {expert_id}")
            return memories

        except Exception as e:
            logger.error(f"❌ Error retrieving personal learning memories: {e}")
            return []

    async def _retrieve_comprehensive_memories(self, expert_id: str, game_context: Dict[str, Any], limit: int, team_specific: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve memories from all bucket types and combine them intelligently.
        Maintains backward compatibility with the original method.
        """
        try:
            # Distribute limit across bucket types
            bucket_limit = max(1, limit // 4)

            # Retrieve from each bucket type
            team_memories = await self._retrieve_team_specific_memories(expert_id, game_context, bucket_limit)
            matchup_memories = await self._retrieve_matchup_specific_memories(expert_id, game_context, bucket_limit)
            situational_memories = await self._retrieve_situational_memories(expert_id, game_context, bucket_limit)
            learning_memories = await self._retrieve_personal_learning_memories(expert_id, game_context, bucket_limit)

            # Combine all memories
            all_memories = team_memories + matchup_memories + situational_memories + learning_memories

            # Remove duplicates based on memory_id
            unique_memories = {mem['memory_id']: mem for mem in all_memories}.values()

            # Sort by similarity score and limit results
            sorted_memories = sorted(unique_memories, key=lambda x: x.get('similarity_score', 0), reverse=True)[:limit]

            # Try vector search if available and team_specific is True
            if team_specific and 'home_team' in game_context and 'away_team' in game_context:
                try:
                    vector_memories = await self._try_vector_search(expert_id, game_context, limit)
                    if vector_memories:
                        # Merge vector results with bucket results, prioritizing vector search
                        vector_ids = {mem['memory_id'] for mem in vector_memories}
                        bucket_memories = [mem for mem in sorted_memories if mem['memory_id'] not in vector_ids]

                        # Combine and limit
                        combined_memories = vector_memories + bucket_memories
                        sorted_memories = combined_memories[:limit]

                        logger.info(f"✅ Enhanced comprehensive memories with vector search for {expert_id}")
                except Exception as vector_error:
                    logger.warning(f"⚠️ Vector search enhancement failed: {vector_error}")

            logger.info(f"✅ Retrieved {len(sorted_memories)} comprehensive memories for {expert_id}")
            return sorted_memories

        except Exception as e:
            logger.error(f"❌ Error retrieving comprehensive memories: {e}")
            return []

    async def _try_vector_search(self, expert_id: str, game_context: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Try vector similarity search with fallback handling"""
        try:
            home_team = game_context['home_team']
            away_team = game_context['away_team']

            # Create query text for embedding
            query_text = f"{away_team} at {home_team} game prediction analysis"

            # Generate embedding for the query using our unified client
            import sys, os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
            from services.unified_ai_client import UnifiedAIClient

            ai_client = UnifiedAIClient()
            query_response = ai_client.create_embedding(query_text)
            query_embedding = query_response.embedding

            # Use the recency-aware search function from our optimized schema
            result = self.supabase.rpc('search_expert_memories', {
                'p_expert_id': expert_id,
                'p_query_embedding': query_embedding,
                'p_match_threshold': 0.5,  # Lower threshold for more results
                'p_match_count': limit,
                'p_alpha': 0.8  # 80% similarity, 20% recency
            }).execute()

            memories = result.data or []

            # Add the similarity score from the function result
            for mem in memories:
                if 'combined_score' not in mem:
                    mem['similarity_score'] = 0.7  # Fallback
                else:
                    mem['similarity_score'] = mem['combined_score']
                mem['bucket_type'] = 'vector_search'
                mem['relevance_explanation'] = f"Vector similarity match for {home_team} vs {away_team}"

            logger.info(f"✅ Vector search retrieved {len(memories)} memories for {expert_id}")
            return memories

        except Exception as e:
            logger.warning(f"⚠️ Vector search failed: {e}")
            return []

    def _calculate_team_similarity_score(self, memory: Dict[str, Any], game_context: Dict[str, Any]) -> float:
        """Calculate similarity score for team-specific memories"""
        score = 0.5  # Base score

        mem_home = memory.get('home_team')
        mem_away = memory.get('away_team')
        ctx_home = game_context.get('home_team')
        ctx_away = game_context.get('away_team')

        # Exact team matches get higher scores
        if mem_home == ctx_home or mem_home == ctx_away:
            score += 0.2
        if mem_away == ctx_home or mem_away == ctx_away:
            score += 0.2

        # Same matchup gets highest score
        if (mem_home == ctx_home and mem_away == ctx_away) or (mem_home == ctx_away and mem_away == ctx_home):
            score += 0.3

        return min(1.0, score)

    def _calculate_situational_similarity_score(self, memory: Dict[str, Any], game_context: Dict[str, Any]) -> float:
        """Calculate similarity score for situational memories"""
        score = 0.6  # Base score for situational match

        # Add bonus for multiple matching factors
        contextual_factors = memory.get('contextual_factors', [])
        matching_factors = 0

        for factor in contextual_factors:
            if isinstance(factor, dict):
                factor_name = factor.get('factor', '')
                if factor_name in ['is_primetime', 'is_divisional', 'playoff_implications']:
                    if game_context.get(factor_name):
                        matching_factors += 1
                elif factor_name in ['cold_weather', 'precipitation', 'high_wind']:
                    # Weather factors get partial credit
                    matching_factors += 0.5

        score += matching_factors * 0.1
        return min(1.0, score)

    def _calculate_learning_similarity_score(self, memory: Dict[str, Any], game_context: Dict[str, Any]) -> float:
        """Calculate similarity score for personal learning memories"""
        score = 0.4  # Base score for learning memories

        # Recent learning memories are more relevant
        created_at = memory.get('created_at')
        if created_at:
            try:
                from datetime import datetime, timezone
                memory_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                days_old = (datetime.now(timezone.utc) - memory_date).days

                # More recent memories get higher scores
                if days_old < 7:
                    score += 0.3
                elif days_old < 30:
                    score += 0.2
                elif days_old < 90:
                    score += 0.1
            except:
                pass

        # High emotional weight memories are more relevant
        emotional_weight = memory.get('emotional_weight', 0.5)
        score += emotional_weight * 0.3

        return min(1.0, score)

    def _generate_team_relevance_explanation(self, memory: Dict[str, Any], game_context: Dict[str, Any]) -> str:
        """Generate explanation for why a team-specific memory is relevant"""
        mem_home = memory.get('home_team', 'Unknown')
        mem_away = memory.get('away_team', 'Unknown')
        ctx_home = game_context.get('home_team', 'Unknown')
        ctx_away = game_context.get('away_team', 'Unknown')

        if (mem_home == ctx_home and mem_away == ctx_away) or (mem_home == ctx_away and mem_away == ctx_home):
            return f"Exact matchup: Previous {mem_away} vs {mem_home} game"
        elif mem_home in [ctx_home, ctx_away]:
            return f"Team pattern: Previous experience with {mem_home} as home team"
        elif mem_away in [ctx_home, ctx_away]:
            return f"Team pattern: Previous experience with {mem_away} as away team"
        else:
            return f"Team experience: Related to {mem_away} at {mem_home}"

    def _generate_matchup_relevance_explanation(self, memory: Dict[str, Any], game_context: Dict[str, Any]) -> str:
        """Generate explanation for why a matchup-specific memory is relevant"""
        mem_home = memory.get('home_team', 'Unknown')
        mem_away = memory.get('away_team', 'Unknown')
        return f"Head-to-head pattern: Previous {mem_away} vs {mem_home} matchup"

    def _generate_situational_relevance_explanation(self, memory: Dict[str, Any], game_context: Dict[str, Any], matching_factor: str) -> str:
        """Generate explanation for why a situational memory is relevant"""
        factor_explanations = {
            'is_primetime': 'Similar primetime game context',
            'is_divisional': 'Similar divisional rivalry context',
            'playoff_implications': 'Similar playoff implications context',
            'cold_weather': 'Similar cold weather conditions',
            'precipitation': 'Similar weather with precipitation',
            'high_wind': 'Similar high wind conditions'
        }

        explanation = factor_explanations.get(matching_factor, f'Similar {matching_factor} context')
        mem_home = memory.get('home_team', 'Unknown')
        mem_away = memory.get('away_team', 'Unknown')
        return f"{explanation} (from {mem_away} at {mem_home})"

    def _generate_learning_relevance_explanation(self, memory: Dict[str, Any], game_context: Dict[str, Any]) -> str:
        """Generate explanation for why a learning memory is relevant"""
        memory_type = memory.get('memory_type', 'learning')

        type_explanations = {
            'success_pattern': 'Previous successful prediction pattern',
            'failure_analysis': 'Previous prediction failure analysis',
            'confidence_calibration': 'Confidence calibration learning',
            'factor_weighting': 'Factor importance learning',
            'pattern_recognition': 'General pattern recognition insight',
            'post_game_reflection': 'Post-game reflection insight'
        }

        explanation = type_explanations.get(memory_type, 'Personal learning insight')

        # Add emotional context if available
        emotional_weight = memory.get('emotional_weight', 0)
        if emotional_weight > 0.7:
            explanation += ' (high impact learning)'
        elif emotional_weight > 0.5:
            explanation += ' (moderate impact learning)'

        return explanation

    async def track_memory_influences(
        self,
        memories: List[Dict[str, Any]],
        game_context: Dict[str, Any],
        expert_id: str
    ) -> List[MemoryInfluence]:
        """
        Create MemoryInfluence tracking for retrieved memories.

        Requirements: 3.5, 8.3, 8.4
        """
        try:
            influences = []

            for memory in memories:
                # Calculate temporal weight based on memory age and access patterns
                temporal_weight = await self._calculate_temporal_weight(memory, expert_id)

                # Get similarity score (should already be set by retrieval methods)
                similarity_score = memory.get('similarity_score', 0.5)

                # Create MemoryInfluence object
                influence = MemoryInfluence.from_memory(
                    memory=memory,
                    similarity_score=similarity_score,
                    temporal_weight=temporal_weight,
                    game_context=game_context
                )

                influences.append(influence)

                # Update memory access tracking
                await self._update_memory_access(memory['memory_id'], expert_id)

            # Sort by influence strength
            influences.sort(key=lambda x: x.influence_strength, reverse=True)

            logger.info(f"✅ Tracked {len(influences)} memory influences for {expert_id}")
            return influences

        except Exception as e:
            logger.error(f"❌ Error tracking memory influences: {e}")
            return []

    async def _calculate_temporal_weight(self, memory: Dict[str, Any], expert_id: str) -> float:
        """
        Calculate temporal weight using expert-specific decay parameters.

        Requirements: 5.1, 5.2, 5.3
        """
        try:
            if not self.temporal_decay_service:
                # Fallback to simple age-based calculation
                return self._calculate_simple_temporal_weight(memory)

            # Get expert type from expert_id
            expert_type = self.temporal_decay_service.get_expert_type_from_id(expert_id)

            # Calculate memory age
            created_at = memory.get('created_at')
            if isinstance(created_at, str):
                try:
                    memory_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    days_old = (datetime.now(memory_date.tzinfo or datetime.now().tzinfo) - memory_date).days
                except:
                    days_old = 30  # Default fallback
            else:
                days_old = 30  # Default fallback

            # Get memory category for category-specific decay
            memory_category = memory.get('memory_category') or memory.get('memory_type')

            # Calculate temporal decay score
            temporal_weight = self.temporal_decay_service.calculate_temporal_decay_score(
                expert_type=expert_type,
                memory_age_days=days_old,
                memory_category=memory_category
            )

            # Apply access count reinforcement
            access_count = memory.get('access_count', 0)
            if access_count > 0:
                # Boost frequently accessed memories (up to 20% boost)
                reinforcement_boost = min(0.2, access_count * 0.02)
                temporal_weight = min(1.0, temporal_weight + reinforcement_boost)

            # Apply memory decay field if present
            memory_decay = memory.get('memory_decay', 1.0)
            temporal_weight *= memory_decay

            logger.debug(f"Temporal weight for {expert_id} memory {memory.get('memory_id', 'unknown')}: {temporal_weight:.3f} (age: {days_old}d)")

            return max(0.01, min(1.0, temporal_weight))

        except Exception as e:
            logger.error(f"❌ Error calculating temporal weight: {e}")
            return self._calculate_simple_temporal_weight(memory)

    def _calculate_simple_temporal_weight(self, memory: Dict[str, Any]) -> float:
        """Fallback temporal weight calculation without decay service"""
        try:
            created_at = memory.get('created_at')
            if isinstance(created_at, str):
                try:
                    memory_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    days_old = (datetime.now(memory_date.tzinfo or datetime.now().tzinfo) - memory_date).days
                except:
                    return 0.5
            else:
                return 0.5

            # Simple exponential decay with 180-day half-life
            temporal_weight = math.pow(0.5, days_old / 180)

            # Apply access count reinforcement
            access_count = memory.get('access_count', 0)
            if access_count > 0:
                reinforcement_boost = min(0.15, access_count * 0.015)
                temporal_weight = min(1.0, temporal_weight + reinforcement_boost)

            return max(0.01, min(1.0, temporal_weight))

        except Exception as e:
            logger.error(f"❌ Error in simple temporal weight calculation: {e}")
            return 0.5

    async def _update_memory_access(self, memory_id: str, expert_id: str) -> bool:
        """
        Update memory access tracking for reinforcement.

        Requirements: 5.4 (memory access count updating and reinforcement)
        """
        try:
            # Update access count and last accessed timestamp
            result = self.supabase.table('expert_episodic_memories') \
                .update({
                    'access_count': 'access_count + 1',
                    'last_accessed': datetime.now().isoformat()
                }) \
                .eq('memory_id', memory_id) \
                .eq('expert_id', expert_id) \
                .execute()

            if result.data:
                logger.debug(f"✅ Updated access tracking for memory {memory_id}")
                return True
            else:
                logger.warning(f"⚠️ No memory found to update: {memory_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Error updating memory access: {e}")
            return False

    def apply_temporal_filtering(self, expert_id: str, base_query) -> Any:
        """
        Apply temporal filtering to optimize memory retrieval performance.

        Requirements: 5.6 (temporal filtering for performance optimization)
        """
        try:
            if not self.temporal_decay_service:
                # Default filtering - last 365 days
                from datetime import timedelta
                cutoff_date = datetime.now() - timedelta(days=365)
                return base_query.gte('created_at', cutoff_date.isoformat())

            # Get expert type and calculate optimal cutoff
            expert_type = self.temporal_decay_service.get_expert_type_from_id(expert_id)
            max_age_days = self.temporal_decay_service.apply_temporal_filtering(expert_type)

            # Apply cutoff date
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            filtered_query = base_query.gte('created_at', cutoff_date.isoformat())

            logger.debug(f"Applied temporal filtering for {expert_id}: max age {max_age_days} days")
            return filtered_query

        except Exception as e:
            logger.error(f"❌ Error applying temporal filtering: {e}")
            # Fallback to unfiltered query
            return base_queryte temporal weight combining temporal decay and reinforcement.

        Requirements: 5.4
        """
        try:
            # Get expert-specific temporal parameters (fallback to defaults)
            expert_config = self.expert_personalities.get(expert_id, {})
            half_life_days = expert_config.get('memory_half_life', 90)  # Default 90 days

            # Calculate age-based decay
            created_at = memory.get('created_at')
            if created_at:
                try:
                    from datetime import datetime, timezone
                    memory_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    age_days = (datetime.now(timezone.utc) - memory_date).days

                    # Exponential decay: 0.5^(age_days / half_life_days)
                    temporal_decay = 0.5 ** (age_days / half_life_days)
                except:
                    temporal_decay = 0.5  # Fallback
            else:
                temporal_decay = 0.5  # Fallback

            # Apply reinforcement based on access patterns
            access_count = memory.get('access_count', 0)
            retrieval_count = memory.get('retrieval_count', 0)
            total_accesses = access_count + retrieval_count

            # Reinforcement boost (logarithmic to prevent runaway growth)
            import math
            reinforcement_boost = min(0.3, math.log(total_accesses + 1) * 0.1)

            # Combine temporal decay with reinforcement
            temporal_weight = min(1.0, temporal_decay + reinforcement_boost)

            return temporal_weight

        except Exception as e:
            logger.warning(f"⚠️ Error calculating temporal weight: {e}")
            return 0.5  # Fallback

    async def _update_memory_access(self, memory_id: str, expert_id: str) -> bool:
        """
        Update memory access count and last accessed timestamp for reinforcement.

        Requirements: 5.4
        """
        try:
            # Get current access count
            result = self.supabase.table('expert_episodic_memories') \
                .select('access_count, retrieval_count') \
                .eq('memory_id', memory_id) \
                .eq('expert_id', expert_id) \
                .execute()

            if result.data and len(result.data) > 0:
                current_data = result.data[0]
                current_access_count = current_data.get('access_count', 0)
                current_retrieval_count = current_data.get('retrieval_count', 0)

                # Update access count and timestamp
                update_result = self.supabase.table('expert_episodic_memories') \
                    .update({
                        'access_count': current_access_count + 1,
                        'last_accessed': datetime.now().isoformat()
                    }) \
                    .eq('memory_id', memory_id) \
                    .eq('expert_id', expert_id) \
                    .execute()

                if update_result.data:
                    logger.debug(f"✅ Updated access count for memory {memory_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Failed to update access count for memory {memory_id}")
                    return False
            else:
                logger.warning(f"⚠️ Memory {memory_id} not found for access update")
                return False

        except Exception as e:
            logger.error(f"❌ Error updating memory access: {e}")
            return False

    async def generate_memory_influence_explanation(
        self,
        influences: List[MemoryInfluence],
        game_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive explanation of how memories influenced the analysis.

        Requirements: 8.4
        """
        try:
            if not influences:
                return {
                    'total_influences': 0,
                    'explanation': 'No relevant memories found for this analysis.',
                    'influence_breakdown': {}
                }

            # Sort influences by strength
            sorted_influences = sorted(influences, key=lambda x: x.influence_strength, reverse=True)

            # Group by bucket type
            bucket_breakdown = {}
            for influence in sorted_influences:
                bucket_type = influence.bucket_type or 'unknown'
                if bucket_type not in bucket_breakdown:
                    bucket_breakdown[bucket_type] = []
                bucket_breakdown[bucket_type].append(influence)

            # Generate explanation text
            explanation_parts = []

            # Overall summary
            total_influences = len(influences)
            avg_influence = sum(inf.influence_strength for inf in influences) / total_influences
            explanation_parts.append(
                f"Analysis influenced by {total_influences} relevant memories "
                f"(average influence strength: {avg_influence:.2f})"
            )

            # Top influences
            top_influences = sorted_influences[:3]
            if top_influences:
                explanation_parts.append("\nMost influential memories:")
                for i, influence in enumerate(top_influences, 1):
                    explanation_parts.append(
                        f"{i}. {influence.memory_summary} "
                        f"(influence: {influence.influence_strength:.2f}) - {influence.why_relevant}"
                    )

            # Bucket type breakdown
            if len(bucket_breakdown) > 1:
                explanation_parts.append(f"\nMemory sources:")
                for bucket_type, bucket_influences in bucket_breakdown.items():
                    avg_bucket_influence = sum(inf.influence_strength for inf in bucket_influences) / len(bucket_influences)
                    explanation_parts.append(
                        f"- {bucket_type.replace('_', ' ').title()}: {len(bucket_influences)} memories "
                        f"(avg influence: {avg_bucket_influence:.2f})"
                    )

            # Temporal analysis
            recent_influences = [inf for inf in influences if inf.temporal_weight > 0.7]
            if recent_influences:
                explanation_parts.append(
                    f"\n{len(recent_influences)} recent high-impact memories strongly influenced this analysis."
                )

            explanation = '\n'.join(explanation_parts)

            # Detailed breakdown for programmatic use
            influence_breakdown = {
                'by_bucket_type': {
                    bucket_type: {
                        'count': len(bucket_influences),
                        'avg_influence': sum(inf.influence_strength for inf in bucket_influences) / len(bucket_influences),
                        'top_influence': max(inf.influence_strength for inf in bucket_influences),
                        'memories': [inf.to_dict() for inf in bucket_influences[:2]]  # Top 2 per bucket
                    }
                    for bucket_type, bucket_influences in bucket_breakdown.items()
                },
                'temporal_analysis': {
                    'recent_memories': len([inf for inf in influences if inf.temporal_weight > 0.7]),
                    'older_memories': len([inf for inf in influences if inf.temporal_weight <= 0.7]),
                    'avg_temporal_weight': sum(inf.temporal_weight for inf in influences) / len(influences)
                },
                'similarity_analysis': {
                    'high_similarity': len([inf for inf in influences if inf.similarity_score > 0.8]),
                    'medium_similarity': len([inf for inf in influences if 0.6 <= inf.similarity_score <= 0.8]),
                    'low_similarity': len([inf for inf in influences if inf.similarity_score < 0.6]),
                    'avg_similarity': sum(inf.similarity_score for inf in influences) / len(influences)
                }
            }

            result = {
                'total_influences': total_influences,
                'avg_influence_strength': avg_influence,
                'explanation': explanation,
                'influence_breakdown': influence_breakdown,
                'top_influences': [inf.to_dict() for inf in top_influences]
            }

            logger.info(f"✅ Generated memory influence explanation with {total_influences} influences")
            return result

        except Exception as e:
            logger.error(f"❌ Error generating memory influence explanation: {e}")
            return {
                'total_influences': 0,
                'explanation': f'Error generating explanation: {str(e)}',
                'influence_breakdown': {}
            }

    async def retrieve_memories_with_influence_tracking(
        self,
        expert_id: str,
        game_context: Dict[str, Any],
        limit: int = 5,
        bucket_type: MemoryBucketType = MemoryBucketType.ALL
    ) -> Dict[str, Any]:
        """
        Enhanced memory retrieval that includes influence tracking and explanation.

        This is the main method that should be used by the AI orchestrator.

        Requirements: 3.5, 8.3, 8.4, 5.4
        """
        try:
            # Retrieve memories using existing method
            memories = await self.retrieve_memories(expert_id, game_context, limit, True, bucket_type)

            if not memories:
                return {
                    'memories': [],
                    'influences': [],
                    'influence_explanation': {
                        'total_influences': 0,
                        'explanation': 'No relevant memories found.',
                        'influence_breakdown': {}
                    }
                }

            # Track memory influences
            influences = await self.track_memory_influences(memories, game_context, expert_id)

            # Generate influence explanation
            influence_explanation = await self.generate_memory_influence_explanation(influences, game_context)

            # Add influence data to memories
            influence_by_id = {inf.memory_id: inf for inf in influences}
            for memory in memories:
                memory_id = memory.get('memory_id')
                if memory_id in influence_by_id:
                    influence = influence_by_id[memory_id]
                    memory['influence_data'] = influence.to_dict()

            result = {
                'memories': memories,
                'influences': [inf.to_dict() for inf in influences],
                'influence_explanation': influence_explanation,
                'retrieval_metadata': {
                    'expert_id': expert_id,
                    'bucket_type': bucket_type.value,
                    'game_context': game_context,
                    'retrieval_timestamp': datetime.now().isoformat()
                }
            }

            logger.info(f"✅ Retrieved {len(memories)} memories with influence tracking for {expert_id}")
            return result

        except Exception as e:
            logger.error(f"❌ Error in enhanced memory retrieval: {e}")
            return {
                'memories': [],
                'influences': [],
                'influence_explanation': {
                    'total_influences': 0,
                    'explanation': f'Error in memory retrieval: {str(e)}',
                    'influence_breakdown': {}
                }
            }

    async def store_reflection_memory(self, reflection_memory) -> bool:
        """
        Store post-game reflection memory with comprehensive learning insights.

        Extends existing memory storage to support reflection-specific data:
        - Uses existing memory_type field with 'post_game_reflection' value
        - Uses existing contextual_factors, lessons_learned, emotional_intensity fields
        - Implements memory categorization (success patterns, failure analysis, factor weighting)
        - Adds emotional weighting for significant wins/losses using existing emotional_weight field

        Requirements: 4.4, 4.5, 4.6, 3.3, 3.4
        """
        try:
            import hashlib

            # Generate memory_id
            memory_id = reflection_memory.memory_id

            # Prepare contextual factors from game context and reflection insights
            contextual_factors = []

            # Game context factors
            contextual_factors.extend([
                {'factor': 'home_team', 'value': reflection_memory.game_context.home_team},
                {'factor': 'away_team', 'value': reflection_memory.game_context.away_team},
                {'factor': 'season', 'value': reflection_memory.game_context.season},
                {'factor': 'week', 'value': reflection_memory.game_context.week},
                {'factor': 'is_divisional', 'value': reflection_memory.game_context.is_divisional},
                {'factor': 'is_primetime', 'value': reflection_memory.game_context.is_primetime}
            ])

            # Reflection-specific factors
            contextual_factors.extend([
                {'factor': 'reflection_type', 'value': reflection_memory.reflection_type.value},
                {'factor': 'overall_accuracy', 'value': reflection_memory.overall_accuracy},
                {'factor': 'successful_predictions_count', 'value': len(reflection_memory.successful_predictions)},
                {'factor': 'high_confidence_errors_count', 'value': len(reflection_memory.high_confidence_errors)},
                {'factor': 'surprise_factor', 'value': reflection_memory.surprise_factor}
            ])

            # Add factor adjustments as contextual factors
            for factor_name, adjustment in reflection_memory.factor_adjustments.items():
                contextual_factors.append({
                    'factor': f'factor_adjustment_{factor_name}',
                    'value': adjustment
                })

            # Add confidence calibration as contextual factors
            for calibration_type, adjustment in reflection_memory.confidence_calibration.items():
                contextual_factors.append({
                    'factor': f'confidence_calibration_{calibration_type}',
                    'value': adjustment
                })

            # Prepare lessons learned (combine all learning insights)
            lessons_learned = []
            lessons_learned.extend(reflection_memory.lessons_learned)
            lessons_learned.extend(reflection_memory.pattern_insights)

            # Add category-specific lessons
            for category_accuracy in reflection_memory.category_accuracies:
                if not category_accuracy.is_correct and category_accuracy.confidence > 0.7:
                    lessons_learned.append(
                        f"High confidence error in {category_accuracy.category_name}: "
                        f"predicted {category_accuracy.predicted_value}, actual {category_accuracy.actual_value}"
                    )
                elif category_accuracy.is_correct and category_accuracy.accuracy_score >= 0.8:
                    lessons_learned.append(
                        f"Strong performance in {category_accuracy.category_name}: "
                        f"correctly predicted {category_accuracy.predicted_value}"
                    )

            # Prepare prediction data (summary of all predictions made)
            prediction_data = {
                'total_categories': len(reflection_memory.category_accuracies),
                'correct_predictions': len(reflection_memory.successful_predictions),
                'overall_accuracy': reflection_memory.overall_accuracy,
                'high_confidence_errors': reflection_memory.high_confidence_errors,
                'successful_predictions': reflection_memory.successful_predictions,
                'memory_influences_count': len(reflection_memory.memory_influences_used),
                'ai_reflection_summary': reflection_memory.ai_reflection_text[:500] + "..." if len(reflection_memory.ai_reflection_text) > 500 else reflection_memory.ai_reflection_text
            }

            # Prepare actual outcome (game results)
            actual_outcome = {
                'game_id': reflection_memory.game_id,
                'reflection_type': reflection_memory.reflection_type.value,
                'overall_accuracy_achieved': reflection_memory.overall_accuracy,
                'learning_insights_count': len(reflection_memory.lessons_learned) + len(reflection_memory.pattern_insights),
                'factor_adjustments_count': len(reflection_memory.factor_adjustments),
                'confidence_calibration_adjustments': len(reflection_memory.confidence_calibration)
            }

            # Determine memory categorization based on reflection type and performance
            memory_type = self._categorize_reflection_memory(reflection_memory)

            # Calculate emotional weight (higher for significant wins/losses)
            emotional_weight = self._calculate_emotional_weight(reflection_memory)

            # Create memory record using existing schema fields
            memory_record = {
                'memory_id': memory_id,
                'expert_id': reflection_memory.expert_id,
                'game_id': reflection_memory.game_id,
                'memory_type': memory_type,  # Uses existing field with reflection-specific values
                'emotional_state': self._determine_emotional_state(reflection_memory),
                'prediction_data': prediction_data,
                'actual_outcome': actual_outcome,
                'contextual_factors': contextual_factors,  # Uses existing field
                'lessons_learned': lessons_learned,  # Uses existing field
                'emotional_intensity': reflection_memory.emotional_intensity,  # Uses existing field
                'memory_vividness': reflection_memory.memory_vividness,
                'retrieval_count': 0,
                'memory_decay': 1.0,
                'home_team': reflection_memory.game_context.home_team,
                'away_team': reflection_memory.game_context.away_team,
                'emotional_weight': emotional_weight,  # Uses existing emotional_weight field
                'created_at': reflection_memory.reflection_timestamp.isoformat()
            }

            # Store in existing expert_episodic_memories table
            result = self.supabase.table('expert_episodic_memories').insert(memory_record).execute()

            if result.data:
                logger.info(f"✅ Stored reflection memory for {reflection_memory.expert_id} game {reflection_memory.game_id}")
                logger.info(f"   Memory type: {memory_type}, Accuracy: {reflection_memory.overall_accuracy:.1%}")
                logger.info(f"   Lessons learned: {len(lessons_learned)}, Factor adjustments: {len(reflection_memory.factor_adjustments)}")
                return True
            else:
                logger.error(f"❌ Failed to store reflection memory: {result}")
                return False

        except Exception as e:
            logger.error(f"❌ Error storing reflection memory: {e}")
            return False

    def _categorize_reflection_memory(self, reflection_memory) -> str:
        """
        Categorize reflection memory based on performance and type.

        Uses existing memory_type field with reflection-specific values:
        - 'success_pattern': High accuracy performance analysis
        - 'failure_analysis': Poor performance analysis and corrections
        - 'confidence_calibration': Confidence adjustment insights
        - 'factor_weighting': Factor importance adjustments
        - 'pattern_recognition': General pattern insights
        """
        from src.ml.post_game_reflection_system import ReflectionType

        if reflection_memory.reflection_type == ReflectionType.SUCCESS_ANALYSIS:
            return 'success_pattern'
        elif reflection_memory.reflection_type == ReflectionType.FAILURE_ANALYSIS:
            return 'failure_analysis'
        elif reflection_memory.reflection_type == ReflectionType.CONFIDENCE_CALIBRATION:
            return 'confidence_calibration'
        elif reflection_memory.reflection_type == ReflectionType.FACTOR_WEIGHTING:
            return 'factor_weighting'
        else:
            return 'pattern_recognition'

    def _determine_emotional_state(self, reflection_memory) -> str:
        """Determine emotional state based on reflection results"""
        if reflection_memory.overall_accuracy >= 0.8:
            return 'confident'
        elif reflection_memory.overall_accuracy >= 0.6:
            return 'satisfied'
        elif reflection_memory.overall_accuracy >= 0.4:
            return 'concerned'
        elif len(reflection_memory.high_confidence_errors) > 0:
            return 'frustrated'
        else:
            return 'disappointed'

    def _calculate_emotional_weight(self, reflection_memory) -> float:
        """
        Calculate emotional weight for significant wins/losses.

        Uses existing emotional_weight field to prioritize important learning experiences:
        - High accuracy: Positive reinforcement weight
        - High confidence errors: High negative learning weight
        - Surprise outcomes: Increased weight for unexpected results
        """
        base_weight = 0.5

        # High accuracy increases positive weight
        if reflection_memory.overall_accuracy >= 0.8:
            base_weight += 0.3
        elif reflection_memory.overall_accuracy >= 0.7:
            base_weight += 0.2

        # Poor accuracy increases learning weight
        if reflection_memory.overall_accuracy <= 0.3:
            base_weight += 0.4
        elif reflection_memory.overall_accuracy <= 0.5:
            base_weight += 0.2

        # High confidence errors are emotionally significant
        if reflection_memory.high_confidence_errors:
            base_weight += 0.2 * len(reflection_memory.high_confidence_errors)

        # Surprise factor increases emotional weight
        base_weight += reflection_memory.surprise_factor * 0.3

        # Factor adjustments indicate important learning
        if reflection_memory.factor_adjustments:
            base_weight += 0.1 * len(reflection_memory.factor_adjustments)

        return min(1.0, base_weight)

    async def retrieve_reflection_memories(
        self,
        expert_id: str,
        memory_types: List[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve reflection memories for learning and pattern analysis.

        Args:
            expert_id: Expert identifier
            memory_types: Filter by memory types (success_pattern, failure_analysis, etc.)
            limit: Maximum memories to retrieve
        """
        try:
            query = self.supabase.table('expert_episodic_memories') \
                .select('*') \
                .eq('expert_id', expert_id)

            # Filter by reflection memory types
            reflection_types = memory_types or [
                'success_pattern', 'failure_analysis', 'confidence_calibration',
                'factor_weighting', 'pattern_recognition'
            ]

            if len(reflection_types) == 1:
                query = query.eq('memory_type', reflection_types[0])
            else:
                query = query.in_('memory_type', reflection_types)

            result = query.order('created_at', desc=True).limit(limit).execute()

            memories = result.data or []
            logger.info(f"✅ Retrieved {len(memories)} reflection memories for {expert_id}")

            return memories

        except Exception as e:
            logger.error(f"❌ Error retrieving reflection memories: {e}")
            return []

    async def get_learning_insights_summary(self, expert_id: str) -> Dict[str, Any]:
        """
        Get summary of learning insights from reflection memories.

        Analyzes stored reflection memories to provide:
        - Success patterns identified
        - Common failure modes
        - Factor adjustment trends
        - Confidence calibration patterns
        """
        try:
            # Get all reflection memories
            reflection_memories = await self.retrieve_reflection_memories(expert_id, limit=50)

            if not reflection_memories:
                return {'expert_id': expert_id, 'total_reflections': 0}

            # Analyze patterns
            success_patterns = []
            failure_patterns = []
            factor_adjustments = {}
            confidence_adjustments = {}

            for memory in reflection_memories:
                memory_type = memory.get('memory_type', '')
                contextual_factors = memory.get('contextual_factors', [])
                lessons_learned = memory.get('lessons_learned', [])

                # Collect success patterns
                if memory_type == 'success_pattern':
                    success_patterns.extend(lessons_learned)

                # Collect failure patterns
                elif memory_type == 'failure_analysis':
                    failure_patterns.extend(lessons_learned)

                # Collect factor adjustments
                for factor in contextual_factors:
                    if isinstance(factor, dict) and factor.get('factor', '').startswith('factor_adjustment_'):
                        factor_name = factor['factor'].replace('factor_adjustment_', '')
                        adjustment_value = factor.get('value', 0)

                        if factor_name not in factor_adjustments:
                            factor_adjustments[factor_name] = []
                        factor_adjustments[factor_name].append(adjustment_value)

                # Collect confidence adjustments
                for factor in contextual_factors:
                    if isinstance(factor, dict) and factor.get('factor', '').startswith('confidence_calibration_'):
                        calibration_type = factor['factor'].replace('confidence_calibration_', '')
                        adjustment_value = factor.get('value', 0)

                        if calibration_type not in confidence_adjustments:
                            confidence_adjustments[calibration_type] = []
                        confidence_adjustments[calibration_type].append(adjustment_value)

            # Calculate average adjustments
            avg_factor_adjustments = {}
            for factor_name, adjustments in factor_adjustments.items():
                avg_factor_adjustments[factor_name] = sum(adjustments) / len(adjustments)

            avg_confidence_adjustments = {}
            for calibration_type, adjustments in confidence_adjustments.items():
                avg_confidence_adjustments[calibration_type] = sum(adjustments) / len(adjustments)

            summary = {
                'expert_id': expert_id,
                'total_reflections': len(reflection_memories),
                'success_patterns_count': len([m for m in reflection_memories if m.get('memory_type') == 'success_pattern']),
                'failure_analyses_count': len([m for m in reflection_memories if m.get('memory_type') == 'failure_analysis']),
                'confidence_calibrations_count': len([m for m in reflection_memories if m.get('memory_type') == 'confidence_calibration']),
                'top_success_patterns': success_patterns[:5],
                'top_failure_patterns': failure_patterns[:5],
                'factor_adjustment_trends': avg_factor_adjustments,
                'confidence_adjustment_trends': avg_confidence_adjustments,
                'recent_reflections': reflection_memories[:3]
            }

            logger.info(f"✅ Generated learning insights summary for {expert_id}")
            return summary

        except Exception as e:
            logger.error(f"❌ Error generating learning insights summary: {e}")
            return {'expert_id': expert_id, 'error': str(e)}


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
