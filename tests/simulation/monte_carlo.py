"""
Monte Carlo Simulator for NFL Expert Prediction System
Simulates thousands of seasons to analyze risk and elimination probabilities
"""

import numpy as np
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt


@dataclass
class SimulationConfig:
    """Configuration for Monte Carlo simulation"""
    num_simulations: int = 1000
    num_weeks: int = 18
    games_per_week: int = 16
    starting_bankroll: float = 10000.0
    min_confidence: float = 0.70
    kelly_fraction: float = 0.25
    elimination_threshold: float = 1000.0
    base_accuracy: float = 0.55  # Base accuracy for experts
    accuracy_std: float = 0.05  # Variation in accuracy


@dataclass
class ExpertProfile:
    """Expert profile for simulation"""
    expert_id: str
    name: str
    base_accuracy: float
    accuracy_variance: float  # How consistent the expert is
    risk_tolerance: float  # Kelly fraction multiplier
    confidence_bias: float  # Overconfidence factor


class MonteCarloSimulator:
    """
    Simulate many seasons to analyze:
    - Bankroll trajectories
    - Elimination probabilities
    - Risk metrics
    - Expected outcomes
    """

    def __init__(self, config: SimulationConfig = None):
        """
        Initialize simulator

        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()
        self.experts = self._create_expert_profiles()

        # Results storage
        self.simulation_results: List[Dict] = []
        self.bankroll_trajectories: Dict[str, List[List[float]]] = {
            e.expert_id: [] for e in self.experts
        }

    def _create_expert_profiles(self) -> List[ExpertProfile]:
        """Create diverse expert profiles"""
        return [
            ExpertProfile("quant_master", "The Quant Master", 0.58, 0.03, 1.0, 0.02),
            ExpertProfile("veteran", "The Veteran", 0.56, 0.04, 0.8, 0.05),
            ExpertProfile("gambler", "The Gambler", 0.52, 0.08, 1.6, 0.10),
            ExpertProfile("contrarian", "The Rebel", 0.54, 0.06, 1.2, 0.08),
            ExpertProfile("conservative", "The Conservative", 0.56, 0.02, 0.6, 0.01),
            ExpertProfile("momentum", "The Momentum Trader", 0.53, 0.07, 1.3, 0.12),
            ExpertProfile("value", "The Value Hunter", 0.57, 0.04, 0.9, 0.03),
            ExpertProfile("emotional", "The Hot Head", 0.51, 0.10, 1.5, 0.15),
        ]

    def run_simulations(self, verbose: bool = True) -> Dict:
        """
        Run multiple season simulations

        Args:
            verbose: Whether to print progress

        Returns:
            Aggregated simulation results
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"Monte Carlo Simulation: {self.config.num_simulations} Seasons")
            print(f"{'='*80}")
            print(f"Experts: {len(self.experts)}")
            print(f"Weeks per season: {self.config.num_weeks}")
            print(f"Starting bankroll: ${self.config.starting_bankroll:,.2f}")
            print(f"{'='*80}\n")

        self.simulation_results = []
        self.bankroll_trajectories = {e.expert_id: [] for e in self.experts}

        for sim_num in range(self.config.num_simulations):
            if verbose and (sim_num + 1) % 100 == 0:
                print(f"Completed {sim_num + 1}/{self.config.num_simulations} simulations...")

            season_result = self._simulate_season()
            self.simulation_results.append(season_result)

            # Store trajectories
            for expert_id, trajectory in season_result['trajectories'].items():
                self.bankroll_trajectories[expert_id].append(trajectory)

        # Calculate aggregate statistics
        aggregate_stats = self._calculate_aggregate_stats()

        if verbose:
            self._print_simulation_summary(aggregate_stats)

        return aggregate_stats

    def _simulate_season(self) -> Dict:
        """Simulate a single season"""
        # Initialize bankrolls
        bankrolls = {e.expert_id: self.config.starting_bankroll for e in self.experts}
        trajectories = {e.expert_id: [self.config.starting_bankroll] for e in self.experts}
        eliminated = {e.expert_id: None for e in self.experts}  # Week of elimination

        # Simulate each week
        for week in range(1, self.config.num_weeks + 1):
            week_results = self._simulate_week(bankrolls, week)

            # Update bankrolls and check eliminations
            for expert in self.experts:
                expert_id = expert.expert_id

                # Skip if already eliminated
                if eliminated[expert_id] is not None:
                    trajectories[expert_id].append(bankrolls[expert_id])
                    continue

                # Update bankroll
                bankrolls[expert_id] = week_results[expert_id]
                trajectories[expert_id].append(bankrolls[expert_id])

                # Check elimination
                if bankrolls[expert_id] <= self.config.elimination_threshold:
                    eliminated[expert_id] = week

        return {
            'final_bankrolls': bankrolls,
            'trajectories': trajectories,
            'eliminated': eliminated,
            'num_eliminated': sum(1 for w in eliminated.values() if w is not None)
        }

    def _simulate_week(self, bankrolls: Dict[str, float], week: int) -> Dict[str, float]:
        """Simulate one week of betting"""
        new_bankrolls = {}

        for expert in self.experts:
            expert_id = expert.expert_id
            current_bankroll = bankrolls[expert_id]

            # Skip if eliminated
            if current_bankroll <= self.config.elimination_threshold:
                new_bankrolls[expert_id] = current_bankroll
                continue

            # Simulate bets for the week
            weekly_profit = 0.0
            num_bets = random.randint(8, 14)  # Random number of bets per week

            for _ in range(num_bets):
                # Generate random confidence
                confidence = np.random.beta(5, 2)  # Beta distribution skewed toward high confidence
                confidence = max(self.config.min_confidence, min(0.95, confidence))

                # Apply overconfidence bias
                stated_confidence = min(1.0, confidence + expert.confidence_bias)

                # Skip if below threshold
                if stated_confidence < self.config.min_confidence:
                    continue

                # Calculate bet size using Kelly Criterion
                kelly_fraction = self.config.kelly_fraction * expert.risk_tolerance
                bet_size = self._calculate_bet_size(
                    current_bankroll + weekly_profit,
                    stated_confidence,
                    kelly_fraction
                )

                # Simulate outcome
                actual_accuracy = np.random.normal(
                    expert.base_accuracy,
                    expert.accuracy_variance
                )
                actual_accuracy = max(0.4, min(0.7, actual_accuracy))  # Clamp

                won = random.random() < actual_accuracy

                # Calculate profit/loss
                if won:
                    profit = bet_size * (100 / 110)  # -110 odds
                else:
                    profit = -bet_size

                weekly_profit += profit

            new_bankrolls[expert_id] = current_bankroll + weekly_profit

        return new_bankrolls

    def _calculate_bet_size(self, bankroll: float, confidence: float,
                           kelly_fraction: float) -> float:
        """Calculate bet size using Kelly Criterion"""
        # Simplified Kelly for -110 odds
        # f* = (p * 1.909 - 1) / 0.909
        # where p is win probability

        kelly_pct = (confidence * 1.909 - 1) / 0.909
        kelly_pct = max(0, kelly_pct * kelly_fraction)
        kelly_pct = min(0.25, kelly_pct)  # Cap at 25%

        return bankroll * kelly_pct

    def _calculate_aggregate_stats(self) -> Dict:
        """Calculate aggregate statistics across all simulations"""
        stats = {}

        for expert in self.experts:
            expert_id = expert.expert_id

            # Extract all final bankrolls for this expert
            final_bankrolls = [
                sim['final_bankrolls'][expert_id]
                for sim in self.simulation_results
            ]

            # Extract elimination data
            eliminations = [
                sim['eliminated'][expert_id]
                for sim in self.simulation_results
            ]
            eliminated_count = sum(1 for e in eliminations if e is not None)

            # Calculate statistics
            stats[expert_id] = {
                'name': expert.name,
                'mean_final_bankroll': np.mean(final_bankrolls),
                'median_final_bankroll': np.median(final_bankrolls),
                'std_final_bankroll': np.std(final_bankrolls),
                'min_final_bankroll': np.min(final_bankrolls),
                'max_final_bankroll': np.max(final_bankrolls),
                'elimination_probability': eliminated_count / self.config.num_simulations,
                'profit_probability': sum(1 for b in final_bankrolls if b > self.config.starting_bankroll) / self.config.num_simulations,
                'ruin_probability': sum(1 for b in final_bankrolls if b <= 0) / self.config.num_simulations,
                'roi_mean': ((np.mean(final_bankrolls) - self.config.starting_bankroll) / self.config.starting_bankroll) * 100,
                'roi_median': ((np.median(final_bankrolls) - self.config.starting_bankroll) / self.config.starting_bankroll) * 100,
            }

        # Overall stats
        stats['overall'] = {
            'total_simulations': self.config.num_simulations,
            'avg_eliminations_per_season': np.mean([sim['num_eliminated'] for sim in self.simulation_results]),
            'min_eliminations': min(sim['num_eliminated'] for sim in self.simulation_results),
            'max_eliminations': max(sim['num_eliminated'] for sim in self.simulation_results),
        }

        return stats

    def _print_simulation_summary(self, stats: Dict):
        """Print summary of simulation results"""
        print(f"\n{'='*80}")
        print(f"Monte Carlo Simulation Results")
        print(f"{'='*80}")

        print(f"\nOverall Statistics:")
        print(f"  Total Simulations: {stats['overall']['total_simulations']}")
        print(f"  Avg Eliminations per Season: {stats['overall']['avg_eliminations_per_season']:.2f}")
        print(f"  Min Eliminations: {stats['overall']['min_eliminations']}")
        print(f"  Max Eliminations: {stats['overall']['max_eliminations']}")

        print(f"\nExpert Performance:")
        print(f"{'='*80}")

        # Sort by mean final bankroll
        sorted_experts = sorted(
            [(eid, s) for eid, s in stats.items() if eid != 'overall'],
            key=lambda x: x[1]['mean_final_bankroll'],
            reverse=True
        )

        for expert_id, expert_stats in sorted_experts:
            print(f"\n{expert_stats['name']}:")
            print(f"  Mean Final Bankroll: ${expert_stats['mean_final_bankroll']:,.2f}")
            print(f"  Median Final Bankroll: ${expert_stats['median_final_bankroll']:,.2f}")
            print(f"  Mean ROI: {expert_stats['roi_mean']:+.2f}%")
            print(f"  Elimination Probability: {expert_stats['elimination_probability']*100:.1f}%")
            print(f"  Profit Probability: {expert_stats['profit_probability']*100:.1f}%")
            print(f"  Ruin Probability: {expert_stats['ruin_probability']*100:.1f}%")

    def plot_trajectories(self, output_file: str, num_samples: int = 100):
        """
        Plot sample bankroll trajectories

        Args:
            output_file: Path to save plot
            num_samples: Number of sample trajectories to plot per expert
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig, axes = plt.subplots(2, 4, figsize=(20, 10))
        axes = axes.flatten()

        for idx, expert in enumerate(self.experts):
            expert_id = expert.expert_id
            trajectories = self.bankroll_trajectories[expert_id]

            # Sample trajectories
            sampled = random.sample(trajectories, min(num_samples, len(trajectories)))

            ax = axes[idx]

            # Plot trajectories
            for trajectory in sampled:
                ax.plot(trajectory, alpha=0.1, color='blue')

            # Plot mean trajectory
            mean_trajectory = np.mean(trajectories, axis=0)
            ax.plot(mean_trajectory, color='red', linewidth=2, label='Mean')

            # Plot elimination threshold
            ax.axhline(y=self.config.elimination_threshold, color='black',
                      linestyle='--', label='Elimination')

            ax.set_title(expert.name)
            ax.set_xlabel('Week')
            ax.set_ylabel('Bankroll ($)')
            ax.grid(True, alpha=0.3)
            ax.legend()

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        print(f"\nTrajectory plot saved to: {output_path}")
        plt.close()

    def export_results(self, output_file: str, stats: Dict):
        """Export simulation results to JSON"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            'config': {
                'num_simulations': self.config.num_simulations,
                'num_weeks': self.config.num_weeks,
                'starting_bankroll': self.config.starting_bankroll,
                'base_accuracy': self.config.base_accuracy,
            },
            'experts': [
                {
                    'expert_id': e.expert_id,
                    'name': e.name,
                    'base_accuracy': e.base_accuracy,
                    'risk_tolerance': e.risk_tolerance,
                }
                for e in self.experts
            ],
            'statistics': stats
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"\nResults exported to: {output_path}")


if __name__ == "__main__":
    # Run Monte Carlo simulation
    config = SimulationConfig(
        num_simulations=1000,
        num_weeks=18,
        starting_bankroll=10000.0,
        base_accuracy=0.55
    )

    simulator = MonteCarloSimulator(config)
    stats = simulator.run_simulations(verbose=True)

    # Generate plots
    reports_dir = "/home/iris/code/experimental/nfl-predictor-api/tests/reports"
    simulator.plot_trajectories(f"{reports_dir}/monte_carlo_trajectories.png", num_samples=50)

    # Export results
    simulator.export_results(f"{reports_dir}/monte_carlo_results.json", stats)

    print("\n" + "="*80)
    print("Monte Carlo Simulation Complete!")
    print("="*80)