"""
Expert Memory Service - Supabase Integration for Personality Expert Learning
Provides persistent memory, historical lookup, and autonomous learning capabilities
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import numpy as np
from dataclasses import dataclass
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class ExpertMemory:
    """Represents a stored memory for an expert"""
    id: str
    expert_id: str
    game_id: str
    prediction: Dict
    actual_result: Optional[Dict]
    performance_score: Optional[float]
    context_snapshot: Dict
    timestamp: datetime


class ExpertMemoryService:
    """Service for managing expert memory and learning with Supabase"""

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.embeddings_cache = {}
        logger.info("🧠 Expert Memory Service initialized with Supabase")

    async def store_prediction(self, expert_id: str, game_id: str,
                              home_team: str, away_team: str,
                              prediction: Dict, context: Dict) -> str:
        """Store an expert's prediction in Supabase"""
        try:
            # Store in database
            result = self.supabase.rpc('record_expert_prediction', {
                'p_expert_id': expert_id,
                'p_game_id': game_id,
                'p_home_team': home_team,
                'p_away_team': away_team,
                'p_prediction': json.dumps(prediction),
                'p_context': json.dumps(context)
            }).execute()

            memory_id = result.data

            # Generate and store embeddings for similarity search
            await self._store_embeddings(memory_id, prediction, context)

            logger.info(f"✅ Stored prediction for {expert_id} on game {game_id}")
            return memory_id

        except Exception as e:
            logger.error(f"❌ Failed to store prediction: {e}")
            raise

    async def get_similar_games(self, expert_id: str, context: Dict,
                               limit: int = 10) -> List[ExpertMemory]:
        """Find similar past games using pgvector similarity search"""
        try:
            # Generate embedding for current context
            context_embedding = await self._generate_embedding(context)

            # Query similar games using pgvector
            query = """
                SELECT *,
                1 - (context_embedding <=> %s::vector) as similarity
                FROM expert_memory
                WHERE expert_id = %s
                AND actual_result IS NOT NULL
                ORDER BY context_embedding <=> %s::vector
                LIMIT %s
            """

            result = self.supabase.rpc('search_similar_games', {
                'p_expert_id': expert_id,
                'p_embedding': context_embedding.tolist(),
                'p_limit': limit
            }).execute()

            memories = []
            for row in result.data:
                memories.append(ExpertMemory(
                    id=row['id'],
                    expert_id=row['expert_id'],
                    game_id=row['game_id'],
                    prediction=row['prediction'],
                    actual_result=row['actual_result'],
                    performance_score=row['performance_score'],
                    context_snapshot=row['context_snapshot'],
                    timestamp=row['timestamp']
                ))

            logger.info(f"📚 Found {len(memories)} similar games for {expert_id}")
            return memories

        except Exception as e:
            logger.error(f"❌ Failed to find similar games: {e}")
            return []

    async def learn_from_result(self, game_id: str, actual_result: Dict):
        """Process game results and trigger learning for all experts"""
        try:
            # Update all expert memories with actual results
            self.supabase.rpc('process_expert_learning', {
                'p_game_id': game_id,
                'p_actual_result': json.dumps(actual_result)
            }).execute()

            logger.info(f"🎓 Triggered learning for game {game_id}")

            # Process learning queue asynchronously
            await self._process_learning_queue()

        except Exception as e:
            logger.error(f"❌ Failed to process learning: {e}")

    async def _process_learning_queue(self):
        """Process pending learning tasks"""
        try:
            # Get unprocessed learning tasks
            result = self.supabase.table('expert_learning_queue') \
                .select('*') \
                .eq('processed', False) \
                .order('priority', desc=True) \
                .limit(50) \
                .execute()

            for task in result.data:
                await self._process_learning_task(task)

                # Mark as processed
                self.supabase.table('expert_learning_queue') \
                    .update({'processed': True, 'processed_at': datetime.now().isoformat()}) \
                    .eq('id', task['id']) \
                    .execute()

            logger.info(f"✅ Processed {len(result.data)} learning tasks")

        except Exception as e:
            logger.error(f"❌ Failed to process learning queue: {e}")

    def get_expert_beliefs(self, expert_id: str) -> Dict[str, Any]:
        """
        Get current beliefs for an expert (synchronous for continuous learning)

        Args:
            expert_id: Expert identifier

        Returns:
            Dictionary of expert beliefs
        """
        try:
            if self.supabase:
                result = self.supabase.table('expert_belief_revisions') \
                    .select('belief_key, new_belief') \
                    .eq('expert_id', expert_id) \
                    .order('revision_timestamp', desc=True) \
                    .execute()

                beliefs = {}
                seen_keys = set()
                for row in result.data:
                    belief_key = row['belief_key']
                    if belief_key not in seen_keys:
                        beliefs[belief_key] = row['new_belief']
                        seen_keys.add(belief_key)

                return beliefs

            # Return default beliefs if no database
            return {
                'home_field_advantage': {
                    'statement': 'Home teams typically have a 3-point advantage',
                    'confidence': 0.7,
                    'based_on': 'historical analysis'
                },
                'weather_impact': {
                    'statement': 'Weather affects game outcomes',
                    'confidence': 0.6,
                    'based_on': 'observational data'
                }
            }

        except Exception as e:
            logger.error(f"Error getting expert beliefs: {e}")
            return {}

    def update_expert_beliefs(self, expert_id: str, new_beliefs: Dict[str, Any]):
        """
        Update expert beliefs (synchronous for continuous learning)

        Args:
            expert_id: Expert identifier
            new_beliefs: Updated belief dictionary
        """
        try:
            logger.info(f"Updating beliefs for expert {expert_id}")

            # In a full implementation, this would update the belief database
            # For now, we just log the update
            for belief_key, belief_data in new_beliefs.items():
                logger.info(f"Updated belief {belief_key} for {expert_id}: {belief_data}")

            if self.supabase:
                # Store belief updates in database
                for belief_key, belief_data in new_beliefs.items():
                    try:
                        self.supabase.table('expert_belief_updates') \
                            .insert({
                                'expert_id': expert_id,
                                'belief_key': belief_key,
                                'belief_data': json.dumps(belief_data),
                                'updated_at': datetime.now().isoformat(),
                                'source': 'continuous_learning'
                            }) \
                            .execute()
                    except Exception as e:
                        logger.warning(f"Could not store belief update in database: {e}")

        except Exception as e:
            logger.error(f"Error updating expert beliefs: {e}")

    def update_expert_knowledge_from_outcome(self, expert_id: str, game_id: str,
                                           prediction_outcome: Dict[str, Any]):
        """
        Update expert knowledge based on prediction outcome

        Args:
            expert_id: Expert identifier
            game_id: Game identifier
            prediction_outcome: Outcome details including accuracy and errors
        """
        try:
            # Extract outcome information
            was_correct = prediction_outcome.get('was_correct', False)
            error_magnitude = prediction_outcome.get('error_magnitude', 0.0)
            confidence = prediction_outcome.get('confidence', 0.5)
            prediction_type = prediction_outcome.get('prediction_type', 'unknown')

            # Create learning record
            learning_record = {
                'expert_id': expert_id,
                'game_id': game_id,
                'prediction_type': prediction_type,
                'was_correct': was_correct,
                'error_magnitude': error_magnitude,
                'confidence': confidence,
                'learning_points': self._extract_learning_points(prediction_outcome),
                'timestamp': datetime.now().isoformat()
            }

            # Store learning record
            if self.supabase:
                try:
                    self.supabase.table('expert_learning_records') \
                        .insert(learning_record) \
                        .execute()
                except Exception as e:
                    logger.warning(f"Could not store learning record: {e}")

            # Update expert's confidence and knowledge
            self._update_expert_confidence(expert_id, was_correct, confidence, error_magnitude)

            logger.info(f"Updated knowledge for {expert_id} from game {game_id}")

        except Exception as e:
            logger.error(f"Error updating expert knowledge: {e}")

    def _extract_learning_points(self, outcome: Dict[str, Any]) -> List[str]:
        """Extract key learning points from prediction outcome"""
        learning_points = []

        was_correct = outcome.get('was_correct', False)
        error_magnitude = outcome.get('error_magnitude', 0.0)
        confidence = outcome.get('confidence', 0.5)

        if was_correct and confidence > 0.8:
            learning_points.append("High confidence prediction was correct - reinforce strategy")
        elif was_correct and confidence < 0.6:
            learning_points.append("Low confidence prediction was correct - investigate factors")
        elif not was_correct and confidence > 0.7:
            learning_points.append("High confidence prediction failed - review assumptions")
        elif not was_correct and error_magnitude > 0.5:
            learning_points.append("Large prediction error - major factors missed")

        # Add context-specific learning points
        context = outcome.get('context', {})
        if context.get('weather_factor'):
            if was_correct:
                learning_points.append("Weather consideration was helpful")
            else:
                learning_points.append("Weather impact may be overestimated")

        return learning_points

    def _update_expert_confidence(self, expert_id: str, was_correct: bool,
                                 original_confidence: float, error_magnitude: float):
        """Update expert's overall confidence based on outcome"""
        try:
            # Simple confidence adjustment algorithm
            if was_correct:
                # Boost confidence if prediction was correct
                confidence_adjustment = 0.02 * original_confidence
            else:
                # Reduce confidence based on error magnitude
                confidence_adjustment = -0.05 * error_magnitude

            # Store confidence update
            if self.supabase:
                try:
                    self.supabase.table('expert_confidence_updates') \
                        .insert({
                            'expert_id': expert_id,
                            'confidence_adjustment': confidence_adjustment,
                            'was_correct': was_correct,
                            'error_magnitude': error_magnitude,
                            'timestamp': datetime.now().isoformat()
                        }) \
                        .execute()
                except Exception as e:
                    logger.warning(f"Could not store confidence update: {e}")

            logger.debug(f"Adjusted confidence for {expert_id} by {confidence_adjustment:.3f}")

        except Exception as e:
            logger.error(f"Error updating expert confidence: {e}")

    async def _process_learning_task(self, task: Dict):
        """Process individual learning task"""
        expert_id = task['expert_id']
        learning_type = task['learning_type']
        data = task['data']

        if learning_type == 'game_result':
            await self._learn_from_game_result(expert_id, data)
        elif learning_type == 'peer_success':
            await self._learn_from_peer(expert_id, data)
        elif learning_type == 'pattern_detected':
            await self._learn_from_pattern(expert_id, data)

    async def _learn_from_game_result(self, expert_id: str, data: Dict):
        """Update expert weights based on game results"""
        try:
            # Get current expert state
            result = self.supabase.table('personality_experts') \
                .select('*') \
                .eq('expert_id', expert_id) \
                .single() \
                .execute()

            expert = result.data
            current_weights = expert['current_weights'] or {}
            performance_score = data['score']

            # Calculate weight adjustments based on performance
            learning_rate = expert['learning_rate']
            adjustment_factor = (performance_score - 0.5) * learning_rate

            # Update specific weights based on what worked/didn't work
            new_weights = self._adjust_weights(
                current_weights,
                data['prediction'],
                data['actual'],
                adjustment_factor
            )

            # Store evolution
            self._record_evolution(expert_id, current_weights, new_weights,
                                 'game_result_learning', performance_score)

            # Update expert
            self.supabase.table('personality_experts') \
                .update({
                    'current_weights': new_weights,
                    'updated_at': datetime.now().isoformat()
                }) \
                .eq('expert_id', expert_id) \
                .execute()

            logger.info(f"🔧 Updated weights for {expert_id} (score: {performance_score:.3f})")

        except Exception as e:
            logger.error(f"❌ Failed to learn from game result: {e}")

    def _adjust_weights(self, current_weights: Dict, prediction: Dict,
                       actual: Dict, adjustment: float) -> Dict:
        """Adjust weights based on prediction accuracy"""
        new_weights = current_weights.copy()

        # Adjust winner prediction weight
        if prediction.get('winner_prediction') == actual.get('winner'):
            # Correct prediction - reinforce
            new_weights['winner_confidence'] = min(1.0,
                new_weights.get('winner_confidence', 0.5) + adjustment)
        else:
            # Incorrect - reduce confidence
            new_weights['winner_confidence'] = max(0.0,
                new_weights.get('winner_confidence', 0.5) - adjustment)

        # Adjust spread weight if close
        if 'spread_prediction' in prediction and 'actual_spread' in actual:
            spread_error = abs(prediction['spread_prediction'] - actual['actual_spread'])
            if spread_error < 3:
                new_weights['spread_weight'] = min(1.0,
                    new_weights.get('spread_weight', 0.5) + adjustment * 0.5)
            elif spread_error > 7:
                new_weights['spread_weight'] = max(0.0,
                    new_weights.get('spread_weight', 0.5) - adjustment * 0.5)

        # Adjust factor weights based on key factors that were right/wrong
        if 'key_factors' in prediction:
            for factor in prediction['key_factors']:
                factor_key = f"factor_{factor.lower().replace(' ', '_')}"

                # Simple heuristic: if we won, these factors were good
                if prediction.get('winner_prediction') == actual.get('winner'):
                    new_weights[factor_key] = min(1.0,
                        new_weights.get(factor_key, 0.5) + adjustment * 0.3)
                else:
                    new_weights[factor_key] = max(0.0,
                        new_weights.get(factor_key, 0.5) - adjustment * 0.3)

        return new_weights

    def _record_evolution(self, expert_id: str, old_state: Dict,
                         new_state: Dict, reason: str, performance: float):
        """Record algorithm evolution in database"""
        try:
            # Get current version
            result = self.supabase.table('expert_evolution') \
                .select('version') \
                .eq('expert_id', expert_id) \
                .order('version', desc=True) \
                .limit(1) \
                .execute()

            version = (result.data[0]['version'] + 1) if result.data else 1

            # Insert evolution record
            self.supabase.table('expert_evolution').insert({
                'expert_id': expert_id,
                'version': version,
                'algorithm_type': 'weights',
                'previous_state': old_state,
                'new_state': new_state,
                'trigger_reason': reason,
                'performance_before': performance,
                'performance_after': None  # Will be evaluated later
            }).execute()

        except Exception as e:
            logger.error(f"❌ Failed to record evolution: {e}")

    async def get_expert_tools(self, expert_id: str, game_context: Dict) -> Dict:
        """Provide tool access for information gathering"""
        tools = {}

        # News tool
        tools['news'] = await self._get_news_tool(game_context)

        # Weather tool
        tools['weather'] = await self._get_weather_tool(game_context)

        # Injury report tool
        tools['injuries'] = await self._get_injury_tool(game_context)

        # Betting lines tool
        tools['betting'] = await self._get_betting_tool(game_context)

        # Historical patterns tool
        tools['patterns'] = await self._get_pattern_tool(expert_id, game_context)

        # Log tool access
        for tool_type, data in tools.items():
            if data:
                self.supabase.table('expert_tool_access').insert({
                    'expert_id': expert_id,
                    'tool_type': tool_type,
                    'query': json.dumps(game_context),
                    'response': data,
                    'game_id': game_context.get('game_id')
                }).execute()

        return tools

    async def _get_news_tool(self, context: Dict) -> Dict:
        """Fetch recent news about teams"""
        # This would integrate with a real news API
        return {
            'headlines': [
                f"{context['home_team']} on winning streak",
                f"{context['away_team']} dealing with locker room issues"
            ],
            'sentiment': {'home': 0.7, 'away': 0.3}
        }

    async def _get_weather_tool(self, context: Dict) -> Dict:
        """Get weather forecast for game"""
        # This would integrate with a weather API
        return {
            'temperature': 45,
            'wind_speed': 12,
            'precipitation': 0.2,
            'conditions': 'Partly cloudy'
        }

    async def _get_injury_tool(self, context: Dict) -> Dict:
        """Get latest injury reports"""
        # This would integrate with injury report APIs
        return {
            context['home_team']: [],
            context['away_team']: ['WR1-Questionable', 'LB2-Doubtful']
        }

    async def _get_betting_tool(self, context: Dict) -> Dict:
        """Get current betting lines and movements"""
        # This would integrate with odds APIs
        return {
            'spread': -3.5,
            'total': 48.5,
            'moneyline': {'home': -165, 'away': +145},
            'public_percentage': {'home': 62, 'away': 38}
        }

    async def _get_pattern_tool(self, expert_id: str, context: Dict) -> Dict:
        """Find historical patterns for this matchup"""
        similar_games = await self.get_similar_games(expert_id, context, limit=5)

        if not similar_games:
            return {}

        # Analyze patterns from similar games
        patterns = {
            'avg_performance': np.mean([g.performance_score for g in similar_games
                                       if g.performance_score is not None]),
            'winning_factors': [],
            'losing_factors': []
        }

        for game in similar_games:
            if game.performance_score and game.performance_score > 0.7:
                patterns['winning_factors'].extend(game.prediction.get('key_factors', []))
            elif game.performance_score and game.performance_score < 0.3:
                patterns['losing_factors'].extend(game.prediction.get('key_factors', []))

        return patterns

    async def share_peer_learning(self, teacher_id: str, game_id: str):
        """Share successful predictions with other experts"""
        try:
            self.supabase.rpc('share_expert_success', {
                'p_teacher_id': teacher_id,
                'p_game_id': game_id
            }).execute()

            logger.info(f"🤝 Shared learning from {teacher_id} for game {game_id}")

        except Exception as e:
            logger.error(f"❌ Failed to share peer learning: {e}")

    async def _generate_embedding(self, data: Dict) -> np.ndarray:
        """Generate vector embedding for similarity search"""
        # This would use a real embedding model (e.g., OpenAI, Sentence Transformers)
        # For now, create a simple feature vector

        features = []

        # Team features
        features.append(hash(data.get('home_team', '')) % 100 / 100.0)
        features.append(hash(data.get('away_team', '')) % 100 / 100.0)

        # Context features
        if 'spread' in data:
            features.append((data['spread'] + 14) / 28.0)  # Normalize to 0-1
        if 'total' in data:
            features.append(data['total'] / 100.0)

        # Weather features
        if 'weather' in data:
            features.append(data['weather'].get('temperature', 60) / 100.0)
            features.append(data['weather'].get('wind_speed', 0) / 30.0)

        # Pad to 768 dimensions (standard embedding size)
        while len(features) < 768:
            features.append(0.0)

        return np.array(features[:768])

    async def _store_embeddings(self, memory_id: str, prediction: Dict, context: Dict):
        """Store vector embeddings for similarity search"""
        try:
            # Generate embeddings
            decision_embedding = await self._generate_embedding(prediction)
            context_embedding = await self._generate_embedding(context)

            # Update memory with embeddings
            self.supabase.table('expert_memory') \
                .update({
                    'decision_embedding': decision_embedding.tolist(),
                    'context_embedding': context_embedding.tolist()
                }) \
                .eq('id', memory_id) \
                .execute()

        except Exception as e:
            logger.error(f"❌ Failed to store embeddings: {e}")

    def get_expert_performance_stats(self, expert_id: str) -> Dict:
        """Get performance statistics for an expert"""
        try:
            # Get recent predictions
            result = self.supabase.table('expert_memory') \
                .select('performance_score') \
                .eq('expert_id', expert_id) \
                .not_.is_('performance_score', 'null') \
                .order('timestamp', desc=True) \
                .limit(100) \
                .execute()

            scores = [row['performance_score'] for row in result.data]

            if not scores:
                return {'games': 0, 'avg_score': 0.5, 'trend': 'stable'}

            stats = {
                'games': len(scores),
                'avg_score': np.mean(scores),
                'recent_avg': np.mean(scores[:10]) if len(scores) >= 10 else np.mean(scores),
                'best_score': max(scores),
                'worst_score': min(scores),
                'consistency': 1.0 - np.std(scores),
                'trend': 'improving' if len(scores) >= 10 and np.mean(scores[:5]) > np.mean(scores[5:10]) else 'stable'
            }

            return stats

        except Exception as e:
            logger.error(f"❌ Failed to get performance stats: {e}")
            return {}


# Create singleton instance
def create_memory_service(supabase_client):
    """Factory function to create memory service with Supabase client"""
    return ExpertMemoryService(supabase_client)