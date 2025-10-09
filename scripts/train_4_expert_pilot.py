#!/usr/bin/env python3
"""
4-Expert Pilot Training & Evaluation Framework
Implements the full training loop with baselines and go/no-go gates.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from pathlib import Path

from src.services.supabase_service import SupabaseService
from src.services.orchestrator_model_switcher import OrchestratorModelSwitcher
from src.services.agentuity_adapter import AgentuityAdapter
from src.validation.expert_predictions_validator import ExpertPredictionsValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrainingPhase:
    name: str
    start_date: str
    end_date: str
    enable_tools: bool
    enable_stakes: bool
    description: str

@dataclass
class BaselineResult:
    name: str
    win_rate: float
    brier_score: float
    roi: float
    total_games: int

class FourExpertPilotTrainer:
    """
    Comprehensive training and evaluation system for 4-expert pilot.
    Implements Phase A (Learn 2020-2023), Phase B (Backtest 2024), Phase C (2025 YTD).
    """

    def __init__(self):
        self.supabase = SupabaseService()
        self.model_switcher = OrchestratorModelSwitcher(self.supabase)
        self.agentuity = AgentuityAdapter()
        self.validator = ExpertPredictionsValidator()

        # 4 pilot experts with max personality spread
        self.pilot_experts = [
            'conservative_analyzer',
            'momentum_rider',
            'contrarian_rebel',
            'value_hunter'
        ]

        # Training phases
        self.phases = [
            TrainingPhase(
                name="Phase A - Learn 2020-2023",
                start_date="2020-09-01",
                end_date="2023-12-31",
                enable_tools=False,  # Start with no tools
                enable_stakes=False,  # Learning focus
                description="Chronological learning to build episodic memories"
            ),
            TrainingPhase(
                name="Phase A2 - Learn 2020-2023 (Tools)",
                start_date="2020-09-01",
                end_date="2023-12-31",
                enable_tools=True,   # Enable tools
                enable_stakes=False,  # Still learning
                description="Same period with tools enabled for comparison"
            ),
            TrainingPhase(
                name="Phase B - Backtest 2024",
                start_date="2024-01-01",
                end_date="2024-12-31",
                enable_tools=True,
                enable_stakes=True,   # Full stakes for PnL
                description="Full 2024 season with baselines comparison"
            ),
            TrainingPhase(
                name="Phase C - 2025 YTD",
                start_date="2025-01-01",
                end_date="2025-10-09",  # Current date
                enable_tools=True,
                enable_stakes=True,
                description="Current season validation"
            )
        ]

    async def run_full_training_pipeline(self) -> Dict:
        """Execute complete training pipeline with all phases and baselines"""

        logger.info("Starting 4-Expert Pilot Training Pipeline")
        results = {}

        # Phase A: Learning (2020-2023)
        logger.info("=== PHASE A: LEARNING 2020-2023 ===")
        phase_a_results = await self.run_learning_phase()
        results['phase_a'] = phase_a_results

        # Phase B: Backtesting 2024 with baselines
        logger.info("=== PHASE B: BACKTEST 2024 WITH BASELINES ===")
        phase_b_results = await self.run_backtest_phase()
        results['phase_b'] = phase_b_results

        # Go/No-Go evaluation
        go_decision = self.evaluate_go_no_go(phase_b_results)
        results['go_no_go'] = go_decision

        if go_decision['proceed_to_full_system']:
            logger.info("✅ GO DECISION: Proceeding to full 15-expert system")
        else:
            logger.warning("❌ NO-GO: Need improvements before scaling")

        # Phase C: 2025 validation (if go decision)
        if go_decision['proceed_to_full_system']:
            logger.info("=== PHASE C: 2025 YTD VALIDATION ===")
            phase_c_results = await self.run_current_season_validation()
            results['phase_c'] = phase_c_results

        # Generate comprehensive report
        report = self.generate_training_report(results)
        await self.save_training_results(results, report)

        return results

    async def run_learning_phase(self) -> Dict:
        """Phase A: Learn from 2020-2023 chronologically"""

        results = {'no_tools': {}, 'with_tools': {}}

        # Track 1: No tools (baseline learning)
        logger.info("Track 1: Learning without tools (2020-2023)")
        for expert_id in self.pilot_experts:
            expert_results = await self.train_expert_chronologically(
                expert_id=expert_id,
                start_date="2020-09-01",
                end_date="2023-12-31",
                enable_tools=False,
                enable_stakes=False
            )
            results['no_tools'][expert_id] = expert_results

        # Track 2: With tools (enhanced learning)
        logger.info("Track 2: Learning with tools (2020-2023)")
        for expert_id in self.pilot_experts:
            expert_results = await self.train_expert_chronologically(
                expert_id=expert_id,
                start_date="2020-09-01",
                end_date="2023-12-31",
                enable_tools=True,
                enable_stakes=False
            )
            results['with_tools'][expert_id] = expert_results

        return results

    async def run_backtest_phase(self) -> Dict:
        """Phase B: Backtest 2024 with all baselines"""

        results = {}

        # Get all 2024 games
        games_2024 = await self.get_games_for_period("2024-01-01", "2024-12-31")
        logger.info(f"Found {len(games_2024)} games for 2024 backtest")

        # Baseline 1: Coin-flip
        logger.info("Running Baseline 1: Coin-flip")
        results['coin_flip'] = await self.run_coin_flip_baseline(games_2024)

        # Baseline 2: Market-only
        logger.info("Running Baseline 2: Market-only")
        results['market_only'] = await self.run_market_only_baseline(games_2024)

        # Baseline 3: One-shot (no Critic/Repair)
        logger.info("Running Baseline 3: One-shot reasoning")
        results['one_shot'] = await self.run_one_shot_baseline(games_2024)

        # Trial 1: Deliberate (Draft -> Critic/Repair) without tools
        logger.info("Running Trial 1: Deliberate reasoning (no tools)")
        results['deliberate_no_tools'] = await self.run_deliberate_trial(games_2024, enable_tools=False)

        # Trial 2: Deliberate with tools
        logger.info("Running Trial 2: Deliberate reasoning (with tools)")
        results['deliberate_with_tools'] = await self.run_deliberate_trial(games_2024, enable_tools=True)

        return results

    async def train_expert_chronologically(
        self,
        expert_id: str,
        start_date: str,
        end_date: str,
        enable_tools: bool,
        enable_stakes: bool
    ) -> Dict:
        """Train single expert chronologically through date range"""

        logger.info(f"Training {expert_id} from {start_date} to {end_date} (tools: {enable_tools})")

        games = await self.get_games_for_period(start_date, end_date)

        results = {
            'games_processed': 0,
            'schema_valid_rate': 0.0,
            'avg_latency_ms': 0.0,
            'memory_growth': [],
            'learning_progression': []
        }

        for i, game in enumerate(games):
            try:
                # Generate predictions for this game
                prediction_result = await self.agentuity.generate_expert_predictions(
                    expert_id=expert_id,
                    game_id=game['game_id'],
                    enable_tools=enable_tools,
                    reasoning_mode='deliberate' if enable_tools else 'one_shot'
                )

                # Validate schema
                is_valid = self.validator.validate_expert_predictions(prediction_result)

                # Store for learning (even if stakes are 0)
                await self.store_learning_predictions(
                    expert_id=expert_id,
                    game_id=game['game_id'],
                    predictions=prediction_result,
                    enable_stakes=enable_stakes
                )

                # Update results
                results['games_processed'] += 1
                results['schema_valid_rate'] = (
                    (results['schema_valid_rate'] * (i) + (1 if is_valid else 0)) / (i + 1)
                )

                # Track memory growth every 10 games
                if i % 10 == 0:
                    memory_count = await self.get_expert_memory_count(expert_id)
                    results['memory_growth'].append({
                        'game_index': i,
                        'memory_count': memory_count,
                        'date': game['game_date']
                    })

                # Log progress
                if i % 50 == 0:
                    logger.info(f"{expert_id}: Processed {i+1}/{len(games)} games")

            except Exception as e:
                logger.error(f"Error training {expert_id} on game {game['game_id']}: {e}")
                continue

        return results

    async def run_coin_flip_baseline(self, games: List[Dict]) -> BaselineResult:
        """Baseline 1: Random coin-flip predictions"""

        total_correct = 0
        total_brier = 0.0
        total_roi = 0.0

        for game in games:
            # Random predictions for each category
            predictions = self.generate_coin_flip_predictions()

            # Simulate outcomes and scoring
            game_result = await self.get_game_outcome(game['game_id'])
            if game_result:
                correct, brier, roi = self.score_predictions(predictions, game_result)
                total_correct += correct
                total_brier += brier
                total_roi += roi

        return BaselineResult(
            name="Coin-flip",
            win_rate=total_correct / len(games) if games else 0,
            brier_score=total_brier / len(games) if games else 0.5,
            roi=total_roi,
            total_games=len(games)
        )

    async def run_market_only_baseline(self, games: List[Dict]) -> BaselineResult:
        """Baseline 2: Use closing line implied probabilities"""

        total_correct = 0
        total_brier = 0.0
        total_roi = 0.0

        for game in games:
            # Get closing lines and convert to implied probabilities
            market_lines = await self.get_closing_lines(game['game_id'])
            predictions = self.generate_market_based_predictions(market_lines)

            # Score against actual outcomes
            game_result = await self.get_game_outcome(game['game_id'])
            if game_result:
                correct, brier, roi = self.score_predictions(predictions, game_result)
                total_correct += correct
                total_brier += brier
                total_roi += roi

        return BaselineResult(
            name="Market-only",
            win_rate=total_correct / len(games) if games else 0,
            brier_score=total_brier / len(games) if games else 0.5,
            roi=total_roi,
            total_games=len(games)
        )

    async def run_deliberate_trial(self, games: List[Dict], enable_tools: bool) -> Dict:
        """Run deliberate reasoning trial with Draft->Critic->Repair"""

        expert_results = {}

        for expert_id in self.pilot_experts:
            logger.info(f"Running deliberate trial for {expert_id} (tools: {enable_tools})")

            expert_metrics = {
                'total_correct': 0,
                'total_brier': 0.0,
                'total_roi': 0.0,
                'schema_valid_count': 0,
                'avg_latency_ms': 0.0,
                'reasoning_mode_distribution': {'deliberate': 0, 'one_shot': 0, 'degraded': 0}
            }

            for game in games:
                try:
                    # Generate predictions with deliberate reasoning
                    result = await self.agentuity.generate_expert_predictions(
                        expert_id=expert_id,
                        game_id=game['game_id'],
                        enable_tools=enable_tools,
                        reasoning_mode='deliberate'
                    )

                    # Track reasoning mode used
                    mode = result.get('reasoningMode', 'unknown')
                    expert_metrics['reasoning_mode_distribution'][mode] += 1

                    # Validate and score
                    is_valid = self.validator.validate_expert_predictions(result)
                    if is_valid:
                        expert_metrics['schema_valid_count'] += 1

                    # Score predictions
                    game_result = await self.get_game_outcome(game['game_id'])
                    if game_result:
                        correct, brier, roi = self.score_predictions(result['predictions'], game_result)
                        expert_metrics['total_correct'] += correct
                        expert_metrics['total_brier'] += brier
                        expert_metrics['total_roi'] += roi

                    # Track latency
                    latency = result.get('processingTimeMs', 0)
                    expert_metrics['avg_latency_ms'] = (
                        (expert_metrics['avg_latency_ms'] * len(expert_results) + latency) /
                        (len(expert_results) + 1)
                    )

                except Exception as e:
                    logger.error(f"Error in deliberate trial for {expert_id}: {e}")
                    continue

            # Calculate final metrics
            total_games = len(games)
            expert_results[expert_id] = {
                'win_rate': expert_metrics['total_correct'] / total_games if total_games else 0,
                'brier_score': expert_metrics['total_brier'] / total_games if total_games else 0.5,
                'roi': expert_metrics['total_roi'],
                'schema_valid_rate': expert_metrics['schema_valid_count'] / total_games if total_games else 0,
                'avg_latency_ms': expert_metrics['avg_latency_ms'],
                'reasoning_modes': expert_metrics['reasoning_mode_distribution']
            }

        return expert_results

    def evaluate_go_no_go(self, phase_b_results: Dict) -> Dict:
        """Evaluate whether to proceed to full 15-expert system"""

        # Go/No-Go criteria from the plan
        criteria = {
            'deliberate_vs_oneshot_brier_improvement': 0.02,  # +2% Brier improvement
            'roi_vs_market_only': 0.0,  # ROI >= market-only
            'retrieval_p95_threshold_ms': 100,  # p95 <= 100ms
            'schema_error_rate_threshold': 0.015  # < 1.5% schema errors
        }

        results = {
            'proceed_to_full_system': True,
            'criteria_met': {},
            'recommendations': []
        }

        # Check each criterion
        deliberate_results = phase_b_results.get('deliberate_no_tools', {})
        oneshot_results = phase_b_results.get('one_shot', {})
        market_results = phase_b_results.get('market_only', {})

        # 1. Deliberate vs One-shot Brier improvement
        if deliberate_results and oneshot_results:
            deliberate_brier = np.mean([r['brier_score'] for r in deliberate_results.values()])
            oneshot_brier = np.mean([r['brier_score'] for r in oneshot_results.values()])
            brier_improvement = oneshot_brier - deliberate_brier  # Lower is better

            meets_brier = brier_improvement >= criteria['deliberate_vs_oneshot_brier_improvement']
            results['criteria_met']['brier_improvement'] = {
                'met': meets_brier,
                'value': brier_improvement,
                'threshold': criteria['deliberate_vs_oneshot_brier_improvement']
            }

            if not meets_brier:
                results['proceed_to_full_system'] = False
                results['recommendations'].append(
                    f"Deliberate reasoning only improved Brier by {brier_improvement:.3f}, "
                    f"need {criteria['deliberate_vs_oneshot_brier_improvement']:.3f}"
                )

        # 2. ROI vs Market-only
        if deliberate_results and market_results:
            deliberate_roi = np.mean([r['roi'] for r in deliberate_results.values()])
            market_roi = market_results.roi

            meets_roi = deliberate_roi >= market_roi
            results['criteria_met']['roi_vs_market'] = {
                'met': meets_roi,
                'deliberate_roi': deliberate_roi,
                'market_roi': market_roi
            }

            if not meets_roi:
                results['proceed_to_full_system'] = False
                results['recommendations'].append(
                    f"Deliberate ROI ({deliberate_roi:.3f}) below market-only ({market_roi:.3f})"
                )

        # 3. Schema error rate
        if deliberate_results:
            schema_rates = [r['schema_valid_rate'] for r in deliberate_results.values()]
            avg_schema_rate = np.mean(schema_rates)
            error_rate = 1.0 - avg_schema_rate

            meets_schema = error_rate < criteria['schema_error_rate_threshold']
            results['criteria_met']['schema_errors'] = {
                'met': meets_schema,
                'error_rate': error_rate,
                'threshold': criteria['schema_error_rate_threshold']
            }

            if not meets_schema:
                results['proceed_to_full_system'] = False
                results['recommendations'].append(
                    f"Schema error rate ({error_rate:.3f}) above threshold "
                    f"({criteria['schema_error_rate_threshold']:.3f})"
                )

        # 4. Latency check (would need retrieval metrics)
        # This would be implemented with actual retrieval timing data

        return results

    def generate_training_report(self, results: Dict) -> str:
        """Generate comprehensive training report"""

        report = []
        report.append("# 4-Expert Pilot Training Report")
        report.append(f"Generated: {datetime.utcnow().isoformat()}")
        report.append("")

        # Phase A Summary
        if 'phase_a' in results:
            report.append("## Phase A: Learning (2020-2023)")
            phase_a = results['phase_a']

            for track in ['no_tools', 'with_tools']:
                if track in phase_a:
                    report.append(f"### Track: {track.replace('_', ' ').title()}")
                    for expert_id, expert_results in phase_a[track].items():
                        report.append(f"- **{expert_id}**: {expert_results['games_processed']} games, "
                                    f"{expert_results['schema_valid_rate']:.1%} schema valid")
            report.append("")

        # Phase B Summary
        if 'phase_b' in results:
            report.append("## Phase B: 2024 Backtest Results")
            phase_b = results['phase_b']

            # Baselines
            report.append("### Baselines")
            for baseline_name in ['coin_flip', 'market_only']:
                if baseline_name in phase_b:
                    baseline = phase_b[baseline_name]
                    report.append(f"- **{baseline.name}**: {baseline.win_rate:.1%} win rate, "
                                f"{baseline.brier_score:.3f} Brier, {baseline.roi:.2f} ROI")

            # Trials
            report.append("### Expert Trials")
            for trial_name in ['deliberate_no_tools', 'deliberate_with_tools']:
                if trial_name in phase_b:
                    report.append(f"#### {trial_name.replace('_', ' ').title()}")
                    trial_results = phase_b[trial_name]
                    for expert_id, metrics in trial_results.items():
                        report.append(f"- **{expert_id}**: {metrics['win_rate']:.1%} win rate, "
                                    f"{metrics['brier_score']:.3f} Brier, {metrics['roi']:.2f} ROI")
            report.append("")

        # Go/No-Go Decision
        if 'go_no_go' in results:
            decision = results['go_no_go']
            report.append("## Go/No-Go Decision")
            report.append(f"**Decision: {'✅ GO' if decision['proceed_to_full_system'] else '❌ NO-GO'}**")

            if decision['recommendations']:
                report.append("### Recommendations:")
                for rec in decision['recommendations']:
                    report.append(f"- {rec}")
            report.append("")

        return "\n".join(report)

    async def save_training_results(self, results: Dict, report: str):
        """Save training results and report"""

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Save JSON results
        results_path = Path(f"data/training_results_{timestamp}.json")
        results_path.parent.mkdir(exist_ok=True)

        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        # Save report
        report_path = Path(f"data/training_report_{timestamp}.md")
        with open(report_path, 'w') as f:
            f.write(report)

        logger.info(f"Training results saved to {results_path}")
        logger.info(f"Training report saved to {report_path}")

    # Helper methods
    async def get_games_for_period(self, start_date: str, end_date: str) -> List[Dict]:
        """Get games for date range"""
        query = """
        SELECT game_id, game_date, home_team, away_team
        FROM games
        WHERE game_date >= %s AND game_date <= %s
        ORDER BY game_date ASC
        """
        result = await self.supabase.execute_query(query, (start_date, end_date))
        return result.data or []

    def generate_coin_flip_predictions(self) -> List[Dict]:
        """Generate random coin-flip predictions"""
        # This would generate 83 random predictions
        return []

    def score_predictions(self, predictions: List[Dict], game_result: Dict) -> Tuple[int, float, float]:
        """Score predictions against actual outcome"""
        # Placeholder - would implement actual scoring logic
        return 0, 0.5, 0.0

# Main execution
async def main():
    trainer = FourExpertPilotTrainer()
    results = await trainer.run_full_training_pipeline()
    print("Training pipeline completed!")
    print(f"Go decision: {results.get('go_no_go', {}).get('proceed_to_full_system', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(main())
