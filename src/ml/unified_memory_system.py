"""
Unified Memory System for NFL Expert Prediction System.
Integrates episodic memories, team knowledge, and matchup memories with optimized retrieval.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import openai
from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class MemoryRetrieval:
    """Container for all retrieved memory context"""
    episodic: List[Dict[str, Any]]
    home_knowledge: List[Dict[str, Any]]
    away_knowledge: List[Dict[str, Any]]
    matchup: Optional[Dict[str, Any]]


class UnifiedMemorySystem:
    """
    Unified memory system that integrates with the optimized database structure.
    Uses the existing episodic memory table with embeddings and adds structured
    team knowledge and matchup memories.
    """

    def __init__(self, supabase_client: Client, openai_api_key: str):
        self.supabase = supabase_client
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.logger = logging.getLogger(__name__)

    def fetch_prediction_context(self, expert_id: str, game_ctx: Dict[str, Any], alpha: float = 0.8) -> MemoryRetrieval:
        """
        Single helper to fetch all relevant context for prediction.
        Uses the optimized recency-aware vector search and structured tables.
        """
        try:
            # Create query text for vector search
            qtext = f"{game_ctx['away_team']} at {game_ctx['home_team']} season:{game_ctx['season']} week:{game_ctx['week']}"
            qvec = self._generate_embedding(qtext)

            # Vector + recency episodic memories
            episodic_result = self.supabase.rpc("search_expert_memories", {
                "p_expert_id": expert_id,
                "p_query_embedding": qvec,
                "p_match_threshold": 0.72,
                "p_match_count": 7,
                "p_alpha": alpha
            }).execute()

            episodic = episodic_result.data if episodic_result.data else []

            # Team knowledge buckets
            home_k_result = self.supabase.table("team_knowledge").select("*") \
                .eq("expert_id", expert_id).eq("team_id", game_ctx["home_team"]) \
                .order("accuracy", desc=True).limit(10).execute()

            away_k_result = self.supabase.table("team_knowledge").select("*") \
                .eq("expert_id", expert_id).eq("team_id", game_ctx["away_team"]) \
                .order("accuracy", desc=True).limit(10).execute()

            home_k = home_k_result.data if home_k_result.data else []
            away_k = away_k_result.data if away_k_result.data else []

            # Matchup-specific memory
            matchup_result = self.supabase.table("matchup_memories").select("*") \
                .eq("expert_id", expert_id) \
                .eq("home_team", game_ctx["home_team"]) \
                .eq("away_team", game_ctx["away_team"]) \
                .limit(1).execute()

            matchup = matchup_result.data[0] if matchup_result.data else None

            return MemoryRetrieval(
                episodic=episodic,
                home_knowledge=home_k,
                away_knowledge=away_k,
                matchup=matchup
            )

        except Exception as e:
            self.logger.error(f"Error fetching prediction context for {expert_id}: {e}")
            return MemoryRetrieval(
                episodic=[],
                home_knowledge=[],
                away_knowledge=[],
                matchup=None
            )

    async def store_game_learning(self, expert_id: str, game_id: str,
                                game_context: Dict[str, Any], prediction: Dict[str, Any],
                                outcome: Dict[str, Any]):
        """
        Store learning after a game across structured tables.
        The episodic memory is handled by existing system + embedding worker.
        """
        try:
            # Update team knowledge for both teams
            for team in [game_context['home_team'], game_context['away_team']]:
                await self._update_team_knowledge(expert_id, team, prediction, outcome, game_context)

            # Update matchup memory
            await self._update_matchup_memory(
                expert_id,
                game_context['home_team'],
                game_context['away_team'],
                prediction,
                outcome,
                game_context
            )

            self.logger.info(f"Stored game learning for {expert_id} - {game_id}")

        except Exception as e:
            self.logger.error(f"Error storing game learning for {expert_id}: {e}")

    async def _update_team_knowledge(self, expert_id: str, team_id: str,
                                   prediction: Dict[str, Any], outcome: Dict[str, Any],
                                   game_context: Dict[str, Any]):
        """Update or create team knowledge entry"""
        try:
            # Check if knowledge exists
            result = self.supabase.table('team_knowledge') \
                .select('*') \
                .eq('expert_id', expert_id) \
                .eq('team_id', team_id) \
                .execute()

            was_correct = self._was_prediction_correct(prediction, outcome, team_id)

            if result.data:
                # Update existing
                knowledge = result.data[0]
                knowledge['games_analyzed'] += 1
                knowledge['predictions_made'] += 1
                if was_correct:
                    knowledge['predictions_correct'] += 1
                knowledge['accuracy'] = knowledge['predictions_correct'] / knowledge['predictions_made']
                knowledge['updated_at'] = 'now()'

                # Update performance context
                is_home = game_context.get('home_team') == team_id
                perf_key = 'home_performance' if is_home else 'away_performance'
                if not knowledge.get(perf_key):
                    knowledge[perf_key] = {}

                perf = knowledge[perf_key]
                perf['games'] = perf.get('games', 0) + 1
                perf['correct'] = perf.get('correct', 0) + (1 if was_correct else 0)
                perf['accuracy'] = perf['correct'] / perf['games']

                self.supabase.table('team_knowledge').update(knowledge) \
                    .eq('id', knowledge['id']).execute()
            else:
                # Create new
                new_knowledge = {
                    'expert_id': expert_id,
                    'team_id': team_id,
                    'games_analyzed': 1,
                    'predictions_made': 1,
                    'predictions_correct': 1 if was_correct else 0,
                    'accuracy': 1.0 if was_correct else 0.0,
                    'overall_assessment': f"Initial assessment for {team_id}",
                    'strengths': [],
                    'weaknesses': [],
                    'key_patterns': {}
                }

                # Set initial performance context
                is_home = game_context.get('home_team') == team_id
                perf_key = 'home_performance' if is_home else 'away_performance'
                new_knowledge[perf_key] = {
                    'games': 1,
                    'correct': 1 if was_correct else 0,
                    'accuracy': 1.0 if was_correct else 0.0
                }

                self.supabase.table('team_knowledge').insert(new_knowledge).execute()

        except Exception as e:
            self.logger.error(f"Error updating team knowledge for {expert_id}-{team_id}: {e}")

    async def _update_matchup_memory(self, expert_id: str, home_team: str, away_team: str,
                                   prediction: Dict[str, Any], outcome: Dict[str, Any],
                                   game_context: Dict[str, Any]):
        """Update matchup-specific memory"""
        try:
            # Check if matchup memory exists
            result = self.supabase.table('matchup_memories') \
                .select('*') \
                .eq('expert_id', expert_id) \
                .eq('home_team', home_team) \
                .eq('away_team', away_team) \
                .execute()

            was_correct = prediction.get('predicted_winner') == outcome.get('winner')
            actual_margin = abs(outcome.get('home_score', 0) - outcome.get('away_score', 0))

            if result.data:
                # Update existing
                memory = result.data[0]
                memory['games_analyzed'] += 1
                memory['predictions_made'] += 1
                if was_correct:
                    memory['predictions_correct'] += 1
                memory['accuracy'] = memory['predictions_correct'] / memory['predictions_made']

                # Update typical margin (running average)
                if memory.get('typical_margin'):
                    memory['typical_margin'] = (memory['typical_margin'] + actual_margin) / 2
                else:
                    memory['typical_margin'] = actual_margin

                memory['updated_at'] = 'now()'

                self.supabase.table('matchup_memories').update(memory) \
                    .eq('id', memory['id']).execute()
            else:
                # Create new
                new_memory = {
                    'expert_id': expert_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'games_analyzed': 1,
                    'predictions_made': 1,
                    'predictions_correct': 1 if was_correct else 0,
                    'accuracy': 1.0 if was_correct else 0.0,
                    'typical_margin': actual_margin,
                    'scoring_pattern': 'Initial pattern',
                    'key_factors': []
                }

                self.supabase.table('matchup_memories').insert(new_memory).execute()

        except Exception as e:
            self.logger.error(f"Error updating matchup memory for {expert_id}-{home_team}-{away_team}: {e}")

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return [0.0] * 1536  # Return zero vector as fallback

    def _was_prediction_correct(self, prediction: Dict[str, Any], outcome: Dict[str, Any], team_id: str) -> bool:
        """Determine if prediction was correct for specific team"""
        predicted_winner = prediction.get('predicted_winner')
        actual_winner = outcome.get('winner')

        if predicted_winner == actual_winner:
            return True

        # Additional logic for spread/total predictions could go here
        return False

    def get_memory_stats(self, expert_id: str) -> Dict[str, Any]:
        """Get memory statistics for an expert"""
        try:
            # Episodic memories count
            episodic_result = self.supabase.table('expert_episodic_memories') \
                .select('memory_id', count='exact') \
                .eq('expert_id', expert_id) \
                .execute()

            # Team knowledge count
            team_k_result = self.supabase.table('team_knowledge') \
                .select('id', count='exact') \
                .eq('expert_id', expert_id) \
                .execute()

            # Matchup memories count
            matchup_result = self.supabase.table('matchup_memories') \
                .select('id', count='exact') \
                .eq('expert_id', expert_id) \
                .execute()

            return {
                'expert_id': expert_id,
                'episodic_memories': episodic_result.count or 0,
                'team_knowledge_entries': team_k_result.count or 0,
                'matchup_memories': matchup_result.count or 0,
                'total_structured_entries': (team_k_result.count or 0) + (matchup_result.count or 0)
            }

        except Exception as e:
            self.logger.error(f"Error getting memory stats for {expert_id}: {e}")
            return {
                'expert_id': expert_id,
                'episodic_memories': 0,
                'team_knowledge_entries': 0,
                'matchup_memories': 0,
                'total_structured_entries': 0,
                'error': str(e)
            }
