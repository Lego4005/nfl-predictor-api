"""
Metrics Calculator for Backtesting
Calculates accuracy, ROI, Sharpe ratio, calibration scores
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Prediction:
    """Expert prediction for backtesting"""
    expert_id: str
    game_id: str
    prediction_type: str  # "spread", "total", "moneyline"
    prediction: str  # "HOME_COVERS", "OVER", "HOME_WIN", etc.
    confidence: float  # 0.0 to 1.0
    bet_amount: float = 0.0
    odds: str = "-110"  # American odds


@dataclass
class PredictionResult:
    """Result of a prediction"""
    prediction: Prediction
    actual_result: str
    correct: bool
    payout: float  # Net payout (positive = win, negative = loss, 0 = push)


class MetricsCalculator:
    """Calculate various performance metrics for experts"""

    @staticmethod
    def calculate_accuracy(results: List[PredictionResult]) -> float:
        """
        Calculate overall prediction accuracy

        Args:
            results: List of prediction results

        Returns:
            Accuracy as percentage (0-100)
        """
        if not results:
            return 0.0

        correct = sum(1 for r in results if r.correct)
        return (correct / len(results)) * 100

    @staticmethod
    def calculate_ats_accuracy(results: List[PredictionResult]) -> float:
        """
        Calculate against-the-spread (ATS) accuracy

        Args:
            results: List of prediction results (should be spread predictions)

        Returns:
            ATS accuracy as percentage
        """
        spread_results = [
            r for r in results
            if r.prediction.prediction_type == "spread"
        ]

        if not spread_results:
            return 0.0

        correct = sum(1 for r in spread_results if r.correct)
        return (correct / len(spread_results)) * 100

    @staticmethod
    def calculate_roi(results: List[PredictionResult]) -> float:
        """
        Calculate return on investment (ROI)

        Args:
            results: List of prediction results with bet amounts

        Returns:
            ROI as percentage
        """
        if not results:
            return 0.0

        total_wagered = sum(r.prediction.bet_amount for r in results)
        total_profit = sum(r.payout for r in results)

        if total_wagered == 0:
            return 0.0

        return (total_profit / total_wagered) * 100

    @staticmethod
    def calculate_sharpe_ratio(results: List[PredictionResult],
                               risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio for risk-adjusted returns

        Args:
            results: List of prediction results
            risk_free_rate: Risk-free rate (default 0)

        Returns:
            Sharpe ratio
        """
        if not results:
            return 0.0

        # Calculate returns per bet
        returns = []
        for r in results:
            if r.prediction.bet_amount > 0:
                roi = r.payout / r.prediction.bet_amount
                returns.append(roi)

        if not returns:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        return (mean_return - risk_free_rate) / std_return

    @staticmethod
    def calculate_calibration_ece(results: List[PredictionResult],
                                   num_bins: int = 10) -> float:
        """
        Calculate Expected Calibration Error (ECE)
        Measures how well confidence matches actual accuracy

        Args:
            results: List of prediction results
            num_bins: Number of confidence bins

        Returns:
            ECE score (0 = perfect calibration, higher = worse)
        """
        if not results:
            return 1.0

        # Create confidence bins
        bins = defaultdict(list)
        bin_size = 1.0 / num_bins

        for result in results:
            bin_idx = min(int(result.prediction.confidence / bin_size), num_bins - 1)
            bins[bin_idx].append(result.correct)

        # Calculate ECE
        ece = 0.0
        total_predictions = len(results)

        for bin_idx, correct_list in bins.items():
            bin_confidence = (bin_idx + 0.5) * bin_size
            bin_accuracy = sum(correct_list) / len(correct_list)
            bin_weight = len(correct_list) / total_predictions

            ece += bin_weight * abs(bin_confidence - bin_accuracy)

        return ece

    @staticmethod
    def calculate_calibration_curve(results: List[PredictionResult],
                                     num_bins: int = 10) -> Tuple[List[float], List[float]]:
        """
        Calculate calibration curve data

        Args:
            results: List of prediction results
            num_bins: Number of confidence bins

        Returns:
            Tuple of (confidence_levels, accuracy_levels)
        """
        if not results:
            return [], []

        bins = defaultdict(list)
        bin_size = 1.0 / num_bins

        for result in results:
            bin_idx = min(int(result.prediction.confidence / bin_size), num_bins - 1)
            bins[bin_idx].append(result.correct)

        confidences = []
        accuracies = []

        for bin_idx in range(num_bins):
            if bin_idx in bins:
                bin_confidence = (bin_idx + 0.5) * bin_size
                bin_accuracy = sum(bins[bin_idx]) / len(bins[bin_idx])

                confidences.append(bin_confidence)
                accuracies.append(bin_accuracy)

        return confidences, accuracies

    @staticmethod
    def calculate_expert_metrics(results: List[PredictionResult],
                                  expert_id: str) -> Dict:
        """
        Calculate comprehensive metrics for a specific expert

        Args:
            results: All prediction results
            expert_id: Expert identifier

        Returns:
            Dictionary of metrics
        """
        expert_results = [r for r in results if r.prediction.expert_id == expert_id]

        if not expert_results:
            return {
                "expert_id": expert_id,
                "total_predictions": 0,
                "accuracy": 0.0,
                "ats_accuracy": 0.0,
                "roi": 0.0,
                "sharpe_ratio": 0.0,
                "ece": 1.0
            }

        return {
            "expert_id": expert_id,
            "total_predictions": len(expert_results),
            "accuracy": MetricsCalculator.calculate_accuracy(expert_results),
            "ats_accuracy": MetricsCalculator.calculate_ats_accuracy(expert_results),
            "roi": MetricsCalculator.calculate_roi(expert_results),
            "sharpe_ratio": MetricsCalculator.calculate_sharpe_ratio(expert_results),
            "ece": MetricsCalculator.calculate_calibration_ece(expert_results),
            "total_wagered": sum(r.prediction.bet_amount for r in expert_results),
            "net_profit": sum(r.payout for r in expert_results),
            "wins": sum(1 for r in expert_results if r.correct),
            "losses": sum(1 for r in expert_results if not r.correct and r.payout != 0),
            "pushes": sum(1 for r in expert_results if r.payout == 0)
        }

    @staticmethod
    def calculate_weekly_performance(results: List[PredictionResult],
                                     week: int) -> Dict:
        """Calculate performance metrics for a specific week"""
        week_results = [r for r in results]  # Filter by week if needed

        if not week_results:
            return {
                "week": week,
                "accuracy": 0.0,
                "roi": 0.0
            }

        return {
            "week": week,
            "total_predictions": len(week_results),
            "accuracy": MetricsCalculator.calculate_accuracy(week_results),
            "roi": MetricsCalculator.calculate_roi(week_results),
            "total_wagered": sum(r.prediction.bet_amount for r in week_results),
            "net_profit": sum(r.payout for r in week_results)
        }

    @staticmethod
    def odds_to_probability(american_odds: str) -> float:
        """
        Convert American odds to implied probability

        Args:
            american_odds: American odds string (e.g., "-110", "+150")

        Returns:
            Implied probability (0-1)
        """
        odds_value = int(american_odds)

        if odds_value < 0:
            # Negative odds (favorite)
            return abs(odds_value) / (abs(odds_value) + 100)
        else:
            # Positive odds (underdog)
            return 100 / (odds_value + 100)

    @staticmethod
    def calculate_payout(bet_amount: float, american_odds: str, won: bool) -> float:
        """
        Calculate payout from a bet

        Args:
            bet_amount: Amount wagered
            american_odds: American odds
            won: Whether bet won

        Returns:
            Net payout (positive = profit, negative = loss)
        """
        if not won:
            return -bet_amount

        odds_value = int(american_odds)

        if odds_value < 0:
            # Negative odds (favorite)
            profit = bet_amount * (100 / abs(odds_value))
        else:
            # Positive odds (underdog)
            profit = bet_amount * (odds_value / 100)

        return profit

    @staticmethod
    def calculate_kelly_bet_size(bankroll: float,
                                  confidence: float,
                                  american_odds: str,
                                  kelly_fraction: float = 0.25) -> float:
        """
        Calculate optimal bet size using Kelly Criterion

        Args:
            bankroll: Current bankroll
            confidence: Expert's confidence (0-1)
            american_odds: American odds
            kelly_fraction: Fraction of Kelly to use (0.25 = quarter Kelly)

        Returns:
            Recommended bet size
        """
        # Convert odds to decimal
        odds_value = int(american_odds)
        if odds_value < 0:
            decimal_odds = 1 + (100 / abs(odds_value))
        else:
            decimal_odds = 1 + (odds_value / 100)

        # Kelly formula: f* = (bp - q) / b
        # where b = decimal odds - 1, p = probability of win, q = 1-p
        b = decimal_odds - 1
        p = confidence
        q = 1 - p

        kelly_pct = (b * p - q) / b

        # Apply fraction and ensure non-negative
        kelly_pct = max(0, kelly_pct * kelly_fraction)

        # Cap at 20% of bankroll for safety
        kelly_pct = min(0.20, kelly_pct)

        return bankroll * kelly_pct


