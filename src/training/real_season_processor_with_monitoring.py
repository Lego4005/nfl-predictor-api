#!/usr/bin/env python3
"""
Real 2020 Season Processor with Comprehensiveg

Processes the complete 2020 NFL season with real LLM calls and comprehensive
monitoring to catch issues early. Implements all the monitoring checkpoints
specified for memory storage, expert state, retrieval relevance, etc.
"""

import sys
import logging
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
sys.path.append('src')

from training.training_loop_orchestrator import TrainingLoopOrchestrator
from training.real_llm_prediction_generator import RealLLMPredictionGenerator
from training.expert_learning_memory_system import ExpertLearningMemorySystem, MemoryType
from training.expert_configuration import ExpertType, ExpertConfigurationManager
from training.nfl_data_loader import NFLDataLoader
from training.prediction_generator import PredictionType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_2020_season_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MonitoringCheckpoint:
    """Monitoring checkpoint data"""
    game_number: int
    timestamp: datetime

    # Memory storage checks
    total_memories_stored: int
    team_memories_count: int
    matchup_memories_count: int
    personal_memories_count: int

    # Expert state checks
    expert_belief_weights: Dict[str, Dict[str, float]]
    expert_accuracy_rates: Dict[str, float]

    # Memory retrieval checks
    sample_memory_retrievals: Dict[str, List[str]]

    # Reasoning evolution checks
    sample_reasoning_chains: Dict[str, List[str]]

    # Performance patterns
    expert_win_rates: Dict[str, float]

    # API call monitoring
    successful_api_calls: int
    failed_api_calls: int
    rate_limit_hits: int

    # Issues detected
    issues_detected: List[str]
    critical_issues: List[str]

