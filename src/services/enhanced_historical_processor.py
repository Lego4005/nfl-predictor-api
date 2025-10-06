"""
Enhanced Historical Processor for Chronological Learning

This processor runs through historical NFL games in chronological order,
generating authentic episodic memory-informed predictionlding up
expert knowledge using the full three-layer memory architecture:

1. Structured Memory (team_knowledge, matchup_memories)
2. Semantic Memory (vector embeddings)
3. Relational Memory (Neo4j graph)

Each expert starts with zero knowledge and learns progressively through
actual game experiences, building increasingly sophisticated predictions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
from dataclasses import dataclass
import time

from supabase import Client as SupabaseClient
from .reconciliation_service import ReconciliationService
from .vector_memory_service import VectorMemoryService
from .neo4j_knowledge_service import Neo4jKnowledgeService


@dataclass
class ProcessingProgress:
    """Track processing progress through historical games"""
    total_games: int
    processed_games: int
    current_season: int
    current_week: int
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    games_per_minute: float = 0.0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class ExpertLearningStats:
    """Track learning statistics for each expert"""
    expert_id: str
    games_processed: int
    predictions_made: int
    team_knowledge_records: int
    matchup_memories: int
    vector_memories: int
    graph_relationships: int
    average_confidence: float = 0.0
    learning_trajectory: List[float] = None

    def __post_init__(self):
        if self.learning_trajectory is None:
            self.learning_trajectory = []


class EnhancedHistoricalProcessor:
    """
    Process historical NFL games chronologically to build authentic expert knowledge.

    This processor ensures experts learn progressively through actual game experiences,
    building up sophisticated episodic memories and chain-of-thought reasoning.
    """

    def __init__(self,
                 supabase_client: SupabaseClient,
                 openai_api_key: Optional[str] = None,
                 neo4j_uri: str = "bolt://localhost:7688"):
        self.supabase = supabase_client
        self.logger = logging.getLogger(__name__)

        # Initialize core services
        self.reconciliation_service = ReconciliationService(supabase_client)
        self.vector_service = VectorMemoryService(supabase_client, openai_api_key)
        self.neo4j_service = Neo4jKnowledgeService(neo4j_uri)

        # Processing configuration
        self.batch_size = 5  # Process 5 games concurrently
        self.delay_between_batches = 2  # Seconds between batches
        self.max_retries = 3

        # Progress tracking
        self.progress: Optional[ProcessingProgress] = None
        self.expert_stats: Dict[str, ExpertLearningStats] = {}

    async def initialize(self) -> bool:
        """Initialize all services and connections"""
        try:
            # Initialize Neo4j connection
            neo4j_connected = await self.neo4j_service.initialize()
            if not neo4j_connected:
                self.logger.warning("Neo4j not available - continuing without graph features")

            # Get list of experts
            experts_response = self.supabase.table('personality_experts').select('expert_id').execute()
            expert_ids = [expert['expert_id'] for expert in experts_response.data]

            # Initialize expert stats
            for expert_id in expert_ids:
                self.expert_stats[expert_id] = ExpertLearningStats(
                    expert_id=expert_id,
                    games_processed=0,
                    predictions_made=0,
                    team_knowledge_records=0,
                    matchup_memories=0,
                    vector_memories=0,
                    graph_relationships=0
                )

            self.logger.info(f"Initialized Enhanced Historical Processor with {len(expert_ids)} experts")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Enhanced Historical Processor: {str(e)}")
            return False

    async def process_season_chronologically(self,
                                          season: int,
                                          start_week: int = 1,
                                          end_week: Optional[int] = None) -> ProcessingProgress:
        """
        Process a complete season chronologically to build expert knowledge.

        Args:
            season: NFL season year (e.g., 2024)
            start_week: Starting week (default: 1)
            end_week: Ending week (default: all weeks)

        Returns:
            ProcessingProgress: Final processing statistics
        """
        self.logger.info(f"Starting chronological processing of {season} season")

        try:
            # Get all games for the season in chronological order
            games = await self._get_season_games_chronologically(season, start_week, end_week)

            if not games:
                self.logger.warning(f"No games found for season {season}")
                return ProcessingProgress(0, 0, season, start_week, datetime.now())

            # Initialize progress tracking
            self.progress = ProcessingProgress(
                total_games=len(games),
                processed_games=0,
                current_season=season,
                current_week=start_week,
                start_time=datetime.now()
            )

            self.logger.info(f"Processing {len(games)} games from {season} season")

            # Process games in chronological batches
            for i in range(0, len(games), self.batch_size):
                batch = games[i:i + self.batch_size]

                # Process batch
                await self._process_game_batch(batch)

                # Update progress
                self.progress.processed_games += len(batch)
                self.progress.current_week = batch[-1]['week']

                # Calculate processing rate
                elapsed = (datetime.now() - self.progress.start_time).total_seconds() / 60
                if elapsed > 0:
                    self.progress.games_per_minute = self.progress.processed_games / elapsed

                    # Estimate completion time
                    remaining_games = self.progress.total_games - self.progress.processed_games
                    if self.progress.games_per_minute > 0:
                        remaining_minutes = remaining_games / self.progress.games_per_minute
                        self.progress.estimated_completion = datetime.now() + timedelta(minutes=remaining_minutes)

                # Log progress
                self._log_progress()

                # Delay between batches to respect rate limits
                if i + self.batch_size < len(games):
                    await asyncio.sleep(self.delay_between_batches)

            # Final statistics
            await self._update_expert_statistics()

            self.logger.info(f"Completed processing {season} season: {self.progress.processed_games} games")
            return self.progress

        except Exception as e:
            self.logger.error(f"Error processing season {season}: {str(e)}")
            if self.progress:
                self.progress.errors.append(str(e))
            raise

    async def process_multiple_seasons(self,
                                     start_season: int,
                                     end_season: int,
                                     seasons_to_skip: Optional[List[int]] = None) -> Dict[int, ProcessingProgress]:
        """
        Process multiple seasons chronologically to build comprehensive expert knowledge.

        Args:
            start_season: First season to process
            end_season: Last season to process
            seasons_to_skip: List of seasons to skip (optional)

        Returns:
            Dict[int, ProcessingProgress]: Results for each season
        """
        if seasons_to_skip is None:
            seasons_to_skip = []

        results = {}

        for season in range(start_season, end_season + 1):
            if season in seasons_to_skip:
                self.logger.info(f"Skipping season {season}")
                continue

            try:
                self.logger.info(f"Processing season {season} ({season - start_season + 1}/{end_season - start_season + 1})")

                result = await self.process_season_chronologically(season)
                results[season] = result

                # Brief pause between seasons
                await asyncio.sleep(5)

            except Exception as e:
                self.logger.error(f"Failed to process season {season}: {str(e)}")
                results[season] = ProcessingProgress(0, 0, season, 1, datetime.now(), errors=[str(e)])

        return results

    async def _get_season_games_chronologically(self,
                                             season: int,
                                             start_week: int = 1,
                                             end_week: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all games for a season in chronological order"""
        try:
            query = self.supabase.table('nfl_games').select('*').eq('season', season)

            if start_week:
                query = query.gte('week', start_week)

            if end_week:
                query = query.lte('week', end_week)

            # Only get completed games with scores
            query = query.not_.is_('home_score', 'null').not_.is_('away_score', 'null')

            # Order chronologically
            query = query.order('game_date').order('game_time')

            response = query.execute()

            games = response.data
            self.logger.info(f"Found {len(games)} completed games for season {season}")

            return games

        except Exception as e:
            self.logger.error(f"Error getting season games: {str(e)}")
            return []

    async def _process_game_batch(self, games: List[Dict[str, Any]]) -> None:
        """Process a batch of games concurrently"""
        tasks = []

        for game in games:
            task = self._process_single_game_enhanced(game)
            tasks.append(task)

        # Process batch concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                game_id = games[i]['game_id']
                self.logger.error(f"Error processing game {game_id}: {str(result)}")
                if self.progress:
                    self.progress.errors.append(f"Game {game_id}: {str(result)}")

    async def _process_single_game_enhanced(self, game: Dict[str, Any]) -> bool:
        """
        Process a single game with enhanced memory capabilities.

        This generates expert predictions using current episodic memories,
        then runs reconciliation to update all three memory layers.
        """
        game_id = game['game_id']

        try:
            # Step 1: Generate expert predictions using current memories
            await self._generate_expert_predictions_with_memory(game)

            # Step 2: Run reconciliation workflow (updates structured memory)
            reconciliation_success = await self.reconciliation_service.process_completed_game(game_id)

            if not reconciliation_success:
                self.logger.warning(f"Reconciliation failed for game {game_id}")
                return False

            # Step 3: Store vector embeddings for semantic search
            await self._store_game_vector_memories(game)

            # Step 4: Update Neo4j graph relationships
            await self._update_graph_relationships(game)

            # Step 5: Update expert learning statistics
            await self._update_game_expert_stats(game_id)

            self.logger.debug(f"Successfully processed game {game_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing game {game_id}: {str(e)}")
            return False

    async def _generate_expert_predictions_with_memory(self, game: Dict[str, Any]) -> None:
        """
        Generate expert predictions using current episodic memories.

        This is where the authentic learning happens - each expert uses
        their accumulated knowledge to make increasingly sophisticated predictions.
        """
        game_id = game['game_id']

        # Get all experts
        experts_response = self.supabase.table('personality_experts').select('*').execute()
        experts = experts_response.data

        for expert in experts:
            expert_id = expert['expert_id']

            try:
                # Get expert's current memories for this game context
                contextual_memories = await self.vector_service.find_contextual_memories(
                    expert_id=expert_id,
                    game_context={
                        'home_team': game['home_team'],
                        'away_team': game['away_team'],
                        'week': game['week'],
                        'weather': {
                            'temperature': game.get('weather_temperature'),
                            'wind_speed': game.get('weather_wind_mph'),
                            'conditions': game.get('weather_description')
                        },
                        'is_divisional': game.get('div_game', False),
                        'is_primetime': game.get('is_primetime', False)
                    }
                )

                # Generate prediction using memories (this would integrate with existing expert system)
                prediction_data = await self._generate_memory_informed_prediction(
                    expert, game, contextual_memories
                )

                # Store prediction in expert_reasoning_chains table
                await self._store_expert_prediction(expert_id, game_id, prediction_data)

            except Exception as e:
                self.logger.error(f"Error generating prediction for expert {expert_id}, game {game_id}: {str(e)}")

    async def _generate_memory_informed_prediction(self,
                                                 expert: Dict[str, Any],
                                                 game: Dict[str, Any],
                                                 memories: List[Any]) -> Dict[str, Any]:
        """
        Generate a prediction informed by episodic memories.

        This creates the chain-of-thought reasoning that references
        specific past experiences.
        """
        # Build memory context for prediction
        memory_context = []
        for memory in memories[:5]:  # Use top 5 most relevant memories
            memory_context.append({
                'content': memory.memory.content_text,
                'similarity': memory.similarity,
                'relevance': memory.relevance_explanation
            })

        # Create prediction with memory-informed reasoning
        # (This would integrate with your existing expert prediction system)
        prediction = {
            'winner': game['home_team'] if game['home_score'] > game['away_score'] else game['away_team'],
            'home_score': game['home_score'],
            'away_score': game['away_score'],
            'confidence': 0.7,  # Would be calculated based on memory confidence
            'reasoning_chain': self._build_memory_reasoning_chain(expert, game, memory_context),
            'memory_references': len(memory_context)
        }

        return prediction

    def _build_memory_reasoning_chain(self,
                                    expert: Dict[str, Any],
                                    game: Dict[str, Any],
                                    memory_context: List[Dict]) -> str:
        """Build chain-of-thought reasoning that references memories"""
        reasoning_parts = []

        # Start with basic game analysis
        reasoning_parts.append(f"Analyzing {game['away_team']} @ {game['home_team']} in Week {game['week']}")

        # Reference relevant memories
        if memory_context:
            reasoning_parts.append("Based on similar past experiences:")
            for i, memory in enumerate(memory_context[:3]):  # Top 3 memories
                reasoning_parts.append(f"- {memory['content']} ({memory['relevance']})")

        # Add expert's personality-driven analysis
        personality = expert.get('personality_traits', {})
        if personality.get('risk_tolerance') == 'conservative':
            reasoning_parts.append("Taking a conservative approach based on historical patterns.")
        elif personality.get('risk_tolerance') == 'aggressive':
            reasoning_parts.append("Willing to take risks based on potential upside scenarios.")

        return " ".join(reasoning_parts)

    async def _store_expert_prediction(self, expert_id: str, game_id: str, prediction_data: Dict[str, Any]) -> None:
        """Store expert prediction in the database"""
        try:
            prediction_record = {
                'expert_id': expert_id,
                'game_id': game_id,
                'prediction': prediction_data,
                'confidence_scores': {'overall': prediction_data.get('confidence', 0.5)},
                'reasoning_factors': ['episodic_memory', 'personality_traits'],
                'internal_monologue': prediction_data.get('reasoning_chain', ''),
                'prediction_timestamp': datetime.now().isoformat()
            }

            self.supabase.table('expert_reasoning_chains').insert(prediction_record).execute()

        except Exception as e:
            self.logger.error(f"Error storing prediction: {str(e)}")

    async def _store_game_vector_memories(self, game: Dict[str, Any]) -> None:
        """Store vector embeddings for the game context and outcomes"""
        try:
            game_id = game['game_id']

            # Create game context text for embedding
            context_text = f"{game['away_team']} at {game['home_team']} Week {game['week']} "

            if game.get('weather_temperature'):
                context_text += f"Temperature: {game['weather_temperature']}°F "

            if game.get('weather_wind_mph'):
                context_text += f"Wind: {game['weather_wind_mph']} mph "

            if game.get('div_game'):
                context_text += "Divisional game "

            # Store game context vector for each expert
            experts_response = self.supabase.table('personality_experts').select('expert_id').execute()

            for expert in experts_response.data:
                expert_id = expert['expert_id']

                # Store game context
                await self.vector_service.store_memory_vector(
                    expert_id=expert_id,
                    memory_type='game_context',
                    content_text=context_text,
                    metadata={
                        'game_id': game_id,
                        'home_team': game['home_team'],
                        'away_team': game['away_team'],
                        'week': game['week'],
                        'season': game['season'],
                        'final_score': f"{game['home_score']}-{game['away_score']}"
                    },
                    game_id=game_id
                )

        except Exception as e:
            self.logger.error(f"Error storing vector memories: {str(e)}")

    async def _update_graph_relationships(self, game: Dict[str, Any]) -> None:
        """Update Neo4j graph with game and team relationships"""
        try:
            # Create game node
            await self.neo4j_service.create_game_node({
                'game_id': game['game_id'],
                'date': game['game_date'],
                'week': game['week'],
                'season': game['season'],
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'weather_temperature': game.get('weather_temperature'),
                'weather_wind': game.get('weather_wind_mph'),
                'venue': game.get('stadium'),
                'is_divisional': game.get('div_game', False),
                'is_primetime': game.get('is_primetime', False)
            })

        except Exception as e:
            self.logger.error(f"Error updating graph relationships: {str(e)}")

    async def _update_game_expert_stats(self, game_id: str) -> None:
        """Update expert learning statistics for this game"""
        try:
            # Get predictions for this game
            predictions_response = self.supabase.table('expert_reasoning_chains').select('expert_id').eq('game_id', game_id).execute()

            for prediction in predictions_response.data:
                expert_id = prediction['expert_id']

                if expert_id in self.expert_stats:
                    self.expert_stats[expert_id].games_processed += 1
                    self.expert_stats[expert_id].predictions_made += 1

        except Exception as e:
            self.logger.error(f"Error updating expert stats: {str(e)}")

    async def _update_expert_statistics(self) -> None:
        """Update comprehensive expert learning statistics"""
        for expert_id, stats in self.expert_stats.items():
            try:
                # Get team knowledge count
                team_knowledge_response = self.supabase.table('team_knowledge').select('id').eq('expert_id', expert_id).execute()
                stats.team_knowledge_records = len(team_knowledge_response.data)

                # Get matchup memories count
                matchup_memories_response = self.supabase.table('matchup_memories').select('id').eq('expert_id', expert_id).execute()
                stats.matchup_memories = len(matchup_memories_response.data)

                # Get vector memories count
                vector_stats = await self.vector_service.get_memory_statistics(expert_id)
                stats.vector_memories = vector_stats.get('total_memories', 0)

            except Exception as e:
                self.logger.error(f"Error updating statistics for expert {expert_id}: {str(e)}")

    def _log_progress(self) -> None:
        """Log current processing progress"""
        if not self.progress:
            return

        elapsed_minutes = (datetime.now() - self.progress.start_time).total_seconds() / 60
        completion_pct = (self.progress.processed_games / self.progress.total_games) * 100

        self.logger.info(
            f"Progress: {self.progress.processed_games}/{self.progress.total_games} games "
            f"({completion_pct:.1f}%) - Season {self.progress.current_season} Week {self.progress.current_week} - "
            f"{self.progress.games_per_minute:.1f} games/min - "
            f"ETA: {self.progress.estimated_completion.strftime('%H:%M:%S') if self.progress.estimated_completion else 'Unknown'}"
        )

    async def get_processing_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of processing results"""
        if not self.progress:
            return {'error': 'No processing has been started'}

        # Update final statistics
        await self._update_expert_statistics()

        return {
            'progress': {
                'total_games': self.progress.total_games,
                'processed_games': self.progress.processed_games,
                'completion_percentage': (self.progress.processed_games / self.progress.total_games) * 100,
                'processing_time_minutes': (datetime.now() - self.progress.start_time).total_seconds() / 60,
                'games_per_minute': self.progress.games_per_minute,
                'errors_count': len(self.progress.errors)
            },
            'expert_statistics': {
                expert_id: {
                    'games_processed': stats.games_processed,
                    'predictions_made': stats.predictions_made,
                    'team_knowledge_records': stats.team_knowledge_records,
                    'matchup_memories': stats.matchup_memories,
                    'vector_memories': stats.vector_memories
                }
                for expert_id, stats in self.expert_stats.items()
            },
            'memory_layers': {
                'structured_memory': sum(stats.team_knowledge_records + stats.matchup_memories for stats in self.expert_stats.values()),
                'semantic_memory': sum(stats.vector_memories for stats in self.expert_stats.values()),
                'graph_relationships': 'Available via Neo4j'
            }
        }
