"""
Neo4j Data Ingestion Pipeline

This service ingests data from the training loop into the Neo4j knowledge grap
reating relationships between teams, games, experts, and memories.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from services.neo4j_knowledge_service import Neo4jKnowledgeService
from training.nfl_data_loader import GameContext
from training.prediction_generator import GamePrediction


@dataclass
class IngestionStats:
    """Statistics for data ingestion"""
    teams_created: int = 0
    games_created: int = 0
    memories_created: int = 0
    relationships_created: int = 0
    errors: int = 0


class Neo4jIngestionPipeline:
    """
    Pipeline for ingesting training loop data into Neo4j knowledge graph.

    This creates the foundational relationships needed for graph-enhanced
    memory retrieval and pattern discovery.
    """

    def __init__(self, neo4j_service: Neo4jKnowledgeService):
        self.neo4j_service = neo4j_service
        self.logger = logging.getLogger(__name__)
        self.stats = IngestionStats()

    async def ingest_game_data(self, game: GameContext,
                              expert_predictions: Dict[str, GamePrediction]) -> bool:
        """
        Ingest a single game and its predictions into the knowledge graph.

        Args:
            game: Game context data
            expert_predictions: Predictions from all experts

        Returns:
            bool: Success status
        """
        try:
            # 1. Create/update team nodes
            await self._ingest_team_data(game.home_team, game)
            await self._ingest_team_data(game.away_team, game)

            # 2. Create game node with relationships
            await self._ingest_game_node(game)

            # 3. Create expert prediction memories
            await self._ingest_expert_predictions(game, expert_predictions)

            # 4. Create team-vs-team relationship
            await self._create_team_matchup_relationship(game)

            self.logger.info(f"✅ Ingested game data: {game.away_team} @ {game.home_team}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to ingest game data: {e}")
            self.stats.errors += 1
            return False

    async def _ingest_team_data(self, team_id: str, game: GameContext) -> None:
        """Create or update team node in the knowledge graph"""
        try:
            # Map team abbreviations to full data
            team_data = self._get_team_data(team_id, game)

            result = await self.neo4j_service.create_team_node(team_data)
            if result:
                self.stats.teams_created += 1

        except Exception as e:
            self.logger.error(f"Failed to ingest team {team_id}: {e}")
            self.stats.errors += 1

    def _get_team_data(self, team_id: str, game: GameContext) -> Dict[str, Any]:
        """Get team data for Neo4j node creation"""
        # Basic team mapping - in production this would come from a comprehensive team database
        team_info = {
            'team_id': team_id,
            'name': team_id,  # Simplified for now
            'city': team_id,  # Simplified for now
            'conference': self._get_team_conference(team_id),
            'division': self._get_team_division(team_id),
            'founded_year': 1960,  # Default
            'stadium': game.stadium if team_id == game.home_team else None
        }

        return team_info

    def _get_team_conference(self, team_id: str) -> str:
        """Get team conference (simplified mapping)"""
        afc_teams = {
            'BUF', 'MIA', 'NE', 'NYJ',  # AFC East
            'BAL', 'CIN', 'CLE', 'PIT',  # AFC North
            'HOU', 'IND', 'JAX', 'TEN',  # AFC South
            'DEN', 'KC', 'LV', 'LAC'     # AFC West
        }
        return 'AFC' if team_id in afc_teams else 'NFC'

    def _get_team_division(self, team_id: str) -> str:
        """Get team division (simplified mapping)"""
        divisions = {
            # AFC
            'BUF': 'AFC East', 'MIA': 'AFC East', 'NE': 'AFC East', 'NYJ': 'AFC East',
            'BAL': 'AFC North', 'CIN': 'AFC North', 'CLE': 'AFC North', 'PIT': 'AFC North',
            'HOU': 'AFC South', 'IND': 'AFC South', 'JAX': 'AFC South', 'TEN': 'AFC South',
            'DEN': 'AFC West', 'KC': 'AFC West', 'LV': 'AFC West', 'LAC': 'AFC West',
            # NFC
            'DAL': 'NFC East', 'NYG': 'NFC East', 'PHI': 'NFC East', 'WAS': 'NFC East',
            'CHI': 'NFC North', 'DET': 'NFC North', 'GB': 'NFC North', 'MIN': 'NFC North',
            'ATL': 'NFC South', 'CAR': 'NFC South', 'NO': 'NFC South', 'TB': 'NFC South',
            'ARI': 'NFC West', 'LAR': 'NFC West', 'SF': 'NFC West', 'SEA': 'NFC West'
        }
        return divisions.get(team_id, 'Unknown')

    async def _ingest_game_node(self, game: GameContext) -> None:
        """Create game node with team relationships"""
        try:
            game_data = {
                'game_id': game.game_id,
                'date': game.game_date.strftime('%Y-%m-%d'),
                'week': game.week,
                'season': game.season,
                'home_score': game.home_score or 0,
                'away_score': game.away_score or 0,
                'weather_temperature': game.weather.get('temperature') if game.weather else None,
                'weather_wind': game.weather.get('wind_speed') if game.weather else None,
                'venue': game.stadium,
                'is_divisional': game.division_game,
                'is_primetime': self._is_primetime_game(game),
                'home_team': game.home_team,
                'away_team': game.away_team
            }

            result = await self.neo4j_service.create_game_node(game_data)
            if result:
                self.stats.games_created += 1

        except Exception as e:
            self.logger.error(f"Failed to ingest game node: {e}")
            self.stats.errors += 1

    def _is_primetime_game(self, game: GameContext) -> bool:
        """Determine if game is primetime (simplified logic)"""
        # This would be more sophisticated in production
        return game.game_date.weekday() in [0, 3, 6]  # Monday, Thursday, Sunday

    async def _ingest_expert_predictions(self, game: GameContext,
                                       expert_predictions: Dict[str, GamePrediction]) -> None:
        """Create expert memory nodes for predictions"""
        for expert_id, prediction in expert_predictions.items():
            try:
                memory_data = {
                    'memory_type': 'game_prediction',
                    'content': json.dumps({
                        'game_id': game.game_id,
                        'predicted_winner': prediction.predicted_winner,
                        'win_probability': prediction.win_probability,
                        'reasoning_chain': prediction.reasoning_chain,
                        'game_context': {
                            'home_team': game.home_team,
                            'away_team': game.away_team,
                            'week': game.week,
                            'season': game.season,
                            'division_game': game.division_game,
                            'weather': game.weather
                        }
                    }),
                    'confidence': prediction.confidence_level,
                    'team_id': game.home_team,  # Associate with home team
                    'game_id': game.game_id
                }

                result = await self.neo4j_service.create_expert_memory_node(expert_id, memory_data)
                if result:
                    self.stats.memories_created += 1

                # Also create memory for away team
                memory_data['team_id'] = game.away_team
                result = await self.neo4j_service.create_expert_memory_node(expert_id, memory_data)
                if result:
                    self.stats.memories_created += 1

            except Exception as e:
                self.logger.error(f"Failed to create memory for expert {expert_id}: {e}")
                self.stats.errors += 1

    async def _create_team_matchup_relationship(self, game: GameContext) -> None:
        """Create historical matchup relationship between teams"""
        try:
            if not self.neo4j_service.driver:
                return

            async with self.neo4j_service.driver.session() as session:
                # Create or update matchup relationship
                query = """
                MATCH (home:Team {team_id: $home_team})
                MATCH (away:Team {team_id: $away_team})
                MERGE (home)-[r:HISTORICAL_MATCHUP]-(away)
                ON CREATE SET r.games_played = 1, r.created_at = datetime()
                ON MATCH SET r.games_played = r.games_played + 1, r.updated_at = datetime()
                SET r.last_game_id = $game_id,
                    r.last_game_date = date($game_date)
                RETURN r
                """

                await session.run(query,
                                home_team=game.home_team,
                                away_team=game.away_team,
                                game_id=game.game_id,
                                game_date=game.game_date.strftime('%Y-%m-%d'))

                self.stats.relationships_created += 1

        except Exception as e:
            self.logger.error(f"Failed to create matchup relationship: {e}")
            self.stats.errors += 1

    async def create_expert_learning_relationships(self, expert_id: str,
                                                 learning_data: Dict[str, Any]) -> bool:
        """
        Create relationships that represent expert learning patterns.

        Args:
            expert_id: Expert identifier
            learning_data: Data about what the expert learned

        Returns:
            bool: Success status
        """
        try:
            if not self.neo4j_service.driver:
                return False

            async with self.neo4j_service.driver.session() as session:
                # Create learning pattern node
                query = """
                MATCH (e:Expert {expert_id: $expert_id})
                CREATE (p:LearningPattern {
                    pattern_id: randomUUID(),
                    pattern_type: $pattern_type,
                    description: $description,
                    confidence: $confidence,
                    created_at: datetime()
                })
                CREATE (e)-[:DISCOVERED_PATTERN]->(p)
                RETURN p.pattern_id as pattern_id
                """

                result = await session.run(query,
                                         expert_id=expert_id,
                                         pattern_type=learning_data.get('pattern_type', 'general'),
                                         description=learning_data.get('description', ''),
                                         confidence=learning_data.get('confidence', 0.5))

                record = await result.single()
                if record:
                    self.logger.info(f"Created learning pattern for expert {expert_id}")
                    return True

                return False

        except Exception as e:
            self.logger.error(f"Failed to create learning relationship: {e}")
            return False

    async def create_memory_similarity_relationships(self, similarity_threshold: float = 0.7) -> int:
        """
        Create similarity relationships between memories based on content similarity.

        Args:
            similarity_threshold: Minimum similarity score to create relationship

        Returns:
            int: Number of relationships created
        """
        relationships_created = 0

        try:
            if not self.neo4j_service.driver:
                return 0

            async with self.neo4j_service.driver.session() as session:
                # Find memories that might be similar (same expert, similar teams)
                query = """
                MATCH (e:Expert)-[:HAS_MEMORY]->(m1:Memory)-[:ABOUT_TEAM]->(t:Team)
                MATCH (e)-[:HAS_MEMORY]->(m2:Memory)-[:ABOUT_TEAM]->(t)
                WHERE m1.memory_id <> m2.memory_id
                AND NOT (m1)-[:SIMILAR_TO]-(m2)
                RETURN m1.memory_id as memory1, m2.memory_id as memory2,
                       m1.content as content1, m2.content as content2
                LIMIT 100
                """

                result = await session.run(query)

                async for record in result:
                    # Simple similarity calculation (in production, use embeddings)
                    similarity = self._calculate_content_similarity(
                        record['content1'], record['content2']
                    )

                    if similarity >= similarity_threshold:
                        success = await self.neo4j_service.create_memory_similarity_relationship(
                            record['memory1'], record['memory2'], similarity
                        )
                        if success:
                            relationships_created += 1

        except Exception as e:
            self.logger.error(f"Failed to create similarity relationships: {e}")

        return relationships_created

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate similarity between two memory contents.

        This is a simplified implementation. In production, you would use
        embeddings and cosine similarity.
        """
        try:
            # Parse JSON content
            data1 = json.loads(content1) if isinstance(content1, str) else content1
            data2 = json.loads(content2) if isinstance(content2, str) else content2

            # Simple similarity based on shared attributes
            similarity_score = 0.0
            total_attributes = 0

            # Compare game context attributes
            if 'game_context' in data1 and 'game_context' in data2:
                context1 = data1['game_context']
                context2 = data2['game_context']

                for key in ['division_game', 'week', 'season']:
                    if key in context1 and key in context2:
                        total_attributes += 1
                        if context1[key] == context2[key]:
                            similarity_score += 1

                # Weather similarity
                if 'weather' in context1 and 'weather' in context2:
                    total_attributes += 1
                    if context1['weather'] == context2['weather']:
                        similarity_score += 1

            # Compare prediction outcomes
            if 'predicted_winner' in data1 and 'predicted_winner' in data2:
                total_attributes += 1
                if data1['predicted_winner'] == data2['predicted_winner']:
                    similarity_score += 1

            return similarity_score / total_attributes if total_attributes > 0 else 0.0

        except Exception:
            return 0.0

    async def batch_ingest_season(self, season_data: List[Dict[str, Any]]) -> IngestionStats:
        """
        Batch ingest an entire season of data.

        Args:
            season_data: List of game data with predictions

        Returns:
            IngestionStats: Statistics about the ingestion
        """
        self.stats = IngestionStats()  # Reset stats

        self.logger.info(f"🚀 Starting batch ingestion of {len(season_data)} games")

        for i, game_data in enumerate(season_data):
            try:
                game = game_data['game']
                predictions = game_data['predictions']

                await self.ingest_game_data(game, predictions)

                # Progress logging
                if (i + 1) % 10 == 0:
                    self.logger.info(f"📈 Ingested {i + 1}/{len(season_data)} games")

            except Exception as e:
                self.logger.error(f"Failed to ingest game {i}: {e}")
                self.stats.errors += 1

        # Create similarity relationships after all data is ingested
        self.logger.info("🔗 Creating memory similarity relationships...")
        similarity_relationships = await self.create_memory_similarity_relationships()
        self.stats.relationships_created += similarity_relationships

        self.logger.info(f"✅ Batch ingestion completed:")
        self.logger.info(f"   Teams created: {self.stats.teams_created}")
        self.logger.info(f"   Games created: {self.stats.games_created}")
        self.logger.info(f"   Memories created: {self.stats.memories_created}")
        self.logger.info(f"   Relationships created: {self.stats.relationships_created}")
        self.logger.info(f"   Errors: {self.stats.errors}")

        return self.stats

    def get_ingestion_stats(self) -> IngestionStats:
        """Get current ingestion statistics"""
        return self.stats
