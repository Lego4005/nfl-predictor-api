"""
Reasoning-Enhanced Vector Memory Service

This enhanced version includes expert reasoning chains and learning reflections
in the embeddings for more sophisticated pattern recognition and learning.
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
class ReasoningMemory:
    """Memory with reasoning chains and learning reflections"""
    id: str
    expert_id: str
    memory_type: str

    # Core game identifiers
    game_id: Optional[str]
    home_team: str
    away_team: str
    week: int
    season: int

    # Enhanced content with reasoning
    reasoning_content: str       # Pre-game reasoning chain
    outcome_analysis: str        # Post-game learning reflection
    contextual_factors: str      # Environmental factors
    market_dynamics: str         # Betting dynamics

    # Structured metadata
    metadata: Dict[str, Any]

    # Vector embeddings
    reasoning_embedding: List[float]      # Reasoning chain similarity
    learning_embedding: List[float]       # Learning reflection similarity
    contextual_embedding: List[float]     # Situational similarity
    market_embedding: List[float]         # Market similarity

    similarity_score: Optional[float] = None


class ReasoningEnhancedVectorMemoryService:
    """
    Vector memory service that captures expert reasoning chains and learning reflections
    for sophisticated pattern recognition and belief revision.
    """

    def __init__(self, supabase_client: SupabaseClient, openai_api_key: Optional[str] = None):
        self.supabase = supabase_client
        self.logger = logging.getLogger(__name__)

        # Initialize OpenAI for embeddings
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimensions = 1536

    async def store_reasoning_memory(
        self,
        expert_id: str,
        memory_type: str,
        game_data: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]] = None,
        outcome_data: Optional[Dict[str, Any]] = None,
        reasoning_chain: Optional[str] = None,
        learning_reflection: Optional[str] = None
    ) -> str:
        """
        Store a memory with expert reasoning chains and learning reflections.

        Args:
            expert_id: ID of the expert
            memory_type: Type of memory ('prediction_reasoning', 'outcome_learning', 'pattern_discovery')
            game_data: Rich game data
            prediction_data: Expert's predictions and confidence
            outcome_data: Actual game outcomes
            reasoning_chain: Expert's pre-game reasoning process
            learning_reflection: Expert's post-game learning analysis

        Returns:
            str: ID of the stored memory
        """
        try:
            # Create rich reasoning content
            reasoning_content = self._create_reasoning_content(
                game_data, prediction_data, reasoning_chain
            )

            outcome_analysis = self._create_outcome_analysis(
                game_data, prediction_data, outcome_data, learning_reflection
            )

            contextual_factors = self._create_contextual_content(game_data)
            market_dynamics = self._create_market_content(game_data, prediction_data)

            # Generate embeddings for each dimension
            reasoning_embedding = await self._generate_embedding(reasoning_content)
            learning_embedding = await self._generate_embedding(outcome_analysis)
            contextual_embedding = await self._generate_embedding(contextual_factors)
            market_embedding = await self._generate_embedding(market_dynamics)

            # Create structured metadata
            metadata = self._create_reasoning_metadata(
                game_data, prediction_data, outcome_data, reasoning_chain, learning_reflection
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
                'reasoning_content': reasoning_content,
                'outcome_analysis': outcome_analysis,
                'contextual_factors': contextual_factors,
                'market_dynamics': market_dynamics,
                'reasoning_embedding': reasoning_embedding,
                'learning_embedding': learning_embedding,
                'contextual_embedding': contextual_embedding,
                'market_embedding': market_embedding,
                'metadata': metadata
            }

            response = self.supabase.table('reasoning_memory_vectors').insert(memory_data).execute()
            memory_id = response.data[0]['id']

            self.logger.info(f"Stored reasoning memory {memory_id} for expert {expert_id}")
            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing reasoning memory: {str(e)}")
            raise

    def _create_reasoning_content(
        self,
        game_data: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]],
        reasoning_chain: Optional[str]
    ) -> str:
        """Create rich reasoning chain content for embedding"""

        reasoning_parts = []

        # Game setup
        home_team = game_data.get('home_team', 'Unknown')
        away_team = game_data.get('away_team', 'Unknown')
        reasoning_parts.append(f"PREDICTION SCENARIO: {away_team} at {home_team}")

        if prediction_data:
            predicted_winner = prediction_data.get('predicted_winner')
            predicted_margin = prediction_data.get('predicted_margin', 0)
            confidence = prediction_data.get('confidence', 0.5)

            reasoning_parts.append(f"MY PREDICTION: {predicted_winner} wins by {predicted_margin} points (confidence: {confidence:.1%})")

            # Include expert's explicit reasoning chain
            if reasoning_chain:
                reasoning_parts.append(f"MY REASONING: {reasoning_chain}")
            else:
                # Generate reasoning from available data and prediction factors
                reasoning_factors = []

                # Weather-based reasoning
                weather = game_data.get('weather', {})
                if weather:
                    temp = weather.get('temperature', 70)
                    wind = weather.get('wind_speed', 0)
                    conditions = weather.get('conditions', 'clear')

                    if temp < 32 and wind > 15:
                        reasoning_factors.append(f"Extreme weather conditions ({temp}°F, {wind}mph winds, {conditions}) will heavily favor ground-based offenses and hurt passing accuracy - this should benefit the team with stronger running attack")
                    elif temp < 45:
                        reasoning_factors.append(f"Cold weather ({temp}°F) typically reduces offensive efficiency, especially for warm-weather teams")

                    if wind > 20:
                        reasoning_factors.append(f"High winds ({wind}mph) will severely impact passing games and field goal accuracy - expect lower-scoring game")
                    elif wind > 15:
                        reasoning_factors.append(f"Moderate winds ({wind}mph) will affect deep passing and kicking games")

                # Injury-based reasoning
                injuries = game_data.get('injuries', {})
                if injuries:
                    home_injuries = injuries.get('home', [])
                    away_injuries = injuries.get('away', [])

                    for injury in away_injuries:
                        if injury.get('severity') == 'out' or injury.get('probability_play', 1) < 0.3:
                            pos = injury.get('position', 'player')
                            reasoning_factors.append(f"Away team missing their key {pos} significantly weakens their {self._get_position_impact(pos)} - this creates a major advantage for the home team")
                        elif injury.get('probability_play', 1) < 0.7:
                            pos = injury.get('position', 'player')
                            reasoning_factors.append(f"Away team's {pos} is questionable which creates uncertainty in their game plan")

                    for injury in home_injuries:
                        if injury.get('severity') == 'out' or injury.get('probability_play', 1) < 0.3:
                            pos = injury.get('position', 'player')
                            reasoning_factors.append(f"Home team missing their {pos} is a significant weakness that the away team should exploit")

                # Market-based reasoning
                line_movement = game_data.get('line_movement', {})
                if line_movement:
                    opening_line = line_movement.get('opening_line', 0)
                    current_line = line_movement.get('current_line', 0)
                    public_pct = line_movement.get('public_percentage', 50)

                    line_move = current_line - opening_line
                    if abs(line_move) >= 2:
                        if line_move > 0:
                            reasoning_factors.append(f"Sharp line movement from {opening_line} to {current_line} indicates professional money backing the home team despite {public_pct}% of public on away team - this suggests value on home side")
                        else:
                            reasoning_factors.append(f"Line movement from {opening_line} to {current_line} shows smart money on away team, creating contrarian value")

                    if public_pct >= 75:
                        reasoning_factors.append(f"Heavy public betting ({public_pct}%) creates potential contrarian value on the other side")
                    elif public_pct <= 25:
                        reasoning_factors.append(f"Public heavily against this team ({public_pct}%) but line hasn't moved much - suggests sharp money agrees with public")

                # Team performance reasoning
                team_stats = game_data.get('team_stats', {})
                if team_stats:
                    home_stats = team_stats.get('home', {})
                    away_stats = team_stats.get('away', {})

                    home_off = home_stats.get('offensive_yards_per_game', 0)
                    away_off = away_stats.get('offensive_yards_per_game', 0)

                    if home_off > away_off + 75:
                        reasoning_factors.append(f"Home team's significant offensive advantage ({home_off} vs {away_off} yards/game) combined with home field should control game flow")
                    elif away_off > home_off + 75:
                        reasoning_factors.append(f"Away team's superior offensive production ({away_off} vs {home_off} yards/game) can overcome road disadvantage")
                    else:
                        reasoning_factors.append(f"Teams are evenly matched offensively ({home_off} vs {away_off} yards/game) so other factors become decisive")

                if reasoning_factors:
                    reasoning_parts.append("MY REASONING: " + " | ".join(reasoning_factors))

        return " | ".join(reasoning_parts)

    def _create_outcome_analysis(
        self,
        game_data: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]],
        outcome_data: Optional[Dict[str, Any]],
        learning_reflection: Optional[str]
    ) -> str:
        """Create post-game learning reflection content"""

        if not (prediction_data and outcome_data):
            return "No outcome analysis available - prediction only"

        analysis_parts = []

        # Outcome summary
        predicted_winner = prediction_data.get('predicted_winner')
        actual_winner = outcome_data.get('winner')
        predicted_margin = prediction_data.get('predicted_margin', 0)
        actual_margin = outcome_data.get('margin', 0)
        home_score = outcome_data.get('home_score', 0)
        away_score = outcome_data.get('away_score', 0)

        analysis_parts.append(f"ACTUAL OUTCOME: {actual_winner} won {home_score}-{away_score} (margin: {actual_margin})")

        # Prediction accuracy assessment
        winner_correct = predicted_winner == actual_winner
        margin_error = abs(predicted_margin - actual_margin)

        if winner_correct:
            if margin_error <= 3:
                analysis_parts.append(f"PREDICTION ACCURACY: EXCELLENT - Correct winner and precise margin (predicted {predicted_margin}, actual {actual_margin})")
            elif margin_error <= 7:
                analysis_parts.append(f"PREDICTION ACCURACY: GOOD - Correct winner but margin off by {margin_error} points")
            else:
                analysis_parts.append(f"PREDICTION ACCURACY: MIXED - Correct winner but significant margin error of {margin_error} points")
        else:
            analysis_parts.append(f"PREDICTION ACCURACY: INCORRECT - Predicted {predicted_winner} but {actual_winner} won by {actual_margin}")

        # Learning analysis
        if learning_reflection:
            analysis_parts.append(f"MY LEARNING: {learning_reflection}")
        else:
            # Generate learning insights based on prediction vs outcome
            learning_insights = []

            if winner_correct and margin_error <= 3:
                learning_insights.append("My reasoning process was validated - the key factors I identified played out as expected")
            elif winner_correct:
                learning_insights.append(f"My winner logic was sound but I {('underestimated' if predicted_margin < actual_margin else 'overestimated')} the margin by {margin_error} points")
            else:
                learning_insights.append("My reasoning had fundamental flaws - need to reassess how I weighted the key factors")

            # Factor-specific learning
            key_factors = prediction_data.get('key_factors', [])

            if 'weather_advantage' in key_factors:
                weather = game_data.get('weather', {})
                if weather.get('wind_speed', 0) > 15:
                    if winner_correct:
                        learning_insights.append("Weather impact analysis was crucial to getting this prediction right")
                    else:
                        learning_insights.append("Weather conditions didn't play out as I expected - need to refine weather impact models")

            if 'injury_impact' in key_factors:
                if winner_correct:
                    learning_insights.append("Injury analysis was a key differentiator in this prediction")
                else:
                    learning_insights.append("Overestimated or underestimated injury impact - need better injury severity assessment")

            if 'contrarian_value' in key_factors:
                line_movement = game_data.get('line_movement', {})
                public_pct = line_movement.get('public_percentage', 50)
                if public_pct >= 75:
                    if winner_correct:
                        learning_insights.append("Contrarian approach paid off - public was wrong as expected")
                    else:
                        learning_insights.append("Public was actually right this time - need to be more selective with contrarian plays")

            if learning_insights:
                analysis_parts.append("MY LEARNING: " + " | ".join(learning_insights))

        return " | ".join(analysis_parts)

    def _get_position_impact(self, position: str) -> str:
        """Get the impact description for a position"""
        position_impacts = {
            'QB': 'passing attack and offensive rhythm',
            'RB': 'running game and red zone efficiency',
            'WR': 'passing game and deep threat capability',
            'TE': 'receiving options and blocking schemes',
            'OL': 'pass protection and run blocking',
            'DE': 'pass rush and run defense',
            'LB': 'run defense and coverage',
            'CB': 'pass coverage and defensive backfield',
            'S': 'deep coverage and run support',
            'K': 'field goal and extra point reliability'
        }
        return position_impacts.get(position, 'overall team performance')

    def _create_contextual_content(self, game_data: Dict[str, Any]) -> str:
        """Create contextual factors content (same as before)"""
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

        return " | ".join(context_parts) if context_parts else "Standard game conditions"

    def _create_market_content(self, game_data: Dict[str, Any], prediction_data: Optional[Dict[str, Any]]) -> str:
        """Create market dynamics content (same as before)"""
        market_parts = []

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

        if prediction_data:
            confidence = prediction_data.get('confidence', 0.5)
            if confidence >= 0.8:
                market_parts.append("High confidence prediction")
            elif confidence <= 0.4:
                market_parts.append("Low confidence prediction")
            else:
                market_parts.append("Moderate confidence prediction")

        return " | ".join(market_parts) if market_parts else "Standard market conditions"

    def _create_reasoning_metadata(
        self,
        game_data: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]],
        outcome_data: Optional[Dict[str, Any]],
        reasoning_chain: Optional[str],
        learning_reflection: Optional[str]
    ) -> Dict[str, Any]:
        """Create enhanced metadata including reasoning analysis"""

        metadata = {
            'game_context': {},
            'prediction_context': {},
            'outcome_context': {},
            'reasoning_analysis': {},
            'learning_tags': []
        }

        # Game context (same as before)
        weather = game_data.get('weather', {})
        if weather:
            metadata['game_context']['temperature'] = weather.get('temperature')
            metadata['game_context']['wind_speed'] = weather.get('wind_speed')
            metadata['game_context']['weather_conditions'] = weather.get('conditions')

        # Prediction context with reasoning analysis
        if prediction_data:
            metadata['prediction_context'] = prediction_data.copy()

            # Analyze reasoning chain
            if reasoning_chain:
                metadata['reasoning_analysis']['has_explicit_reasoning'] = True
                metadata['reasoning_analysis']['reasoning_length'] = len(reasoning_chain)

                # Identify reasoning types
                reasoning_types = []
                if any(word in reasoning_chain.lower() for word in ['weather', 'wind', 'cold', 'hot']):
                    reasoning_types.append('weather_based')
                if any(word in reasoning_chain.lower() for word in ['injury', 'injured', 'out', 'questionable']):
                    reasoning_types.append('injury_based')
                if any(word in reasoning_chain.lower() for word in ['line', 'public', 'sharp', 'betting']):
                    reasoning_types.append('market_based')
                if any(word in reasoning_chain.lower() for word in ['yards', 'offense', 'defense', 'stats']):
                    reasoning_types.append('statistical_based')

                metadata['reasoning_analysis']['reasoning_types'] = reasoning_types

        # Outcome context with learning analysis
        if outcome_data:
            metadata['outcome_context'] = outcome_data.copy()

            if prediction_data and outcome_data:
                predicted_winner = prediction_data.get('predicted_winner')
                actual_winner = outcome_data.get('winner')
                predicted_margin = prediction_data.get('predicted_margin', 0)
                actual_margin = outcome_data.get('margin', 0)

                metadata['outcome_context']['winner_correct'] = predicted_winner == actual_winner
                metadata['outcome_context']['margin_error'] = abs(predicted_margin - actual_margin)

                # Learning quality assessment
                if learning_reflection:
                    metadata['reasoning_analysis']['has_learning_reflection'] = True
                    metadata['reasoning_analysis']['reflection_length'] = len(learning_reflection)

        # Learning tags for filtering
        tags = []

        if prediction_data and outcome_data:
            if metadata['outcome_context'].get('winner_correct'):
                if metadata['outcome_context'].get('margin_error', 10) <= 3:
                    tags.append('excellent_prediction')
                else:
                    tags.append('correct_winner')
            else:
                tags.append('incorrect_prediction')

        if reasoning_chain:
            tags.append('explicit_reasoning')

        if learning_reflection:
            tags.append('learning_reflection')

        metadata['learning_tags'] = tags

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

    async def find_similar_reasoning_memories(
        self,
        expert_id: str,
        query_game_data: Dict[str, Any],
        query_reasoning: Optional[str] = None,
        embedding_type: str = 'reasoning',  # 'reasoning', 'learning', 'contextual', 'market'
        similarity_threshold: float = 0.6,
        max_results: int = 7
    ) -> List[ReasoningMemory]:
        """
        Find memories with similar reasoning patterns or learning outcomes.

        Args:
            expert_id: ID of the expert
            query_game_data: Current game data
            query_reasoning: Expert's current reasoning (optional)
            embedding_type: Which dimension to search ('reasoning', 'learning', 'contextual', 'market')
            similarity_threshold: Minimum similarity score
            max_results: Maximum results to return

        Returns:
            List[ReasoningMemory]: Similar memories with reasoning context
        """
        try:
            # Create query content based on embedding type
            if embedding_type == 'reasoning':
                if query_reasoning:
                    query_content = f"PREDICTION REASONING: {query_reasoning}"
                else:
                    query_content = self._create_reasoning_content(query_game_data, None, None)
            elif embedding_type == 'learning':
                query_content = "LEARNING ANALYSIS: Similar outcome patterns and learning insights"
            elif embedding_type == 'contextual':
                query_content = self._create_contextual_content(query_game_data)
            elif embedding_type == 'market':
                query_content = self._create_market_content(query_game_data, None)
            else:
                raise ValueError(f"Unknown embedding type: {embedding_type}")

            # Generate query embedding
            query_embedding = await self._generate_embedding(query_content)

            # Search database
            embedding_column = f"{embedding_type}_embedding"

            response = self.supabase.rpc(f'match_reasoning_memory_vectors_{embedding_type}', {
                'query_embedding': query_embedding,
                'filter_expert_id': expert_id,
                'match_threshold': similarity_threshold,
                'match_count': max_results
            }).execute()

            # Convert to ReasoningMemory objects
            results = []
            for memory_data in response.data or []:
                reasoning_memory = ReasoningMemory(
                    id=memory_data['id'],
                    expert_id=memory_data['expert_id'],
                    memory_type=memory_data['memory_type'],
                    game_id=memory_data['game_id'],
                    home_team=memory_data['home_team'],
                    away_team=memory_data['away_team'],
                    week=memory_data['week'],
                    season=memory_data['season'],
                    reasoning_content=memory_data['reasoning_content'],
                    outcome_analysis=memory_data['outcome_analysis'],
                    contextual_factors=memory_data['contextual_factors'],
                    market_dynamics=memory_data['market_dynamics'],
                    reasoning_embedding=[],
                    learning_embedding=[],
                    contextual_embedding=[],
                    market_embedding=[],
                    metadata=memory_data['metadata'],
                    similarity_score=memory_data['similarity']
                )
                results.append(reasoning_memory)

            self.logger.info(f"Found {len(results)} similar {embedding_type} memories for expert {expert_id}")
            return results

        except Exception as e:
            self.logger.error(f"Error finding similar reasoning memories: {str(e)}")
            return []
