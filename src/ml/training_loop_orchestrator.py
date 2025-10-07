#!/usr/bin/env python3
"""
Training Loop Orchestrator - Comprehensive Traiystem

Extends the existing historical_training_2020_2023.py to support all 15 experts
with comprehensive predictions (30+ categories) instead of basic win/loss.

Integrates:
- AIExpertOrchestrator for sophisticated thinking process
- All 15 experts from src/ml/expert_models/__init__.py EXPERT_MODELS
- Comprehensive predictions across all categories
- Training progress tracking and statistics
- Memory retrieval during prediction
- Post-game reflection system after outcomes

Requirements: 7.1, 7.2, 7.5, 7.6
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
from dataclasses import dataclass, field
from enum import Enum

# Initialize logger first
logger = logging.getLogger(__name__)

# Import Supabase with graceful handling
try:
    from supabase import create_client
except ImportError:
    logger.warning("Supabase client not available")
    create_client = None
# Import services with graceful handling of missing dependencies
try:
    from src.services.openrouter_service import OpenRouterService
except ImportError:
    logger.warning("OpenRouterService not available")
    OpenRouterService = None

try:
    from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
except ImportError:
    logger.warning("SupabaseEpisodicMemoryManager not available")
    SupabaseEpisodicMemoryManager = None

try:
    from src.ml.ai_expert_orchestrator import AIExpertOrchestrator
except ImportError:
    logger.warning("AIExpertOrchestrator not available")
    AIExpertOrchestrator = None

try:
    from src.ml.post_game_reflection_system import PostGameReflectionOrchestrator, GameOutcome
except ImportError:
    logger.warning("PostGameReflectionOrchestrator not available")
    PostGameReflectionOrchestrator = None
    GameOutcome = None

try:
    from src.ml.comprehensive_expert_predictions import GameContext, ComprehensiveExpertPrediction
except ImportError:
    logger.warning("Comprehensive predictions not available")
    GameContext = None
    ComprehensiveExpertPrediction = None
# Import expert models with graceful handling of missing dependencies
try:
    from src.ml.expert_models import EXPERT_MODELS
except ImportError as e:
    logger.warning(f"Could not import EXPERT_MODELS: {e}")
    # Fallback: define the expert IDs directly
    EXPERT_MODELS = {
        'conservative_analyzer': None,
        'risk_taking_gambler': None,
        'contrarian_rebel': None,
        'value_hunter': None,
        'momentum_rider': None,
        'fundamentalist_scholar': None,
        'chaos_theory_believer': None,
        'gut_instinct_expert': None,
        'statistics_purist': None,
        'trend_reversal_specialist': None,
        'popular_narrative_fader': None,
        'sharp_money_follower': None,
        'underdog_champion': None,
        'consensus_follower': None,
        'market_inefficiency_exploiter': None,
    }
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TrainingPhase(Enum):
    """Training phases"""
    INITIALIZATION = "initialization"
    HISTORICAL_TRAINING = "historical_training"
    PREDICTION_TESTING = "prediction_testing"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPLETION = "completion"

@dataclass
class TrainingStats:
    """Comprehensive training statistics"""
    # Basic counts
    training_games_processed: int = 0
    test_games_processed: int = 0
    total_predictions_made: int = 0
    total_memories_created: int = 0
    total_reflections_generated: int = 0

    # Expert performance
    expert_accuracies: Dict[str, Dict[str, float]] = field(default_factory=dict)
    expert_prediction_counts: Dict[str, int] = field(default_factory=dict)
    expert_memory_counts: Dict[str, int] = field(default_factory=dict)

    # Category performance
    category_accuracies: Dict[str, List[float]] = field(default_factory=dict)

    # Timing and performance
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    total_api_calls: int = 0
    total_api_time: float = 0.0
    average_prediction_time: float = 0.0

    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    failed_predictions: int = 0
    failed_reflections: int = 0

    # Progress tracking
    current_phase: TrainingPhase = TrainingPhase.INITIALIZATION
    games_by_season: Dict[int, int] = field(default_factory=dict)

    def add_expert_accuracy(self, expert_id: str, category: str, accuracy: float):
        """Add accuracy score for expert in specific category"""
        if expert_id not in self.expert_accuracies:
            self.expert_accuracies[expert_id] = {}
        if category not in self.expert_accuracies[expert_id]:
            self.expert_accuracies[expert_id][category] = []

        if isinstance(self.expert_accuracies[expert_id][category], list):
            self.expert_accuracies[expert_id][category].append(accuracy)
        else:
            self.expert_accuracies[expert_id][category] = [self.expert_accuracies[expert_id][category], accuracy]

    def get_expert_overall_accuracy(self, expert_id: str) -> float:
        """Calculate overall accuracy for an expert"""
        if expert_id not in self.expert_accuracies:
            return 0.0

        all_accuracies = []
        for category_scores in self.expert_accuracies[expert_id].values():
            if isinstance(category_scores, list):
                all_accuracies.extend(category_scores)
            else:
                all_accuracies.append(category_scores)

        return sum(all_accuracies) / len(all_accuracies) if all_accuracies else 0.0

    def get_elapsed_time(self) -> float:
        """Get elapsed training time"""
        if not self.start_time:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

class TrainingLoopOrchestrator:
    """
    Comprehensive training loop orchestrator that extends the existing training system
    to support all 15 experts with sophisticated AI thinking and comprehensive predictions.

    Key enhancements over historical_training_2020_2023.py:
    - All 15 experts instead of 5
    - Comprehensive predictions (30+ categories) instead of basic win/loss
    - Memory retrieval during prediction phase
    - Post-game reflection and learning after outcomes
    - Advanced training progress tracking and statistics
    """

    def __init__(self, supabase_url: str = None, supabase_key: str = None, openrouter_key: str = None):
        """Initialize the training orchestrator with all required services"""

        # Initialize database connection (with graceful handling)
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_ANON_KEY')

        if create_client and self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                logger.warning(f"Failed to create Supabase client: {e}")
                self.supabase = None
        else:
            logger.warning("Supabase client not available or credentials missing")
            self.supabase = None

        # Initialize AI services (with graceful handling)
        self.openrouter_key = openrouter_key or os.getenv('VITE_OPENROUTER_API_KEY') or os.getenv('OPENROUTER_API_KEY')

        if OpenRouterService and self.openrouter_key:
            try:
                self.openrouter = OpenRouterService(self.openrouter_key)
            except Exception as e:
                logger.warning(f"Failed to create OpenRouter service: {e}")
                self.openrouter = None
        else:
            logger.warning("OpenRouter service not available or key missing")
            self.openrouter = None

        # Initialize core services (with graceful handling)
        if SupabaseEpisodicMemoryManager and self.supabase:
            try:
                self.memory_service = SupabaseEpisodicMemoryManager(self.supabase)
            except Exception as e:
                logger.warning(f"Failed to create memory service: {e}")
                self.memory_service = None
        else:
            self.memory_service = None

        if AIExpertOrchestrator and self.supabase:
            try:
                self.ai_orchestrator = AIExpertOrchestrator(self.supabase, self.openrouter)
            except Exception as e:
                logger.warning(f"Failed to create AI orchestrator: {e}")
                self.ai_orchestrator = None
        else:
            self.ai_orchestrator = None

        if PostGameReflectionOrchestrator and self.openrouter and self.memory_service:
            try:
                self.reflection_orchestrator = PostGameReflectionOrchestrator(self.openrouter, self.memory_service)
            except Exception as e:
                logger.warning(f"Failed to create reflection orchestrator: {e}")
                self.reflection_orchestrator = None
        else:
            self.reflection_orchestrator = None

        # All 15 experts from expert_models
        self.all_expert_ids = list(EXPERT_MODELS.keys())
        logger.info(f"🎯 Initialized training for {len(self.all_expert_ids)} experts: {', '.join(self.all_expert_ids)}")

        # Enhanced expert model mapping (extends existing 5 to all 15)
        self.expert_model_mapping = {
            # Original 5 experts from historical_training_2020_2023.py
            'conservative_analyzer': {
                'name': 'The Analyst',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Conservative, methodical, data-driven analysis',
                'specialty': 'Risk-averse predictions with statistical backing'
            },
            'risk_taking_gambler': {
                'name': 'The Gambler',
                'model': 'x-ai/grok-4-fast',
                'personality': 'Bold, high-risk, high-reward mentality',
                'specialty': 'Aggressive betting strategies and upset picks'
            },
            'contrarian_rebel': {
                'name': 'The Rebel',
                'model': 'google/gemini-2.5-flash-preview-09-2025',
                'personality': 'Goes against popular opinion and conventional wisdom',
                'specialty': 'Contrarian plays and market inefficiencies'
            },
            'value_hunter': {
                'name': 'The Hunter',
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'personality': 'Seeks undervalued opportunities and hidden gems',
                'specialty': 'Finding value in overlooked situations'
            },
            'momentum_rider': {
                'name': 'The Rider',
                'model': 'openai/gpt-5',
                'personality': 'Follows trends and momentum patterns',
                'specialty': 'Momentum-based predictions and trend analysis'
            },

            # Additional 10 experts to complete the 15-expert council
            'fundamentalist_scholar': {
                'name': 'The Scholar',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Deep statistical analysis and historical patterns',
                'specialty': 'Fundamental analysis and long-term trends'
            },
            'chaos_theory_believer': {
                'name': 'The Chaos',
                'model': 'x-ai/grok-4-fast',
                'personality': 'Embraces unpredictability and random events',
                'specialty': 'Chaos theory and unexpected outcomes'
            },
            'gut_instinct_expert': {
                'name': 'The Intuition',
                'model': 'openai/gpt-5',
                'personality': 'Relies on intuition and feel for the game',
                'specialty': 'Intuitive analysis and gut feelings'
            },
            'statistics_purist': {
                'name': 'The Quant',
                'model': 'google/gemini-2.5-flash-preview-09-2025',
                'personality': 'Pure statistical analysis and mathematical models',
                'specialty': 'Quantitative analysis and statistical modeling'
            },
            'trend_reversal_specialist': {
                'name': 'The Reversal',
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'personality': 'Identifies trend reversals and inflection points',
                'specialty': 'Trend reversal analysis and timing'
            },
            'popular_narrative_fader': {
                'name': 'The Fader',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Fades popular narratives and media hype',
                'specialty': 'Anti-narrative analysis and media fade'
            },
            'sharp_money_follower': {
                'name': 'The Sharp',
                'model': 'openai/gpt-5',
                'personality': 'Follows professional betting patterns',
                'specialty': 'Sharp money analysis and line movement'
            },
            'underdog_champion': {
                'name': 'The Underdog',
                'model': 'x-ai/grok-4-fast',
                'personality': 'Champions underdogs and upset potential',
                'specialty': 'Underdog analysis and upset predictions'
            },
            'consensus_follower': {
                'name': 'The Consensus',
                'model': 'google/gemini-2.5-flash-preview-09-2025',
                'personality': 'Follows consensus and popular opinion',
                'specialty': 'Consensus analysis and market following'
            },
            'market_inefficiency_exploiter': {
                'name': 'The Exploiter',
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'personality': 'Exploits market inefficiencies and pricing errors',
                'specialty': 'Market inefficiency analysis and arbitrage'
            }
        }

        # Training statistics
        self.training_stats = TrainingStats()

        # Configuration
        self.max_concurrent_experts = 5  # Limit concurrent API calls
        self.prediction_timeout = 60  # Seconds per expert prediction
        self.reflection_timeout = 45  # Seconds per expert reflection

    async def train_on_historical_data(self, start_season: int = 2020, end_season: int = 2023,
                                     games_per_season: int = 50, test_season: int = 2024,
                                     test_games: int = 20) -> TrainingStats:
        """
        Main training method that processes historical games chronologically
        to build realistic memory patterns and learning trajectories.

        Requirements: 7.1, 7.2, 7.5, 7.6

        Args:
            start_season: First season for training data
            end_season: Last season for training data
            games_per_season: Number of games to process per season
            test_season: Season to use for testing predictions
            test_games: Number of test games to process

        Returns:
            TrainingStats with comprehensive training results
        """
        logger.info("🚀 STARTING COMPREHENSIVE TRAINING LOOP ORCHESTRATOR")
        logger.info("=" * 80)
        logger.info(f"📚 Training: {start_season}-{end_season} seasons ({games_per_season} games/season)")
        logger.info(f"🎯 Testing: {test_season} season ({test_games} games)")
        logger.info(f"👥 Experts: {len(self.all_expert_ids)} AI experts with comprehensive predictions")
        logger.info(f"🧠 Features: Memory retrieval + AI thinking + Post-game reflection")
        logger.info("=" * 80)

        self.training_stats.start_time = time.time()
        self.training_stats.current_phase = TrainingPhase.INITIALIZATION

        try:
            # Phase 1: Historical Training (2020-2023)
            logger.info("\\n📚 PHASE 1: HISTORICAL TRAINING WITH MEMORY BUILDING")
            logger.info("-" * 60)
            self.training_stats.current_phase = TrainingPhase.HISTORICAL_TRAINING

            for season in range(start_season, end_season + 1):
                logger.info(f"\\n🏈 Processing {season} season...")

                # Fetch games for this season
                training_games = await self.fetch_training_games(season, games_per_season)
                if not training_games:
                    logger.warning(f"⚠️ No training games found for {season}")
                    continue

                self.training_stats.games_by_season[season] = len(training_games)

                # Process games chronologically
                for i, game in enumerate(training_games, 1):
                    logger.info(f"\\n📖 Training game {i}/{len(training_games)}: "
                              f"{game['away_team']} @ {game['home_team']} ({season})")

                    await self.process_single_game(game, phase="training")

                    # Brief pause to avoid overwhelming APIs
                    await asyncio.sleep(0.5)

                logger.info(f"✅ Completed {season} season: {len(training_games)} games processed")

            # Phase 2: Prediction Testing (2024)
            logger.info("\\n\\n🎯 PHASE 2: PREDICTION TESTING WITH LEARNED MEMORIES")
            logger.info("-" * 60)
            self.training_stats.current_phase = TrainingPhase.PREDICTION_TESTING

            test_games_data = await self.fetch_test_games(test_season, test_games)
            if test_games_data:
                for i, game in enumerate(test_games_data, 1):
                    logger.info(f"\\n🎯 Test game {i}/{len(test_games_data)}: "
                              f"{game['away_team']} @ {game['home_team']} ({test_season})")

                    await self.process_single_game(game, phase="testing")

                    # Brief pause
                    await asyncio.sleep(0.5)

            # Phase 3: Performance Analysis
            logger.info("\\n\\n📊 PHASE 3: PERFORMANCE ANALYSIS AND REPORTING")
            logger.info("-" * 60)
            self.training_stats.current_phase = TrainingPhase.PERFORMANCE_ANALYSIS

            training_report = await self.generate_training_report()

            # Phase 4: Completion
            self.training_stats.current_phase = TrainingPhase.COMPLETION
            self.training_stats.end_time = time.time()

            logger.info("\\n\\n🎉 COMPREHENSIVE TRAINING COMPLETE!")
            logger.info("=" * 80)
            logger.info(f"⏱️  Total Time: {self.training_stats.get_elapsed_time()/60:.1f} minutes")
            logger.info(f"📚 Training Games: {self.training_stats.training_games_processed}")
            logger.info(f"🎯 Test Games: {self.training_stats.test_games_processed}")
            logger.info(f"🔮 Total Predictions: {self.training_stats.total_predictions_made}")
            logger.info(f"🧠 Memories Created: {self.training_stats.total_memories_created}")
            logger.info(f"💭 Reflections Generated: {self.training_stats.total_reflections_generated}")
            logger.info("=" * 80)

            return self.training_stats

        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            self.training_stats.errors.append({
                'phase': self.training_stats.current_phase.value,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            raise

    async def fetch_training_games(self, season: int, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch completed games from specified season for training.

        Extends the existing fetch_training_games method to support single seasons
        and maintain chronological ordering.
        """
        try:
            logger.info(f"📚 Fetching {limit} training games from {season} season...")

            response = self.supabase.table('nfl_games').select('*').eq(
                'season', season
            ).not_.is_('home_score', 'null').not_.is_('away_score', 'null').order(
                'game_date', desc=False  # Chronological order
            ).limit(limit).execute()

            games = response.data
            logger.info(f"✅ Loaded {len(games)} training games from {season}")

            return games

        except Exception as e:
            logger.error(f"❌ Failed to fetch training games for {season}: {e}")
            return []

    async def fetch_test_games(self, season: int, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch completed games from specified season for testing predictions.

        Uses the same structure as existing fetch_test_games method.
        """
        try:
            logger.info(f"🎯 Fetching {limit} test games from {season} season...")

            response = self.supabase.table('nfl_games').select('*').eq(
                'season', season
            ).not_.is_('home_score', 'null').not_.is_('away_score', 'null').order(
                'game_date', desc=False
            ).limit(limit).execute()

            games = response.data
            logger.info(f"✅ Loaded {len(games)} test games from {season}")

            return games

        except Exception as e:
            logger.error(f"❌ Failed to fetch test games for {season}: {e}")
            return []

    async def process_single_game(self, game: Dict[str, Any], phase: str = "training") -> Dict[str, Any]:
        """
        Process a single game with all 15 experts using comprehensive predictions.

        This method coordinates:
        1. Expert prediction phase (with memory retrieval)
        2. Outcome learning phase (with post-game reflection)

        Requirements: 7.2, 7.3, 7.4, 7.5
        """
        game_id = f"{phase}_{game['season']}_{game['week']}_{game['home_team']}_{game['away_team']}"

        try:
            # Create game context for comprehensive analysis
            game_context = self._create_game_context(game)

            # Create game outcome for reflection (if training phase)
            game_outcome = self._create_game_outcome(game) if phase == "training" else None

            # Process all experts for this game
            expert_results = []

            # Process experts in batches to manage API load
            expert_batches = [self.all_expert_ids[i:i + self.max_concurrent_experts]
                            for i in range(0, len(self.all_expert_ids), self.max_concurrent_experts)]

            for batch_num, expert_batch in enumerate(expert_batches, 1):
                logger.info(f"   Processing expert batch {batch_num}/{len(expert_batches)}: "
                          f"{', '.join([self.expert_model_mapping[eid]['name'] for eid in expert_batch])}")

                # Process experts in this batch concurrently
                batch_tasks = []
                for expert_id in expert_batch:
                    if phase == "training":
                        task = self.expert_prediction_phase(expert_id, game_context)
                    else:
                        task = self.expert_prediction_phase(expert_id, game_context)
                    batch_tasks.append(task)

                # Wait for batch completion
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Process results and handle post-game learning for training phase
                for expert_id, result in zip(expert_batch, batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"❌ Expert {expert_id} failed: {result}")
                        self.training_stats.failed_predictions += 1
                        continue

                    expert_results.append(result)

                    # Post-game reflection for training phase
                    if phase == "training" and game_outcome and result.get('prediction'):
                        try:
                            await self.outcome_learning_phase(expert_id, result['prediction'], game_outcome)
                        except Exception as e:
                            logger.error(f"❌ Reflection failed for {expert_id}: {e}")
                            self.training_stats.failed_reflections += 1

                # Brief pause between batches
                await asyncio.sleep(1.0)

            # Update statistics
            if phase == "training":
                self.training_stats.training_games_processed += 1
            else:
                self.training_stats.test_games_processed += 1

            successful_predictions = len([r for r in expert_results if r.get('success', False)])
            self.training_stats.total_predictions_made += successful_predictions

            logger.info(f"   ✅ Game processed: {successful_predictions}/{len(self.all_expert_ids)} experts successful")

            return {
                'game_id': game_id,
                'phase': phase,
                'expert_results': expert_results,
                'successful_predictions': successful_predictions,
                'total_experts': len(self.all_expert_ids)
            }

        except Exception as e:
            logger.error(f"❌ Failed to process game {game_id}: {e}")
            self.training_stats.errors.append({
                'game_id': game_id,
                'phase': phase,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            raise

    def _create_game_context(self, game: Dict[str, Any]) -> GameContext:
        """Create GameContext object from game data"""
        return GameContext(
            home_team=game['home_team'],
            away_team=game['away_team'],
            season=game['season'],
            week=game.get('week', 1),
            game_date=datetime.fromisoformat(game['game_date'].replace('Z', '+00:00')) if game.get('game_date') else datetime.now(),

            # Environmental data (with defaults)
            weather_conditions=game.get('weather_description', 'Unknown'),
            stadium_info=game.get('stadium', 'Unknown'),

            # Team states (simplified for now)
            home_team_stats={},
            away_team_stats={},
            home_injuries=[],
            away_injuries=[],

            # Situational context
            is_divisional=game.get('is_divisional', False),
            is_primetime=game.get('is_primetime', False),
            playoff_implications=game.get('playoff_implications', False),

            # Betting context
            opening_spread=game.get('spread_line', 0.0),
            current_spread=game.get('spread_line', 0.0),
            total_line=game.get('total_line', 45.5),
            public_betting_percentage=game.get('public_betting_percentage', 50.0)
        )

    def _create_game_outcome(self, game: Dict[str, Any]) -> GameOutcome:
        """Create GameOutcome object from completed game data"""
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

            # Calculated fields will be set by __post_init__
        )
    async def expert_prediction_phase(self, expert_id: str, game_context: GameContext) -> Dict[str, Any]:
        """
        Generate comprehensive predictiing available memories.

        This method integrates memory retrieval during prediction, which was missing
        in the original training script. Uses AIExpertOrchestrator for sophisticated
        thinking process.

        Requirements: 7.2, 7.3, 7.4, 7.5
        """
        start_time = time.time()
        expert_config = self.expert_model_mapping.get(expert_id, {})
        expert_name = expert_config.get('name', expert_id)

        try:
            logger.debug(f"🔮 {expert_name}: Starting prediction with memory retrieval")

            # Use AIExpertOrchestrator for comprehensive analysis with memory integration
            prediction = await asyncio.wait_for(
                self.ai_orchestrator.analyze_game(expert_id, game_context),
                timeout=self.prediction_timeout
            )

            elapsed_time = time.time() - start_time
            self.training_stats.total_api_calls += 1
            self.training_stats.total_api_time += elapsed_time

            # Update expert statistics
            if expert_id not in self.training_stats.expert_prediction_counts:
                self.training_stats.expert_prediction_counts[expert_id] = 0
            self.training_stats.expert_prediction_counts[expert_id] += 1

            logger.debug(f"✅ {expert_name}: Prediction complete in {elapsed_time:.2f}s")

            return {
                'expert_id': expert_id,
                'expert_name': expert_name,
                'prediction': prediction,
                'success': True,
                'elapsed_time': elapsed_time,
                'memories_used': len(prediction.memory_influences),
                'confidence_overall': prediction.confidence_distribution.get('overall', 0.5)
            }

        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            logger.warning(f"⏰ {expert_name}: Prediction timeout after {elapsed_time:.2f}s")
            return {
                'expert_id': expert_id,
                'expert_name': expert_name,
                'success': False,
                'error': 'timeout',
                'elapsed_time': elapsed_time
            }

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ {expert_name}: Prediction failed after {elapsed_time:.2f}s: {e}")
            return {
                'expert_id': expert_id,
                'expert_name': expert_name,
                'success': False,
                'error': str(e),
                'elapsed_time': elapsed_time
            }

    async def outcome_learning_phase(self, expert_id: str, prediction: ComprehensiveExpertPrediction,
                                   outcome: GameOutcome) -> Dict[str, Any]:
        """
        Trigger post-game reflection after outcomes are known.

        This integrates the post-game reflection system after outcomes, which was
        missing in the original training script. Creates learning memories for
        future improvement.

        Requirements: 7.2, 7.3, 7.4, 7.5
        """
        start_time = time.time()
        expert_config = self.expert_model_mapping.get(expert_id, {})
        expert_name = expert_config.get('name', expert_id)

        try:
            logger.debug(f"💭 {expert_name}: Starting post-game reflection")

            # Use PostGameReflectionOrchestrator for comprehensive learning
            reflection_memory = await asyncio.wait_for(
                self.reflection_orchestrator.post_game_reflection(expert_id, prediction, outcome),
                timeout=self.reflection_timeout
            )

            # Store reflection memory using existing memory service
            memory_data = {
                'memory_type': 'post_game_reflection',
                'reflection_type': reflection_memory.reflection_type.value,
                'overall_accuracy': reflection_memory.overall_accuracy,
                'lessons_learned': reflection_memory.lessons_learned,
                'pattern_insights': reflection_memory.pattern_insights,
                'factor_adjustments': reflection_memory.factor_adjustments,
                'confidence_calibration': reflection_memory.confidence_calibration,
                'emotional_intensity': reflection_memory.emotional_intensity,
                'surprise_factor': reflection_memory.surprise_factor,
                'memory_vividness': reflection_memory.memory_vividness,
                'ai_reflection_text': reflection_memory.ai_reflection_text,
                'contextual_factors': [
                    {'factor': 'home_team', 'value': outcome.home_team},
                    {'factor': 'away_team', 'value': outcome.away_team},
                    {'factor': 'final_score', 'value': f"{outcome.home_score}-{outcome.away_score}"},
                    {'factor': 'winner', 'value': outcome.winner},
                    {'factor': 'margin', 'value': outcome.margin_of_victory}
                ]
            }

            await self.memory_service.store_memory(expert_id, outcome.game_id, memory_data)

            elapsed_time = time.time() - start_time

            # Update statistics
            self.training_stats.total_reflections_generated += 1
            self.training_stats.total_memories_created += 1

            if expert_id not in self.training_stats.expert_memory_counts:
                self.training_stats.expert_memory_counts[expert_id] = 0
            self.training_stats.expert_memory_counts[expert_id] += 1

            # Track accuracy by category
            for category_accuracy in reflection_memory.category_accuracies:
                category_name = category_accuracy.category_name
                accuracy_score = category_accuracy.accuracy_score

                if category_name not in self.training_stats.category_accuracies:
                    self.training_stats.category_accuracies[category_name] = []
                self.training_stats.category_accuracies[category_name].append(accuracy_score)

                # Track expert-specific accuracy
                self.training_stats.add_expert_accuracy(expert_id, category_name, accuracy_score)

            logger.debug(f"✅ {expert_name}: Reflection complete in {elapsed_time:.2f}s "
                        f"(accuracy: {reflection_memory.overall_accuracy:.1%})")

            return {
                'expert_id': expert_id,
                'expert_name': expert_name,
                'reflection_memory': reflection_memory,
                'success': True,
                'elapsed_time': elapsed_time,
                'overall_accuracy': reflection_memory.overall_accuracy,
                'lessons_count': len(reflection_memory.lessons_learned)
            }

        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            logger.warning(f"⏰ {expert_name}: Reflection timeout after {elapsed_time:.2f}s")
            return {
                'expert_id': expert_id,
                'expert_name': expert_name,
                'success': False,
                'error': 'timeout',
                'elapsed_time': elapsed_time
            }

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ {expert_name}: Reflection failed after {elapsed_time:.2f}s: {e}")
            return {
                'expert_id': expert_id,
                'expert_name': expert_name,
                'success': False,
                'error': str(e),
                'elapsed_time': elapsed_time
            }

    async def generate_training_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive training report with expert development metrics.

        Extends existing training_stats tracking with advanced performance analysis,
        accuracy trends, and expert development insights.

        Requirements: 7.6, 10.1, 10.2, 10.6
        """
        logger.info("📊 Generating comprehensive training report...")

        try:
            # Calculate overall statistics
            total_time = self.training_stats.get_elapsed_time()
            avg_prediction_time = (self.training_stats.total_api_time /
                                 max(1, self.training_stats.total_api_calls))

            # Expert performance analysis
            expert_performance = {}
            for expert_id in self.all_expert_ids:
                expert_config = self.expert_model_mapping.get(expert_id, {})
                expert_name = expert_config.get('name', expert_id)

                overall_accuracy = self.training_stats.get_expert_overall_accuracy(expert_id)
                prediction_count = self.training_stats.expert_prediction_counts.get(expert_id, 0)
                memory_count = self.training_stats.expert_memory_counts.get(expert_id, 0)

                expert_performance[expert_id] = {
                    'name': expert_name,
                    'model': expert_config.get('model', 'unknown'),
                    'specialty': expert_config.get('specialty', 'unknown'),
                    'overall_accuracy': overall_accuracy,
                    'predictions_made': prediction_count,
                    'memories_created': memory_count,
                    'category_accuracies': self.training_stats.expert_accuracies.get(expert_id, {})
                }

            # Category performance analysis
            category_performance = {}
            for category, accuracies in self.training_stats.category_accuracies.items():
                if accuracies:
                    category_performance[category] = {
                        'average_accuracy': sum(accuracies) / len(accuracies),
                        'best_accuracy': max(accuracies),
                        'worst_accuracy': min(accuracies),
                        'total_predictions': len(accuracies),
                        'accuracy_trend': self._calculate_accuracy_trend(accuracies)
                    }

            # System performance metrics
            system_performance = {
                'total_training_time_minutes': total_time / 60,
                'average_prediction_time_seconds': avg_prediction_time,
                'total_api_calls': self.training_stats.total_api_calls,
                'api_calls_per_minute': self.training_stats.total_api_calls / max(1, total_time / 60),
                'success_rate_predictions': (
                    (self.training_stats.total_predictions_made /
                     max(1, self.training_stats.total_predictions_made + self.training_stats.failed_predictions))
                ),
                'success_rate_reflections': (
                    (self.training_stats.total_reflections_generated /
                     max(1, self.training_stats.total_reflections_generated + self.training_stats.failed_reflections))
                )
            }

            # Training progression analysis
            training_progression = {
                'games_by_season': self.training_stats.games_by_season,
                'total_training_games': self.training_stats.training_games_processed,
                'total_test_games': self.training_stats.test_games_processed,
                'memories_per_expert': (
                    self.training_stats.total_memories_created / max(1, len(self.all_expert_ids))
                ),
                'predictions_per_expert': (
                    self.training_stats.total_predictions_made / max(1, len(self.all_expert_ids))
                )
            }

            # Error analysis
            error_analysis = {
                'total_errors': len(self.training_stats.errors),
                'failed_predictions': self.training_stats.failed_predictions,
                'failed_reflections': self.training_stats.failed_reflections,
                'error_types': self._analyze_error_types(),
                'error_rate': len(self.training_stats.errors) / max(1, self.training_stats.total_api_calls)
            }

            # Create comprehensive report
            training_report = {
                'report_timestamp': datetime.now().isoformat(),
                'training_summary': {
                    'start_time': datetime.fromtimestamp(self.training_stats.start_time).isoformat(),
                    'end_time': datetime.fromtimestamp(self.training_stats.end_time).isoformat() if self.training_stats.end_time else None,
                    'total_duration_minutes': total_time / 60,
                    'current_phase': self.training_stats.current_phase.value
                },
                'expert_performance': expert_performance,
                'category_performance': category_performance,
                'system_performance': system_performance,
                'training_progression': training_progression,
                'error_analysis': error_analysis,
                'top_performers': self._identify_top_performers(expert_performance),
                'improvement_recommendations': self._generate_improvement_recommendations(expert_performance, category_performance)
            }

            # Log key insights
            logger.info("📊 TRAINING REPORT SUMMARY:")
            logger.info(f"   ⏱️  Total Time: {total_time/60:.1f} minutes")
            logger.info(f"   🎯 Success Rate: {system_performance['success_rate_predictions']:.1%}")
            logger.info(f"   📈 Avg Prediction Time: {avg_prediction_time:.2f}s")
            logger.info(f"   🧠 Total Memories: {self.training_stats.total_memories_created}")

            # Log top performers
            top_performers = training_report['top_performers']
            if top_performers:
                logger.info("   🏆 Top Performers:")
                for i, (expert_id, performance) in enumerate(top_performers[:3], 1):
                    logger.info(f"      {i}. {performance['name']}: {performance['overall_accuracy']:.1%}")

            return training_report

        except Exception as e:
            logger.error(f"❌ Failed to generate training report: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'partial_stats': self.training_stats.__dict__
            }

    def _calculate_accuracy_trend(self, accuracies: List[float]) -> str:
        """Calculate accuracy trend (improving, declining, stable)"""
        if len(accuracies) < 3:
            return "insufficient_data"

        # Compare first third vs last third
        first_third = accuracies[:len(accuracies)//3]
        last_third = accuracies[-len(accuracies)//3:]

        first_avg = sum(first_third) / len(first_third)
        last_avg = sum(last_third) / len(last_third)

        diff = last_avg - first_avg

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    def _analyze_error_types(self) -> Dict[str, int]:
        """Analyze types of errors encountered during training"""
        error_types = {}

        for error in self.training_stats.errors:
            error_msg = error.get('error', '').lower()

            if 'timeout' in error_msg:
                error_types['timeout'] = error_types.get('timeout', 0) + 1
            elif 'api' in error_msg or 'rate limit' in error_msg:
                error_types['api_error'] = error_types.get('api_error', 0) + 1
            elif 'memory' in error_msg:
                error_types['memory_error'] = error_types.get('memory_error', 0) + 1
            elif 'parsing' in error_msg:
                error_types['parsing_error'] = error_types.get('parsing_error', 0) + 1
            else:
                error_types['other'] = error_types.get('other', 0) + 1

        return error_types

    def _identify_top_performers(self, expert_performance: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """Identify top performing experts by overall accuracy"""
        performers = [(expert_id, perf) for expert_id, perf in expert_performance.items()
                     if perf['predictions_made'] > 0]

        # Sort by overall accuracy
        performers.sort(key=lambda x: x[1]['overall_accuracy'], reverse=True)

        return performers

    def _generate_improvement_recommendations(self, expert_performance: Dict[str, Any],
                                           category_performance: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving training performance"""
        recommendations = []

        # Analyze expert performance
        low_performers = [expert_id for expert_id, perf in expert_performance.items()
                         if perf['overall_accuracy'] < 0.5 and perf['predictions_made'] > 5]

        if low_performers:
            recommendations.append(f"Consider adjusting prompts or models for low-performing experts: {', '.join(low_performers)}")

        # Analyze category performance
        difficult_categories = [category for category, perf in category_performance.items()
                              if perf['average_accuracy'] < 0.4 and perf['total_predictions'] > 10]

        if difficult_categories:
            recommendations.append(f"Focus on improving prediction accuracy for: {', '.join(difficult_categories)}")

        # System performance recommendations
        if self.training_stats.total_api_time / max(1, self.training_stats.total_api_calls) > 10:
            recommendations.append("Consider optimizing API calls or increasing timeout limits")

        if len(self.training_stats.errors) / max(1, self.training_stats.total_api_calls) > 0.1:
            recommendations.append("High error rate detected - review error logs and improve error handling")

        # Memory utilization recommendations
        avg_memories_per_expert = self.training_stats.total_memories_created / max(1, len(self.all_expert_ids))
        if avg_memories_per_expert < 10:
            recommendations.append("Low memory creation rate - ensure post-game reflection is working properly")

        return recommendations

# Example usage and testing
async def main():
    """Example usage of the TrainingLoopOrchestrator"""

    # Initialize orchestrator
    orchestrator = TrainingLoopOrchestrator()

    # Run comprehensive training
    try:
        training_results = await orchestrator.train_on_historical_data(
            start_season=2020,
            end_season=2021,  # Reduced for testing
            games_per_season=10,  # Reduced for testing
            test_season=2024,
            test_games=5  # Reduced for testing
        )

        print("\\n🎉 Training completed successfully!")
        print(f"📊 Final Statistics:")
        print(f"   Training Games: {training_results.training_games_processed}")
        print(f"   Test Games: {training_results.test_games_processed}")
        print(f"   Total Predictions: {training_results.total_predictions_made}")
        print(f"   Total Memories: {training_results.total_memories_created}")
        print(f"   Success Rate: {(training_results.total_predictions_made / max(1, training_results.total_predictions_made + training_results.failed_predictions)):.1%}")

    except Exception as e:
        print(f"❌ Training failed: {e}")
        raise

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Run the training
    asyncio.run(main())
