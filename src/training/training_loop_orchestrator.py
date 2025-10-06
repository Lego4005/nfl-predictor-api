#!/usr/bin/env python3
"""
Training Loop Orchestrator

Processes NFL games sequentially, generates predictions from all experts,
and manages expert state across games. Core component of the pragmatic training loop.
"""

import sys
import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
sys.path.append('src')

from training.nfl_data_loader import NFLDataLoader, GameContext
from training.expert_configuration import ExpertConfigurationManager, ExpertType
from training.prediction_generator import PredictionGenerator, PredictionType, GamePrediction
from training.real_llm_prediction_generator import RealLLMPredictionGenerator
from training.expert_learning_memory_system import ExpertLearningMemorySystem
from training.temporal_decay_calculator import TemporalDecayCalculator
from training.memory_retrieval_system import MemoryRetrievalSystem
from services.neo4j_knowledge_service import Neo4jKnowledgeService
from services.neo4j_ingestion_pipeline import Neo4jIngestionPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExpertState:
    """State tracking for individual experts"""
    expert_id: str
    expert_type: ExpertType
    games_processed: int = 0
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy: float = 0.0
    confidence_sum: float = 0.0
    avg_confidence: float = 0.0
    last_updated: Optional[datetime] = None

    def update_performance(self, prediction: GamePrediction, actual_result: Dict[str, Any], game: GameContext = None):
        """Update expert performance metrics"""
        self.games_processed += 1
        self.total_predictions += 1

        # Check if prediction was correct (simplified - just winner for now)
        home_score = actual_result.get('home_score', 0)
        away_score = actual_result.get('away_score', 0)

        actual_winner = 'home' if home_score > away_score else 'away'

        # Use the actual predicted_winner field instead of deriving from win_probability
        predicted_winner = None
        if prediction.predicted_winner and game:
            # Convert team name to home/away using actual game context
            if prediction.predicted_winner.upper() == game.home_team.upper():
                predicted_winner = 'home'
            elif prediction.predicted_winner.upper() == game.away_team.upper():
                predicted_winner = 'away'
            else:
                # Fallback to win_probability method
                predicted_winner = 'home' if prediction.win_probability and prediction.win_probability > 0.5 else 'away'
        else:
            # Fallback to win_probability method
            predicted_winner = 'home' if prediction.win_probability and prediction.win_probability > 0.5 else 'away'

        is_correct = (actual_winner == predicted_winner)
        if is_correct:
            self.correct_predictions += 1

        # Log the prediction evaluation for debugging
        logger.debug(f"🎯 {self.expert_id} prediction: {prediction.predicted_winner} -> {predicted_winner}, "
                    f"actual: {actual_winner}, correct: {is_correct}")

        if game:
            logger.debug(f"   Game: {game.away_team} @ {game.home_team}, Score: {away_score}-{home_score}")

        # Update accuracy
        self.accuracy = self.correct_predictions / self.total_predictions if self.total_predictions > 0 else 0.0

        # Update confidence tracking
        self.confidence_sum += prediction.confidence_level
        self.avg_confidence = self.confidence_sum / self.total_predictions

        self.last_updated = datetime.now()

