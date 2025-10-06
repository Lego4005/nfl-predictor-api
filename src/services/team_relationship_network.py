"""
Team and Game Relationship Network Builder

This service builds comprehensive relationship networks between teams and games,
modeling historical patterns, coaching relationships, and divisionalmics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

from services.neo4j_knowledge_service import Neo4jKnowledgeService


@dataclass
class TeamRelationshipStats:
    """Statistics for team relationships"""
    total_matchups: int = 0
    divisional_games: int = 0
    coaching_connections: int = 0
    player_transfers: int = 0
    rivalry_relationships: int = 0


class TeamRelationshipNetwork:
    """
    Builds and manages team and game relationship networks in Neo4j.

    This creates the foundational relationship patterns needed for
    discovering hidden patterns in team interactions.
    """

    def __init__(self, neo4j_service: Neo4jKnowledgeService):
        self.neo4j_service = neo4j_service
        self.logger = logging.getLogger(__name__)
        self.stats = TeamRelationshipStats()

    async def build_team_vs_team_relationships(self) -> bool:
        """Build historical team-vs-team relationship patterns"""
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Create head-to-head relationships with detailed statistics
                query = """
                MATCH (home:Team)-[:PLAYED_HOME]->(g:Game)<-[:PLAYED_AWAY]-(away:Team)
                WITH home, away,
                     count(g) as total_games,
                     sum(CASE WHEN g.home_score > g.away_score THEN 1 ELSE 0 END) as home_wins,
                     sum(CASE WHEN g.away_score > g.home_score THEN 1 ELSE 0 END) as away_wins,
                     avg(g.home_score) as avg_home_score,
                     avg(g.away_score) as avg_away_score,
                     sum(CASE WHEN g.is_divisional THEN 1 ELSE 0 END) as divisional_games
                WHERE total_games > 0
                MERGE (home)-[r:HEAD_TO_HEAD]-(away)
                SET r.total_games = total_games,
                    r.home_wins = home_wins,
                    r.away_wins = away_wins,
                    r.avg_home_score = avg_home_score,
                    r.avg_away_score = avg_away_score,
                    r.divisional_games = divisional_games,
                    r.home_win_percentage = toFloat(home_wins) / total_games,
                    r.updated_at = datetime()
                RETURN count(r) as relationships_created
                """

                result = await session.run(query)
                record = await result.single()

                if record:
                    self.stats.total_matchups = record['relationships_created']
                    self.logger.info(f"✅ Created {self.stats.total_matchups} head-to-head relationships")

                return True

        except Exception as e:
            self.logger.error(f"Failed to build team-vs-team relationships: {e}")
            return False

    async def build_divisional_relationships(self) -> bool:
        """Build divisional rivalry and competition relationships"""
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Create divisional rivalry relationships
                query = """
                MATCH (t1:Team)-[:MEMBER_OF]->(d:Division)<-[:MEMBER_OF]-(t2:Team)
                WHERE t1.team_id <> t2.team_id
                MERGE (t1)-[r:DIVISIONAL_RIVAL]->(t2)
                SET r.division = d.name,
                    r.created_at = datetime()

                // Calculate rivalry intensity based on game history
                WITH t1, t2, r
                OPTIONAL MATCH (t1)-[h:HEAD_TO_HEAD]-(t2)
                SET r.rivalry_intensity = CASE
                    WHEN h.total_games > 20 THEN 'high'
                    WHEN h.total_games > 10 THEN 'medium'
                    ELSE 'low'
                END,
                r.games_played = coalesce(h.total_games, 0)

                RETURN count(r) as divisional_relationships
                """

                result = await session.run(query)
                record = await result.single()

                if record:
                    self.stats.rivalry_relationships = record['divisional_relationships']
                    self.logger.info(f"✅ Created {self.stats.rivalry_relationships} divisional relationships")

                return True

        except Exception as e:
            self.logger.error(f"Failed to build divisional relationships: {e}")
            return False

    async def build_coaching_relationships(self) -> bool:
        """Build coaching staff relationship networks"""
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Create coaching tree relationships (simplified for now)
                # In production, this would use real coaching data
                coaching_data = self._get_coaching_relationships()

                for relationship in coaching_data:
                    query = """
                    MERGE (c1:Coach {coach_id: $mentor_id, name: $mentor_name})
                    MERGE (c2:Coach {coach_id: $protege_id, name: $protege_name})
                    MERGE (c1)-[r:MENTORED]->(c2)
                    SET r.years_together = $years_together,
                        r.relationship_type = $relationship_type,
                        r.created_at = datetime()
                    RETURN r
                    """

                    await session.run(query, **relationship)

                # Connect coaches to teams they've coached
                team_coaching_data = self._get_team_coaching_history()

                for coaching_stint in team_coaching_data:
                    query = """
                    MATCH (c:Coach {coach_id: $coach_id})
                    MATCH (t:Team {team_id: $team_id})
                    MERGE (c)-[r:COACHED]->(t)
                    SET r.start_year = $start_year,
                        r.end_year = $end_year,
                        r.position = $position,
                        r.created_at = datetime()
                    RETURN r
                    """

                    await session.run(query, **coaching_stint)

                self.stats.coaching_connections = len(coaching_data) + len(team_coaching_data)
                self.logger.info(f"✅ Created {self.stats.coaching_connections} coaching relationships")

                return True

        except Exception as e:
            self.logger.error(f"Failed to build coaching relationships: {e}")
            return False

    async def build_game_influence_patterns(self) -> bool:
        """Build game-to-game influence pattern relationships"""
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Create momentum relationships between consecutive games
                query = """
                MATCH (t:Team)-[:PLAYED_HOME|PLAYED_AWAY]->(g1:Game)
                MATCH (t)-[:PLAYED_HOME|PLAYED_AWAY]->(g2:Game)
                WHERE g1.date < g2.date
                AND duration.between(g1.date, g2.date).days <= 14
                WITH t, g1, g2,
                     CASE WHEN (t)-[:PLAYED_HOME]->(g1) THEN g1.home_score > g1.away_score
                          ELSE g1.away_score > g1.home_score END as g1_won,
                     CASE WHEN (t)-[:PLAYED_HOME]->(g2) THEN g2.home_score > g2.away_score
                          ELSE g2.away_score > g2.home_score END as g2_won
                MERGE (g1)-[r:MOMENTUM_INFLUENCE]->(g2)
                SET r.team_id = t.team_id,
                    r.previous_result = CASE WHEN g1_won THEN 'win' ELSE 'loss' END,
                    r.next_result = CASE WHEN g2_won THEN 'win' ELSE 'loss' END,
                    r.days_between = duration.between(g1.date, g2.date).days,
                    r.momentum_type = CASE
                        WHEN g1_won AND g2_won THEN 'positive_momentum'
                        WHEN NOT g1_won AND NOT g2_won THEN 'negative_momentum'
                        WHEN g1_won AND NOT g2_won THEN 'momentum_broken'
                        ELSE 'momentum_gained'
                    END,
                    r.created_at = datetime()
                RETURN count(r) as influence_relationships
                """

                result = await session.run(query)
                record = await result.single()

                if record:
                    influence_count = record['influence_relationships']
                    self.logger.info(f"✅ Created {influence_count} game influence relationships")

                return True

        except Exception as e:
            self.logger.error(f"Failed to build game influence patterns: {e}")
            return False

    async def build_conference_relationships(self) -> bool:
        """Build conference-level competitive relationships"""
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Create inter-conference relationships
                query = """
                MATCH (afc_team:Team {conference: 'AFC'})
                MATCH (nfc_team:Team {conference: 'NFC'})
                OPTIONAL MATCH (afc_team)-[h:HEAD_TO_HEAD]-(nfc_team)
                WHERE h.total_games > 0
                MERGE (afc_team)-[r:INTER_CONFERENCE_OPPONENT]->(nfc_team)
                SET r.games_played = coalesce(h.total_games, 0),
                    r.competitive_balance = CASE
                        WHEN abs(h.home_win_percentage - 0.5) < 0.1 THEN 'balanced'
                        WHEN h.home_win_percentage > 0.6 THEN 'home_favored'
                        ELSE 'away_favored'
                    END,
                    r.created_at = datetime()
                RETURN count(r) as inter_conference_relationships
                """

                result = await session.run(query)
                record = await result.single()

                if record:
                    inter_conf_count = record['inter_conference_relationships']
                    self.logger.info(f"✅ Created {inter_conf_count} inter-conference relationships")

                return True

        except Exception as e:
            self.logger.error(f"Failed to build conference relationships: {e}")
            return False

    async def discover_team_patterns(self) -> List[Dict[str, Any]]:
        """Discover hidden patterns in team relationships"""
        try:
            if not self.neo4j_service.driver:
                return []

            async with self.neo4j_service.driver.session() as session:
                patterns = []

                # 1. Find teams with unusual home/away performance splits
                query1 = """
                MATCH (t:Team)-[h:HEAD_TO_HEAD]-(opponent:Team)
                WITH t, avg(h.home_win_percentage) as avg_home_win_pct, count(h) as opponents
                WHERE opponents > 5
                AND (avg_home_win_pct > 0.7 OR avg_home_win_pct < 0.3)
                RETURN t.team_id as team_id, avg_home_win_pct, opponents,
                       CASE WHEN avg_home_win_pct > 0.7 THEN 'strong_home_advantage'
                            ELSE 'weak_home_performance' END as pattern_type
                ORDER BY abs(avg_home_win_pct - 0.5) DESC
                LIMIT 10
                """

                result1 = await session.run(query1)
                async for record in result1:
                    patterns.append({
                        'pattern_type': 'home_advantage_anomaly',
                        'team_id': record['team_id'],
                        'home_win_percentage': record['avg_home_win_pct'],
                        'opponents_analyzed': record['opponents'],
                        'classification': record['pattern_type']
                    })

                # 2. Find divisional dominance patterns
                query2 = """
                MATCH (t:Team)-[r:DIVISIONAL_RIVAL]->(rival:Team)
                MATCH (t)-[h:HEAD_TO_HEAD]-(rival)
                WITH t, avg(h.home_win_percentage) as divisional_dominance, count(rival) as divisional_opponents
                WHERE divisional_opponents >= 3
                RETURN t.team_id as team_id, divisional_dominance, divisional_opponents,
                       CASE WHEN divisional_dominance > 0.6 THEN 'divisional_dominant'
                            WHEN divisional_dominance < 0.4 THEN 'divisional_weak'
                            ELSE 'divisional_balanced' END as dominance_type
                ORDER BY divisional_dominance DESC
                """

                result2 = await session.run(query2)
                async for record in result2:
                    patterns.append({
                        'pattern_type': 'divisional_dominance',
                        'team_id': record['team_id'],
                        'dominance_score': record['divisional_dominance'],
                        'divisional_opponents': record['divisional_opponents'],
                        'classification': record['dominance_type']
                    })

                # 3. Find momentum pattern teams
                query3 = """
                MATCH (g1:Game)-[m:MOMENTUM_INFLUENCE]->(g2:Game)
                WITH m.team_id as team_id,
                     sum(CASE WHEN m.momentum_type = 'positive_momentum' THEN 1 ELSE 0 END) as positive_momentum,
                     sum(CASE WHEN m.momentum_type = 'negative_momentum' THEN 1 ELSE 0 END) as negative_momentum,
                     count(m) as total_momentum_games
                WHERE total_momentum_games > 10
                WITH team_id, positive_momentum, negative_momentum, total_momentum_games,
                     toFloat(positive_momentum) / total_momentum_games as momentum_consistency
                RETURN team_id, momentum_consistency, total_momentum_games,
                       CASE WHEN momentum_consistency > 0.6 THEN 'momentum_consistent'
                            WHEN momentum_consistency < 0.4 THEN 'momentum_inconsistent'
                            ELSE 'momentum_average' END as momentum_type
                ORDER BY momentum_consistency DESC
                """

                result3 = await session.run(query3)
                async for record in result3:
                    patterns.append({
                        'pattern_type': 'momentum_consistency',
                        'team_id': record['team_id'],
                        'momentum_score': record['momentum_consistency'],
                        'games_analyzed': record['total_momentum_games'],
                        'classification': record['momentum_type']
                    })

                self.logger.info(f"🔍 Discovered {len(patterns)} team relationship patterns")
                return patterns

        except Exception as e:
            self.logger.error(f"Failed to discover team patterns: {e}")
            return []

    def _get_coaching_relationships(self) -> List[Dict[str, Any]]:
        """Get coaching tree relationships (simplified data)"""
        # In production, this would come from a comprehensive coaching database
        return [
            {
                'mentor_id': 'bill_belichick',
                'mentor_name': 'Bill Belichick',
                'protege_id': 'josh_mcdaniels',
                'protege_name': 'Josh McDaniels',
                'years_together': 8,
                'relationship_type': 'offensive_coordinator'
            },
            {
                'mentor_id': 'andy_reid',
                'mentor_name': 'Andy Reid',
                'protege_id': 'doug_pederson',
                'protege_name': 'Doug Pederson',
                'years_together': 5,
                'relationship_type': 'assistant_coach'
            },
            {
                'mentor_id': 'sean_payton',
                'mentor_name': 'Sean Payton',
                'protege_id': 'dan_campbell',
                'protege_name': 'Dan Campbell',
                'years_together': 3,
                'relationship_type': 'assistant_coach'
            }
        ]

    def _get_team_coaching_history(self) -> List[Dict[str, Any]]:
        """Get team coaching history (simplified data)"""
        # In production, this would come from a comprehensive coaching database
        return [
            {
                'coach_id': 'bill_belichick',
                'team_id': 'NE',
                'start_year': 2000,
                'end_year': 2023,
                'position': 'head_coach'
            },
            {
                'coach_id': 'andy_reid',
                'team_id': 'KC',
                'start_year': 2013,
                'end_year': 2024,
                'position': 'head_coach'
            },
            {
                'coach_id': 'sean_payton',
                'team_id': 'NO',
                'start_year': 2006,
                'end_year': 2021,
                'position': 'head_coach'
            }
        ]

    async def build_all_team_relationships(self) -> TeamRelationshipStats:
        """Build all team and game relationship networks"""
        self.logger.info("🏗️ Building comprehensive team relationship networks...")

        # Build all relationship types
        success_count = 0

        if await self.build_team_vs_team_relationships():
            success_count += 1

        if await self.build_divisional_relationships():
            success_count += 1

        if await self.build_coaching_relationships():
            success_count += 1

        if await self.build_game_influence_patterns():
            success_count += 1

        if await self.build_conference_relationships():
            success_count += 1

        # Discover patterns
        patterns = await self.discover_team_patterns()

        self.logger.info(f"✅ Team relationship network building completed:")
        self.logger.info(f"   Successful operations: {success_count}/5")
        self.logger.info(f"   Total matchups: {self.stats.total_matchups}")
        self.logger.info(f"   Rivalry relationships: {self.stats.rivalry_relationships}")
        self.logger.info(f"   Coaching connections: {self.stats.coaching_connections}")
        self.logger.info(f"   Patterns discovered: {len(patterns)}")

        return self.stats

    def get_relationship_stats(self) -> TeamRelationshipStats:
        """Get current relationship building statistics"""
        return self.stats
