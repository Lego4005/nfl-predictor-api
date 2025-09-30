"""
Backtest Runner for Expert Prediction System
Replays historical seasons to validate expert accuracy
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.backtesting.historical_data_loader import HistoricalDataLoader, NFLGame
from tests.backtesting.metrics import MetricsCalculator, Prediction, PredictionResult


@dataclass
class ExpertConfig:
    """Configuration for an expert to backtest"""
    expert_id: str
    name: str
    archetype: str
    starting_bankroll: float = 10000.0
    min_confidence_threshold: float = 0.70
    kelly_fraction: float = 0.25


class BacktestRunner:
    """
    Run backtests on historical NFL data
    Simulates expert predictions and tracks performance
    """

    def __init__(self, experts: List[ExpertConfig] = None):
        """
        Initialize backtest runner

        Args:
            experts: List of expert configurations to test
        """
        self.loader = HistoricalDataLoader()
        self.metrics_calc = MetricsCalculator()

        # Default experts if none provided
        self.experts = experts or self._create_default_experts()

        # Track state
        self.bankrolls = {e.expert_id: e.starting_bankroll for e in self.experts}
        self.all_results: List[PredictionResult] = []
        self.weekly_results: Dict[int, List[PredictionResult]] = {}
        self.eliminated_experts: List[str] = []

    def _create_default_experts(self) -> List[ExpertConfig]:
        """Create default expert configurations"""
        return [
            ExpertConfig("quant_master", "The Quant Master", "data_driven", 10000, 0.70, 0.25),
            ExpertConfig("veteran", "The Veteran", "experience", 10000, 0.75, 0.20),
            ExpertConfig("gambler", "The Gambler", "high_risk", 10000, 0.65, 0.40),
            ExpertConfig("contrarian", "The Rebel", "contrarian", 10000, 0.70, 0.30),
            ExpertConfig("conservative", "The Conservative", "safe", 10000, 0.80, 0.15),
        ]

    def replay_season(self, year: int, verbose: bool = True) -> Dict:
        """
        Replay an entire season week by week

        Args:
            year: Season year to replay
            verbose: Whether to print progress

        Returns:
            Dictionary of season metrics
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"Starting Backtest: {year} NFL Season")
            print(f"{'='*80}")
            print(f"Experts: {len(self.experts)}")
            print(f"Starting Bankrolls: ${self.experts[0].starting_bankroll:,.2f}")
            print(f"{'='*80}\n")

        # Reset state
        self.bankrolls = {e.expert_id: e.starting_bankroll for e in self.experts}
        self.all_results = []
        self.weekly_results = {}
        self.eliminated_experts = []

        # Load all games for the season
        all_games = self.loader.load_season(year)
        max_week = max(g.week for g in all_games)

        # Replay each week
        for week in range(1, max_week + 1):
            week_games = [g for g in all_games if g.week == week]

            if verbose:
                print(f"\n--- Week {week} ---")
                print(f"Games: {len(week_games)}")

            week_results = self.replay_week(week, week_games, verbose=verbose)
            self.weekly_results[week] = week_results

            # Check for eliminations
            self._check_eliminations(week, verbose)

            if verbose:
                self._print_week_summary(week, week_results)

        # Calculate final metrics
        final_metrics = self.calculate_final_metrics(year)

        if verbose:
            self._print_season_summary(final_metrics)

        return final_metrics

    def replay_week(self, week_num: int, games: List[NFLGame],
                    verbose: bool = False) -> List[PredictionResult]:
        """
        Replay a single week of games

        Args:
            week_num: Week number
            games: List of games for the week
            verbose: Whether to print details

        Returns:
            List of prediction results for the week
        """
        week_results = []

        for game in games:
            # Generate predictions from each active expert
            for expert in self.experts:
                if expert.expert_id in self.eliminated_experts:
                    continue

                # Generate prediction
                prediction = self._generate_prediction(expert, game)

                # Skip if confidence too low
                if prediction.confidence < expert.min_confidence_threshold:
                    continue

                # Calculate bet size
                current_bankroll = self.bankrolls[expert.expert_id]
                bet_size = self.metrics_calc.calculate_kelly_bet_size(
                    current_bankroll,
                    prediction.confidence,
                    prediction.odds,
                    expert.kelly_fraction
                )

                # Skip if bet size too small
                if bet_size < 10:
                    continue

                prediction.bet_amount = bet_size

                # Evaluate prediction
                result = self._evaluate_prediction(prediction, game)

                # Update bankroll
                self.bankrolls[expert.expert_id] += result.payout

                # Store result
                week_results.append(result)
                self.all_results.append(result)

        return week_results

    def _generate_prediction(self, expert: ExpertConfig, game: NFLGame) -> Prediction:
        """
        Generate a prediction for a game (simplified model)

        In production, this would call the actual expert ML model.
        For backtesting, we simulate reasonable predictions.

        Args:
            expert: Expert configuration
            game: Game to predict

        Returns:
            Prediction object
        """
        import random

        # Simulate prediction based on expert archetype
        if expert.archetype == "data_driven":
            # Quant master: High accuracy, moderate confidence
            base_accuracy = 0.58
            confidence = random.uniform(0.70, 0.85)
        elif expert.archetype == "high_risk":
            # Gambler: Lower accuracy, high confidence
            base_accuracy = 0.52
            confidence = random.uniform(0.75, 0.95)
        elif expert.archetype == "safe":
            # Conservative: Good accuracy, lower confidence
            base_accuracy = 0.56
            confidence = random.uniform(0.70, 0.80)
        elif expert.archetype == "contrarian":
            # Rebel: Variable accuracy, high confidence
            base_accuracy = 0.54
            confidence = random.uniform(0.65, 0.90)
        else:
            # Veteran: Balanced
            base_accuracy = 0.55
            confidence = random.uniform(0.70, 0.85)

        # Determine if prediction will be correct (probabilistically)
        correct = random.random() < base_accuracy

        # Generate prediction
        if correct:
            prediction_str = game.spread_result
        else:
            # Predict wrong
            if game.spread_result == "HOME_COVERS":
                prediction_str = "AWAY_COVERS"
            elif game.spread_result == "AWAY_COVERS":
                prediction_str = "HOME_COVERS"
            else:
                prediction_str = random.choice(["HOME_COVERS", "AWAY_COVERS"])

        return Prediction(
            expert_id=expert.expert_id,
            game_id=game.game_id,
            prediction_type="spread",
            prediction=prediction_str,
            confidence=confidence,
            odds="-110"
        )

    def _evaluate_prediction(self, prediction: Prediction,
                            game: NFLGame) -> PredictionResult:
        """
        Evaluate a prediction against actual game result

        Args:
            prediction: Expert prediction
            game: Actual game result

        Returns:
            PredictionResult with outcome
        """
        actual_result = game.spread_result
        correct = prediction.prediction == actual_result

        # Handle pushes
        if actual_result == "PUSH":
            payout = 0.0
        else:
            payout = self.metrics_calc.calculate_payout(
                prediction.bet_amount,
                prediction.odds,
                correct
            )

        return PredictionResult(
            prediction=prediction,
            actual_result=actual_result,
            correct=correct,
            payout=payout
        )

    def _check_eliminations(self, week: int, verbose: bool = True):
        """Check if any experts should be eliminated"""
        for expert in self.experts:
            if expert.expert_id in self.eliminated_experts:
                continue

            current_bankroll = self.bankrolls[expert.expert_id]

            # Eliminate if bankroll drops to $1000 or below
            if current_bankroll <= 1000:
                self.eliminated_experts.append(expert.expert_id)

                if verbose:
                    print(f"  ❌ {expert.name} ELIMINATED (Bankroll: ${current_bankroll:.2f})")

    def _print_week_summary(self, week: int, results: List[PredictionResult]):
        """Print summary for a week"""
        if not results:
            print("  No predictions made this week")
            return

        accuracy = self.metrics_calc.calculate_accuracy(results)
        total_wagered = sum(r.prediction.bet_amount for r in results)
        net_profit = sum(r.payout for r in results)

        print(f"  Predictions: {len(results)}")
        print(f"  Accuracy: {accuracy:.1f}%")
        print(f"  Wagered: ${total_wagered:,.2f}")
        print(f"  Net Profit: ${net_profit:+,.2f}")

        # Show top performers
        print("\n  Expert Bankrolls:")
        bankroll_items = sorted(self.bankrolls.items(), key=lambda x: x[1], reverse=True)
        for expert_id, bankroll in bankroll_items:
            if expert_id not in self.eliminated_experts:
                expert = next(e for e in self.experts if e.expert_id == expert_id)
                change = bankroll - expert.starting_bankroll
                print(f"    {expert.name}: ${bankroll:,.2f} ({change:+,.2f})")

    def _print_season_summary(self, metrics: Dict):
        """Print final season summary"""
        print(f"\n{'='*80}")
        print(f"Season Complete: {metrics['season']}")
        print(f"{'='*80}")

        print(f"\nOverall Performance:")
        print(f"  Total Predictions: {metrics['total_predictions']}")
        print(f"  Overall Accuracy: {metrics['overall_accuracy']:.2f}%")
        print(f"  ATS Accuracy: {metrics['ats_accuracy']:.2f}%")
        print(f"  Total ROI: {metrics['overall_roi']:.2f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")

        print(f"\nExpert Results:")
        for expert_metrics in metrics['expert_metrics']:
            if expert_metrics['expert_id'] not in self.eliminated_experts:
                print(f"\n  {expert_metrics['expert_id']}:")
                print(f"    Accuracy: {expert_metrics['accuracy']:.2f}%")
                print(f"    ROI: {expert_metrics['roi']:.2f}%")
                print(f"    Final Bankroll: ${self.bankrolls[expert_metrics['expert_id']]:,.2f}")
                print(f"    Net Profit: ${expert_metrics['net_profit']:+,.2f}")
                print(f"    Calibration (ECE): {expert_metrics['ece']:.3f}")

        if self.eliminated_experts:
            print(f"\nEliminated Experts: {len(self.eliminated_experts)}")
            for expert_id in self.eliminated_experts:
                expert = next(e for e in self.experts if e.expert_id == expert_id)
                print(f"  - {expert.name}")

    def calculate_final_metrics(self, year: int) -> Dict:
        """Calculate comprehensive final metrics"""
        expert_metrics = []

        for expert in self.experts:
            metrics = self.metrics_calc.calculate_expert_metrics(
                self.all_results,
                expert.expert_id
            )
            expert_metrics.append(metrics)

        return {
            "season": year,
            "total_predictions": len(self.all_results),
            "overall_accuracy": self.metrics_calc.calculate_accuracy(self.all_results),
            "ats_accuracy": self.metrics_calc.calculate_ats_accuracy(self.all_results),
            "overall_roi": self.metrics_calc.calculate_roi(self.all_results),
            "sharpe_ratio": self.metrics_calc.calculate_sharpe_ratio(self.all_results),
            "expert_metrics": expert_metrics,
            "eliminations": len(self.eliminated_experts),
            "eliminated_experts": self.eliminated_experts,
            "final_bankrolls": dict(self.bankrolls)
        }

    def export_results(self, output_file: str):
        """Export backtest results to JSON"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert results to serializable format
        results_data = []
        for result in self.all_results:
            results_data.append({
                "expert_id": result.prediction.expert_id,
                "game_id": result.prediction.game_id,
                "prediction": result.prediction.prediction,
                "confidence": result.prediction.confidence,
                "bet_amount": result.prediction.bet_amount,
                "actual_result": result.actual_result,
                "correct": result.correct,
                "payout": result.payout
            })

        export_data = {
            "timestamp": datetime.now().isoformat(),
            "experts": [e.__dict__ for e in self.experts],
            "results": results_data,
            "final_bankrolls": self.bankrolls,
            "eliminated_experts": self.eliminated_experts
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"\nResults exported to: {output_path}")


if __name__ == "__main__":
    # Run backtest
    runner = BacktestRunner()

    # Ensure sample data exists
    loader = HistoricalDataLoader()
    if not loader.get_available_seasons():
        print("Creating sample historical data...")
        loader.create_sample_data(2023, 18)
        loader.create_sample_data(2024, 18)

    # Run 2023 season
    metrics_2023 = runner.replay_season(2023, verbose=True)

    # Export results
    runner.export_results("/home/iris/code/experimental/nfl-predictor-api/tests/reports/backtest_2023.json")

    print("\n" + "="*80)
    print("Backtest Complete!")
    print("="*80)