#!/usr/bin/env python3
"""
Enhanced Historical Training - Training Phase Coordination

Extends the existing train_expertal_game() method to integrate:
- Memory retrieval during prediction (currently missing)
- Post-game reflection system after outcomes
- Comprehensive predictions using available memories
- All 15 experts with sophisticated thinking process

This module coordinates the training phases as specified in requirements 7.2, 7.3, 7.4, 7.5
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import logging
from datetime import datetime, timedelta
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Initialize logger first
logger = logging.getLogger(__name__)

# Import dependencies with graceful handling
try:
    from supabase import create_client
except ImportError:
    create_client = None

try:
    from src.services.openrouter_service import OpenRouterService
except ImportError:
    OpenRouterService = None

try:
    from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
except ImportError:
    SupabaseEpisodicMemoryManager = None

try:
    from src.ml.training_loop_orchestrator import TrainingLoopOrchestrator
except ImportError:
    TrainingLoopOrchestrator = None

try:
    from src.ml.comprehensive_expert_predictions import GameContext, ComprehensiveExpertPrediction
except ImportError:
    GameContext = None
    ComprehensiveExpertPrediction = None

try:
    from src.ml.post_game_reflection_system import GameOutcome
except ImportError:
    GameOutcome = None
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class TrainingPhaseResult:
    """Result of a training phase execution"""
    phase_name: str
    expert_id: str
    game_id: str
    success: bool
    elapsed_time: float
    memories_retrieved: int = 0
    prediction_generated: bool = False
    reflection_completed: bool = False
    error_message: Optional[str] = None
    accuracy_scores: Dict[str, float] = None

class EnhancedHistoricalTrainer:
    """
    Enhanced version of the historical trainer that extends the existing
    train_expert_on_historical_game() method with comprehensive training phases.

    Key enhancements:
    - Memory retrieval during prediction (currently missing in original)
    - Post-game reflection system after outcomes
    - Comprehensive predictions using available memories
    - Integration with AIExpertOrchestrator for sophisticated thinking
    """

    def __init__(self):
        """Initialize enhanced trainer with all required services"""

        # Initialize core services (with graceful handling)
        if create_client:
            try:
                self.supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
            except Exception as e:
                logger.warning(f"Failed to create Supabase client: {e}")
                self.supabase = None
        else:
            self.supabase = None

        if OpenRouterService:
            try:
                self.openrouter = OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY'))
            except Exception as e:
                logger.warning(f"Failed to create OpenRouter service: {e}")
                self.openrouter = None
        else:
            self.openrouter = None

        if SupabaseEpisodicMemoryManager and self.supabase:
            try:
                self.memory_service = SupabaseEpisodicMemoryManager(self.supabase)
            except Exception as e:
                logger.warning(f"Failed to create memory service: {e}")
                self.memory_service = None
        else:
            self.memory_service = None

        # Initialize enhanced orchestrator
        if TrainingLoopOrchestrator:
            try:
                self.training_orchestrator = TrainingLoopOrchestrator()
            except Exception as e:
                logger.warning(f"Failed to create training orchestrator: {e}")
                self.training_orchestrator = None
        else:
            self.training_orchestrator = None

        # Reference existing memory storage structure (123 memories already stored)
        logger.info("🧠 Enhanced trainer initialized with existing memory structure")
        logger.info("📚 Will integrate memory retrieval during prediction phase")
        logger.info("💭 Will add post-game reflection after outcome phase")

    async def train_expert_on_historical_game_enhanced(self, expert_id: str, game: Dict[str, Any]) -> TrainingPhaseResult:
        """
        Enhanced version of train_expert_on_historical_game() that integrates:
        - Memory retrieval during prediction (currently missing)
        - Post-game reflection system after outcomes
        - Comprehensive predictions using available memories

        This extends the existing method while maintaining compatibility.

        Requirements: 7.2, 7.3, 7.4, 7.5
        """
        start_time = time.time()
        game_id = f"enhanced_{game['season']}_{game['week']}_{game['home_team']}_{game['away_team']}"

        logger.info(f"🎯 Enhanced training for {expert_id} on {game['away_team']} @ {game['home_team']}")

        try:
            # Phase 1: Expert Prediction Phase (with memory retrieval)
            logger.debug(f"📚 Phase 1: Expert prediction with memory retrieval")
            prediction_result = await self.expert_prediction_phase(expert_id, game)

            if not prediction_result['success']:
                return TrainingPhaseResult(
                    phase_name="prediction_phase",
                    expert_id=expert_id,
                    game_id=game_id,
                    success=False,
                    elapsed_time=time.time() - start_time,
                    error_message=prediction_result.get('error', 'Prediction phase failed')
                )

            # Phase 2: Outcome Learning Phase (post-game reflection)
            logger.debug(f"💭 Phase 2: Post-game reflection and learning")
            learning_result = await self.outcome_learning_phase(
                expert_id,
                prediction_result['prediction'],
                prediction_result['game_outcome']
            )

            elapsed_time = time.time() - start_time

            return TrainingPhaseResult(
                phase_name="complete_training",
                expert_id=expert_id,
                game_id=game_id,
                success=True,
                elapsed_time=elapsed_time,
                memories_retrieved=prediction_result.get('memories_used', 0),
                prediction_generated=prediction_result['success'],
                reflection_completed=learning_result['success'],
                accuracy_scores=learning_result.get('accuracy_scores', {}),
                error_message=None
            )

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Enhanced training failed for {expert_id}: {e}")

            return TrainingPhaseResult(
                phase_name="training_error",
                expert_id=expert_id,
                game_id=game_id,
                success=False,
                elapsed_time=elapsed_time,
                error_message=str(e)
            )

    async def expert_prediction_phase(self, expert_id: str, game: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive predictions using available memories.

        This method integrates memory retrieval during prediction, which was missing
        in the original training script. It creates the game context and uses the
        AIExpertOrchestrator for sophisticated thinking process.

        Requirements: 7.2, 7.3, 7.4, 7.5
        """
        logger.debug(f"🔮 Starting prediction phase for {expert_id}")

        try:
            # Create comprehensive game context
            game_context = self._create_enhanced_game_context(game)

            # Create game outcome for training (since we know the result)
            game_outcome = self._create_game_outcome_from_data(game)

            # Use training orchestrator for comprehensive prediction with memory retrieval
            prediction_result = await self.training_orchestrator.expert_prediction_phase(expert_id, game_context)

            if prediction_result['success']:
                logger.debug(f"✅ Prediction successful for {expert_id}: "
                           f"{prediction_result.get('memories_used', 0)} memories used, "
                           f"confidence: {prediction_result.get('confidence_overall', 0.5):.1%}")

                return {
                    'success': True,
                    'prediction': prediction_result['prediction'],
                    'game_context': game_context,
                    'game_outcome': game_outcome,
                    'memories_used': prediction_result.get('memories_used', 0),
                    'confidence_overall': prediction_result.get('confidence_overall', 0.5),
                    'elapsed_time': prediction_result.get('elapsed_time', 0.0)
                }
            else:
                logger.warning(f"⚠️ Prediction failed for {expert_id}: {prediction_result.get('error', 'unknown')}")
                return {
                    'success': False,
                    'error': prediction_result.get('error', 'Prediction generation failed'),
                    'game_context': game_context,
                    'game_outcome': game_outcome
                }

        except Exception as e:
            logger.error(f"❌ Prediction phase failed for {expert_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def outcome_learning_phase(self, expert_id: str, prediction: ComprehensiveExpertPrediction,
                                   outcome: GameOutcome) -> Dict[str, Any]:
        """
        Trigger post-game reflection after outcomes are known.

        This implements the outcome learning phase that triggers post-game reflection,
        which was missing in the original training script. It uses the existing
        memory storage structure (123 memories already stored).

        Requirements: 7.2, 7.3, 7.4, 7.5
        """
        logger.debug(f"💭 Starting outcome learning phase for {expert_id}")

        try:
            # Use training orchestrator for comprehensive post-game reflection
            learning_result = await self.training_orchestrator.outcome_learning_phase(expert_id, prediction, outcome)

            if learning_result['success']:
                reflection_memory = learning_result['reflection_memory']

                logger.debug(f"✅ Learning successful for {expert_id}: "
                           f"accuracy: {learning_result.get('overall_accuracy', 0.0):.1%}, "
                           f"lessons: {learning_result.get('lessons_count', 0)}")

                # Extract accuracy scores by category for tracking
                accuracy_scores = {}
                if hasattr(reflection_memory, 'category_accuracies'):
                    for cat_accuracy in reflection_memory.category_accuracies:
                        accuracy_scores[cat_accuracy.category_name] = cat_accuracy.accuracy_score

                return {
                    'success': True,
                    'reflection_memory': reflection_memory,
                    'overall_accuracy': learning_result.get('overall_accuracy', 0.0),
                    'lessons_learned': reflection_memory.lessons_learned if hasattr(reflection_memory, 'lessons_learned') else [],
                    'accuracy_scores': accuracy_scores,
                    'elapsed_time': learning_result.get('elapsed_time', 0.0)
                }
            else:
                logger.warning(f"⚠️ Learning failed for {expert_id}: {learning_result.get('error', 'unknown')}")
                return {
                    'success': False,
                    'error': learning_result.get('error', 'Post-game reflection failed')
                }

        except Exception as e:
            logger.error(f"❌ Outcome learning phase failed for {expert_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_enhanced_game_context(self, game: Dict[str, Any]) -> GameContext:
        """
        Create enhanced GameContext with comprehensive data.

        This extends the basic game context creation to include all available
        contextual information for sophisticated AI analysis.
        """
        return GameContext(
            home_team=game['home_team'],
            away_team=game['away_team'],
            season=game['season'],
            week=game.get('week', 1),
            game_date=datetime.fromisoformat(game['game_date'].replace('Z', '+00:00')) if game.get('game_date') else datetime.now(),

            # Environmental context
            weather_conditions=game.get('weather_description', 'Unknown'),
            stadium_info=game.get('stadium', 'Unknown'),

            # Team states (enhanced with available data)
            home_team_stats=self._extract_team_stats(game, 'home'),
            away_team_stats=self._extract_team_stats(game, 'away'),
            home_injuries=game.get('home_injuries', []),
            away_injuries=game.get('away_injuries', []),

            # Situational context (enhanced)
            is_divisional=self._determine_divisional_game(game),
            is_primetime=self._determine_primetime_game(game),
            playoff_implications=self._determine_playoff_implications(game),

            # Betting context
            opening_spread=game.get('spread_line', 0.0),
            current_spread=game.get('spread_line', 0.0),
            total_line=game.get('total_line', 45.5),
            public_betting_percentage=game.get('public_betting_percentage', 50.0)
        )

    def _create_game_outcome_from_data(self, game: Dict[str, Any]) -> GameOutcome:
        """
        Create GameOutcome from completed game data for training.

        This creates the outcome structure needed for post-game reflection.
        """
        return GameOutcome(
            game_id=f"{game['season']}_{game['week']}_{game['home_team']}_{game['away_team']}",
            home_team=game['home_team'],
            away_team=game['away_team'],
            home_score=game.get('home_score', 0),
            away_score=game.get('away_score', 0),

            # Quarter scores (if available)
            q1_home=game.get('q1_home', 0),
            q1_away=game.get('q1_away', 0),
            q2_home=game.get('q2_home', 0),
            q2_away=game.get('q2_away', 0),
            q3_home=game.get('q3_home', 0),
            q3_away=game.get('q3_away', 0),
            q4_home=game.get('q4_home', 0),
            q4_away=game.get('q4_away', 0),

            # Additional game stats
            turnover_differential=game.get('turnover_differential', 0),
            time_of_possession_home=game.get('time_of_possession_home', 30.0),
            penalties_home=game.get('penalties_home', 0),
            penalties_away=game.get('penalties_away', 0),

            # Player stats (if available)
            player_stats=game.get('player_stats', {})
        )

    def _extract_team_stats(self, game: Dict[str, Any], team_side: str) -> Dict[str, Any]:
        """Extract available team statistics from game data"""
        stats = {}

        # Basic team info
        team_name = game.get(f'{team_side}_team', '')
        stats['team_name'] = team_name

        # Season record (if available)
        stats['wins'] = game.get(f'{team_side}_wins', 0)
        stats['losses'] = game.get(f'{team_side}_losses', 0)

        # Recent performance (if available)
        stats['points_per_game'] = game.get(f'{team_side}_ppg', 0.0)
        stats['points_allowed_per_game'] = game.get(f'{team_side}_papg', 0.0)

        # Advanced stats (if available)
        stats['offensive_rating'] = game.get(f'{team_side}_off_rating', 0.0)
        stats['defensive_rating'] = game.get(f'{team_side}_def_rating', 0.0)

        return stats

    def _determine_divisional_game(self, game: Dict[str, Any]) -> bool:
        """Determine if this is a divisional matchup"""
        # This would need actual division data - for now return from game data or False
        return game.get('is_divisional', False)

    def _determine_primetime_game(self, game: Dict[str, Any]) -> bool:
        """Determine if this is a primetime game"""
        # Check game time or explicit flag
        if game.get('is_primetime'):
            return True

        # Check game date/time for primetime slots (simplified)
        game_date = game.get('game_date', '')
        if 'T20:' in game_date or 'T21:' in game_date:  # 8 PM or 9 PM starts
            return True

        return False

    def _determine_playoff_implications(self, game: Dict[str, Any]) -> bool:
        """Determine if this game has playoff implications"""
        # This would need season context - for now return from game data or check week
        if game.get('playoff_implications'):
            return True

        # Late season games likely have playoff implications
        week = game.get('week', 1)
        if week >= 15:  # Weeks 15+ often have playoff implications
            return True

        return False

    async def run_enhanced_training_batch(self, games: List[Dict[str, Any]], expert_ids: List[str]) -> Dict[str, Any]:
        """
        Run enhanced training on a batch of games with multiple experts.

        This method coordinates the training phases for multiple experts across
        multiple games, providing comprehensive training statistics.
        """
        logger.info(f"🚀 Starting enhanced training batch: {len(games)} games, {len(expert_ids)} experts")

        start_time = time.time()
        results = {
            'total_games': len(games),
            'total_experts': len(expert_ids),
            'expert_results': {},
            'game_results': {},
            'overall_stats': {
                'successful_predictions': 0,
                'successful_reflections': 0,
                'total_memories_used': 0,
                'total_accuracy_scores': [],
                'errors': []
            }
        }

        # Process each game
        for game_idx, game in enumerate(games, 1):
            game_id = f"{game['season']}_{game['week']}_{game['home_team']}_{game['away_team']}"
            logger.info(f"\\n📖 Processing game {game_idx}/{len(games)}: {game['away_team']} @ {game['home_team']}")

            game_results = []

            # Process each expert for this game
            for expert_id in expert_ids:
                try:
                    result = await self.train_expert_on_historical_game_enhanced(expert_id, game)
                    game_results.append(result)

                    # Update expert-specific results
                    if expert_id not in results['expert_results']:
                        results['expert_results'][expert_id] = {
                            'games_processed': 0,
                            'successful_predictions': 0,
                            'successful_reflections': 0,
                            'total_memories_used': 0,
                            'accuracy_scores': [],
                            'errors': []
                        }

                    expert_stats = results['expert_results'][expert_id]
                    expert_stats['games_processed'] += 1

                    if result.success:
                        if result.prediction_generated:
                            expert_stats['successful_predictions'] += 1
                            results['overall_stats']['successful_predictions'] += 1

                        if result.reflection_completed:
                            expert_stats['successful_reflections'] += 1
                            results['overall_stats']['successful_reflections'] += 1

                        expert_stats['total_memories_used'] += result.memories_retrieved
                        results['overall_stats']['total_memories_used'] += result.memories_retrieved

                        if result.accuracy_scores:
                            for category, score in result.accuracy_scores.items():
                                expert_stats['accuracy_scores'].append(score)
                                results['overall_stats']['total_accuracy_scores'].append(score)
                    else:
                        expert_stats['errors'].append(result.error_message)
                        results['overall_stats']['errors'].append({
                            'expert_id': expert_id,
                            'game_id': game_id,
                            'error': result.error_message
                        })

                except Exception as e:
                    logger.error(f"❌ Failed to process {expert_id} for game {game_id}: {e}")
                    results['overall_stats']['errors'].append({
                        'expert_id': expert_id,
                        'game_id': game_id,
                        'error': str(e)
                    })

            results['game_results'][game_id] = game_results

            # Brief pause between games
            await asyncio.sleep(0.5)

        # Calculate final statistics
        elapsed_time = time.time() - start_time
        total_operations = len(games) * len(expert_ids)

        results['summary'] = {
            'elapsed_time_minutes': elapsed_time / 60,
            'total_operations': total_operations,
            'success_rate_predictions': (
                results['overall_stats']['successful_predictions'] / max(1, total_operations)
            ),
            'success_rate_reflections': (
                results['overall_stats']['successful_reflections'] / max(1, total_operations)
            ),
            'average_accuracy': (
                sum(results['overall_stats']['total_accuracy_scores']) /
                max(1, len(results['overall_stats']['total_accuracy_scores']))
            ),
            'error_rate': len(results['overall_stats']['errors']) / max(1, total_operations)
        }

        logger.info(f"\\n✅ Enhanced training batch complete!")
        logger.info(f"   ⏱️  Time: {elapsed_time/60:.1f} minutes")
        logger.info(f"   🎯 Prediction Success: {results['summary']['success_rate_predictions']:.1%}")
        logger.info(f"   💭 Reflection Success: {results['summary']['success_rate_reflections']:.1%}")
        logger.info(f"   📊 Average Accuracy: {results['summary']['average_accuracy']:.1%}")
        logger.info(f"   🧠 Total Memories Used: {results['overall_stats']['total_memories_used']}")

        return results

# Example usage and testing
async def main():
    """Example usage of the enhanced historical trainer"""

    # Initialize enhanced trainer
    trainer = EnhancedHistoricalTrainer()

    # Test with a small batch of games
    try:
        # Fetch a few test games
        supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
        response = supabase.table('nfl_games').select('*').eq('season', 2020).not_.is_(
            'home_score', 'null'
        ).limit(3).execute()

        test_games = response.data
        test_experts = ['conservative_analyzer', 'risk_taking_gambler', 'contrarian_rebel']

        if test_games:
            logger.info(f"🧪 Testing enhanced training with {len(test_games)} games and {len(test_experts)} experts")

            results = await trainer.run_enhanced_training_batch(test_games, test_experts)

            print("\\n🎉 Enhanced training test completed!")
            print(f"📊 Results Summary:")
            print(f"   Prediction Success Rate: {results['summary']['success_rate_predictions']:.1%}")
            print(f"   Reflection Success Rate: {results['summary']['success_rate_reflections']:.1%}")
            print(f"   Average Accuracy: {results['summary']['average_accuracy']:.1%}")
            print(f"   Total Memories Used: {results['overall_stats']['total_memories_used']}")
        else:
            print("⚠️ No test games found")

    except Exception as e:
        print(f"❌ Enhanced training test failed: {e}")
        raise

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Run the test
    asyncio.run(main())
