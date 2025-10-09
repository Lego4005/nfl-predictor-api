"""
Integration helper for existing training scripts to use the unified memory system.
Drop-in replacement that maintains compatibility with existing code.
"""

import os
from typing import Dict, Any, Optional
from src.ml.unified_memory_system import UnifiedMemorySystem, MemoryRetrieval
from src.services.supabase_service import get_supabase_client


class MemoryIntegrationHelper:
    """
    Helper class to integrate the unified memory system with existing training scripts.
    Provides a simple interface that existing code can use without major changes.
    """

    def __init__(self):
        self.supabase = get_supabase_client()
        self.unified_memory = UnifiedMemorySystem(
            supabase_client=self.supabase,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )

    def get_prediction_context(self, expert_id: str, game_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get all relevant memory context for making a prediction.
        Returns a dictionary with episodic memories, team knowledge, and matchup data.
        """
        try:
            memory_retrieval = self.unified_memory.fetch_prediction_context(expert_id, game_context)

            # Format for compatibility with existing code
            return {
                'episodic_memories': memory_retrieval.episodic,
                'home_team_knowledge': memory_retrieval.home_knowledge,
                'away_team_knowledge': memory_retrieval.away_knowledge,
                'matchup_memory': memory_retrieval.matchup,
                'context_summary': self._create_context_summary(memory_retrieval),
                'memory_count': len(memory_retrieval.episodic),
                'has_team_knowledge': len(memory_retrieval.home_knowledge) > 0 or len(memory_retrieval.away_knowledge) > 0,
                'has_matchup_data': memory_retrieval.matchup is not None
            }
        except Exception as e:
            print(f"Error getting prediction context: {e}")
            return {
                'episodic_memories': [],
                'home_team_knowledge': [],
                'away_team_knowledge': [],
                'matchup_memory': None,
                'context_summary': "No context available due to error",
                'memory_count': 0,
                'has_team_knowledge': False,
                'has_matchup_data': False,
                'error': str(e)
            }

    async def store_learning(self, expert_id: str, game_id: str, game_context: Dict[str, Any],
                           prediction: Dict[str, Any], outcome: Dict[str, Any]):
        """
        Store learning from a completed game.
        This will update team knowledge and matchup memories.
        The episodic memory should be handled by the existing system.
        """
        try:
            await self.unified_memory.store_game_learning(
                expert_id=expert_id,
                game_id=game_id,
                game_context=game_context,
                prediction=prediction,
                outcome=outcome
            )
            return True
        except Exception as e:
            print(f"Error storing learning: {e}")
            return False

    def get_expert_memory_stats(self, expert_id: str) -> Dict[str, Any]:
        """Get memory statistics for an expert"""
        return self.unified_memory.get_memory_stats(expert_id)

    def _create_context_summary(self, memory_retrieval: MemoryRetrieval) -> str:
        """Create a human-readable summary of the retrieved context"""
        summary_parts = []

        if memory_retrieval.episodic:
            summary_parts.append(f"{len(memory_retrieval.episodic)} relevant past experiences")

        if memory_retrieval.home_knowledge:
            summary_parts.append(f"knowledge about home team")

        if memory_retrieval.away_knowledge:
            summary_parts.append(f"knowledge about away team")

        if memory_retrieval.matchup:
            accuracy = memory_retrieval.matchup.get('accuracy', 0)
            games = memory_retrieval.matchup.get('games_analyzed', 0)
            summary_parts.append(f"matchup history ({games} games, {accuracy:.1%} accuracy)")

        if not summary_parts:
            return "No relevant context found"

        return "Retrieved: " + ", ".join(summary_parts)


# Global instance for easy import
memory_helper = MemoryIntegrationHelper()


def get_memory_helper() -> MemoryIntegrationHelper:
    """Get the global memory helper instance"""
    return memory_helper


# Convenience functions for existing code
def get_prediction_context(expert_id: str, game_context: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to get prediction context"""
    return memory_helper.get_prediction_context(expert_id, game_context)


async def store_game_learning(expert_id: str, game_id: str, game_context: Dict[str, Any],
                            prediction: Dict[str, Any], outcome: Dict[str, Any]) -> bool:
    """Convenience function to store game learning"""
    return await memory_helper.store_learning(expert_id, game_id, game_context, prediction, outcome)


def get_expert_stats(expert_id: str) -> Dict[str, Any]:
    """Convenience function to get expert memory stats"""
    return memory_helper.get_expert_memory_stats(expert_id)
