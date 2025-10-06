"""
Enhanced Vector Memory Service for NFL Expert Learning

This service creates rich, multi-dimensional embeddings that capture the analytical
diexperts care about for finding truly similar game situations.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
import os
from dataclasses import dataclass

from supabase import Client as SupabaseClient


@dataclass
class AnalyticalMemory:
    """Rich analytical memory with multiple embedding dimensions"""
    id: str
    expert_id: str
    memory_type: str  # 'game_context', 'prediction_outcome', 'pattern_discovery', 'belief_revision'

    # Core game identifiers
    game_id: Optional[str]
    home_team: str
    away_team: str
    week: int
    season: int

    # Analytical content for embedding
    analytical_content: str  # Rich analytical description
    contextual_factors: str  # Environmental and situational factors
    market_dynamics: str     # Betting and market information

    # Structured metadata for filtering
    metadata: Dict[str, Any]

    # Vector embeddings (multiple types)
    analytical_embedding: List[float]      # Main analytical similarity
    contextual_embedding: List[float]      # Situational similarity
    market_embedding: List[float]          # Market/betting similarity

    similarity_score: Optional[float] = None


class EnhancedVectorMemoryService:
    """
    Enhanced vector memory service that creates rich, multi-dimensional embeddings
    for expert learning and pattern recognition.
    """

    def __init__(self, supabase_client: SupabaseClient, openai_api_key: Optional[str] = None):
        self.supabase = supabase_client
        self.logger = logging.getLogger(__name__)

        # Initialize OpenAI for embeddings
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimensions = 1536

    async def store_analytical_memory(
        self,
        expert_id: str,
        memory_type: str,
        game_data: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]] = None,
        outcome_data: Optional[Dict[str, Any]] = None,
        expert_insights: Optional[str] = None
    ) -> str:
        """
        Store a rich analytical memory with multiple embedding dimensions.

        Args:
            expert_id: ID of the expert creating the memory
            memory_type: Type of memory being stored
            game_data: Rich game data (UniversalGameData format)
            prediction_data: Expert's predictions (if applicable)
            outcome_data: Actual game outcomes (if applicable)
            expert_insights: Expert's analytical insights

        Returns:
            str: ID of the stored memory
        """
        try:
            # Create rich analytical content for embeddings
            analytical_content = self._create_analytical_content(
                game_data, prediction_data, outcome_data, expert_insights
            )

            contextual_factors = self._create_contextual_content(game_data)
            market_dynamics = self._create_market_content(game_data, prediction_data)

            # Generate multiple embeddings
            analytical_embedding = await self._generate_embedding(analytical_content)
            contextual_embedding = await self._generate_embedding(contextual_factors)
            market_embedding = await self._generate_embedding(market_dynamics)

            # Create structured metadata
            metadata = self._create_structured_metadata(
                game_data, prediction_data, outcome_data, expert_insights
            )

            # Store in database
            memory_data = {
                'expert_id': expert_id,
                'memory_type': memory_type,
                'game_id': game_data.get('game_id'),
                'home_team': game_data.get('home_team'),
                'away_team': game_data.get('away_team'),
                'week': game_data.get('week'),
                'season': game_data.get('season'),
                'analytical_content': analytical_content,
                'contextual_factors': contextual_factors,
                'market_dynamics': market_dynamics,
                'analytical_embedding': analytical_embedding,
                'contextual_embedding': contextual_embedding,
                'market_embedding': market_embedding,
                'metadata': metadata
            }

            response = self.supabase.table('enhanced_memory_vectors').insert(memory_data).execute()
            memory_id = response.data[0]['id']

            self.logger.info(f"Stored enhanced memory {memory_id} for expert {expert_id}")
            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing analytical memory: {str(e)}")
            raise

    def _create_analytical_content(
        self,
        game_data: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]],
        outcome_data: Optional[Dict[str, Any]],
        expert_insights: Optional[str]
    ) -> str:
        """Create rich analytical content for embedding"""

        content_parts = []

        # Team matchup analysis
        home_team = game_data.get('home_team', 'Unknown')
        away_team = game_data.get('away_team', 'Unknown')
        content_parts.append(f"Matchup: {away_team} at {home_team}")

        # Team performance context
        team_stats = game_data.get('team_stats', {})
        if team_stats:
            home_stats = team_stats.get('home', {})
            away_stats = team_stats.get('away', {})

            home_off_yards = home_stats.get('offensive_yards_per_game', 0)
            away_off_yards = away_stats.get('offensive_yards_per_game', 0)

            if home_off_yards and away_off_yards:
                if home_off_yards > away_off_yards + 50:
                    content_parts.append("Home team has significant offensive advantage")
                elif away_off_yards > home_off_yards + 50:
                    content_parts.append("Away team has significant offensive advantage")
                else:
                    content_parts.append("Teams have similar offensive capabilities")

        # Injury impact analysis
        injuries = game_data.get('injuries', {})
        if injuries:
            home_injuries = injuries.get('home', [])
            away_injuries = injuries.get('away', [])

            for injury in home_injuries:
                severity = injury.get('severity', 'unknown')
                position = injury.get('position', 'unknown')
                prob_play = injury.get('probability_play', 0)

                if severity == 'out' or prob_play < 0.3:
                    content_parts.append(f"Home team missing key {position}")
                elif prob_play < 0.7:
                    content_parts.append(f"Home team {position} questionable")

            for injury in away_injuries:
                severity = injury.get('severity', 'unknown')
                position = injury.get('position', 'unknown')
                prob_play = injury.get('probability_play', 0)

                if severity == 'out' or prob_play < 0.3:
                    content_parts.append(f"Away team missing key {position}")
                elif prob_play < 0.7:
                    content_parts.append(f"Away team {position} questionable")

        # Prediction accuracy analysis (if outcome available)
        if prediction_data and outcome_data:
            predicted_winner = prediction_data.get('predicted_winner')
            actual_winner = outcome_data.get('winner')
            predicted_margin = prediction_data.get('predicted_margin', 0)
            actual_margin = outcome_data.get('margin', 0)

            if predicted_winner == actual_winner:
                margin_diff = abs(predicted_margin - actual_margin)
                if margin_diff <= 3:
                    content_parts.append("Accurate prediction with precise margin")
                elif margin_diff <= 7:
                    content_parts.append("Correct winner prediction with reasonable margin")
                else:
                    content_parts.append("Correct winner but significant margin error")
            else:
                content_parts.append("Incorrect winner prediction")

        # Expert insights
        if expert_insights:
            content_parts.append(f"Expert insight: {expert_insights}")

        return " | ".join(content_parts)

    def _create_contextual_content(self, game_data: Dict[str, Any]) -> str:
        """Create contextual factors content for embedding"""

        context_parts = []

        # Weather impact
        weather = game_data.get('weather', {})
        if weather:
            temp = weather.get('temperature', 70)
            wind = weather.get('wind_speed', 0)
            conditions = weather.get('conditions', 'clear')

            if temp < 32:
                context_parts.append("Freezing temperature conditions")
            elif temp < 45:
                context_parts.append("Cold weather game")
            elif temp > 85:
                context_parts.append("Hot weather conditions")

            if wind > 20:
                context_parts.append("High wind conditions affecting passing")
            elif wind > 15:
                context_parts.append("Moderate wind conditions")

            if 'rain' in conditions.lower() or 'storm' in conditions.lower():
                context_parts.append("Wet weather conditions")
            elif 'snow' in conditions.lower():
                context_parts.append("Snow conditions")

        # Game timing context
        week = game_data.get('week', 1)
        if week <= 4:
            context_parts.append("Early season game")
        elif week >= 15:
            context_parts.append("Late season game with playoff implications")
        elif 9 <= week <= 12:
            context_parts.append("Mid-season game")

        # Location context
        location = game_data.get('location', '')
        if any(cold_city in location.lower() for cold_city in ['green bay', 'buffalo', 'chicago', 'cleveland']):
            context_parts.append("Cold weather home venue")
        elif any(dome in location.lower() for dome in ['atlanta', 'detroit', 'minnesota', 'new orleans']):
            context_parts.append("Dome game controlled environment")

        return " | ".join(context_parts) if context_parts else "Standard game conditions"

    def _create_market_content(
        self,
        game_data: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]]
    ) -> str:
        """Create market dynamics content for embedding"""

        market_parts = []

        # Line movement analysis
        line_movement = game_data.get('line_movement', {})
        if line_movement:
            opening_line = line_movement.get('opening_line', 0)
            current_line = line_movement.get('current_line', 0)
            public_percentage = line_movement.get('public_percentage', 50)

            line_move = current_line - opening_line
            if abs(line_move) >= 2:
                if line_move > 0:
                    market_parts.append("Significant line movement toward home team")
                else:
                    market_parts.append("Significant line movement toward away team")

            if public_percentage >= 70:
                market_parts.append("Heavy public betting on favorite")
            elif public_percentage <= 30:
                market_parts.append("Heavy public betting on underdog")
            else:
                market_parts.append("Balanced public betting")

        # Prediction confidence context
        if prediction_data:
            confidence = prediction_data.get('confidence', 0.5)
            if confidence >= 0.8:
                market_parts.append("High confidence prediction")
            elif confidence <= 0.4:
                market_parts.append("Low confidence prediction")
            else:
                market_parts.append("Moderate confidence prediction")

        return " | ".join(market_parts) if market_parts else "Standard market conditions"

    def _create_structured_metadata(
        self,
        game_data: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]],
        outcome_data: Optional[Dict[str, Any]],
        expert_insights: Optional[str]
    ) -> Dict[str, Any]:
        """Create structured metadata for filtering and analysis"""

        metadata = {
            'game_context': {},
            'prediction_context': {},
            'outcome_context': {},
            'analytical_tags': []
        }

        # Game context metadata
        weather = game_data.get('weather', {})
        if weather:
            metadata['game_context']['temperature'] = weather.get('temperature')
            metadata['game_context']['wind_speed'] = weather.get('wind_speed')
            metadata['game_context']['weather_conditions'] = weather.get('conditions')

        injuries = game_data.get('injuries', {})
        if injuries:
            metadata['game_context']['home_injuries'] = len(injuries.get('home', []))
            metadata['game_context']['away_injuries'] = len(injuries.get('away', []))

        line_movement = game_data.get('line_movement', {})
        if line_movement:
            metadata['game_context']['opening_line'] = line_movement.get('opening_line')
            metadata['game_context']['current_line'] = line_movement.get('current_line')
            metadata['game_context']['public_percentage'] = line_movement.get('public_percentage')

        # Prediction context
        if prediction_data:
            metadata['prediction_context'] = prediction_data.copy()

        # Outcome context
        if outcome_data:
            metadata['outcome_context'] = outcome_data.copy()

            # Calculate prediction accuracy if both available
            if prediction_data and outcome_data:
                predicted_winner = prediction_data.get('predicted_winner')
                actual_winner = outcome_data.get('winner')
                metadata['outcome_context']['winner_correct'] = predicted_winner == actual_winner

                predicted_margin = prediction_data.get('predicted_margin', 0)
                actual_margin = outcome_data.get('margin', 0)
                metadata['outcome_context']['margin_error'] = abs(predicted_margin - actual_margin)

        # Analytical tags for easy filtering
        tags = []

        # Weather tags
        if weather:
            temp = weather.get('temperature', 70)
            wind = weather.get('wind_speed', 0)

            if temp < 32:
                tags.append('freezing_weather')
            elif temp < 45:
                tags.append('cold_weather')
            elif temp > 85:
                tags.append('hot_weather')

            if wind > 15:
                tags.append('windy_conditions')

        # Injury tags
        if injuries:
            if injuries.get('home') or injuries.get('away'):
                tags.append('injury_impact')

        # Market tags
        if line_movement:
            public_pct = line_movement.get('public_percentage', 50)
            if public_pct >= 70:
                tags.append('public_favorite')
            elif public_pct <= 30:
                tags.append('contrarian_play')

        # Outcome tags
        if prediction_data and outcome_data:
            if metadata['outcome_context'].get('winner_correct'):
                tags.append('correct_prediction')
            else:
                tags.append('incorrect_prediction')

        metadata['analytical_tags'] = tags

        return metadata

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text using OpenAI"""
        try:
            if not self.openai_api_key:
                self.logger.warning("OpenAI API key not set - returning zero vector")
                return [0.0] * self.embedding_dimensions

            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)

            response = client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            embedding = response.data[0].embedding
            return embedding

        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}")
            return [0.0] * self.embedding_dimensions

    async def find_similar_analytical_memories(
        self,
        expert_id: str,
        query_game_data: Dict[str, Any],
        memory_types: Optional[List[str]] = None,
        similarity_threshold: float = 0.6,
        max_results: int = 7,
        embedding_type: str = 'analytical'  # 'analytical', 'contextual', 'market'
    ) -> List[AnalyticalMemory]:
        """
        Find memories similar to the query game using rich analytical embeddings.

        Args:
            expert_id: ID of the expert searching
            query_game_data: Game data to find similar memories for
            memory_types: Filter by memory types
            similarity_threshold: Minimum similarity score
            max_results: Maximum results to return
            embedding_type: Which embedding dimension to use for similarity

        Returns:
            List[AnalyticalMemory]: Similar memories with rich context
        """
        try:
            # Create query content based on embedding type
            if embedding_type == 'analytical':
                query_content = self._create_analytical_content(query_game_data, None, None, None)
            elif embedding_type == 'contextual':
                query_content = self._create_contextual_content(query_game_data)
            elif embedding_type == 'market':
                query_content = self._create_market_content(query_game_data, None)
            else:
                raise ValueError(f"Unknown embedding type: {embedding_type}")

            # Generate query embedding
            query_embedding = await self._generate_embedding(query_content)

            # Search database using appropriate embedding column
            embedding_column = f"{embedding_type}_embedding"

            # Use RPC function for vector similarity search
            response = self.supabase.rpc(f'match_enhanced_memory_vectors_{embedding_type}', {
                'query_embedding': query_embedding,
                'filter_expert_id': expert_id,
                'filter_memory_types': memory_types,
                'match_threshold': similarity_threshold,
                'match_count': max_results
            }).execute()

            # Convert to AnalyticalMemory objects
            results = []
            for memory_data in response.data or []:
                analytical_memory = AnalyticalMemory(
                    id=memory_data['id'],
                    expert_id=memory_data['expert_id'],
                    memory_type=memory_data['memory_type'],
                    game_id=memory_data['game_id'],
                    home_team=memory_data['home_team'],
                    away_team=memory_data['away_team'],
                    week=memory_data['week'],
                    season=memory_data['season'],
                    analytical_content=memory_data['analytical_content'],
                    contextual_factors=memory_data['contextual_factors'],
                    market_dynamics=memory_data['market_dynamics'],
                    analytical_embedding=[],  # Don't return full embeddings
                    contextual_embedding=[],
                    market_embedding=[],
                    metadata=memory_data['metadata'],
                    similarity_score=memory_data['similarity']
                )
                results.append(analytical_memory)

            self.logger.info(f"Found {len(results)} similar {embedding_type} memories for expert {expert_id}")
            return results

        except Exception as e:
            self.logger.error(f"Error finding similar analytical memories: {str(e)}")
            return []

    async def get_multi_dimensional_memories(
        self,
        expert_id: str,
        query_game_data: Dict[str, Any],
        max_results_per_dimension: int = 3
    ) -> Dict[str, List[AnalyticalMemory]]:
        """
        Get similar memories across all embedding dimensions for comprehensive analysis.

        Returns:
            Dict with keys 'analytical', 'contextual', 'market' containing relevant memories
        """
        results = {}

        for embedding_type in ['analytical', 'contextual', 'market']:
            memories = await self.find_similar_analytical_memories(
                expert_id=expert_id,
                query_game_data=query_game_data,
                max_results=max_results_per_dimension,
                embedding_type=embedding_type
            )
            results[embedding_type] = memories

        return results