class Real2020SeasonProcessor:
    """Processes 2020 season with real LLM calls and comprehensive monitoring"""

    def __init__(self):
        """Initialize the real season processor"""
        self.config_manager = ExpertConfigurationManager()
        self.data_loader = NFLDataLoader()
        self.real_llm_generator = RealLLMPredictionGenerator(self.config_manager)
        self.learning_memory_system = ExpertLearningMemorySystem(self.config_manager)

        # Monitoring data
        self.checkpoints: List[MonitoringCheckpoint] = []
        self.games_processed = 0
        self.start_time = None
        self.expert_predictions: Dict[str, List[Dict]] = {}  # expert_id -> predictions
        self.expert_outcomes: Dict[str, List[bool]] = {}  # expert_id -> correct/incorrect
        self.api_call_stats = {
            'successful': 0,
            'failed': 0,
            'rate_limited': 0,
            'total_time': 0.0
        }

        # Initialize expert tracking
        for expert_type in ExpertType:
            expert_id = expert_type.value
            self.expert_predictions[expert_id] = []
            self.expert_outcomes[expert_id] = []

        # Output directory
        self.output_dir = Path("real_2020_season_results")
        self.output_dir.mkdir(exist_ok=True)

        logger.info("✅ Real 2020 Season Processor initialized")

    async def process_complete_2020_season(self) -> Dict[str, Any]:
        """Process the complete 2020 season with monitoring"""
        logger.info("🚀 Starting REAL 2020 season processing with LLM calls")
        logger.info("=" * 80)

        self.start_time = datetime.now()

        try:
            # Load 2020 season games
            logger.info("📊 Loading 2020 season games...")
            season_data = self.data_loader.load_season_games(2020, completed_only=True)

            if not season_data.games:
                raise ValueError("No 2020 season games found")

            total_games = len(season_data.games)
            logger.info(f"🎯 Processing {total_games} games from 2020 season")
            logger.info(f"📅 Date range: {season_data.date_range[0]} to {season_data.date_range[1]}")

            # Process games with monitoring checkpoints
            for i, game in enumerate(season_data.games):
                game_number = i + 1

                logger.info(f"\n🏈 Processing Game {game_number}/{total_games}: {game.away_team} @ {game.home_team} (Week {game.week})")

                try:
                    # Process single game
                    await self._process_single_game_with_monitoring(game, game_number)

                    # Monitoring checkpoints
                    if game_number in [20, 50, 100, 150, 200, 256]:
                        logger.info(f"\n🔍 MONITORING CHECKPOINT at Game {game_number}")
                        checkpoint = await self._run_monitoring_checkpoint(game_number)

                        # Check for critical issues
                        if checkpoint.critical_issues:
                            logger.error(f"🚨 CRITICAL ISSUES DETECTED at Game {game_number}:")
                            for issue in checkpoint.critical_issues:
                                logger.error(f"   ❌ {issue}")

                            # Save checkpoint and stop
                            await self._save_checkpoint(checkpoint)
                            raise RuntimeError(f"Critical issues detected at game {game_number} - stopping processing")

                        # Log checkpoint results
                        await self._log_checkpoint_results(checkpoint)
                        await self._save_checkpoint(checkpoint)

                    # Progress logging
                    if game_number % 10 == 0:
                        elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
                        rate = game_number / elapsed if elapsed > 0 else 0
                        remaining = (total_games - game_number) / rate if rate > 0 else 0
                        logger.info(f"📈 Progress: {game_number}/{total_games} ({game_number/total_games:.1%}) - {rate:.1f} games/hour - ETA: {remaining:.1f} hours")

                except Exception as e:
                    logger.error(f"❌ Failed to process game {game_number}: {e}")
                    # Continue with next game rather than stopping
                    continue

            # Final results
            end_time = datetime.now()
            total_duration = end_time - self.start_time

            results = {
                'season': 2020,
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration_hours': total_duration.total_seconds() / 3600,
                'games_processed': self.games_processed,
                'total_predictions': sum(len(preds) for preds in self.expert_predictions.values()),
                'api_call_stats': self.api_call_stats,
                'expert_final_stats': await self._calculate_final_expert_stats(),
                'checkpoints': [asdict(cp) for cp in self.checkpoints]
            }

            # Save final results
            await self._save_final_results(results)

            logger.info(f"\n🎉 REAL 2020 SEASON PROCESSING COMPLETED!")
            logger.info(f"⏱️  Total Duration: {total_duration.total_seconds()/3600:.2f} hours")
            logger.info(f"🎯 Games Processed: {self.games_processed}")
            logger.info(f"🤖 Total API Calls: {self.api_call_stats['successful'] + self.api_call_stats['failed']}")
            logger.info(f"✅ Success Rate: {self.api_call_stats['successful']/(self.api_call_stats['successful'] + self.api_call_stats['failed']):.1%}")

            return results

        except Exception as e:
            logger.error(f"❌ Real season processing failed: {e}")
            raise

    async def _process_single_game_with_monitoring(self, game, game_number: int):
        """Process a single game with all 15 experts and monitoring"""

        game_context = self._game_to_context_dict(game)
        expert_predictions = {}

        # Generate predictions from all 15 experts
        for expert_type in ExpertType:
            expert_id = expert_type.value

            try:
                # Retrieve relevant memories for this expert
                memories = await self._retrieve_memories_for_expert(expert_type, game_context)

                # Generate real LLM prediction
                start_time = time.time()
                prediction = await self.real_llm_generator.generate_real_prediction(
                    expert_type, game_context, memories, PredictionType.WINNER
                )
                api_time = time.time() - start_time

                # Track API call success
                self.api_call_stats['successful'] += 1
                self.api_call_stats['total_time'] += api_time

                expert_predictions[expert_id] = prediction

                # Store prediction for tracking
                self.expert_predictions[expert_id].append({
                    'game_number': game_number,
                    'game_id': game.game_id,
                    'prediction': prediction.to_dict(),
                    'api_time': api_time
                })

                logger.debug(f"   ✅ {expert_id}: {prediction.predicted_winner} ({prediction.confidence_level:.1%})")

            except Exception as e:
                logger.error(f"   ❌ {expert_id} prediction failed: {e}")
                self.api_call_stats['failed'] += 1
                continue

        # Process actual game outcome and learning
        if game.home_score is not None and game.away_score is not None:
            actual_outcome = {
                'home_score': game.home_score,
                'away_score': game.away_score,
                'overtime': game.overtime
            }

            # Process post-game learning for each expert
            for expert_id, prediction in expert_predictions.items():
                try:
                    # Generate learning reflection
                    reflection = await self.learning_memory_system.process_post_game_learning(
                        expert_id, game_context, prediction, actual_outcome
                    )

                    # Track prediction accuracy
                    self.expert_outcomes[expert_id].append(reflection.was_correct)

                    logger.debug(f"   🧠 {expert_id} learning: {'✅' if reflection.was_correct else '❌'} - {len(reflection.lessons_learned)} lessons")

                except Exception as e:
                    logger.error(f"   ❌ {expert_id} learning failed: {e}")
                    continue

        self.games_processed += 1

    async def _retrieve_memories_for_expert(self, expert_type: ExpertType, game_context: Dict[str, Any]) -> List:
        """Retrieve relevant memories for an expert (simplified for now)"""
        # This would normally use the memory retrieval system
        # For now, return empty list - memories will be built as we process games
        return []

    def _game_to_context_dict(self, game) -> Dict[str, Any]:
        """Convert game object to context dictionary"""
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
            'away_qb': game.away_qb,
            'home_score': game.home_score,
            'away_score': game.away_score,
            'overtime': game.overtime
        }

    async def _run_monitoring_checkpoint(self, game_number: int) -> MonitoringCheckpoint:
        """Run comprehensive monitoring checkpoint"""

        logger.info(f"🔍 Running monitoring checkpoint at game {game_number}...")

        issues_detected = []
        critical_issues = []

        # 1. Memory storage checks
        memory_stats = await self._check_memory_storage()
        if memory_stats['total_memories'] == 0 and game_number >= 20:
            critical_issues.append("No memories stored after 20+ games - storage system failure")

        # 2. Expert state checks
        expert_states = await self._check_expert_states()

        # 3. Memory retrieval relevance checks
        retrieval_stats = await self._check_memory_retrieval_relevance(game_number)

        # 4. Reasoning evolution checks
        reasoning_evolution = await self._check_reasoning_evolution(game_number)

        # 5. Performance pattern checks
        performance_stats = await self._check_performance_patterns(game_number)
        extreme_performers = [
            expert_id for expert_id, rate in performance_stats.items()
            if rate > 0.8 or rate < 0.2
        ]
        if len(extreme_performers) > 2 and game_number >= 50:
            issues_detected.append(f"Extreme performance detected: {extreme_performers}")

        # 6. API call failure checks
        api_success_rate = self.api_call_stats['successful'] / (self.api_call_stats['successful'] + self.api_call_stats['failed']) if (self.api_call_stats['successful'] + self.api_call_stats['failed']) > 0 else 1.0
        if api_success_rate < 0.8:
            critical_issues.append(f"API success rate too low: {api_success_rate:.1%}")

        # 7. Memory bank growth checks
        memory_growth_stats = await self._check_memory_bank_growth(game_number)

        checkpoint = MonitoringCheckpoint(
            game_number=game_number,
            timestamp=datetime.now(),
            total_memories_stored=memory_stats['total_memories'],
            team_memories_count=memory_stats['team_memories'],
            matchup_memories_count=memory_stats['matchup_memories'],
            personal_memories_count=memory_stats['personal_memories'],
            expert_belief_weights=expert_states,
            expert_accuracy_rates=performance_stats,
            sample_memory_retrievals=retrieval_stats,
            sample_reasoning_chains=reasoning_evolution,
            expert_win_rates=performance_stats,
            successful_api_calls=self.api_call_stats['successful'],
            failed_api_calls=self.api_call_stats['failed'],
            rate_limit_hits=self.api_call_stats['rate_limited'],
            issues_detected=issues_detected,
            critical_issues=critical_issues
        )

        self.checkpoints.append(checkpoint)
        return checkpoint

    async def _check_memory_storage(self) -> Dict[str, int]:
        """Check memory storage systems"""

        total_memories = 0
        team_memories = 0
        matchup_memories = 0
        personal_memories = 0

        # Count memories in learning memory system
        for expert_id in self.learning_memory_system.personal_memories:
            personal_memories += len(self.learning_memory_system.personal_memories[expert_id])
            total_memories += len(self.learning_memory_system.personal_memories[expert_id])

        for expert_id in self.learning_memory_system.team_memories:
            team_memories += len(self.learning_memory_system.team_memories[expert_id])

        for expert_id in self.learning_memory_system.matchup_memories:
            matchup_memories += len(self.learning_memory_system.matchup_memories[expert_id])

        return {
            'total_memories': total_memories,
            'team_memories': team_memories,
            'matchup_memories': matchup_memories,
            'personal_memories': personal_memories
        }

    async def _check_expert_states(self) -> Dict[str, Dict[str, float]]:
        """Check expert belief weights and states"""

        expert_states = {}

        for expert_type in ExpertType:
            expert_id = expert_type.value
            config = self.config_manager.get_configuration(expert_type)

            if config:
                # Get current analytical focus weights
                expert_states[expert_id] = dict(config.analytical_focus)

        return expert_states

    async def _check_memory_retrieval_relevance(self, game_number: int) -> Dict[str, List[str]]:
        """Check memory retrieval relevance"""

        # Sample a few experts and check their memory retrieval
        sample_experts = ['contrarian_rebel', 'momentum_rider', 'chaos_theory_believer']
        retrieval_stats = {}

        for expert_id in sample_experts:
            if expert_id in self.learning_memory_system.personal_memories:
                memories = self.learning_memory_system.get_expert_memories(expert_id)
                retrieval_stats[expert_id] = [
                    f"{m.memory_type.value}: {m.memory_title[:50]}..."
                    for m in memories[:3]
                ]
            else:
                retrieval_stats[expert_id] = []

        return retrieval_stats

    async def _check_reasoning_evolution(self, game_number: int) -> Dict[str, List[str]]:
        """Check reasoning chain evolution"""

        reasoning_evolution = {}

        # Sample reasoning from early vs recent games
        for expert_id in self.expert_predictions:
            predictions = self.expert_predictions[expert_id]

            if len(predictions) >= 10:
                # Early reasoning (first 10 games)
                early_reasoning = predictions[9]['prediction']['reasoning_chain']

                # Recent reasoning (latest)
                recent_reasoning = predictions[-1]['prediction']['reasoning_chain']

                reasoning_evolution[expert_id] = {
                    'early': early_reasoning[:2],  # First 2 reasoning points
                    'recent': recent_reasoning[:2]  # First 2 reasoning points
                }

        return reasoning_evolution

    async def _check_performance_patterns(self, game_number: int) -> Dict[str, float]:
        """Check expert performance patterns"""

        performance_stats = {}

        for expert_id in self.expert_outcomes:
            outcomes = self.expert_outcomes[expert_id]
            if outcomes:
                accuracy = sum(outcomes) / len(outcomes)
                performance_stats[expert_id] = accuracy
            else:
                performance_stats[expert_id] = 0.0

        return performance_stats

    async def _check_memory_bank_growth(self, game_number: int) -> Dict[str, int]:
        """Check memory bank growth rates"""

        growth_stats = {
            'expected_memories_per_game': 2,  # Rough estimate
            'expected_total': game_number * 2 * len(ExpertType),
            'actual_total': 0
        }

        # Count actual memories
        memory_stats = await self._check_memory_storage()
        growth_stats['actual_total'] = memory_stats['total_memories']

        return growth_stats

    async def _log_checkpoint_results(self, checkpoint: MonitoringCheckpoint):
        """Log checkpoint results"""

        logger.info(f"📊 CHECKPOINT RESULTS - Game {checkpoint.game_number}")
        logger.info(f"   💾 Memories: {checkpoint.total_memories_stored} total ({checkpoint.personal_memories_count} personal)")
        logger.info(f"   🎯 API Calls: {checkpoint.successful_api_calls} success, {checkpoint.failed_api_calls} failed")

        # Log top/bottom performers
        sorted_performers = sorted(checkpoint.expert_win_rates.items(), key=lambda x: x[1], reverse=True)
        logger.info(f"   🏆 Top Performer: {sorted_performers[0][0]} ({sorted_performers[0][1]:.1%})")
        logger.info(f"   📉 Bottom Performer: {sorted_performers[-1][0]} ({sorted_performers[-1][1]:.1%})")

        # Log issues
        if checkpoint.issues_detected:
            logger.warning(f"   ⚠️ Issues: {len(checkpoint.issues_detected)}")
            for issue in checkpoint.issues_detected:
                logger.warning(f"      • {issue}")

        if checkpoint.critical_issues:
            logger.error(f"   🚨 Critical Issues: {len(checkpoint.critical_issues)}")
            for issue in checkpoint.critical_issues:
                logger.error(f"      • {issue}")

    async def _save_checkpoint(self, checkpoint: MonitoringCheckpoint):
        """Save checkpoint data"""

        checkpoint_file = self.output_dir / f"checkpoint_game_{checkpoint.game_number}.json"

        with open(checkpoint_file, 'w') as f:
            json.dump(asdict(checkpoint), f, indent=2, default=str)

        logger.info(f"💾 Checkpoint saved: {checkpoint_file}")

    async def _calculate_final_expert_stats(self) -> Dict[str, Any]:
        """Calculate final expert statistics"""

        final_stats = {}

        for expert_id in self.expert_outcomes:
            outcomes = self.expert_outcomes[expert_id]
            predictions = self.expert_predictions[expert_id]

            if outcomes and predictions:
                accuracy = sum(outcomes) / len(outcomes)
                total_predictions = len(predictions)
                avg_confidence = sum(p['prediction']['confidence_level'] for p in predictions) / total_predictions

                final_stats[expert_id] = {
                    'total_predictions': total_predictions,
                    'correct_predictions': sum(outcomes),
                    'accuracy': accuracy,
                    'average_confidence': avg_confidence,
                    'memories_created': len(self.learning_memory_system.get_expert_memories(expert_id))
                }

        return final_stats

    async def _save_final_results(self, results: Dict[str, Any]):
        """Save final processing results"""

        results_file = self.output_dir / "real_2020_season_final_results.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"📁 Final results saved: {results_file}")


