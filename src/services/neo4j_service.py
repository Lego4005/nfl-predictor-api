"""
Neo4j Service - Expert Learning Graph Database
Provides connection and query utilities for the NFL Expert Learning System
"""
import os
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver, Session
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Neo4jService:
    """
    Neo4j connection service for Expert Learning System
    Manages connections to Neo4j graph database for tracking:
    - Expert predictions and accuracy
    - Team matchup history
    - Memory influence on predictions
    - Expert knowledge graphs
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize Neo4j connection

        Args:
            uri: Neo4j URI (defaults to NEO4J_URI env var)
            user: Neo4j username (defaults to NEO4J_USER env var)
            password: Neo4j password (defaults to NEO4J_PASSWORD env var)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7688")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "nflpredictor123")

        self._driver: Optional[Driver] = None

    def connect(self) -> Driver:
        """Establish connection to Neo4j"""
        if not self._driver:
            try:
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password)
                )
                # Verify connectivity
                self._driver.verify_connectivity()
                logger.info(f"Connected to Neo4j at {self.uri}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise
        return self._driver

    def close(self):
        """Close Neo4j connection"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    @contextmanager
    def session(self) -> Session:
        """Context manager for Neo4j session"""
        driver = self.connect()
        session = driver.session()
        try:
            yield session
        finally:
            session.close()

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a write transaction

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query execution summary
        """
        with self.session() as session:
            result = session.run(query, parameters or {})
            summary = result.consume()
            return {
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created,
                "properties_set": summary.counters.properties_set,
            }

    # Expert Node Operations

    def get_expert(self, expert_id: str) -> Optional[Dict[str, Any]]:
        """Get expert node by ID"""
        query = """
        MATCH (e:Expert {id: $expert_id})
        RETURN e.id as id, e.name as name, e.personality as personality,
               e.decision_style as decision_style
        """
        results = self.execute_query(query, {"expert_id": expert_id})
        return results[0] if results else None

    def list_experts(self) -> List[Dict[str, Any]]:
        """Get all expert nodes"""
        query = """
        MATCH (e:Expert)
        RETURN e.id as id, e.name as name, e.personality as personality,
               e.decision_style as decision_style
        ORDER BY e.name
        """
        return self.execute_query(query)

    # Team Node Operations

    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team node by ID"""
        query = """
        MATCH (t:Team {id: $team_id})
        RETURN t.id as id, t.name as name, t.division as division,
               t.conference as conference
        """
        results = self.execute_query(query, {"team_id": team_id})
        return results[0] if results else None

    def list_teams(self, division: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all teams, optionally filtered by division"""
        if division:
            query = """
            MATCH (t:Team {division: $division})
            RETURN t.id as id, t.name as name, t.division as division,
                   t.conference as conference
            ORDER BY t.name
            """
            return self.execute_query(query, {"division": division})
        else:
            query = """
            MATCH (t:Team)
            RETURN t.id as id, t.name as name, t.division as division,
                   t.conference as conference
            ORDER BY t.name
            """
            return self.execute_query(query)

    # Game and Prediction Operations

    def create_game(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        season: int,
        week: int,
        game_date: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a game node"""
        query = """
        MERGE (g:Game {id: $game_id})
        SET g.home_team = $home_team,
            g.away_team = $away_team,
            g.season = $season,
            g.week = $week,
            g.date = date($game_date)
        RETURN g.id as id
        """
        params = {
            "game_id": game_id,
            "home_team": home_team,
            "away_team": away_team,
            "season": season,
            "week": week,
            "game_date": game_date,
        }
        params.update(kwargs)
        return self.execute_write(query, params)

    def record_prediction(
        self,
        expert_id: str,
        game_id: str,
        winner: str,
        confidence: float,
        win_probability: float,
        reasoning: str
    ) -> Dict[str, Any]:
        """Record an expert's prediction for a game"""
        query = """
        MATCH (e:Expert {id: $expert_id})
        MATCH (g:Game {id: $game_id})
        MERGE (e)-[p:PREDICTED]->(g)
        SET p.winner = $winner,
            p.confidence = $confidence,
            p.win_probability = $win_probability,
            p.reasoning = $reasoning,
            p.created_at = datetime()
        RETURN p
        """
        params = {
            "expert_id": expert_id,
            "game_id": game_id,
            "winner": winner,
            "confidence": confidence,
            "win_probability": win_probability,
            "reasoning": reasoning,
        }
        return self.execute_write(query, params)

    def get_expert_predictions(
        self,
        expert_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent predictions by an expert"""
        query = """
        MATCH (e:Expert {id: $expert_id})-[p:PREDICTED]->(g:Game)
        RETURN g.id as game_id, g.date as game_date,
               g.home_team as home_team, g.away_team as away_team,
               p.winner as predicted_winner, p.confidence as confidence,
               p.reasoning as reasoning, p.created_at as predicted_at
        ORDER BY g.date DESC
        LIMIT $limit
        """
        return self.execute_query(query, {"expert_id": expert_id, "limit": limit})

    # Memory Operations

    def record_memory_usage(
        self,
        memory_id: str,
        game_id: str,
        expert_id: str,
        influence_weight: float,
        retrieval_rank: int
    ) -> Dict[str, Any]:
        """Record that a memory was used in a prediction"""
        query = """
        MATCH (m:Memory {id: $memory_id})
        MATCH (g:Game {id: $game_id})
        MERGE (m)-[u:USED_IN]->(g)
        SET u.expert_id = $expert_id,
            u.influence_weight = $influence_weight,
            u.retrieval_rank = $retrieval_rank
        RETURN u
        """
        params = {
            "memory_id": memory_id,
            "game_id": game_id,
            "expert_id": expert_id,
            "influence_weight": influence_weight,
            "retrieval_rank": retrieval_rank,
        }
        return self.execute_write(query, params)

    def get_prediction_provenance(
        self,
        expert_id: str,
        game_id: str
    ) -> List[Dict[str, Any]]:
        """Get all memories that influenced a prediction"""
        query = """
        MATCH (e:Expert {id: $expert_id})-[:PREDICTED]->(g:Game {id: $game_id})
        MATCH (m:Memory)-[u:USED_IN {expert_id: $expert_id}]->(g)
        RETURN m.id as memory_id, m.type as memory_type,
               m.content as memory_content, u.influence_weight as influence,
               u.retrieval_rank as rank
        ORDER BY u.retrieval_rank
        """
        return self.execute_query(query, {"expert_id": expert_id, "game_id": game_id})

    # Health Check

    def health_check(self) -> bool:
        """Verify Neo4j connection is healthy"""
        try:
            with self.session() as session:
                result = session.run("RETURN 1 as health")
                return result.single()["health"] == 1
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Global singleton instance
_neo4j_service: Optional[Neo4jService] = None


def get_neo4j_service() -> Neo4jService:
    """Get or create global Neo4j service instance"""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
    return _neo4j_service
