"""
Vector Memory Service for Semantic Memory Search

This service provides semantic memory capabilities using vector embeddings
to find contextually similar memories across different games and situations.

Features:
- OpenAI embeddings for semantic understanding
- Supabase Vector (pgvector) for primary
 Upstash Vector for backup/redundancy
- Contextual similarity search
- Memory clustering and organization
"""

import asyncio
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
import openai
import os
from dataclasses import dataclass

from supabase import Client as SupabaseClient


@dataclass
class MemoryVector:
    """Vector representation of a memory"""
    id: str
    expert_id: str
    memory_type: str  # 'game_context', 'prediction', 'outcome', 'pattern'
    content_text: str
    embedding: List[float]
    metadata: Dict[str, Any]
    similarity_score: Optional[float] = None


@dataclass
class SimilarMemory:
    """Similar memory with context"""
    memory: MemoryVector
    similarity: float
    relevance_explanation: str


class VectorMemoryService:
    """
    Service for semantic memory storage and retrieval using vector embeddings.

    This enables experts to find contextually similar memories even when
    the exact teams or situations are different.
    """

    def __init__(self, supabase_client: SupabaseClient, openai_api_key: Optional[str] = None):
        self.supabase = supabase_client
        self.logger = logging.getLogger(__name__)

        # Initialize OpenAI for embeddings
        if openai_api_key:
            openai.api_key = openai_api_key
        else:
            openai.api_key = os.getenv('OPENAI_API_KEY')

        # Embedding configuration - using 3-small to fit within pgvector limits
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimensions = 1536  # text-embedding-3-small has 1536 dimensions

        # Upstash Vector configuration (if available)
        self.upstash_url = os.getenv('UPSTASH_VECTOR_URL')
        self.upstash_token = os.getenv('UPSTASH_VECTOR_TOKEN')
        self.upstash_enabled = bool(self.upstash_url and self.upstash_token)

        if self.upstash_enabled:
            self.logger.info("Upstash Vector backup enabled")
        else:
            self.logger.info("Upstash Vector backup not configured")

    async def store_memory_vector(
        self,
        expert_id: str,
        memory_type: str,
        content_text: str,
        metadata: Dict[str, Any],
        game_id: Optional[str] = None,
        team_id: Optional[str] = None,
        matchup_id: Optional[str] = None
    ) -> str:
        """
        Store a memory with vector embedding for semantic search.

        Args:
            expert_id: ID of the expert creating the memory
            memory_type: Type of memory ('game_context', 'prediction', 'outcome', 'pattern')
            content_text: Text content to be embedded
            metadata: Additional metadata about the memory
            game_id: Associated game ID (if applicable)
            team_id: Associated team ID (if applicable)
            matchup_id: Associated matchup ID (if applicable)

        Returns:
            str: ID of the stored memory vector
        """
        try:
            # Generate embedding for the content
            embedding = await self._generate_embedding(content_text)

            # Store in Supabase Vector
            memory_data = {
                'expert_id': expert_id,
                'memory_type': memory_type,
                'game_id': game_id,
                'team_id': team_id,
                'matchup_id': matchup_id,
                'content_text': content_text,
                'embedding': embedding,
                'metadata': metadata
            }

            response = self.supabase.table('memory_vectors').insert(memory_data).execute()
            memory_id = response.data[0]['id']

            # Store in Upstash Vector as backup (if enabled)
            if self.upstash_enabled:
                await self._store_upstash_vector(memory_id, embedding, metadata)

            self.logger.info(f"Stored memory vector {memory_id} for expert {expert_id}")
            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing memory vector: {str(e)}")
            raise

    async def find_similar_memories(
        self,
        expert_id: str,
        query_text: str,
        memory_types: Optional[List[str]] = None,
        similarity_threshold: float = 0.6,
        max_results: int = 10,
        include_cross_expert: bool = False
    ) -> List[SimilarMemory]:
        """
        Find memories similar to the query text using semantic search.

        Args:
            expert_id: ID of the expert searching for memories
            query_text: Text to find similar memories for
            memory_types: Filter by memory types (optional)
            similarity_threshold: Minimum similarity score (0-1)
            max_results: Maximum number of results to return
            include_cross_expert: Whether to include memories from other experts

        Returns:
            List[SimilarMemory]: List of similar memories with similarity scores
        """
        try:
            # Generate embedding for query
            query_embedding = await self._generate_embedding(query_text)

            # Search in Supabase Vector
            similar_memories = await self._search_supabase_vectors(
                query_embedding=query_embedding,
                expert_id=expert_id if not include_cross_expert else None,
                memory_types=memory_types,
                similarity_threshold=similarity_threshold,
                max_results=max_results
            )

            # Convert to SimilarMemory objects with explanations
            results = []
            for memory_data in similar_memories:
                memory = MemoryVector(
                    id=memory_data['id'],
                    expert_id=memory_data['expert_id'],
                    memory_type=memory_data['memory_type'],
                    content_text=memory_data['content_text'],
                    embedding=[],  # Don't need to return full embedding
                    metadata=memory_data['metadata'],
                    similarity_score=memory_data['similarity']
                )

                explanation = self._generate_relevance_explanation(
                    query_text, memory.content_text, memory.similarity_score
                )

                results.append(SimilarMemory(
                    memory=memory,
                    similarity=memory_data['similarity'],
                    relevance_explanation=explanation
                ))

            self.logger.info(f"Found {len(results)} similar memories for expert {expert_id}")
            return results

        except Exception as e:
            self.logger.error(f"Error finding similar memories: {str(e)}")
            return []

    async def find_contextual_memories(
        self,
        expert_id: str,
        game_context: Dict[str, Any],
        max_results: int = 7  # Working memory capacity (7±2)
    ) -> List[SimilarMemory]:
        """
        Find memories relevant to a specific game context.

        This creates a contextual query from game information and finds
        the most relevant memories for making predictions.

        Args:
            expert_id: ID of the expert
            game_context: Dictionary with game information (teams, weather, etc.)
            max_results: Maximum memories to return (working memory limit)

        Returns:
            List[SimilarMemory]: Most relevant memories for this context
        """
        # Create contextual query text
        query_parts = []

        if 'home_team' in game_context and 'away_team' in game_context:
            query_parts.append(f"{game_context['home_team']} vs {game_context['away_team']}")

        if 'weather' in game_context:
            weather = game_context['weather']
            if weather.get('temperature'):
                query_parts.append(f"temperature {weather['temperature']}°F")
            if weather.get('wind_speed'):
                query_parts.append(f"wind {weather['wind_speed']} mph")
            if weather.get('conditions'):
                query_parts.append(f"{weather['conditions']} conditions")

        if 'week' in game_context:
            query_parts.append(f"week {game_context['week']}")

        if 'is_divisional' in game_context and game_context['is_divisional']:
            query_parts.append("divisional game")

        if 'is_primetime' in game_context and game_context['is_primetime']:
            query_parts.append("primetime game")

        query_text = " ".join(query_parts)

        # Find similar memories
        return await self.find_similar_memories(
            expert_id=expert_id,
            query_text=query_text,
            memory_types=['game_context', 'outcome', 'pattern'],
            similarity_threshold=0.7,  # Slightly lower threshold for context
            max_results=max_results
        )

    async def cluster_memories_by_similarity(
        self,
        expert_id: str,
        memory_type: Optional[str] = None,
        cluster_threshold: float = 0.85
    ) -> Dict[str, List[MemoryVector]]:
        """
        Cluster memories by semantic similarity to identify patterns.

        Args:
            expert_id: ID of the expert
            memory_type: Filter by memory type (optional)
            cluster_threshold: Similarity threshold for clustering

        Returns:
            Dict[str, List[MemoryVector]]: Clusters of similar memories
        """
        try:
            # Get all memories for the expert
            query = self.supabase.table('memory_vectors').select('*').eq('expert_id', expert_id)

            if memory_type:
                query = query.eq('memory_type', memory_type)

            response = query.execute()
            memories = response.data

            if not memories:
                return {}

            # Simple clustering based on pairwise similarity
            clusters = {}
            cluster_id = 0

            for memory in memories:
                assigned = False

                # Check if this memory belongs to an existing cluster
                for cluster_name, cluster_memories in clusters.items():
                    if cluster_memories:
                        # Compare with first memory in cluster
                        representative = cluster_memories[0]
                        similarity = await self._calculate_similarity(
                            memory['embedding'], representative['embedding']
                        )

                        if similarity >= cluster_threshold:
                            clusters[cluster_name].append(memory)
                            assigned = True
                            break

                # Create new cluster if not assigned
                if not assigned:
                    cluster_name = f"cluster_{cluster_id}"
                    clusters[cluster_name] = [memory]
                    cluster_id += 1

            # Convert to MemoryVector objects
            result_clusters = {}
            for cluster_name, cluster_memories in clusters.items():
                result_clusters[cluster_name] = [
                    MemoryVector(
                        id=mem['id'],
                        expert_id=mem['expert_id'],
                        memory_type=mem['memory_type'],
                        content_text=mem['content_text'],
                        embedding=mem['embedding'],
                        metadata=mem['metadata']
                    )
                    for mem in cluster_memories
                ]

            self.logger.info(f"Created {len(result_clusters)} memory clusters for expert {expert_id}")
            return result_clusters

        except Exception as e:
            self.logger.error(f"Error clustering memories: {str(e)}")
            return {}

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text using OpenAI"""
        try:
            # Check if API key is available
            api_key = openai.api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                self.logger.warning("OpenAI API key not set - returning zero vector")
                return [0.0] * self.embedding_dimensions

            # Use the modern OpenAI client
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            response = client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            embedding = response.data[0].embedding

            # Ensure correct dimensions
            if len(embedding) != self.embedding_dimensions:
                self.logger.warning(f"Embedding dimension mismatch: expected {self.embedding_dimensions}, got {len(embedding)}")
                # Update our expected dimensions if needed
                self.embedding_dimensions = len(embedding)

            return embedding

        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dimensions

    async def _search_supabase_vectors(
        self,
        query_embedding: List[float],
        expert_id: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        similarity_threshold: float = 0.8,
        max_results: int = 10
    ) -> List[Dict]:
        """Search for similar vectors in Supabase"""
        try:
            # Use the match_memory_vectors function we created
            memory_type_filter = memory_types[0] if memory_types and len(memory_types) == 1 else None

            response = self.supabase.rpc('match_memory_vectors', {
                'query_embedding': query_embedding,
                'filter_expert_id': expert_id,
                'filter_memory_type': memory_type_filter,
                'match_threshold': similarity_threshold,
                'match_count': max_results
            }).execute()

            return response.data or []

        except Exception as e:
            self.logger.error(f"Error searching Supabase vectors: {str(e)}")
            return []

    async def _store_upstash_vector(self, memory_id: str, embedding: List[float], metadata: Dict) -> None:
        """Store vector in Upstash as backup"""
        if not self.upstash_enabled:
            return

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.upstash_url}/upsert",
                    headers={
                        "Authorization": f"Bearer {self.upstash_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "id": memory_id,
                        "vector": embedding,
                        "metadata": metadata
                    }
                )

                if response.status_code != 200:
                    self.logger.warning(f"Upstash backup failed: {response.text}")

        except Exception as e:
            self.logger.warning(f"Upstash backup error: {str(e)}")

    async def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Ensure we have actual float lists, not strings
            if isinstance(embedding1, str):
                embedding1 = json.loads(embedding1) if embedding1.startswith('[') else [0.0] * self.embedding_dimensions
            if isinstance(embedding2, str):
                embedding2 = json.loads(embedding2) if embedding2.startswith('[') else [0.0] * self.embedding_dimensions

            # Convert to numpy arrays with explicit float type
            vec1 = np.array(embedding1, dtype=np.float32)
            vec2 = np.array(embedding2, dtype=np.float32)

            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            self.logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0

    def _generate_relevance_explanation(self, query: str, memory_text: str, similarity: float) -> str:
        """Generate human-readable explanation of why a memory is relevant"""
        if similarity > 0.9:
            return f"Very similar context: {similarity:.1%} match"
        elif similarity > 0.8:
            return f"Similar situation: {similarity:.1%} match"
        elif similarity > 0.7:
            return f"Somewhat related: {similarity:.1%} match"
        else:
            return f"Potentially relevant: {similarity:.1%} match"

    async def get_memory_statistics(self, expert_id: str) -> Dict[str, Any]:
        """Get statistics about stored memories for an expert"""
        try:
            response = self.supabase.table('memory_vectors').select('memory_type').eq('expert_id', expert_id).execute()

            memories = response.data
            total_memories = len(memories)

            # Count by type
            type_counts = {}
            for memory in memories:
                memory_type = memory['memory_type']
                type_counts[memory_type] = type_counts.get(memory_type, 0) + 1

            return {
                'total_memories': total_memories,
                'memory_types': type_counts,
                'expert_id': expert_id,
                'vector_dimensions': self.embedding_dimensions,
                'upstash_backup_enabled': self.upstash_enabled
            }

        except Exception as e:
            self.logger.error(f"Error getting memory statistics: {str(e)}")
            return {
                'total_memories': 0,
                'memory_types': {},
                'expert_id': expert_id,
                'error': str(e)
            }
