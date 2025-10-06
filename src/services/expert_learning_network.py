"""
Expert Learning Relationship Network Builder

This service buildsnship graphs that model expert prediction patterns,
learning evolution, and inter-expert influence networks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import math

from services.neo4j_knowledge_service import Neo4jKnowledgeService


@dataclass
class ExpertLearningStats:
    """Statistics for expert learning relationships"""
    prediction_patterns: int = 0
    learning_influences: int = 0
    specialization_mappings: int = 0
    council_formations: int = 0
    evolution_tracks: int = 0


class ExpertLearningNetwork:
    """
    Builds and manages expert learning relationship networks in Neo4j.

    This models how experts learn, evolve, and influence each other's
    prediction patterns over time.
    """

    def __init__(self, neo4j_service: Neo4jKnowledgeService):
        self.neo4j_service = neo4j_service
        self.logger = logging.getLogger(__name__)
        self.stats = ExpertLearningStats()

    async def build_expert_prediction_patterns(self) -> bool:
        """Build expert prediction pattern relationships"""
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Create prediction pattern nodes based on expert memories
                query = """
                MATCH (e:Expert)-[:HAS_MEMORY]->(m:Memory)
                WHERE m.memory_type = 'game_prediction'
                WITH e, m,
                     apoc.convert.fromJsonMap(m.content) as prediction_data
                WITH e, prediction_data,
                     prediction_data.game_context.division_game as is_divisional,
                     prediction_data.game_context.weather as weather_conditions,
                     prediction_data.predicted_winner as predicted_winner,
                     prediction_data.win_probability as win_probability,
                     m.confidence as confidence

                // Create pattern nodes for different prediction contexts
                MERGE (p:PredictionPattern {
                    pattern_id: e.expert_id + '_' +
                               CASE WHEN is_divisional THEN 'divisional' ELSE 'non_divisional' END + '_' +
                               CASE WHEN win_probability > 0.7 THEN 'confident'
                                    WHEN win_probability < 0.3 THEN 'contrarian'
                                    ELSE 'moderate' END
                })
                SET p.expert_id = e.expert_id,
                    p.context_type = CASE WHEN is_divisional THEN 'divisional' ELSE 'non_divisional' END,
                    p.confidence_level = CASE WHEN win_probability > 0.7 THEN 'confident'
                                              WHEN win_probability < 0.3 THEN 'contrarian'
                                              ELSE 'moderate' END,
                    p.avg_win_probability = avg(win_probability),
                    p.avg_confidence = avg(confidence),
                    p.prediction_count = count(*),
                    p.updated_at = datetime()

                MERGE (e)-[:HAS_PATTERN]->(p)

                RETURN count(DISTINCT p) as patterns_created
                """

                result = await session.run(query)
                record = await result.single()

                if record:
                    self.stats.prediction_patterns = record['patterns_created']
                    self.logger.info(f"✅ Created {self.stats.prediction_patterns} prediction patterns")

                return True

        except Exception as e:
            self.logger.error(f"Failed to build prediction patterns: {e}")
            return False

    async def build_expert_specialization_mapping(self) -> bool:
        """Build expert specialization relationships"""
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Create specialization relationships based on memory patterns
                query = """
                MATCH (e:Expert)-[:HAS_MEMORY]->(m:Memory)-[:ABOUT_TEAM]->(t:Team)
                WITH e, t, count(m) as memories_about_team, avg(m.confidence) as avg_confidence
                WHERE memories_about_team >= 3

                MERGE (e)-[s:SPECIALIZES_IN]->(t)
                SET s.memory_count = memories_about_team,
                    s.avg_confidence = avg_confidence,
                    s.specialization_strength = CASE
                        WHEN memories_about_team > 10 AND avg_confidence > 0.7 THEN 'high'
                        WHEN memories_about_team > 5 AND avg_confidence > 0.6 THEN 'medium'
                        ELSE 'low'
                    END,
                    s.created_at = datetime()

                RETURN count(s) as specializations_created
                """

                result = await session.run(query)
                record = await result.single()

                if record:
                    self.stats.specialization_mappings = record['specializations_created']
                    self.logger.info(f"✅ Created {self.stats.specialization_mappings} specialization mappings")

                # Create division specializations
                division_query = """
                MATCH (e:Expert)-[s:SPECIALIZES_IN]->(t:Team)-[:MEMBER_OF]->(d:Division)
                WITH e, d, count(s) as teams_in_division, avg(s.avg_confidence) as division_confidence
                WHERE teams_in_division >= 2

                MERGE (e)-[ds:DIVISION_SPECIALIST]->(d)
                SET ds.teams_specialized = teams_in_division,
                    ds.avg_confidence = division_confidence,
                    ds.specialization_depth = CASE
                        WHEN teams_in_division >= 3 THEN 'deep'
                        ELSE 'moderate'
                    END,
                    ds.created_at = datetime()

                RETURN count(ds) as division_specializations
                """

                div_result = await session.run(division_query)
                div_record = await div_result.single()

                if div_record:
                    div_specs = div_record['division_specializations']
                    self.stats.specialization_mappings += div_specs
                    self.logger.info(f"✅ Created {div_specs} division specializations")

                return True

        except Exception as e:
            self.logger.error(f"Failed to build specialization mapping: {e}")
            return False

    async def build_expert_influence_networks(self) -> bool:
        """Build expert-to-expert learning influence networks"""
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Find experts with similar prediction patterns
                query = """
                MATCH (e1:Expert)-[:HAS_PATTERN]->(p1:PredictionPattern)
                MATCH (e2:Expert)-[:HAS_PATTERN]->(p2:PredictionPattern)
                WHERE e1.expert_id <> e2.expert_id
                AND p1.context_type = p2.context_type
                AND p1.confidence_level = p2.confidence_level
                AND abs(p1.avg_win_probability - p2.avg_win_probability) < 0.2

                WITH e1, e2, count(*) as shared_patterns,
                     avg(abs(p1.avg_win_probability - p2.avg_win_probability)) as avg_difference
                WHERE shared_patterns > 1

                MERGE (e1)-[i:SIMILAR_APPROACH]->(e2)
                SET i.shared_patterns = shared_patterns,
                    i.avg_prediction_difference = avg_difference,
                    i.similarity_strength = CASE
                        WHEN shared_patterns > 3 AND avg_difference < 0.1 THEN 'high'
                        WHEN shared_patterns > 2 AND avg_difference < 0.15 THEN 'medium'
                        ELSE 'low'
                    END,
                    i.created_at = datetime()

                RETURN count(i) as influence_relationships
                """

                result = await session.run(query)
                record = await result.single()

                if record:
                    self.stats.learning_influences = record['influence_relationships']
                    self.logger.info(f"✅ Created {self.stats.learning_influences} influence relationships")

                # Create complementary expert relationships
                complement_query = """
                MATCH (e1:Expert)-[:HAS_PATTERN]->(p1:PredictionPattern)
                MATCH (e2:Expert)-[:HAS_PATTERN]->(p2:PredictionPattern)
                WHERE e1.expert_id <> e2.expert_id
                AND p1.context_type = p2.context_type
                AND ((p1.confidence_level = 'confident' AND p2.confidence_level = 'contrarian') OR
                     (p1.confidence_level = 'contrarian' AND p2.confidence_level = 'confident'))

                WITH e1, e2, count(*) as complementary_patterns
                WHERE complementary_patterns > 1

                MERGE (e1)-[c:COMPLEMENTARY_APPROACH]->(e2)
                SET c.complementary_patterns = complementary_patterns,
                    c.relationship_type = 'opposing_perspectives',
                    c.created_at = datetime()

                RETURN count(c) as complementary_relationships
                """

                comp_result = await session.run(complement_query)
                comp_record = await comp_result.single()

                if comp_record:
                    comp_rels = comp_record['complementary_relationships']
                    self.stats.learning_influences += comp_rels
                    self.logger.info(f"✅ Created {comp_rels} complementary relationships")

                return True

        except Exception as e:
            self.logger.error(f"Failed to build influence networks: {e}")
            return False

    async def build_expert_evolution_tracking(self) -> bool:
        """Build expert evolution and learning progression tracking"""
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Create evolution nodes based on temporal memory patterns
                query = """
                MATCH (e:Expert)-[:HAS_MEMORY]->(m:Memory)
                WHERE m.memory_type = 'game_prediction'
                WITH e, m,
                     apoc.convert.fromJsonMap(m.content) as prediction_data,
                     m.created_at as memory_date

                // Group memories by time periods (monthly)
                WITH e,
                     date.truncate('month', memory_date) as time_period,
                     avg(prediction_data.win_probability) as avg_win_prob,
                     avg(m.confidence) as avg_confidence,
                     count(m) as predictions_count
                WHERE predictions_count >= 3

                MERGE (ev:ExpertEvolution {
                    evolution_id: e.expert_id + '_' + toString(time_period)
                })
                SET ev.expert_id = e.expert_id,
                    ev.time_period = time_period,
                    ev.avg_win_probability = avg_win_prob,
                    ev.avg_confidence = avg_confidence,
                    ev.predictions_count = predictions_count,
                    ev.created_at = datetime()

                MERGE (e)-[:EVOLVED_TO]->(ev)

                // Create temporal progression relationships
                WITH e, ev, time_period
                ORDER BY time_period
                WITH e, collect(ev) as evolution_nodes

                UNWIND range(0, size(evolution_nodes)-2) as i
                WITH evolution_nodes[i] as prev_ev, evolution_nodes[i+1] as next_ev

                MERGE (prev_ev)-[p:PROGRESSED_TO]->(next_ev)
                SET p.confidence_change = next_ev.avg_confidence - prev_ev.avg_confidence,
                    p.probability_change = next_ev.avg_win_probability - prev_ev.avg_win_probability,
                    p.learning_trend = CASE
                        WHEN next_ev.avg_confidence > prev_ev.avg_confidence THEN 'improving'
                        WHEN next_ev.avg_confidence < prev_ev.avg_confidence THEN 'declining'
                        ELSE 'stable'
                    END,
                    p.created_at = datetime()

                RETURN count(DISTINCT prev_ev) as evolution_tracks
                """

                result = await session.run(query)
                record = await result.single()

                if record:
                    self.stats.evolution_tracks = record['evolution_tracks']
                    self.logger.info(f"✅ Created {self.stats.evolution_tracks} evolution tracks")

                return True

        except Exception as e:
            self.logger.error(f"Failed to build evolution tracking: {e}")
            return False

    async def build_council_formation_patterns(self) -> bool:
        """Build expert council formation pattern analysis"""
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Create council formation patterns based on complementary specializations
                query = """
                // Find experts with different but complementary specializations
                MATCH (e1:Expert)-[:SPECIALIZES_IN]->(t1:Team)
                MATCH (e2:Expert)-[:SPECIALIZES_IN]->(t2:Team)
                MATCH (e3:Expert)-[:SPECIALIZES_IN]->(t3:Team)
                WHERE e1.expert_id <> e2.expert_id
                AND e2.expert_id <> e3.expert_id
                AND e1.expert_id <> e3.expert_id
                AND t1.team_id <> t2.team_id
                AND t2.team_id <> t3.team_id
                AND t1.team_id <> t3.team_id

                // Check if they have complementary approaches
                OPTIONAL MATCH (e1)-[c1:COMPLEMENTARY_APPROACH]-(e2)
                OPTIONAL MATCH (e2)-[c2:COMPLEMENTARY_APPROACH]-(e3)
                OPTIONAL MATCH (e1)-[c3:COMPLEMENTARY_APPROACH]-(e3)

                WITH e1, e2, e3,
                     CASE WHEN c1 IS NOT NULL THEN 1 ELSE 0 END +
                     CASE WHEN c2 IS NOT NULL THEN 1 ELSE 0 END +
                     CASE WHEN c3 IS NOT NULL THEN 1 ELSE 0 END as complementary_connections

                WHERE complementary_connections >= 2

                CREATE (council:ExpertCouncil {
                    council_id: randomUUID(),
                    member_1: e1.expert_id,
                    member_2: e2.expert_id,
                    member_3: e3.expert_id,
                    complementary_score: complementary_connections,
                    formation_type: 'diverse_specialization',
                    created_at: datetime()
                })

                CREATE (e1)-[:MEMBER_OF_COUNCIL]->(council)
                CREATE (e2)-[:MEMBER_OF_COUNCIL]->(council)
                CREATE (e3)-[:MEMBER_OF_COUNCIL]->(council)

                RETURN count(council) as councils_formed
                """

                result = await session.run(query)
                record = await result.single()

                if record:
                    self.stats.council_formations = record['councils_formed']
                    self.logger.info(f"✅ Created {self.stats.council_formations} council formations")

                # Create consensus-based councils
                consensus_query = """
                // Find experts with similar high-confidence patterns
                MATCH (e1:Expert)-[:HAS_PATTERN]->(p1:PredictionPattern {confidence_level: 'confident'})
                MATCH (e2:Expert)-[:HAS_PATTERN]->(p2:PredictionPattern {confidence_level: 'confident'})
                MATCH (e3:Expert)-[:HAS_PATTERN]->(p3:PredictionPattern {confidence_level: 'confident'})
                WHERE e1.expert_id <> e2.expert_id
                AND e2.expert_id <> e3.expert_id
                AND e1.expert_id <> e3.expert_id
                AND p1.context_type = p2.context_type
                AND p2.context_type = p3.context_type
                AND abs(p1.avg_win_probability - p2.avg_win_probability) < 0.15
                AND abs(p2.avg_win_probability - p3.avg_win_probability) < 0.15

                CREATE (council:ExpertCouncil {
                    council_id: randomUUID(),
                    member_1: e1.expert_id,
                    member_2: e2.expert_id,
                    member_3: e3.expert_id,
                    consensus_score: 1.0 - (abs(p1.avg_win_probability - p2.avg_win_probability) +
                                           abs(p2.avg_win_probability - p3.avg_win_probability)) / 2,
                    formation_type: 'consensus_building',
                    context_type: p1.context_type,
                    created_at: datetime()
                })

                CREATE (e1)-[:MEMBER_OF_COUNCIL]->(council)
                CREATE (e2)-[:MEMBER_OF_COUNCIL]->(council)
                CREATE (e3)-[:MEMBER_OF_COUNCIL]->(council)

                RETURN count(council) as consensus_councils
                """

                cons_result = await session.run(consensus_query)
                cons_record = await cons_result.single()

                if cons_record:
                    cons_councils = cons_record['consensus_councils']
                    self.stats.council_formations += cons_councils
                    self.logger.info(f"✅ Created {cons_councils} consensus councils")

                return True

        except Exception as e:
            self.logger.error(f"Failed to build council formations: {e}")
            return False

    async def analyze_expert_learning_patterns(self) -> List[Dict[str, Any]]:
        """Analyze expert learning and evolution patterns"""
        try:
            if not self.neo4j_service.driver:
                return []

            async with self.neo4j_service.driver.session() as session:
                patterns = []

                # 1. Find experts with strongest learning trends
                query1 = """
                MATCH (e:Expert)-[:EVOLVED_TO]->(ev1:ExpertEvolution)-[p:PROGRESSED_TO]->(ev2:ExpertEvolution)
                WITH e, avg(p.confidence_change) as avg_confidence_change, count(p) as evolution_steps
                WHERE evolution_steps >= 3
                RETURN e.expert_id as expert_id, avg_confidence_change, evolution_steps,
                       CASE WHEN avg_confidence_change > 0.05 THEN 'strong_learner'
                            WHEN avg_confidence_change < -0.05 THEN 'declining_performance'
                            ELSE 'stable_performance' END as learning_pattern
                ORDER BY avg_confidence_change DESC
                """

                result1 = await session.run(query1)
                async for record in result1:
                    patterns.append({
                        'pattern_type': 'learning_trend',
                        'expert_id': record['expert_id'],
                        'confidence_change': record['avg_confidence_change'],
                        'evolution_steps': record['evolution_steps'],
                        'classification': record['learning_pattern']
                    })

                # 2. Find most influential expert relationships
                query2 = """
                MATCH (e1:Expert)-[i:SIMILAR_APPROACH]->(e2:Expert)
                WHERE i.similarity_strength = 'high'
                RETURN e1.expert_id as influencer, e2.expert_id as influenced,
                       i.shared_patterns as shared_patterns, i.avg_prediction_difference as difference
                ORDER BY i.shared_patterns DESC, i.avg_prediction_difference ASC
                LIMIT 10
                """

                result2 = await session.run(query2)
                async for record in result2:
                    patterns.append({
                        'pattern_type': 'expert_influence',
                        'influencer': record['influencer'],
                        'influenced': record['influenced'],
                        'shared_patterns': record['shared_patterns'],
                        'prediction_difference': record['difference']
                    })

                # 3. Find best council formations
                query3 = """
                MATCH (council:ExpertCouncil)
                WHERE council.formation_type = 'diverse_specialization'
                RETURN council.council_id as council_id, council.member_1, council.member_2, council.member_3,
                       council.complementary_score as score, council.formation_type
                ORDER BY council.complementary_score DESC
                LIMIT 5
                """

                result3 = await session.run(query3)
                async for record in result3:
                    patterns.append({
                        'pattern_type': 'optimal_council',
                        'council_id': record['council_id'],
                        'members': [record['member_1'], record['member_2'], record['member_3']],
                        'complementary_score': record['score'],
                        'formation_type': record['formation_type']
                    })

                self.logger.info(f"🔍 Analyzed {len(patterns)} expert learning patterns")
                return patterns

        except Exception as e:
            self.logger.error(f"Failed to analyze learning patterns: {e}")
            return []

    async def build_all_expert_relationships(self) -> ExpertLearningStats:
        """Build all expert learning relationship networks"""
        self.logger.info("🧠 Building comprehensive expert learning networks...")

        # Build all relationship types
        success_count = 0

        if await self.build_expert_prediction_patterns():
            success_count += 1

        if await self.build_expert_specialization_mapping():
            success_count += 1

        if await self.build_expert_influence_networks():
            success_count += 1

        if await self.build_expert_evolution_tracking():
            success_count += 1

        if await self.build_council_formation_patterns():
            success_count += 1

        # Analyze patterns
        patterns = await self.analyze_expert_learning_patterns()

        self.logger.info(f"✅ Expert learning network building completed:")
        self.logger.info(f"   Successful operations: {success_count}/5")
        self.logger.info(f"   Prediction patterns: {self.stats.prediction_patterns}")
        self.logger.info(f"   Learning influences: {self.stats.learning_influences}")
        self.logger.info(f"   Specialization mappings: {self.stats.specialization_mappings}")
        self.logger.info(f"   Council formations: {self.stats.council_formations}")
        self.logger.info(f"   Evolution tracks: {self.stats.evolution_tracks}")
        self.logger.info(f"   Patterns analyzed: {len(patterns)}")

        return self.stats

    def get_learning_stats(self) -> ExpertLearningStats:
        """Get current expert learning statistics"""
        return self.stats
