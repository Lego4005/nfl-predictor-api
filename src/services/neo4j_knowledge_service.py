"""
Neo4j Knowledge Graph Service for NFL Relationships

This service manages the knowledge graph that models relationships between:
- Teams, players, coaches
- Games and their connections
- Expert leang patterns
- Memory relationships and discoveries

The graph enables relationship-based memory retrieval and pattern discovery.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
from dataclasses import dataclass

try:
    from neo4j import AsyncGraphDatabase, AsyncDriver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    AsyncGraphDatabase = None
    AsyncDriver = None


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph"""
    id: str
    labels: List[str]
    properties: Dict[str, Any]


@dataclass
class GraphRelationship:
    """Represents a relationship in the knowledge graph"""
    start_node: str
    end_node: str
    type: str
    properties: Dict[str, Any]


@dataclass
class GraphPath:
    """Represents a path through the knowledge graph"""
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]
    length: int


class Neo4jKnowledgeService:
    """
    Service for managing NFL knowledge graph using Neo4j.

    This enables relationship-based memory retrieval and pattern discovery
    by modeling the complex relationships in NFL data.
    """

    def __init__(self, neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "nflpredictor123"):
        self.logger = logging.getLogger(__name__)

        if not NEO4J_AVAILABLE:
            self.logger.warning("Neo4j driver not available. Install with: pip install neo4j")
            self.driver = None
            return

        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver: Optional[AsyncDriver] = None

    async def initialize(self) -> bool:
        """Initialize connection to Neo4j"""
        if not NEO4J_AVAILABLE:
            self.logger.error("Neo4j driver not available")
            return False

        try:
            self.driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )

            # Test connection
            await self.driver.verify_connectivity()
            self.logger.info("Neo4j connection established")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {str(e)}")
            return False

    async def close(self) -> None:
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()

    async def create_team_node(self, team_data: Dict[str, Any]) -> str:
        """Create or update a team node in the knowledge graph"""
        if not self.driver:
            return ""

        try:
            async with self.driver.session() as session:
                query = """
                MERGE (t:Team {team_id: $team_id})
                SET t.name = $name,
                    t.city = $city,
                    t.conference = $conference,
                    t.division = $division,
                    t.founded_year = $founded_year,
                    t.stadium = $stadium,
                    t.updated_at = datetime()
                RETURN t.team_id as team_id
                """

                result = await session.run(query, **team_data)
                record = await result.single()

                if record:
                    team_id = record["team_id"]

                    # Create division relationship
                    if 'division' in team_data:
                        await self._create_division_relationship(team_id, team_data['division'])

                    self.logger.info(f"Created/updated team node: {team_id}")
                    return team_id

                return ""

        except Exception as e:
            self.logger.error(f"Error creating team node: {str(e)}")
            return ""

    async def create_game_node(self, game_data: Dict[str, Any]) -> str:
        """Create a game node and its relationships"""
        if not self.driver:
            return ""

        try:
            async with self.driver.session() as session:
                # Create game node
                query = """
                MERGE (g:Game {game_id: $game_id})
                SET g.date = date($date),
                    g.week = $week,
                    g.season = $season,
                    g.home_score = $home_score,
                    g.away_score = $away_score,
                    g.weather_temperature = $weather_temperature,
                    g.weather_wind = $weather_wind,
                    g.venue = $venue,
                    g.is_divisional = $is_divisional,
                    g.is_primetime = $is_primetime,
                    g.updated_at = datetime()
                RETURN g.game_id as game_id
                """

                result = await session.run(query, **game_data)
                record = await result.single()

                if record:
                    game_id = record["game_id"]

                    # Create team relationships
                    if 'home_team' in game_data:
                        await self._create_game_team_relationship(game_id, game_data['home_team'], 'PLAYED_HOME')

                    if 'away_team' in game_data:
                        await self._create_game_team_relationship(game_id, game_data['away_team'], 'PLAYED_AWAY')

                    self.logger.info(f"Created game node: {game_id}")
                    return game_id

                return ""

        except Exception as e:
            self.logger.error(f"Error creating game node: {str(e)}")
            return ""

    async def create_expert_memory_node(self, expert_id: str, memory_data: Dict[str, Any]) -> str:
        """Create an expert memory node and its relationships"""
        if not self.driver:
            return ""

        try:
            async with self.driver.session() as session:
                # Create memory node
                query = """
                MERGE (e:Expert {expert_id: $expert_id})
                CREATE (m:Memory {
                    memory_id: randomUUID(),
                    expert_id: $expert_id,
                    memory_type: $memory_type,
                    content: $content,
                    confidence: $confidence,
                    created_at: datetime(),
                    last_accessed: datetime()
                })
                CREATE (e)-[:HAS_MEMORY]->(m)
                RETURN m.memory_id as memory_id
                """

                params = {
                    'expert_id': expert_id,
                    'memory_type': memory_data.get('memory_type', 'general'),
                    'content': memory_data.get('content', ''),
                    'confidence': memory_data.get('confidence', 0.5)
                }

                result = await session.run(query, **params)
                record = await result.single()

                if record:
                    memory_id = record["memory_id"]

                    # Create relationships to teams/games if specified
                    if 'team_id' in memory_data:
                        await self._create_memory_team_relationship(memory_id, memory_data['team_id'])

                    if 'game_id' in memory_data:
                        await self._create_memory_game_relationship(memory_id, memory_data['game_id'])

                    self.logger.info(f"Created memory node: {memory_id}")
                    return memory_id

                return ""

        except Exception as e:
            self.logger.error(f"Error creating memory node: {str(e)}")
            return ""

    async def find_related_memories(self, expert_id: str, context: Dict[str, Any],
                                  max_depth: int = 3, max_results: int = 10) -> List[Dict[str, Any]]:
        """Find memories related through graph relationships"""
        if not self.driver:
            return []

        try:
            async with self.driver.session() as session:
                # Build query based on context
                query_parts = []
                params = {'expert_id': expert_id, 'max_results': max_results}

                if 'team_id' in context:
                    query_parts.append("""
                    MATCH (e:Expert {expert_id: $expert_id})-[:HAS_MEMORY]->(m:Memory)
                    MATCH (m)-[:ABOUT_TEAM]->(t:Team {team_id: $team_id})
                    """)
                    params['team_id'] = context['team_id']

                elif 'game_id' in context:
                    query_parts.append("""
                    MATCH (e:Expert {expert_id: $expert_id})-[:HAS_MEMORY]->(m:Memory)
                    MATCH (m)-[:ABOUT_GAME]->(g:Game {game_id: $game_id})
                    """)
                    params['game_id'] = context['game_id']

                else:
                    # General memory search
                    query_parts.append("""
                    MATCH (e:Expert {expert_id: $expert_id})-[:HAS_MEMORY]->(m:Memory)
                    """)

                # Add return clause
                query_parts.append("""
                RETURN m.memory_id as memory_id,
                       m.memory_type as memory_type,
                       m.content as content,
                       m.confidence as confidence,
                       m.created_at as created_at
                ORDER BY m.confidence DESC, m.created_at DESC
                LIMIT $max_results
                """)

                query = " ".join(query_parts)
                result = await session.run(query, **params)

                memories = []
                async for record in result:
                    memories.append({
                        'memory_id': record['memory_id'],
                        'memory_type': record['memory_type'],
                        'content': record['content'],
                        'confidence': record['confidence'],
                        'created_at': record['created_at']
                    })

                self.logger.info(f"Found {len(memories)} related memories for expert {expert_id}")
                return memories

        except Exception as e:
            self.logger.error(f"Error finding related memories: {str(e)}")
            return []

    async def discover_relationship_patterns(self, expert_id: str) -> List[Dict[str, Any]]:
        """Discover patterns in expert's memory relationships"""
        if not self.driver:
            return []

        try:
            async with self.driver.session() as session:
                # Find common relationship patterns
                query = """
                MATCH (e:Expert {expert_id: $expert_id})-[:HAS_MEMORY]->(m:Memory)
                MATCH (m)-[r]->(n)
                WITH type(r) as relationship_type, labels(n) as node_labels, count(*) as frequency
                WHERE frequency > 1
                RETURN relationship_type, node_labels, frequency
                ORDER BY frequency DESC
                LIMIT 20
                """

                result = await session.run(query, expert_id=expert_id)

                patterns = []
                async for record in result:
                    patterns.append({
                        'relationship_type': record['relationship_type'],
                        'node_labels': record['node_labels'],
                        'frequency': record['frequency']
                    })

                self.logger.info(f"Discovered {len(patterns)} relationship patterns for expert {expert_id}")
                return patterns

        except Exception as e:
            self.logger.error(f"Error discovering patterns: {str(e)}")
            return []

    async def find_expert_knowledge_gaps(self, expert_id: str) -> List[Dict[str, Any]]:
        """Find teams or situations the expert has limited knowledge about"""
        if not self.driver:
            return []

        try:
            async with self.driver.session() as session:
                # Find teams with few memories
                query = """
                MATCH (t:Team)
                OPTIONAL MATCH (e:Expert {expert_id: $expert_id})-[:HAS_MEMORY]->(m:Memory)-[:ABOUT_TEAM]->(t)
                WITH t, count(m) as memory_count
                WHERE memory_count < 3
                RETURN t.team_id as team_id, t.name as team_name, memory_count
                ORDER BY memory_count ASC, t.name ASC
                """

                result = await session.run(query, expert_id=expert_id)

                gaps = []
                async for record in result:
                    gaps.append({
                        'team_id': record['team_id'],
                        'team_name': record['team_name'],
                        'memory_count': record['memory_count'],
                        'gap_type': 'team_knowledge'
                    })

                self.logger.info(f"Found {len(gaps)} knowledge gaps for expert {expert_id}")
                return gaps

        except Exception as e:
            self.logger.error(f"Error finding knowledge gaps: {str(e)}")
            return []

    async def create_memory_similarity_relationship(self, memory_id1: str, memory_id2: str,
                                                  similarity_score: float) -> bool:
        """Create similarity relationship between memories"""
        if not self.driver:
            return False

        try:
            async with self.driver.session() as session:
                query = """
                MATCH (m1:Memory {memory_id: $memory_id1})
                MATCH (m2:Memory {memory_id: $memory_id2})
                MERGE (m1)-[r:SIMILAR_TO]->(m2)
                SET r.similarity_score = $similarity_score,
                    r.created_at = datetime()
                RETURN r
                """

                result = await session.run(query,
                                         memory_id1=memory_id1,
                                         memory_id2=memory_id2,
                                         similarity_score=similarity_score)

                record = await result.single()
                success = record is not None

                if success:
                    self.logger.info(f"Created similarity relationship: {memory_id1} <-> {memory_id2}")

                return success

        except Exception as e:
            self.logger.error(f"Error creating similarity relationship: {str(e)}")
            return False

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        if not self.driver:
            return {'error': 'Neo4j not available'}

        try:
            async with self.driver.session() as session:
                # Count nodes by label
                node_query = """
                CALL db.labels() YIELD label
                CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) YIELD value
                RETURN label, value.count as count
                """

                # Count relationships by type
                rel_query = """
                CALL db.relationshipTypes() YIELD relationshipType
                CALL apoc.cypher.run('MATCH ()-[r:' + relationshipType + ']->() RETURN count(r) as count', {}) YIELD value
                RETURN relationshipType, value.count as count
                """

                # Get node counts
                node_result = await session.run(node_query)
                node_counts = {}
                async for record in node_result:
                    node_counts[record['label']] = record['count']

                # Get relationship counts
                rel_result = await session.run(rel_query)
                rel_counts = {}
                async for record in rel_result:
                    rel_counts[record['relationshipType']] = record['count']

                return {
                    'node_counts': node_counts,
                    'relationship_counts': rel_counts,
                    'total_nodes': sum(node_counts.values()),
                    'total_relationships': sum(rel_counts.values())
                }

        except Exception as e:
            self.logger.error(f"Error getting graph statistics: {str(e)}")
            return {'error': str(e)}

    # Helper methods

    async def _create_division_relationship(self, team_id: str, division: str) -> None:
        """Create relationship between team and division"""
        if not self.driver:
            return

        async with self.driver.session() as session:
            query = """
            MATCH (t:Team {team_id: $team_id})
            MERGE (d:Division {name: $division})
            MERGE (t)-[:MEMBER_OF]->(d)
            """
            await session.run(query, team_id=team_id, division=division)

    async def _create_game_team_relationship(self, game_id: str, team_id: str, relationship_type: str) -> None:
        """Create relationship between game and team"""
        if not self.driver:
            return

        async with self.driver.session() as session:
            query = f"""
            MATCH (g:Game {{game_id: $game_id}})
            MATCH (t:Team {{team_id: $team_id}})
            MERGE (t)-[:{relationship_type}]->(g)
            """
            await session.run(query, game_id=game_id, team_id=team_id)

    async def _create_memory_team_relationship(self, memory_id: str, team_id: str) -> None:
        """Create relationship between memory and team"""
        if not self.driver:
            return

        async with self.driver.session() as session:
            query = """
            MATCH (m:Memory {memory_id: $memory_id})
            MATCH (t:Team {team_id: $team_id})
            MERGE (m)-[:ABOUT_TEAM]->(t)
            """
            await session.run(query, memory_id=memory_id, team_id=team_id)

    async def _create_memory_game_relationship(self, memory_id: str, game_id: str) -> None:
        """Create relationship between memory and game"""
        if not self.driver:
            return

        async with self.driver.session() as session:
            query = """
            MATCH (m:Memory {memory_id: $memory_id})
            MATCH (g:Game {game_id: $game_id})
            MERGE (m)-[:ABOUT_GAME]->(g)
            """
            await session.run(query, memory_id=memory_id, game_id=game_id)

    async def execute_basic_relationship_queries(self) -> Dict[str, Any]:
        """Execute basic relationship queries for testing and validation"""
        if not self.driver:
            return {'error': 'Neo4j not available'}

        try:
            async with self.driver.session() as session:
                queries = {}

                # 1. Find teams with most games played
                queries['teams_by_games'] = await self._query_teams_by_games(session)

                # 2. Find expert memory patterns
                queries['expert_memory_patterns'] = await self._query_expert_memory_patterns(session)

                # 3. Find team matchup history
                queries['team_matchups'] = await self._query_team_matchups(session)

                # 4. Find expert specializations
                queries['expert_specializations'] = await self._query_expert_specializations(session)

                return queries

        except Exception as e:
            self.logger.error(f"Error executing relationship queries: {str(e)}")
            return {'error': str(e)}

    async def _query_teams_by_games(self, session) -> List[Dict[str, Any]]:
        """Query teams ordered by number of games played"""
        query = """
        MATCH (t:Team)-[:PLAYED_HOME|PLAYED_AWAY]->(g:Game)
        WITH t, count(g) as games_played
        RETURN t.team_id as team_id, t.name as team_name, games_played
        ORDER BY games_played DESC
        LIMIT 10
        """

        result = await session.run(query)
        teams = []
        async for record in result:
            teams.append({
                'team_id': record['team_id'],
                'team_name': record['team_name'],
                'games_played': record['games_played']
            })
        return teams

    async def _query_expert_memory_patterns(self, session) -> List[Dict[str, Any]]:
        """Query expert memory patterns"""
        query = """
        MATCH (e:Expert)-[:HAS_MEMORY]->(m:Memory)
        WITH e, count(m) as memory_count, avg(m.confidence) as avg_confidence
        RETURN e.expert_id as expert_id, memory_count, avg_confidence
        ORDER BY memory_count DESC
        """

        result = await session.run(query)
        patterns = []
        async for record in result:
            patterns.append({
                'expert_id': record['expert_id'],
                'memory_count': record['memory_count'],
                'avg_confidence': record['avg_confidence']
            })
        return patterns

    async def _query_team_matchups(self, session) -> List[Dict[str, Any]]:
        """Query team historical matchups"""
        query = """
        MATCH (t1:Team)-[r:HISTORICAL_MATCHUP]-(t2:Team)
        WHERE t1.team_id < t2.team_id  // Avoid duplicates
        RETURN t1.team_id as team1, t2.team_id as team2, r.games_played as games_played
        ORDER BY r.games_played DESC
        LIMIT 10
        """

        result = await session.run(query)
        matchups = []
        async for record in result:
            matchups.append({
                'team1': record['team1'],
                'team2': record['team2'],
                'games_played': record['games_played']
            })
        return matchups

    async def _query_expert_specializations(self, session) -> List[Dict[str, Any]]:
        """Query expert specializations by team"""
        query = """
        MATCH (e:Expert)-[:HAS_MEMORY]->(m:Memory)-[:ABOUT_TEAM]->(t:Team)
        WITH e, t, count(m) as memories_about_team
        WHERE memories_about_team > 2
        RETURN e.expert_id as expert_id, t.team_id as team_id, memories_about_team
        ORDER BY memories_about_team DESC
        LIMIT 20
        """

        result = await session.run(query)
        specializations = []
        async for record in result:
            specializations.append({
                'expert_id': record['expert_id'],
                'team_id': record['team_id'],
                'memories_about_team': record['memories_about_team']
            })
        return specializations
