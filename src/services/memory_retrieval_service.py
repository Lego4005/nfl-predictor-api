"""
Memory Retrieval Service - Vector-based episodic memory with recency blending
Implements K=10-20 adaptive retrieval with persona tuning and graceful degradation
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
from loguru import logger

from src.config import settings
from src.database.supabase_client import supabase


@dataclass
class MemoryItem:
    """Individual memory item with scores"""
    memory_id: str
    content: str
    similarity_score: float
    recency_score: float
    combined_score: float
    metadata: Dict[str, Any]


@dataclass
class MemoryContext:
    """Complete memory context for expert prediction"""
    episodic_memories: List[MemoryItem]
    team_knowledge: Dict[str, Any]
    matchup_memories: List[MemoryItem]
    retrieval_stats: Dict[str, Any]


class MemoryRetrievalService:
    """
    Vector-based memory retrieval with adaptive K and recency blending
    Targets p95 < 100ms with graceful degradation
    """

    def __init__(self):
        self.default_k = int(settings.DEFAULT_MEMORY_K)
        self.min_k = int(settings.MIN_MEMORY_K)
        self.max_k = int(settings.MAX_MEMORY_K)
        self.timeout_ms = int(settings.MEMORY_RETRIEVAL_TIMEOUT_MS)

    async def retrieve_memory_context(
        self,
        expert_id: str,
        game_context: Dict[str, Any],
        persona_config: Optional[Dict[str, Any]] = None,
        run_id: str = "run_2025_pilot4"
    ) -> MemoryContext:
        """
        Retrieve complete memory context for expert prediction

        Args:
            expert_id: Expert identifier
            game_context: Current game information
            persona_config: Expert-specific retrieval parameters

        Returns:
            MemoryContext with episodic memories, team knowledge, and matchup data
        """
        start_time = time.time()

        try:
            # Get persona-tuned parameters
            k, alpha = self._get_retrieval_parameters(expert_id, persona_config)

            # Build query embedding from game context
            query_text = self._build_query_text(game_context)

            # Retrieve episodic memories with timeout protection
            episodic_memories = await asyncio.wait_for(
                self._retrieve_episodic_memories(expert_id, query_text, k, alpha, run_id),
                timeout=self.timeout_ms / 1000.0
            )

            # Get team knowledge buckets
            team_knowledge = await self._retrieve_team_knowledge(
                game_context.get('home_team'),
                game_context.get('away_team')
            )

            # Get role-aware matchup memories
            matchup_memories = await self._retrieve_matchup_memories(
                game_context.get('home_team'),
                game_context.get('away_team'),
                expert_id
            )

            retrieval_duration = (time.time() - start_time) * 1000

            # Log performance metrics
            logger.info(f"Memory retrieval completed for {expert_id}", {
                "duration_ms": retrieval_duration,
                "k_used": k,
                "alpha_used": alpha,
                "episodic_count": len(episodic_memories),
                "team_knowledge_keys": len(team_knowledge),
                "matchup_count": len(matchup_memories)
            })

            return MemoryContext(
                episodic_memories=episodic_memories,
                team_knowledge=team_knowledge,
                matchup_memories=matchup_memories,
                retrieval_stats={
                    "duration_ms": retrieval_duration,
                    "k_used": k,
                    "alpha_used": alpha,
                    "target_k": self._get_target_k(expert_id, persona_config),
                    "degraded": k < self._get_target_k(expert_id, persona_config)
                }
            )

        except asyncio.TimeoutError:
            logger.warning(f"Memory retrieval timeout for {expert_id}, falling back")
            return await self._fallback_retrieval(expert_id, game_context, run_id)
        except Exception as e:
            logger.error(f"Memory retrieval failed for {expert_id}: {e}")
            return await self._fallback_retrieval(expert_id, game_context, run_id)

    async def _retrieve_episodic_memories(
        self,
        expert_id: str,
        query_text: str,
        k: int,
        alpha: float,
        run_id: str
    ) -> List[MemoryItem]:
        """
        Retrieve episodic memories using pgvector RPC with recency blending
        """
        try:
            # Call pgvector RPC function with run_id filtering
            result = await supabase.rpc(
                'search_expert_memories',
                {
                    'p_expert_id': expert_id,
                    'p_query_text': query_text,
                    'p_k': k,
                    'p_alpha': alpha,
                    'p_run_id': run_id
                }
            ).execute()

            if not result.data:
                logger.warning(f"No memories found for expert {expert_id}")
                return []

            memories = []
            for item in result.data:
                memories.append(MemoryItem(
                    memory_id=item['memory_id'],
                    content=item['content'],
                    similarity_score=item['similarity_score'],
                    recency_score=item['recency_score'],
                    combined_score=item['combined_score'],
                    metadata=item.get('metadata', {})
                ))

            return memories

        except Exception as e:
            logger.error(f"pgvector RPC failed for {expert_id}: {e}")
            # Fallback to timestamp-based retrieval
            return await self._timestamp_fallback_retrieval(expert_id, k)

    async def _retrieve_team_knowledge(
        self,
        home_team: str,
        away_team: str
    ) -> Dict[str, Any]:
        """
        Retrieve team knowledge buckets for both teams
        """
        try:
            result = await supabase.table('team_knowledge').select('*').in_(
                'team_id', [home_team, away_team]
            ).execute()

            team_knowledge = {}
            for item in result.data:
                team_knowledge[item['team_id']] = {
                    'offensive_stats': item.get('offensive_stats', {}),
                    'defensive_stats': item.get('defensive_stats', {}),
                    'recent_form': item.get('recent_form', {}),
                    'injury_report': item.get('injury_report', {}),
                    'coaching_tendencies': item.get('coaching_tendencies', {})
                }

            return team_knowledge

        except Exception as e:
            logger.error(f"Team knowledge retrieval failed: {e}")
            return {}

    async def _retrieve_matchup_memories(
        self,
        home_team: str,
        away_team: str,
        expert_id: str
    ) -> List[MemoryItem]:
        """
        Retrieve role-aware matchup memories for team head-to-head
        """
        try:
            result = await supabase.table('matchup_memories').select('*').eq(
                'expert_id', expert_id
            ).or_(
                f'and(home_team.eq.{home_team},away_team.eq.{away_team}),'
                f'and(home_team.eq.{away_team},away_team.eq.{home_team})'
            ).order('created_at', desc=True).limit(5).execute()

            memories = []
            for item in result.data:
                memories.append(MemoryItem(
                    memory_id=item['memory_id'],
                    content=item['content'],
                    similarity_score=1.0,  # Exact matchup
                    recency_score=self._calculate_recency_score(item['created_at']),
                    combined_score=1.0,
                    metadata={
                        'home_team': item['home_team'],
                        'away_team': item['away_team'],
                        'role_aware': True
                    }
                ))

            return memories

        except Exception as e:
            logger.error(f"Matchup memory retrieval failed: {e}")
            return []

    def _get_retrieval_parameters(
        self,
        expert_id: str,
        persona_config: Optional[Dict[str, Any]]
    ) -> Tuple[int, float]:
        """
        Get persona-tuned K and alpha parameters with adaptive degradation
        """
        if persona_config:
            base_k = persona_config.get('memory_k', self.default_k)
            alpha = persona_config.get('recency_alpha', 0.8)
        else:
            # Default persona-based parameters
            base_k = self._get_default_k_for_expert(expert_id)
            alpha = self._get_default_alpha_for_expert(expert_id)

        # Ensure K is within bounds
        k = max(self.min_k, min(self.max_k, base_k))

        return k, alpha

    def _get_target_k(
        self,
        expert_id: str,
        persona_config: Optional[Dict[str, Any]]
    ) -> int:
        """Get the target K before any degradation"""
        if persona_config:
            return persona_config.get('memory_k', self.default_k)
        return self._get_default_k_for_expert(expert_id)

    def _get_default_k_for_expert(self, expert_id: str) -> int:
        """Get default K based on expert personality"""
        # Momentum and intuition experts get more memories
        if expert_id in ['momentum_rider', 'gut_instinct_expert', 'chaos_theory_believer']:
            return 20
        # Conservative experts get fewer memories
        elif expert_id in ['conservative_analyzer', 'statistics_purist', 'consensus_follower']:
            return 12
        # Default for balanced experts
        else:
            return 15

    def _get_default_alpha_for_expert(self, expert_id: str) -> float:
        """Get default recency alpha based on expert personality"""
        # Momentum experts weight recency higher
        if expert_id in ['momentum_rider', 'trend_reversal_specialist']:
            return 0.9
        # Conservative experts balance similarity and recency
        elif expert_id in ['conservative_analyzer', 'statistics_purist']:
            return 0.6
        # Default balanced weighting
        else:
            return 0.8

    def _build_query_text(self, game_context: Dict[str, Any]) -> str:
        """Build compact query text from game context"""
        parts = []

        if game_context.get('home_team') and game_context.get('away_team'):
            parts.append(f"{game_context['away_team']} at {game_context['home_team']}")

        if game_context.get('week'):
            parts.append(f"Week {game_context['week']}")

        if game_context.get('season'):
            parts.append(f"{game_context['season']} season")

        if game_context.get('weather'):
            parts.append(f"Weather: {game_context['weather']}")

        return " | ".join(parts)

    def _calculate_recency_score(self, created_at: str) -> float:
        """Calculate recency score with 90-day exponential decay"""
        try:
            from datetime import datetime, timezone
            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            days_ago = (now - created_time).days

            # 90-day half-life exponential decay
            return 0.5 ** (days_ago / 90.0)
        except:
            return 0.5  # Default moderate recency

    async def _timestamp_fallback_retrieval(
        self,
        expert_id: str,
        k: int
    ) -> List[MemoryItem]:
        """
        Fallback to timestamp-based retrieval when vector search fails
        """
        logger.warning(f"Using timestamp fallback for {expert_id}")

        try:
            result = await supabase.table('expert_episodic_memories').select(
                'memory_id, content, created_at, metadata'
            ).eq('expert_id', expert_id).order(
                'created_at', desc=True
            ).limit(k).execute()

            memories = []
            for item in result.data:
                memories.append(MemoryItem(
                    memory_id=item['memory_id'],
                    content=item['content'],
                    similarity_score=0.5,  # Unknown similarity
                    recency_score=self._calculate_recency_score(item['created_at']),
                    combined_score=0.5,
                    metadata=item.get('metadata', {})
                ))

            return memories

        except Exception as e:
            logger.error(f"Timestamp fallback failed for {expert_id}: {e}")
            return []

    async def _fallback_retrieval(
        self,
        expert_id: str,
        game_context: Dict[str, Any],
        run_id: str
    ) -> MemoryContext:
        """
        Complete fallback when all retrieval methods fail
        """
        logger.error(f"Complete retrieval fallback for {expert_id}")

        return MemoryContext(
            episodic_memories=[],
            team_knowledge={},
            matchup_memories=[],
            retrieval_stats={
                "duration_ms": 0,
                "k_used": 0,
                "alpha_used": 0.0,
                "target_k": self._get_target_k(expert_id, None),
                "degraded": True,
                "fallback": True
            }
        )


# Singleton instance
memory_retrieval_service = MemoryRetrievalService()
