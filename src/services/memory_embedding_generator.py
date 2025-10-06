"""
Memory Embedding Generator for NFL Expert Training Loop

This service generates vector embeddings for game contexts, predictions, and outcomes
specifically for the expert training loop system. Itates with the episodic
memory system and provides semantic similarity search capabilities.
"""

import asyncio
import logging
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from supabase import Client as SupabaseClient
from .local_llm_service import LocalLLMService, get_llm_service


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    embedding: List[float]
    model_name: str
    model_version: str
    dimensions: int
    generation_time_ms: int
    source_text_length: int
    confidence_score: float


@dataclass
class MemoryEmbedding:
    """Complete memory embedding with metadata"""
    memory_id: str
    expert_id: str
    game_context_embedding: Optional[List[float]]
    prediction_embedding: Optional[List[float]]
    outcome_embedding: Optional[List[float]]
    combined_embedding: Optional[List[float]]
    embedding_metadata: Dict[str, Any]


@dataclass
class SimilarityResult:
    """Result of similarity search"""
    memory_id: str
    expert_id: str
    game_id: str
    memory_type: str
    similarity_score: float
    relevance_score: float
    memory_vividness: float
    memory_decay: float
    retrieval_count: int
    created_at: datetime


class MemoryEmbeddingGenerator:
    """
    Generates and manages vector embeddings for expert episodic memories
    in the NFL prediction training loop system.
    """

    def __init__(
        self,
        supabase_client: SupabaseClient,
        llm_service: Optional[LocalLLMService] = None,
        openai_api_key: Optional[str] = None
    ):
        self.supabase = supabase_client
        self.llm_service = llm_service or get_llm_service()
        self.logger = logging.getLogger(__name__)

        # Embedding configuration
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimensions = 1536
        self.model_version = "v1.0"

        # OpenAI fallback for embeddings
        self.openai_api_key = openai_api_key
        if openai_api_key:
            import openai
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
        else:
            self.openai_client = None

        self.logger.info("MemoryEmbeddingGenerator initialized")

    async def generate_memory_embeddings(
        self,
        memory_id: str,
        expert_id: str,
        game_context: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]] = None,
        outcome_data: Optional[Dict[str, Any]] = None,
        expert_reasoning: Optional[str] = None
    ) -> MemoryEmbedding:
        """
        Generate all embedding types for a memory.

        Args:
            memory_id: Unique identifier for the memory
            expert_id: ID of the expert who created the memory
            game_context: Game context data
            prediction_data: Expert's prediction data (optional)
            outcome_data: Actual game outcome data (optional)
            expert_reasoning: Expert's reasoning text (optional)

        Returns:
            MemoryEmbedding: Complete embedding data
        """
        try:
            start_time = time.time()

            # Generate text representations for embedding
            game_context_text = self._create_game_context_text(game_context)
            prediction_text = self._create_prediction_text(prediction_data, expert_reasoning) if prediction_data else None
            outcome_text = self._create_outcome_text(outcome_data, game_context) if outcome_data else None
            combined_text = self._create_combined_text(game_context_text, prediction_text, outcome_text)

            # Generate embeddings
            embeddings = {}
            embedding_metadata = {}

            # Game context embedding
            if game_context_text:
                result = await self._generate_embedding(game_context_text, "game_context")
                embeddings['game_context_embedding'] = result.embedding
                embedding_metadata['game_context'] = self._create_embedding_metadata(result)

            # Prediction embedding
            if prediction_text:
                result = await self._generate_embedding(prediction_text, "prediction")
                embeddings['prediction_embedding'] = result.embedding
                embedding_metadata['prediction'] = self._create_embedding_metadata(result)

            # Outcome embedding
            if outcome_text:
                result = await self._generate_embedding(outcome_text, "outcome")
                embeddings['outcome_embedding'] = result.embedding
                embedding_metadata['outcome'] = self._create_embedding_metadata(result)

            # Combined embedding
            if combined_text:
                result = await self._generate_embedding(combined_text, "combined")
                embeddings['combined_embedding'] = result.embedding
                embedding_metadata['combined'] = self._create_embedding_metadata(result)

            # Store embeddings in database
            await self._store_embeddings_in_database(memory_id, embeddings, embedding_metadata)

            generation_time = (time.time() - start_time) * 1000
            self.logger.info(f"Generated embeddings for memory {memory_id} in {generation_time:.1f}ms")

            return MemoryEmbedding(
                memory_id=memory_id,
                expert_id=expert_id,
                game_context_embedding=embeddings.get('game_context_embedding'),
                prediction_embedding=embeddings.get('prediction_embedding'),
                outcome_embedding=embeddings.get('outcome_embedding'),
                combined_embedding=embeddings.get('combined_embedding'),
                embedding_metadata=embedding_metadata
            )

        except Exception as e:
            self.logger.error(f"Error generating memory embeddings: {str(e)}")
            raise

    def _create_game_context_text(self, game_context: Dict[str, Any]) -> str:
        """Create rich text representation of game context for embedding"""
        context_parts = []

        # Basic game info
        home_team = game_context.get('home_team', 'Unknown')
        away_team = game_context.get('away_team', 'Unknown')
        week = game_context.get('week', 0)
        season = game_context.get('season', 2024)

        context_parts.append(f"NFL Week {week} {season}: {away_team} at {home_team}")

        # Weather conditions
        weather = game_context.get('weather', {})
        if weather:
            temp = weather.get('temperature')
            wind = weather.get('wind_speed')
            conditions = weather.get('conditions', 'clear')

            weather_desc = f"Weather: {conditions}"
            if temp is not None:
                weather_desc += f", {temp}°F"
            if wind is not None:
                weather_desc += f", {wind}mph wind"
            context_parts.append(weather_desc)

        # Team performance context
        team_stats = game_context.get('team_stats', {})
        if team_stats:
            home_stats = team_stats.get('home', {})
            away_stats = team_stats.get('away', {})

            # Offensive capabilities
            home_off_yards = home_stats.get('offensive_yards_per_game', 0)
            away_off_yards = away_stats.get('offensive_yards_per_game', 0)

            if home_off_yards and away_off_yards:
                context_parts.append(f"Offensive yards: {home_team} {home_off_yards}, {away_team} {away_off_yards}")

            # Defensive capabilities
            home_def_yards = home_stats.get('defensive_yards_allowed', 0)
            away_def_yards = away_stats.get('defensive_yards_allowed', 0)

            if home_def_yards and away_def_yards:
                context_parts.append(f"Defensive yards allowed: {home_team} {home_def_yards}, {away_team} {away_def_yards}")

        # Injury context
        injuries = game_context.get('injuries', {})
        if injuries:
            home_injuries = injuries.get('home', [])
            away_injuries = injuries.get('away', [])

            if home_injuries:
                key_injuries = [inj for inj in home_injuries if inj.get('severity') in ['out', 'doubtful']]
                if key_injuries:
                    positions = [inj.get('position', 'player') for inj in key_injuries]
                    context_parts.append(f"{home_team} missing: {', '.join(positions)}")

            if away_injuries:
                key_injuries = [inj for inj in away_injuries if inj.get('severity') in ['out', 'doubtful']]
                if key_injuries:
                    positions = [inj.get('position', 'player') for inj in key_injuries]
                    context_parts.append(f"{away_team} missing: {', '.join(positions)}")

        # Betting context
        line_movement = game_context.get('line_movement', {})
        if line_movement:
            opening_line = line_movement.get('opening_line')
            current_line = line_movement.get('current_line')
            public_percentage = line_movement.get('public_percentage')

            if opening_line is not None and current_line is not None:
                line_move = current_line - opening_line
                if abs(line_move) >= 1:
                    direction = "toward home" if line_move > 0 else "toward away"
                    context_parts.append(f"Line moved {abs(line_move)} points {direction}")

            if public_percentage is not None:
                if public_percentage >= 70:
                    context_parts.append(f"Heavy public betting ({public_percentage}%) on favorite")
                elif public_percentage <= 30:
                    context_parts.append(f"Contrarian opportunity ({public_percentage}%) on favorite")

        # Situational context
        if game_context.get('is_divisional'):
            context_parts.append("Divisional rivalry game")

        if game_context.get('is_primetime'):
            context_parts.append("Primetime game")

        if game_context.get('playoff_implications'):
            context_parts.append("Playoff implications")

        return " | ".join(context_parts)

    def _create_prediction_text(self, prediction_data: Dict[str, Any], expert_reasoning: Optional[str]) -> str:
        """Create text representation of prediction for embedding"""
        pred_parts = []

        # Winner prediction
        predicted_winner = prediction_data.get('predicted_winner')
        if predicted_winner:
            pred_parts.append(f"Predicted winner: {predicted_winner}")

        # Confidence and margin
        confidence = prediction_data.get('confidence', 0)
        margin = prediction_data.get('predicted_margin', 0)

        if confidence:
            pred_parts.append(f"Confidence: {confidence:.1%}")

        if margin:
            pred_parts.append(f"Predicted margin: {abs(margin)} points")

        # Spread prediction
        spread_pick = prediction_data.get('spread_pick')
        if spread_pick:
            pred_parts.append(f"Spread pick: {spread_pick}")

        # Total prediction
        total_pick = prediction_data.get('total_pick')
        if total_pick:
            pred_parts.append(f"Total pick: {total_pick}")

        # Key factors
        key_factors = prediction_data.get('key_factors', [])
        if key_factors:
            pred_parts.append(f"Key factors: {', '.join(key_factors)}")

        # Expert reasoning
        if expert_reasoning:
            pred_parts.append(f"Reasoning: {expert_reasoning}")

        return " | ".join(pred_parts)

    def _create_outcome_text(self, outcome_data: Dict[str, Any], game_context: Dict[str, Any]) -> str:
        """Create text representation of game outcome for embedding"""
        outcome_parts = []

        # Basic outcome
        winner = outcome_data.get('winner')
        home_score = outcome_data.get('home_score', 0)
        away_score = outcome_data.get('away_score', 0)
        margin = outcome_data.get('margin', 0)

        home_team = game_context.get('home_team', 'Home')
        away_team = game_context.get('away_team', 'Away')

        if winner:
            outcome_parts.append(f"Winner: {winner}")

        if home_score and away_score:
            outcome_parts.append(f"Final score: {home_team} {home_score}, {away_team} {away_score}")

        if margin:
            outcome_parts.append(f"Margin: {margin} points")

        # Spread outcome
        spread_result = outcome_data.get('spread_result')
        if spread_result:
            outcome_parts.append(f"Spread result: {spread_result}")

        # Total outcome
        total_result = outcome_data.get('total_result')
        total_points = outcome_data.get('total_points')
        if total_result:
            outcome_parts.append(f"Total result: {total_result}")
        if total_points:
            outcome_parts.append(f"Total points: {total_points}")

        # Game flow
        game_flow = outcome_data.get('game_flow', {})
        if game_flow:
            if game_flow.get('lead_changes'):
                outcome_parts.append(f"Lead changes: {game_flow['lead_changes']}")
            if game_flow.get('largest_lead'):
                outcome_parts.append(f"Largest lead: {game_flow['largest_lead']}")

        return " | ".join(outcome_parts)

    def _create_combined_text(
        self,
        game_context_text: str,
        prediction_text: Optional[str],
        outcome_text: Optional[str]
    ) -> str:
        """Create combined text for comprehensive embedding"""
        parts = [game_context_text]

        if prediction_text:
            parts.append(f"Prediction: {prediction_text}")

        if outcome_text:
            parts.append(f"Outcome: {outcome_text}")

        return " | ".join(parts)

    async def _generate_embedding(self, text: str, embedding_type: str) -> EmbeddingResult:
        """Generate vector embedding for text"""
        start_time = time.time()

        try:
            # Try OpenAI first if available
            if self.openai_client:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                embedding = response.data[0].embedding
                generation_time_ms = int((time.time() - start_time) * 1000)

                return EmbeddingResult(
                    embedding=embedding,
                    model_name=self.embedding_model,
                    model_version=self.model_version,
                    dimensions=len(embedding),
                    generation_time_ms=generation_time_ms,
                    source_text_length=len(text),
                    confidence_score=1.0  # OpenAI embeddings are reliable
                )

            # Fallback to local LLM for embedding generation
            # Note: This is a simplified approach - in practice, you'd want a dedicated embedding model
            else:
                self.logger.warning("OpenAI not available, using local LLM for embedding generation")

                # Use local LLM to generate a semantic representation
                # This is not ideal but provides a fallback
                system_message = """You are an embedding generator. Convert the input text into a semantic vector representation.
                Respond with exactly 1536 comma-separated floating point numbers between -1 and 1."""

                response = self.llm_service.generate_completion(
                    system_message=system_message,
                    user_message=f"Generate embedding for: {text}",
                    temperature=0.0,
                    max_tokens=4000
                )

                # Parse the response to extract numbers (this is a simplified approach)
                try:
                    # Extract numbers from response
                    import re
                    numbers = re.findall(r'-?\d+\.?\d*', response.content)
                    embedding = [float(n) for n in numbers[:self.embedding_dimensions]]

                    # Pad with zeros if not enough numbers
                    while len(embedding) < self.embedding_dimensions:
                        embedding.append(0.0)

                    # Truncate if too many numbers
                    embedding = embedding[:self.embedding_dimensions]

                    generation_time_ms = int((time.time() - start_time) * 1000)

                    return EmbeddingResult(
                        embedding=embedding,
                        model_name="local_llm_embedding",
                        model_version=self.model_version,
                        dimensions=len(embedding),
                        generation_time_ms=generation_time_ms,
                        source_text_length=len(text),
                        confidence_score=0.5  # Lower confidence for local generation
                    )

                except Exception as e:
                    self.logger.error(f"Error parsing local LLM embedding: {e}")
                    # Return zero vector as ultimate fallback
                    return EmbeddingResult(
                        embedding=[0.0] * self.embedding_dimensions,
                        model_name="zero_vector",
                        model_version=self.model_version,
                        dimensions=self.embedding_dimensions,
                        generation_time_ms=int((time.time() - start_time) * 1000),
                        source_text_length=len(text),
                        confidence_score=0.0
                    )

        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}")
            # Return zero vector as fallback
            return EmbeddingResult(
                embedding=[0.0] * self.embedding_dimensions,
                model_name="error_fallback",
                model_version=self.model_version,
                dimensions=self.embedding_dimensions,
                generation_time_ms=int((time.time() - start_time) * 1000),
                source_text_length=len(text),
                confidence_score=0.0
            )

    def _create_embedding_metadata(self, result: EmbeddingResult) -> Dict[str, Any]:
        """Create metadata for embedding result"""
        return {
            'model_name': result.model_name,
            'model_version': result.model_version,
            'embedding_dimensions': result.dimensions,
            'source_text_length': result.source_text_length,
            'generation_time_ms': result.generation_time_ms,
            'confidence_score': result.confidence_score,
            'generated_at': datetime.now().isoformat()
        }

    async def _store_embeddings_in_database(
        self,
        memory_id: str,
        embeddings: Dict[str, List[float]],
        metadata: Dict[str, Any]
    ) -> None:
        """Store embeddings in the expert_episodic_memories table"""
        try:
            # Update the memory record with embeddings
            update_data = {
                'embedding_model': self.embedding_model,
                'embedding_generated_at': datetime.now().isoformat(),
                'embedding_version': 1
            }

            # Add embeddings
            for embedding_type, embedding_vector in embeddings.items():
                update_data[embedding_type] = embedding_vector

            # Update the memory record
            response = self.supabase.table('expert_episodic_memories').update(update_data).eq('memory_id', memory_id).execute()

            # Store detailed metadata
            for embedding_type, embedding_metadata in metadata.items():
                metadata_record = {
                    'memory_id': memory_id,
                    'embedding_type': embedding_type,
                    'model_name': embedding_metadata['model_name'],
                    'model_version': embedding_metadata['model_version'],
                    'embedding_dimensions': embedding_metadata['embedding_dimensions'],
                    'source_text_length': embedding_metadata['source_text_length'],
                    'generation_time_ms': embedding_metadata['generation_time_ms'],
                    'confidence_score': embedding_metadata['confidence_score']
                }

                self.supabase.table('memory_embeddings_metadata').insert(metadata_record).execute()

            self.logger.debug(f"Stored embeddings for memory {memory_id}")

        except Exception as e:
            self.logger.error(f"Error storing embeddings in database: {str(e)}")
            raise

    async def find_similar_memories(
        self,
        expert_id: str,
        query_game_context: Dict[str, Any],
        embedding_type: str = 'combined',
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        recency_weight: float = 0.3,
        vividness_weight: float = 0.4,
        similarity_weight: float = 0.3
    ) -> List[SimilarityResult]:
        """
        Find similar memories using vector similarity search.

        Args:
            expert_id: ID of the expert
            query_game_context: Game context to find similar memories for
            embedding_type: Type of embedding to use ('game_context', 'prediction', 'outcome', 'combined')
            similarity_threshold: Minimum similarity score
            max_results: Maximum results to return
            recency_weight: Weight for recency in relevance scoring
            vividness_weight: Weight for memory vividness
            similarity_weight: Weight for similarity score

        Returns:
            List[SimilarityResult]: Similar memories with relevance scores
        """
        try:
            # Generate query embedding
            query_text = self._create_game_context_text(query_game_context)
            embedding_result = await self._generate_embedding(query_text, embedding_type)
            query_embedding = embedding_result.embedding

            # Search using the database function
            response = self.supabase.rpc('search_relevant_memories', {
                'target_embedding': query_embedding,
                'expert_id_filter': expert_id,
                'embedding_type': embedding_type,
                'recency_weight': recency_weight,
                'vividness_weight': vividness_weight,
                'similarity_weight': similarity_weight,
                'max_results': max_results
            }).execute()

            # Convert to SimilarityResult objects
            results = []
            for row in response.data or []:
                result = SimilarityResult(
                    memory_id=row['memory_id'],
                    expert_id=row['expert_id'],
                    game_id=row['game_id'],
                    memory_type=row['memory_type'],
                    similarity_score=float(row['similarity_score']),
                    relevance_score=float(row['relevance_score']),
                    memory_vividness=float(row['memory_vividness']),
                    memory_decay=float(row['memory_decay']),
                    retrieval_count=int(row['retrieval_count']),
                    created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
                )
                results.append(result)

            # Track memory retrievals
            for result in results:
                await self._track_memory_retrieval(result.memory_id)

            self.logger.info(f"Found {len(results)} similar memories for expert {expert_id}")
            return results

        except Exception as e:
            self.logger.error(f"Error finding similar memories: {str(e)}")
            return []

    async def _track_memory_retrieval(self, memory_id: str) -> None:
        """Track that a memory was retrieved"""
        try:
            self.supabase.rpc('track_memory_retrieval', {
                'memory_id_param': memory_id,
                'retrieval_context': 'prediction_generation'
            }).execute()
        except Exception as e:
            self.logger.warning(f"Error tracking memory retrieval: {str(e)}")

    async def get_embedding_coverage_stats(self, expert_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about embedding coverage"""
        try:
            if expert_id:
                response = self.supabase.table('embedding_coverage_analysis').select('*').eq('expert_id', expert_id).execute()
            else:
                response = self.supabase.table('embedding_coverage_analysis').select('*').execute()

            return {
                'coverage_stats': response.data,
                'total_experts': len(response.data) if response.data else 0
            }

        except Exception as e:
            self.logger.error(f"Error getting embedding coverage stats: {str(e)}")
            return {'coverage_stats': [], 'total_experts': 0}

    async def regenerate_embeddings_for_memory(self, memory_id: str) -> bool:
        """Regenerate embeddings for a specific memory"""
        try:
            # Get the memory data
            response = self.supabase.table('expert_episodic_memories').select('*').eq('memory_id', memory_id).execute()

            if not response.data:
                self.logger.error(f"Memory {memory_id} not found")
                return False

            memory_data = response.data[0]

            # Extract game context from memory data
            game_context = {
                'home_team': memory_data.get('home_team'),
                'away_team': memory_data.get('away_team'),
                'week': memory_data.get('week'),
                'season': memory_data.get('season')
            }

            # Add contextual factors if available
            contextual_factors = memory_data.get('contextual_factors', [])
            if contextual_factors:
                game_context['contextual_factors'] = contextual_factors

            # Regenerate embeddings
            await self.generate_memory_embeddings(
                memory_id=memory_id,
                expert_id=memory_data['expert_id'],
                game_context=game_context,
                prediction_data=memory_data.get('prediction_data'),
                outcome_data=memory_data.get('actual_outcome')
            )

            self.logger.info(f"Regenerated embeddings for memory {memory_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error regenerating embeddings for memory {memory_id}: {str(e)}")
            return False


# Global instance for easy access
_embedding_generator = None

def get_embedding_generator(supabase_client: SupabaseClient, openai_api_key: Optional[str] = None) -> MemoryEmbeddingGenerator:
    """Get global embedding generator instance"""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = MemoryEmbeddingGenerator(supabase_client, openai_api_key=openai_api_key)
    return _embedding_generator