@dataclass
class TrainingSession:
    """Training session metadata and results"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    season: int = 0
    games_processed: int = 0
    total_predictions: int = 0
    expert_states: Dict[str, ExpertState] = None

    def __post_init__(self):
        if self.expert_states is None:
            self.expert_states = {}

class TrainingLoopOrchestrator:
    """Orchestrates the training loop for expert learning"""

    def __init__(self, checkpoint_dir: str = "training_checkpoints"):
        """Initialize the training orchestrator"""
        self.data_loader = NFLDataLoader()
        self.config_manager = ExpertConfigurationManager()
        self.temporal_calculator = TemporalDecayCalculator(self.config_manager)
        self.learning_memory_system = ExpertLearningMemorySystem(self.config_manager)
        self.memory_retrieval = MemoryRetrievalSystem(self.config_manager, self.temporal_calculator, self.learning_memory_system)
        # Use real LLM prediction generator instead of simulation
        self.real_prediction_generator = RealLLMPredictionGenerator(self.config_manager)
        self.learning_memory_system = ExpertLearningMemorySystem(self.config_manager)

        # Keep original for fallback
        self.prediction_generator = PredictionGenerator(
            self.config_manager, self.temporal_calculator, self.memory_retrieval
        )

        # Neo4j knowledge graph integration
        self.neo4j_service = Neo4jKnowledgeService()
        self.ingestion_pipeline = Neo4jIngestionPipeline(self.neo4j_service)

        # Learning memory system integration (already initialized above)

        # Training state
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.current_session: Optional[TrainingSession] = None
        self.expert_states: Dict[str, ExpertState] = {}

        # Track first predictions for logging
        self.experts_first_prediction_logged: set = set()

        # Initialize expert states
        self._initialize_expert_states()

        logger.info("✅ Training Loop Orchestrator initialized")

    async def initialize_neo4j(self) -> bool:
        """Initialize Neo4j connection"""
        success = await self.neo4j_service.initialize()
        if success:
            logger.info("✅ Neo4j knowledge graph connected")
        else:
            logger.warning("⚠️ Neo4j knowledge graph not available")
        return success

    def _initialize_expert_states(self):
        """Initialize state tracking for all experts"""
        for expert_type in ExpertType:
            config = self.config_manager.get_configuration(expert_type)
            self.expert_states[expert_type.value] = ExpertState(
                expert_id=expert_type.value,
                expert_type=expert_type
            )

        logger.info(f"✅ Initialized state for {len(self.expert_states)} experts")

    async def start_training_session(self, season: int, session_name: Optional[str] = None) -> str:
        """Start a new training session"""
        session_id = session_name or f"season_{season}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.current_session = TrainingSession(
            session_id=session_id,
            start_time=datetime.now(),
            season=season,
            expert_states=self.expert_states.copy()
        )

        logger.info(f"🚀 Started training session: {session_id}")
        return session_id

    async def process_season(self, season: int, max_games: Optional[int] = None) -> TrainingSession:
        """Process an entire season of games"""
        session_id = await self.start_training_session(season)

        try:
            # Load season games
            logger.info(f"📊 Loading {season} season games...")
            season_games = self.data_loader.load_season_games(season, completed_only=True)

            if not season_games.games:
                logger.warning(f"⚠️ No completed games found for {season} season")
                return self.current_session

            games_to_process = season_games.games
            if max_games:
                games_to_process = games_to_process[:max_games]

            logger.info(f"🎯 Processing {len(games_to_process)} games from {season} season")

            # Process games sequentially
            for i, game in enumerate(games_to_process):
                try:
                    await self.process_single_game(game)

                    # Progress logging
                    if (i + 1) % 10 == 0:
                        logger.info(f"📈 Processed {i + 1}/{len(games_to_process)} games")

                    # Save checkpoint every 50 games
                    if (i + 1) % 50 == 0:
                        await self.save_checkpoint()

                except Exception as e:
                    logger.error(f"❌ Failed to process game {game.game_id}: {e}")
                    continue

            # Finalize session
            await self.finalize_training_session()

            logger.info(f"✅ Completed {season} season training: {len(games_to_process)} games processed")
            return self.current_session

        except Exception as e:
            logger.error(f"❌ Training session failed: {e}")
            raise

    async def process_single_game(self, game: GameContext):
        """Process a single game through the training loop"""
        try:
            logger.debug(f"🏈 Processing {game.away_team} @ {game.home_team} (Week {game.week})")

            # Generate memory retrieval results for all experts first
            logger.debug(f"🧠 Retrieving memories for all experts...")
            memory_results = {}
            game_context_dict = self._game_context_to_dict(game)

            for expert_type in ExpertType:
                try:
                    memory_result = await self.memory_retrieval.retrieve_memories_for_expert(
                        expert_type, game_context_dict
                    )
                    memory_results[expert_type.value] = memory_result
                except Exception as e:
                    logger.warning(f"⚠️ Memory retrieval failed for {expert_type.value}: {e}")
                    # Create empty memory result
                    from training.memory_retrieval_system import MemoryRetrievalResult
                    memory_results[expert_type.value] = MemoryRetrievalResult(
                        expert_type=expert_type,
                        game_context=game_context_dict,
                        retrieved_memories=[],
                        total_candidates_evaluated=0,
                        retrieval_time_ms=0.0,
                        retrieval_summary="Memory retrieval failed"
                    )

            # Generate predictions from all experts in parallel using real LLM
            logger.info(f"🚀 Generating parallel predictions for {game.away_team} @ {game.home_team}")
            start_time = datetime.now()

            expert_predictions = await self.real_prediction_generator.generate_all_predictions_parallel(
                game_context_dict, memory_results
            )

            end_time = datetime.now()
            prediction_time = (end_time - start_time).total_seconds()
            logger.info(f"⚡ Parallel predictions completed in {prediction_time:.1f}s ({len(expert_predictions)} experts)")

            # Log first predictions from each expert
            for expert_id, prediction in expert_predictions.items():
                if expert_id not in self.experts_first_prediction_logged:
                    logger.info(f"🎯 FIRST PREDICTION - {expert_id}: {prediction.predicted_winner} "
                              f"({prediction.win_probability:.1%} confidence) for {game.away_team} @ {game.home_team}")
                    self.experts_first_prediction_logged.add(expert_id)

            # Store predictions (for now, just log them)
            await self._store_predictions(game, expert_predictions)

            # Ingest data into Neo4j knowledge graph
            await self.ingestion_pipeline.ingest_game_data(game, expert_predictions)

            # Process actual game outcome
            if game.home_score is not None and game.away_score is not None:
                await self._process_game_outcome(game, expert_predictions)

                # Post-game learning for each expert
                await self._process_post_game_learning(game, expert_predictions)

            # Update session stats
            if self.current_session:
                self.current_session.games_processed += 1
                self.current_session.total_predictions += len(expert_predictions)

                # Check system health at monitoring checkpoints
                await self._check_monitoring_checkpoints(self.current_session.games_processed)

        except Exception as e:
            logger.error(f"❌ Failed to process game {game.game_id}: {e}")
            raise

    def _game_context_to_dict(self, game: GameContext) -> Dict[str, Any]:
        """Convert GameContext to dictionary for prediction generator"""
        return {
            'game_id': game.game_id,
            'home_team': game.home_team,
            'away_team': game.away_team,
            'season': game.season,
            'week': game.week,
            'game_date': game.game_date.isoformat(),
            'weather': game.weather,
            'spread_line': game.spread_line,
            'total_line': game.total_line,
            'home_moneyline': game.home_moneyline,
            'away_moneyline': game.away_moneyline,
            'division_game': game.division_game,
            'stadium': game.stadium,
            'surface': game.surface,
            'roof': game.roof,
            'home_coach': game.home_coach,
            'away_coach': game.away_coach,
            'home_qb': game.home_qb,
            'away_qb': game.away_qb
        }

    async def _store_predictions(self, game: GameContext, predictions: Dict[str, GamePrediction]):
        """Store expert predictions (basic implementation)"""
        # For now, just create a simple log file
        predictions_file = self.checkpoint_dir / f"predictions_{game.season}.jsonl"

        prediction_record = {
            'game_id': game.game_id,
            'game_date': game.game_date.isoformat(),
            'home_team': game.home_team,
            'away_team': game.away_team,
            'week': game.week,
            'season': game.season,
            'predictions': {}
        }

        for expert_id, prediction in predictions.items():
            prediction_record['predictions'][expert_id] = {
                'predicted_winner': prediction.predicted_winner,
                'win_probability': prediction.win_probability,
                'confidence_level': prediction.confidence_level,
                'reasoning_chain': prediction.reasoning_chain
            }

        # Append to JSONL file
        with open(predictions_file, 'a') as f:
            f.write(json.dumps(prediction_record) + '\n')

    async def _process_game_outcome(self, game: GameContext, predictions: Dict[str, GamePrediction]):
        """Process actual game outcome and update expert performance"""
        actual_result = {
            'home_score': game.home_score,
            'away_score': game.away_score,
            'overtime': game.overtime
        }

        # Update expert states based on prediction accuracy
        for expert_id, prediction in predictions.items():
            if expert_id in self.expert_states:
                self.expert_states[expert_id].update_performance(prediction, actual_result, game)

        # Store outcome analysis
        outcome_file = self.checkpoint_dir / f"outcomes_{game.season}.jsonl"

        outcome_record = {
            'game_id': game.game_id,
            'game_date': game.game_date.isoformat(),
            'actual_result': actual_result,
            'expert_performance': {}
        }

        for expert_id, prediction in predictions.items():
            if expert_id in self.expert_states:
                state = self.expert_states[expert_id]
                outcome_record['expert_performance'][expert_id] = {
                    'accuracy': state.accuracy,
                    'games_processed': state.games_processed,
                    'avg_confidence': state.avg_confidence
                }

        with open(outcome_file, 'a') as f:
            f.write(json.dumps(outcome_record) + '\n')

    async def save_checkpoint(self):
        """Save current training state to checkpoint"""
        if not self.current_session:
            return

        checkpoint_file = self.checkpoint_dir / f"checkpoint_{self.current_session.session_id}.json"

        checkpoint_data = {
            'session': asdict(self.current_session),
            'expert_states': {k: asdict(v) for k, v in self.expert_states.items()},
            'timestamp': datetime.now().isoformat()
        }

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        logger.info(f"💾 Checkpoint saved: {checkpoint_file}")

    async def load_checkpoint(self, session_id: str) -> bool:
        """Load training state from checkpoint"""
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{session_id}.json"

        if not checkpoint_file.exists():
            logger.warning(f"⚠️ Checkpoint not found: {checkpoint_file}")
            return False

        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)

            # Restore session
            session_data = checkpoint_data['session']
            self.current_session = TrainingSession(**session_data)

            # Restore expert states
            for expert_id, state_data in checkpoint_data['expert_states'].items():
                # Convert string back to ExpertType
                expert_type = ExpertType(expert_id)
                state_data['expert_type'] = expert_type

                # Convert datetime strings back to datetime objects
                if state_data.get('last_updated'):
                    state_data['last_updated'] = datetime.fromisoformat(state_data['last_updated'])

                self.expert_states[expert_id] = ExpertState(**state_data)

            logger.info(f"📂 Checkpoint loaded: {session_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load checkpoint: {e}")
            return False

    async def finalize_training_session(self):
        """Finalize the current training session"""
        if not self.current_session:
            return

        self.current_session.end_time = datetime.now()

        # Save final checkpoint
        await self.save_checkpoint()

        # Generate session summary
        await self._generate_session_summary()

        logger.info(f"🏁 Training session finalized: {self.current_session.session_id}")

    async def _generate_session_summary(self):
        """Generate summary report for the training session"""
        if not self.current_session:
            return

        summary_file = self.checkpoint_dir / f"summary_{self.current_session.session_id}.json"

        # Calculate overall statistics
        total_accuracy = sum(state.accuracy for state in self.expert_states.values()) / len(self.expert_states)
        total_confidence = sum(state.avg_confidence for state in self.expert_states.values()) / len(self.expert_states)

        # Find best and worst performing experts
        best_expert = max(self.expert_states.values(), key=lambda x: x.accuracy)
        worst_expert = min(self.expert_states.values(), key=lambda x: x.accuracy)

        summary = {
            'session_id': self.current_session.session_id,
            'season': self.current_session.season,
            'duration_minutes': (self.current_session.end_time - self.current_session.start_time).total_seconds() / 60,
            'games_processed': self.current_session.games_processed,
            'total_predictions': self.current_session.total_predictions,
            'overall_stats': {
                'average_accuracy': total_accuracy,
                'average_confidence': total_confidence,
                'best_expert': {
                    'id': best_expert.expert_id,
                    'accuracy': best_expert.accuracy,
                    'games': best_expert.games_processed
                },
                'worst_expert': {
                    'id': worst_expert.expert_id,
                    'accuracy': worst_expert.accuracy,
                    'games': worst_expert.games_processed
                }
            },
            'expert_performance': {
                expert_id: {
                    'accuracy': state.accuracy,
                    'games_processed': state.games_processed,
                    'avg_confidence': state.avg_confidence,
                    'correct_predictions': state.correct_predictions,
                    'total_predictions': state.total_predictions
                }
                for expert_id, state in self.expert_states.items()
            }
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"📊 Session summary saved: {summary_file}")

        # Log key metrics
        logger.info(f"📈 Session Results:")
        logger.info(f"   Games Processed: {self.current_session.games_processed}")
        logger.info(f"   Average Accuracy: {total_accuracy:.1%}")
        logger.info(f"   Best Expert: {best_expert.expert_id} ({best_expert.accuracy:.1%})")
        logger.info(f"   Worst Expert: {worst_expert.expert_id} ({worst_expert.accuracy:.1%})")

    def get_expert_performance_summary(self) -> Dict[str, Any]:
        """Get current expert performance summary"""
        return {
            expert_id: {
                'accuracy': state.accuracy,
                'games_processed': state.games_processed,
                'avg_confidence': state.avg_confidence,
                'correct_predictions': state.correct_predictions,
                'total_predictions': state.total_predictions
            }
            for expert_id, state in self.expert_states.items()
        }

    async def _process_post_game_learning(self, game: GameContext, expert_predictions: Dict[str, GamePrediction]):
        """Process post-game learning for all experts"""

        try:
            # Create actual outcome dictionary
            actual_outcome = {
                'home_score': game.home_score,
                'away_score': game.away_score,
                'overtime': game.overtime,
                'winner': 'home' if game.home_score > game.away_score else 'away' if game.away_score > game.home_score else 'tie',
                'margin': abs(game.home_score - game.away_score),
                'total_points': game.home_score + game.away_score
            }

            # Create game context dictionary
            game_context = self._game_context_to_dict(game)

            # Process learning for each expert
            for expert_id, prediction in expert_predictions.items():
                try:
                    reflection = await self.learning_memory_system.process_post_game_learning(
                        expert_id, game_context, prediction, actual_outcome
                    )

                    logger.debug(f"🧠 Post-game learning completed for {expert_id}")

                except Exception as e:
                    logger.warning(f"⚠️ Post-game learning failed for {expert_id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Post-game learning process failed: {e}")

    def get_learning_system_status(self) -> Dict[str, Any]:
        """Get status of the learning memory system"""

        try:
            status = {
                'total_experts': len(self.expert_states),
                'memory_banks': {
                    'personal_memories': {},
                    'team_memories': {},
                    'matchup_memories': {}
                }
            }

            # Count memories for each expert
            for expert_id in self.expert_states.keys():
                # Personal memories
                personal_memories = self.learning_memory_system.get_expert_memories(expert_id)
                status['memory_banks']['personal_memories'][expert_id] = len(personal_memories)

                # Team memories
                if expert_id in self.learning_memory_system.team_memories:
                    status['memory_banks']['team_memories'][expert_id] = len(self.learning_memory_system.team_memories[expert_id])
                else:
                    status['memory_banks']['team_memories'][expert_id] = 0

                # Matchup memories
                if expert_id in self.learning_memory_system.matchup_memories:
                    status['memory_banks']['matchup_memories'][expert_id] = len(self.learning_memory_system.matchup_memories[expert_id])
                else:
                    status['memory_banks']['matchup_memories'][expert_id] = 0

            return status

        except Exception as e:
            logger.error(f"❌ Failed to get learning system status: {e}")
            return {'error': str(e)}

    async def _check_monitoring_checkpoints(self, games_processed: int):
        """Check system health at monitoring checkpoints"""

        if games_processed == 20:
            await self._check_memory_storage_health()
        elif games_processed == 50:
            await self._check_expert_state_evolution()
        elif games_processed == 100:
            await self._check_memory_retrieval_relevance()
        elif games_processed == 200:
            await self._check_reasoning_evolution()

    async def _check_memory_storage_health(self):
        """Check memory storage is working (Checkpoint: Game 20)"""

        logger.info("🔍 CHECKPOINT 20: Checking memory storage health...")

        try:
            issues = []

            # Check each expert has memories
            for expert_id in self.expert_states.keys():
                personal_memories = self.learning_memory_system.get_expert_memories(expert_id)

                if len(personal_memories) == 0:
                    issues.append(f"❌ {expert_id} has no personal memories")
                else:
                    logger.info(f"✅ {expert_id}: {len(personal_memories)} personal memories")

            if issues:
                logger.error("🚨 MEMORY STORAGE ISSUES DETECTED:")
                for issue in issues:
                    logger.error(f"   {issue}")
                logger.error("🛑 Consider stopping and fixing memory storage before continuing")
            else:
                logger.info("✅ Memory storage health check PASSED")

        except Exception as e:
            logger.error(f"❌ Memory storage health check failed: {e}")

    async def _check_expert_state_evolution(self):
        """Check expert states are evolving properly (Checkpoint: Game 50)"""

        logger.info("🔍 CHECKPOINT 50: Checking expert state evolution...")

        try:
            issues = []

            for expert_id, state in self.expert_states.items():
                # Check accuracy is reasonable
                if state.accuracy < 0.3 or state.accuracy > 0.8:
                    issues.append(f"⚠️ {expert_id} has extreme accuracy: {state.accuracy:.1%}")

                # Check games processed
                if state.games_processed < 40:  # Should have processed most games by now
                    issues.append(f"⚠️ {expert_id} has only processed {state.games_processed} games")

                # Check confidence is reasonable
                if state.avg_confidence < 0.1 or state.avg_confidence > 0.95:
                    issues.append(f"⚠️ {expert_id} has extreme confidence: {state.avg_confidence:.1%}")

                logger.info(f"📊 {expert_id}: {state.accuracy:.1%} accuracy, {state.avg_confidence:.1%} confidence, {state.games_processed} games")

            if issues:
                logger.warning("⚠️ EXPERT STATE ISSUES DETECTED:")
                for issue in issues:
                    logger.warning(f"   {issue}")
            else:
                logger.info("✅ Expert state evolution check PASSED")

        except Exception as e:
            logger.error(f"❌ Expert state evolution check failed: {e}")

    async def _check_memory_retrieval_relevance(self):
        """Check memory retrieval is working properly (Checkpoint: Game 100)"""

        logger.info("🔍 CHECKPOINT 100: Checking memory retrieval relevance...")

        try:
            # Test memory retrieval for a few experts
            test_experts = list(self.expert_states.keys())[:3]

            for expert_id in test_experts:
                try:
                    # Get some memories for this expert
                    memories = self.learning_memory_system.get_expert_memories(expert_id)

                    if len(memories) == 0:
                        logger.warning(f"⚠️ {expert_id} has no retrievable memories")
                        continue

                    # Check memory ages and relevance
                    recent_memories = [m for m in memories if (datetime.now() - m.created_date).days < 100]

                    logger.info(f"📚 {expert_id}: {len(memories)} total memories, {len(recent_memories)} recent")

                    # Sample a few memories to check content
                    for i, memory in enumerate(memories[:2]):
                        age_days = (datetime.now() - memory.created_date).days
                        logger.info(f"   Memory {i+1}: {memory.memory_title} (age: {age_days} days)")

                except Exception as e:
                    logger.warning(f"⚠️ Memory retrieval test failed for {expert_id}: {e}")

            logger.info("✅ Memory retrieval relevance check completed")

        except Exception as e:
            logger.error(f"❌ Memory retrieval relevance check failed: {e}")

    async def _check_reasoning_evolution(self):
        """Check reasoning chains are evolving (Checkpoint: Game 200)"""

        logger.info("🔍 CHECKPOINT 200: Checking reasoning evolution...")

        try:
            # This would require storing early vs late reasoning chains for comparison
            # For now, just check that experts have diverse reasoning patterns

            for expert_id in list(self.expert_states.keys())[:3]:
                memories = self.learning_memory_system.get_expert_memories(expert_id)

                if len(memories) > 10:
                    # Check for learning-related memories
                    learning_memories = [m for m in memories if 'lesson' in m.memory_content.lower() or 'learn' in m.memory_content.lower()]

                    logger.info(f"🧠 {expert_id}: {len(memories)} total memories, {len(learning_memories)} learning-related")

                    # Sample some learning insights
                    for memory in learning_memories[:2]:
                        logger.info(f"   Learning: {memory.memory_content[:100]}...")
                else:
                    logger.warning(f"⚠️ {expert_id} has insufficient memories for reasoning evolution analysis")

            logger.info("✅ Reasoning evolution check completed")

        except Exception as e:
            logger.error(f"❌ Reasoning evolution check failed: {e}")


async def main():
    """Test the Training Loop Orchestrator"""

    print("🚀 Training Loop Orchestrator Test")
    print("=" * 60)

    # Initialize orchestrator
    orchestrator = TrainingLoopOrchestrator()

    # Test with a small subset of 2020 season (first 10 games)
    print("\n📊 Testing with 2020 Season (first 10 games)...")

    try:
        session = await orchestrator.process_season(2020, max_games=10)

        print(f"\n✅ Training session completed!")
        print(f"Session ID: {session.session_id}")
        print(f"Games processed: {session.games_processed}")
        print(f"Total predictions: {session.total_predictions}")

        # Show expert performance
        print(f"\n📈 Expert Performance Summary:")
        performance = orchestrator.get_expert_performance_summary()

        # Sort by accuracy
        sorted_experts = sorted(performance.items(), key=lambda x: x[1]['accuracy'], reverse=True)

        for expert_id, stats in sorted_experts[:5]:  # Top 5
            print(f"  {expert_id}: {stats['accuracy']:.1%} accuracy ({stats['correct_predictions']}/{stats['total_predictions']})")

        print(f"\n💾 Check training_checkpoints/ directory for detailed logs and checkpoints")

    except Exception as e:
        logger.error(f"❌ Training test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
