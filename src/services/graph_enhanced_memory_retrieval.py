"""
Graph-Enhanced Memory Retrieval System

This service uses Neo4j relationships to enhance memory search and discovery,
providing contextual memory retrieval based on graph patterns and relationships.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Di, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import math

from services.neo4j_knowledge_service import Neo4jKnowledgeService


@dataclass
class GraphMemoryResult:
    """Result from graph-enhanced memory retrieval"""
    memory_id: str
    content: str
    confidence: float
    relevance_score: float
    relationship_path: List[str]
    context_type: str
    created_at: datetime


@dataclass
class MemoryRetrievalStats:
    """Statistics for memory retrieval operations"""
    total_queries: int = 0
    graph_enhanced_queries: int = 0
    avg_results_per_query: float = 0.0
    avg_relevance_score: float = 0.0
    relationship_types_used: List[str] = None

    def __post_init__(self):
        if self.relationship_types_used is None:
            self.relationship_types_used = []


class GraphEnhancedMemoryRetrieval:
    """
    Enhanced memory retrieval system using Neo4j graph relationships.

    This system leverages the relationship networks to find more contextually
    relevant memories through graph traversal and pattern matching.
    """

    def __init__(self, neo4j_service: Neo4jKnowledgeService):
        self.neo4j_service = neo4j_service
        self.logger = logging.getLogger(__name__)
        self.stats = MemoryRetrievalStats()

    async def retrieve_memories_by_team_relationships(self, expert_id: str,
                                                    target_team: str,
                                                    max_results: int = 10) -> List[GraphMemoryResult]:
        """
        Retrieve memories using team relationship patterns.

        This finds memories about teams that have relationships with the target team
        (divisional rivals, historical matchups, etc.)
        """
        try:
            if not self.neo4j_service.driver:
                return []

            async with self.neo4j_service.driver.session() as session:
                # Find memories through team relationships
                query = """
                MATCH (e:Expert {expert_id: $expert_id})-[:HAS_MEMORY]->(m:Memory)-[:ABOUT_TEAM]->(target:Team {team_id: $target_team})

                // Direct memories about the target team
                WITH collect({
                    memory_id: m.memory_id,
                    content: m.content,
                    confidence: m.confidence,
                    relevance_score: 1.0,
                    relationship_path: ['direct'],
                    context_type: 'direct_team_memory',
                    created_at: m.created_at
                }) as direct_memories

                // Memories about divisional rivals
                MATCH (e:Expert {expert_id: $expert_id})-[:HAS_MEMORY]->(m2:Memory)-[:ABOUT_TEAM]->(rival:Team)
                MATCH (target:Team {team_id: $target_team})-[:DIVISIONAL_RIVAL]-(rival)
                WHERE NOT m2.memory_id IN [mem.memory_id | mem IN direct_memories]

                WITH direct_memories + collect({
                    memory_id: m2.memory_id,
                    content: m2.content,
                    confidence: m2.confidence,
                    relevance_score: 0.8,
                    relationship_path: ['divisional_rival'],
                    context_type: 'divisional_context',
                    created_at: m2.created_at
                }) as divisional_memories

                // Memories about historical matchup opponents
                MATCH (e:Expert {expert_id: $expert_id})-[:HAS_MEMORY]->(m3:Memory)-[:ABOUT_TEAM]->(opponent:Team)
                MATCH (target:Team {team_id: $target_team})-[h:HEAD_TO_HEAD]-(opponent)
                WHERE h.total_games > 5
                AND NOT m3.memory_id IN [mem.memory_id | mem IN divisional_memories]

                WITH divisional_memories + collect({
                    memory_id: m3.memory_id,
                    content: m3.content,
                    confidence: m3.confidence,
                    relevance_score: 0.6 * (toFloat(h.total_games) / 20.0),
                    relationship_path: ['historical_matchup'],
                    context_type: 'historical_opponent',
                    created_at: m3.created_at
                }) as all_memories

                UNWIND all_memories as memory
                RETURN memory.memory_id as memory_id,
                       memory.content as content,
                       memory.confidence as confidence,
                       memory.relevance_score as relevance_score,
                       memory.relationship_path as relationship_path,
                       memory.context_type as context_type,
                       memory.created_at as created_at
                ORDER BY memory.relevance_score DESC, memory.confidence DESC
                LIMIT $max_results
                """

                result = await session.run(query,
                                         expert_id=expert_id,
                                         target_team=target_team,
                                         max_results=max_results)

                memories = []
                async for record in result:
                    memories.append(GraphMemoryResult(
                        memory_id=record['memory_id'],
                        content=record['content'],
                        confidence=record['confidence'],
                        relevance_score=record['relevance_score'],
                        relationship_path=record['relationship_path'],
                        context_type=record['context_type'],
                        created_at=record['created_at']
                    ))

                self.stats.total_queries += 1
                self.stats.graph_enhanced_queries += 1
                self._update_stats(memories)

                self.logger.info(f"🔍 Retrieved {len(memories)} memories for {expert_id} about {target_team}")
                return memories

        except Exception as e:
            self.logger.error(f"Failed to retrieve team relationship memories: {e}")
            return []

    async def retrieve_memories_by_game_patterns(self, expert_id: str,
                                               game_context: Dict[str, Any],
                                               max_results: int = 10) -> List[GraphMemoryResult]:
        """
        Retrieve memories using game pattern relationships.

        This finds memories about similar game contexts through pattern matching.
        """
        try:
            if not self.neo4j_service.driver:
                return []

            async with self.neo4j_service.driver.session() as session:
                # Extract game context features
                is_divisional = game_context.get('division_game', False)
                home_team = game_context.get('home_team', '')
                away_team = game_context.get('away_team', '')
                weather = game_context.get('weather', {})

                query = """
                MATCH (e:Expert {expert_id: $expert_id})-[:HAS_MEMORY]->(m:Memory)
                WHERE m.memory_type = 'game_prediction'

                WITH e, m, apoc.convert.fromJsonMap(m.content) as prediction_data

                // Calculate similarity scores based on game context
                WITH e, m, prediction_data,
                     CASE WHEN prediction_data.game_context.division_game = $is_divisional THEN 0.3 ELSE 0.0 END +
                     CASE WHEN prediction_data.game_context.home_team = $home_team OR
                               prediction_data.game_context.away_team = $home_team OR
                               prediction_data.game_context.home_team = $away_team OR
                               prediction_data.game_context.away_team = $away_team THEN 0.4 ELSE 0.0 END +
                     CASE WHEN prediction_data.game_context.weather IS NOT NULL THEN 0.2 ELSE 0.0 END +
                     0.1 as base_relevance_score

                WHERE base_relevance_score > 0.3

                // Find memories connected through momentum patterns
                OPTIONAL MATCH (m)-[:ABOUT_GAME]->(g1:Game)-[mom:MOMENTUM_INFLUENCE]->(g2:Game)
                WHERE mom.team_id IN [$home_team, $away_team]

                WITH m, prediction_data, base_relevance_score,
                     CASE WHEN mom IS NOT NULL THEN base_relevance_score + 0.2 ELSE base_relevance_score END as final_relevance_score

                RETURN m.memory_id as memory_id,
                       m.content as content,
                       m.confidence as confidence,
                       final_relevance_score as relevance_score,
                       CASE WHEN mom IS NOT NULL THEN ['momentum_pattern'] ELSE ['context_similarity'] END as relationship_path,
                       'game_pattern_match' as context_type,
                       m.created_at as created_at
                ORDER BY final_relevance_score DESC, m.confidence DESC
                LIMIT $max_results
                """

                result = await session.run(query,
                                         expert_id=expert_id,
                                         is_divisional=is_divisional,
                                         home_team=home_team,
                                         away_team=away_team,
                                         max_results=max_results)

                memories = []
                async for record in result:
                    memories.append(GraphMemoryResult(
                        memory_id=record['memory_id'],
                        content=record['content'],
                        confidence=record['confidence'],
                        relevance_score=record['relevance_score'],
                        relationship_path=record['relationship_path'],
                        context_type=record['context_type'],
                        created_at=record['created_at']
                    ))

                self.stats.total_queries += 1
                self.stats.graph_enhanced_queries += 1
                self._update_stats(memories)

                self.logger.info(f"🎯 Retrieved {len(memories)} pattern-matched memories for {expert_id}")
                return memories

        except Exception as e:
            self.logger.error(f"Failed to retrieve game pattern memories: {e}")
            return []

    async def retrieve_memories_by_expert_specialization(self, expert_id: str,
                                                       context: Dict[str, Any],
                                                       max_results: int = 10) -> List[GraphMemoryResult]:
        """
        Retrieve memories using expert specialization relationships.

        This leverages expert specialization patterns to find the most relevant memories.
        """
        try:
            if not self.neo4j_service.driver:
                return []

            async with self.neo4j_service.driver.session() as session:
                team_id = context.get('team_id', context.get('home_team', ''))

                query = """
                MATCH (e:Expert {expert_id: $expert_id})

                // Find memories from expert's specializations
                OPTIONAL MATCH (e)-[s:SPECIALIZES_IN]->(t:Team {team_id: $team_id})
                OPTIONAL MATCH (e)-[:HAS_MEMORY]->(m1:Memory)-[:ABOUT_TEAM]->(t)

                WITH e, s, collect({
                    memory_id: m1.memory_id,
                    content: m1.content,
                    confidence: m1.confidence,
                    relevance_score: CASE WHEN s.specialization_strength = 'high' THEN 1.0
                                          WHEN s.specialization_strength = 'medium' THEN 0.8
                                          ELSE 0.6 END,
                    relationship_path: ['specialization'],
                    context_type: 'expert_specialization',
                    created_at: m1.created_at
                }) as specialized_memories

                // Find memories from similar experts with same specialization
                OPTIONAL MATCH (other:Expert)-[s2:SPECIALIZES_IN]->(t:Team {team_id: $team_id})
                OPTIONAL MATCH (e)-[sim:SIMILAR_APPROACH]-(other)
                OPTIONAL MATCH (other)-[:HAS_MEMORY]->(m2:Memory)-[:ABOUT_TEAM]->(t)
                WHERE other.expert_id <> e.expert_id
                AND sim.similarity_strength IN ['high', 'medium']
                AND NOT m2.memory_id IN [mem.memory_id | mem IN specialized_memories WHERE mem.memory_id IS NOT NULL]

                WITH specialized_memories + collect({
                    memory_id: m2.memory_id,
                    content: m2.content,
                    confidence: m2.confidence,
                    relevance_score: CASE WHEN sim.similarity_strength = 'high' THEN 0.7 ELSE 0.5 END,
                    relationship_path: ['similar_expert_specialization'],
                    context_type: 'peer_expert_knowledge',
                    created_at: m2.created_at
                }) as all_memories

                UNWIND all_memories as memory
                WHERE memory.memory_id IS NOT NULL
                RETURN memory.memory_id as memory_id,
                       memory.content as content,
                       memory.confidence as confidence,
                       memory.relevance_score as relevance_score,
                       memory.relationship_path as relationship_path,
                       memory.context_type as context_type,
                       memory.created_at as created_at
                ORDER BY memory.relevance_score DESC, memory.confidence DESC
                LIMIT $max_results
                """

                result = await session.run(query,
                                         expert_id=expert_id,
                                         team_id=team_id,
                                         max_results=max_results)

                memories = []
                async for record in result:
                    memories.append(GraphMemoryResult(
                        memory_id=record['memory_id'],
                        content=record['content'],
                        confidence=record['confidence'],
                        relevance_score=record['relevance_score'],
                        relationship_path=record['relationship_path'],
                        context_type=record['context_type'],
                        created_at=record['created_at']
                    ))

                self.stats.total_queries += 1
                self.stats.graph_enhanced_queries += 1
                self._update_stats(memories)

                self.logger.info(f"🎓 Retrieved {len(memories)} specialization-based memories for {expert_id}")
                return memories

        except Exception as e:
            self.logger.error(f"Failed to retrieve specialization memories: {e}")
            return []

    async def retrieve_memories_by_council_wisdom(self, expert_id: str,
                                                context: Dict[str, Any],
                                                max_results: int = 15) -> List[GraphMemoryResult]:
        """
        Retrieve memories using expert council relationships.

        This finds memories from other experts in the same councils.
        """
        try:
            if not self.neo4j_service.driver:
                return []

            async with self.neo4j_service.driver.session() as session:
                query = """
                MATCH (e:Expert {expert_id: $expert_id})-[:MEMBER_OF_COUNCIL]->(council:ExpertCouncil)
                MATCH (council)<-[:MEMBER_OF_COUNCIL]-(peer:Expert)
                WHERE peer.expert_id <> e.expert_id

                MATCH (peer)-[:HAS_MEMORY]->(m:Memory)
                WHERE m.memory_type = 'game_prediction'

                WITH e, peer, m, council,
                     apoc.convert.fromJsonMap(m.content) as prediction_data

                // Calculate relevance based on council type and context match
                WITH e, peer, m, council, prediction_data,
                     CASE WHEN council.formation_type = 'diverse_specialization' THEN 0.8
                          WHEN council.formation_type = 'consensus_building' THEN 0.9
                          ELSE 0.7 END as council_relevance,
                     CASE WHEN $team_id IN [prediction_data.game_context.home_team, prediction_data.game_context.away_team] THEN 0.3
                          ELSE 0.0 END as team_relevance

                WHERE council_relevance + team_relevance > 0.5

                RETURN m.memory_id as memory_id,
                       m.content as content,
                       m.confidence as confidence,
                       council_relevance + team_relevance as relevance_score,
                       ['council_member'] as relationship_path,
                       'council_wisdom' as context_type,
                       m.created_at as created_at,
                       peer.expert_id as source_expert
                ORDER BY relevance_score DESC, m.confidence DESC
                LIMIT $max_results
                """

                team_id = context.get('team_id', context.get('home_team', ''))
                result = await session.run(query,
                                         expert_id=expert_id,
                                         team_id=team_id,
                                         max_results=max_results)

                memories = []
                async for record in result:
                    memories.append(GraphMemoryResult(
                        memory_id=record['memory_id'],
                        content=record['content'],
                        confidence=record['confidence'],
                        relevance_score=record['relevance_score'],
                        relationship_path=record['relationship_path'],
                        context_type=record['context_type'],
                        created_at=record['created_at']
                    ))

                self.stats.total_queries += 1
                self.stats.graph_enhanced_queries += 1
                self._update_stats(memories)

                self.logger.info(f"🤝 Retrieved {len(memories)} council wisdom memories for {expert_id}")
                return memories

        except Exception as e:
            self.logger.error(f"Failed to retrieve council memories: {e}")
            return []

    async def comprehensive_memory_retrieval(self, expert_id: str,
                                           context: Dict[str, Any],
                                           max_results: int = 20) -> List[GraphMemoryResult]:
        """
        Comprehensive memory retrieval using all graph relationship types.

        This combines multiple retrieval strategies and ranks results by relevance.
        """
        try:
            all_memories = []

            # Get memories from different relationship types
            team_memories = await self.retrieve_memories_by_team_relationships(
                expert_id, context.get('home_team', ''), max_results // 4
            )
            all_memories.extend(team_memories)

            pattern_memories = await self.retrieve_memories_by_game_patterns(
                expert_id, context, max_results // 4
            )
            all_memories.extend(pattern_memories)

            specialization_memories = await self.retrieve_memories_by_expert_specialization(
                expert_id, context, max_results // 4
            )
            all_memories.extend(specialization_memories)

            council_memories = await self.retrieve_memories_by_council_wisdom(
                expert_id, context, max_results // 4
            )
            all_memories.extend(council_memories)

            # Remove duplicates and sort by relevance
            unique_memories = {}
            for memory in all_memories:
                if memory.memory_id not in unique_memories:
                    unique_memories[memory.memory_id] = memory
                else:
                    # Keep the one with higher relevance score
                    if memory.relevance_score > unique_memories[memory.memory_id].relevance_score:
                        unique_memories[memory.memory_id] = memory

            # Sort by relevance score and confidence
            sorted_memories = sorted(
                unique_memories.values(),
                key=lambda x: (x.relevance_score, x.confidence),
                reverse=True
            )

            # Limit results
            final_memories = sorted_memories[:max_results]

            self.logger.info(f"🔍 Comprehensive retrieval: {len(final_memories)} unique memories from {len(all_memories)} total")
            return final_memories

        except Exception as e:
            self.logger.error(f"Failed comprehensive memory retrieval: {e}")
            return []

    async def discover_memory_patterns(self, expert_id: str) -> List[Dict[str, Any]]:
        """Discover patterns in memory relationships for an expert"""
        try:
            if not self.neo4j_service.driver:
                return []

            async with self.neo4j_service.driver.session() as session:
                # Find memory usage patterns
                query = """
                MATCH (e:Expert {expert_id: $expert_id})-[:HAS_MEMORY]->(m:Memory)
                OPTIONAL MATCH (m)-[r]->(related)

                WITH e, m, type(r) as relationship_type, labels(related) as related_labels
                WHERE relationship_type IS NOT NULL

                WITH e, relationship_type, related_labels, count(m) as memory_count
                RETURN relationship_type, related_labels, memory_count
                ORDER BY memory_count DESC
                """

                result = await session.run(query, expert_id=expert_id)
                patterns = []

                async for record in result:
                    patterns.append({
                        'relationship_type': record['relationship_type'],
                        'related_labels': record['related_labels'],
                        'memory_count': record['memory_count']
                    })

                return patterns

        except Exception as e:
            self.logger.error(f"Failed to discover memory patterns: {e}")
            return []

    def _update_stats(self, memories: List[GraphMemoryResult]) -> None:
        """Update retrieval statistics"""
        if not memories:
            return

        # Update averages
        total_queries = self.stats.total_queries
        current_avg_results = self.stats.avg_results_per_query
        current_avg_relevance = self.stats.avg_relevance_score

        new_results_count = len(memories)
        new_avg_relevance = sum(m.relevance_score for m in memories) / len(memories)

        # Calculate running averages
        self.stats.avg_results_per_query = (
            (current_avg_results * (total_queries - 1) + new_results_count) / total_queries
        )

        self.stats.avg_relevance_score = (
            (current_avg_relevance * (total_queries - 1) + new_avg_relevance) / total_queries
        )

        # Track relationship types used
        for memory in memories:
            for rel_type in memory.relationship_path:
                if rel_type not in self.stats.relationship_types_used:
                    self.stats.relationship_types_used.append(rel_type)

    def get_retrieval_stats(self) -> MemoryRetrievalStats:
        """Get current memory retrieval statistics"""
        return self.stats

    async def test_graph_enhanced_retrieval(self, expert_id: str = "the_momentum_rider") -> Dict[str, Any]:
        """Test the graph-enhanced memory retrieval system"""
        test_context = {
            'home_team': 'KC',
            'away_team': 'DEN',
            'division_game': True,
            'weather': {'temperature': 75, 'wind_speed': 5}
        }

        results = {}

        # Test each retrieval method
        results['team_relationships'] = await self.retrieve_memories_by_team_relationships(
            expert_id, 'KC', 5
        )

        results['game_patterns'] = await self.retrieve_memories_by_game_patterns(
            expert_id, test_context, 5
        )

        results['specialization'] = await self.retrieve_memories_by_expert_specialization(
            expert_id, test_context, 5
        )

        results['council_wisdom'] = await self.retrieve_memories_by_council_wisdom(
            expert_id, test_context, 5
        )

        results['comprehensive'] = await self.comprehensive_memory_retrieval(
            expert_id, test_context, 10
        )

        results['memory_patterns'] = await self.discover_memory_patterns(expert_id)

        results['stats'] = self.get_retrieval_stats()

        return results