async def main():
    """Run the real 2020 season processing"""
    print("🚀 Real 2020 NFL Season Processing with LLM Calls")
    print("=" * 80)
    print("This will process all 2020 regular season games with:")
    print("• Real LLM API calls for all 15 experts")
    print("• Post-game learning and memory formation")
    print("• Comprehensive monitoring at games 20, 50, 100, 150, 200, 256")
    print("• Estimated duration: 4-8 hours")
    print("=" * 80)

    # Confirm before starting
    response = input("\nProceed with real LLM processing? (yes/no): ")
    if response.lower() != 'yes':
        print("Processing cancelled.")
        return

    processor = Real2020SeasonProcessor()

    try:
        results = await processor.process_complete_2020_season()

        print(f"\n🎉 SUCCESS! Real 2020 season processing completed!")
        print(f"📊 Final Statistics:")
        print(f"   Games Processed: {results['games_processed']}")
        print(f"   Total Duration: {results['total_duration_hours']:.2f} hours")
        print(f"   API Success Rate: {results['api_call_stats']['successful']/(results['api_call_stats']['successful'] + results['api_call_stats']['failed']):.1%}")
        print(f"   Total Predictions: {results['total_predictions']}")

        print(f"\n📁 Results saved to: real_2020_season_results/")

    except Exception as e:
        print(f"\n❌ Processing failed: {e}")
        logger.error(f"Real season processing failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