if __name__ == "__main__":
    # Example usage and testing
    print("Testing Metrics Calculator")
    print("="*60)

    # Create sample predictions and results
    sample_results = [
        PredictionResult(
            prediction=Prediction("expert_1", "game_1", "spread", "HOME_COVERS", 0.85, 100, "-110"),
            actual_result="HOME_COVERS",
            correct=True,
            payout=90.91
        ),
        PredictionResult(
            prediction=Prediction("expert_1", "game_2", "spread", "AWAY_COVERS", 0.75, 75, "-110"),
            actual_result="HOME_COVERS",
            correct=False,
            payout=-75
        ),
        PredictionResult(
            prediction=Prediction("expert_1", "game_3", "spread", "HOME_COVERS", 0.90, 150, "-110"),
            actual_result="HOME_COVERS",
            correct=True,
            payout=136.36
        ),
    ]

    # Calculate metrics
    accuracy = MetricsCalculator.calculate_accuracy(sample_results)
    roi = MetricsCalculator.calculate_roi(sample_results)
    sharpe = MetricsCalculator.calculate_sharpe_ratio(sample_results)
    ece = MetricsCalculator.calculate_calibration_ece(sample_results)

    print(f"Accuracy: {accuracy:.2f}%")
    print(f"ROI: {roi:.2f}%")
    print(f"Sharpe Ratio: {sharpe:.3f}")
    print(f"ECE: {ece:.3f}")

    # Test Kelly Criterion
    print("\n" + "="*60)
    print("Kelly Criterion Bet Sizing")
    print("="*60)

    bankroll = 10000
    confidence = 0.60
    odds = "-110"

    bet_size = MetricsCalculator.calculate_kelly_bet_size(bankroll, confidence, odds)
    print(f"Bankroll: ${bankroll}")
    print(f"Confidence: {confidence*100:.1f}%")
    print(f"Odds: {odds}")
    print(f"Recommended Bet: ${bet_size:.2f} ({(bet_size/bankroll)*100:.2f}% of bankroll)")