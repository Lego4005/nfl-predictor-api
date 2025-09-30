# Monte Carlo Simulation Framework

Simulate thousands of NFL seasons to analyze risk, elimination probabilities, and expected outcomes.

## Overview

The Monte Carlo simulator runs thousands of season simulations to provide statistical insights about:

- Bankroll trajectory distributions
- Elimination probabilities per expert
- Risk-adjusted performance metrics
- Expected ROI and variance
- Probability of ruin

## Features

- **1000+ Season Simulations**: Run thousands of seasons in minutes
- **Diverse Expert Profiles**: Simulate different betting strategies and risk tolerances
- **Bankroll Trajectories**: Track and visualize bankroll evolution over time
- **Risk Analysis**: Calculate elimination and ruin probabilities
- **Statistical Analysis**: Mean, median, variance, percentiles
- **Visualization**: Generate trajectory plots and distribution charts

## Components

### 1. Monte Carlo Simulator (`monte_carlo.py`)

Main simulation engine that runs thousands of seasons.

**Key Classes:**
- `SimulationConfig`: Configuration for simulations
- `ExpertProfile`: Expert betting profile with risk parameters
- `MonteCarloSimulator`: Main simulation engine

### 2. Expert Profiles

Predefined expert profiles with different characteristics:

| Expert | Base Accuracy | Risk Tolerance | Confidence Bias | Consistency |
|--------|---------------|----------------|-----------------|-------------|
| The Quant Master | 58% | 1.0x | Low | High |
| The Veteran | 56% | 0.8x | Medium | Medium |
| The Gambler | 52% | 1.6x | High | Low |
| The Rebel | 54% | 1.2x | Medium | Medium-Low |
| The Conservative | 56% | 0.6x | Very Low | Very High |
| The Momentum Trader | 53% | 1.3x | High | Low |
| The Value Hunter | 57% | 0.9x | Low | Medium-High |
| The Hot Head | 51% | 1.5x | Very High | Very Low |

## Usage

### Basic Usage

```python
from tests.simulation import MonteCarloSimulator, SimulationConfig

# Configure simulation
config = SimulationConfig(
    num_simulations=1000,
    num_weeks=18,
    starting_bankroll=10000.0,
    base_accuracy=0.55
)

# Run simulations
simulator = MonteCarloSimulator(config)
stats = simulator.run_simulations(verbose=True)

# Generate visualizations
simulator.plot_trajectories("reports/trajectories.png", num_samples=50)

# Export results
simulator.export_results("reports/monte_carlo_results.json", stats)
```

### Quick Start

```bash
# Run Monte Carlo simulation
cd /home/iris/code/experimental/nfl-predictor-api
python -m tests.simulation.monte_carlo
```

### Advanced Configuration

```python
from tests.simulation import MonteCarloSimulator, SimulationConfig, ExpertProfile

# Custom configuration
config = SimulationConfig(
    num_simulations=5000,  # More simulations for better statistics
    num_weeks=18,
    games_per_week=16,
    starting_bankroll=15000.0,
    min_confidence=0.75,
    kelly_fraction=0.20,
    elimination_threshold=1500.0,
    base_accuracy=0.57
)

# Add custom expert profile
custom_expert = ExpertProfile(
    expert_id="custom",
    name="My Custom Expert",
    base_accuracy=0.59,
    accuracy_variance=0.03,
    risk_tolerance=1.1,
    confidence_bias=0.05
)

simulator = MonteCarloSimulator(config)
simulator.experts.append(custom_expert)
stats = simulator.run_simulations(verbose=True)
```

## Output Metrics

### Per-Expert Statistics

- **Mean Final Bankroll**: Average bankroll after 18 weeks
- **Median Final Bankroll**: Median bankroll (robust to outliers)
- **Standard Deviation**: Variability in outcomes
- **Min/Max Bankroll**: Range of possible outcomes
- **Elimination Probability**: Chance of bankroll dropping below threshold
- **Profit Probability**: Chance of ending with profit
- **Ruin Probability**: Chance of complete bankroll loss
- **ROI Mean/Median**: Expected return on investment

### Overall Statistics

- **Average Eliminations per Season**: How many experts typically eliminated
- **Min/Max Eliminations**: Range of elimination outcomes
- **System Stability**: Consistency across simulations

## Sample Output

```
================================================================================
Monte Carlo Simulation: 1000 Seasons
================================================================================
Experts: 8
Weeks per season: 18
Starting bankroll: $10,000.00
================================================================================

Completed 100/1000 simulations...
Completed 200/1000 simulations...
...
Completed 1000/1000 simulations...

================================================================================
Monte Carlo Simulation Results
================================================================================

Overall Statistics:
  Total Simulations: 1000
  Avg Eliminations per Season: 2.34
  Min Eliminations: 0
  Max Eliminations: 5

Expert Performance:
================================================================================

The Quant Master:
  Mean Final Bankroll: $13,245.67
  Median Final Bankroll: $12,890.34
  Mean ROI: +32.46%
  Elimination Probability: 8.2%
  Profit Probability: 78.5%
  Ruin Probability: 2.1%

The Conservative:
  Mean Final Bankroll: $11,856.23
  Median Final Bankroll: $11,623.45
  Mean ROI: +18.56%
  Elimination Probability: 12.5%
  Profit Probability: 71.3%
  Ruin Probability: 3.8%

The Gambler:
  Mean Final Bankroll: $9,234.12
  Median Final Bankroll: $8,456.78
  Mean ROI: -7.66%
  Elimination Probability: 45.6%
  Profit Probability: 42.1%
  Ruin Probability: 18.9%

...
```

## Visualizations

### Bankroll Trajectory Plot

The simulator generates a plot showing:
- 50-100 sample trajectories per expert (transparent blue lines)
- Mean trajectory (red line)
- Elimination threshold (black dashed line)

Example: `/tests/reports/monte_carlo_trajectories.png`

### Interpretation

- **High variance** (wide spread): Expert has inconsistent results
- **Trajectories crossing elimination line**: High elimination risk
- **Mean above starting bankroll**: Expected profit
- **Mean below starting bankroll**: Expected loss

## Risk Analysis

### Elimination Risk

Experts with **elimination probability > 30%** are at high risk:
- Consider reducing Kelly fraction
- Lower minimum confidence threshold
- Improve accuracy or calibration

### Ruin Risk

Experts with **ruin probability > 10%** may go completely broke:
- Implement stricter bet sizing
- Add stop-loss mechanisms
- Review betting strategy

### Profit Consistency

Experts with **profit probability < 60%** are inconsistent:
- More than 40% chance of losing money
- Consider eliminating from council
- Improve prediction model

## Configuration Parameters

### SimulationConfig

```python
@dataclass
class SimulationConfig:
    num_simulations: int = 1000      # Number of seasons to simulate
    num_weeks: int = 18              # Weeks per season
    games_per_week: int = 16         # Games per week (approximate)
    starting_bankroll: float = 10000.0  # Starting bankroll
    min_confidence: float = 0.70     # Minimum confidence to bet
    kelly_fraction: float = 0.25     # Fraction of Kelly to use
    elimination_threshold: float = 1000.0  # Bankroll threshold for elimination
    base_accuracy: float = 0.55      # Base accuracy for experts
    accuracy_std: float = 0.05       # Variation in accuracy
```

### ExpertProfile

```python
@dataclass
class ExpertProfile:
    expert_id: str              # Unique identifier
    name: str                   # Display name
    base_accuracy: float        # Base prediction accuracy (0-1)
    accuracy_variance: float    # How much accuracy varies week-to-week
    risk_tolerance: float       # Kelly fraction multiplier (1.0 = full Kelly)
    confidence_bias: float      # Overconfidence factor (0 = well-calibrated)
```

## Use Cases

### 1. Validate System Before Launch

Run 1000+ simulations to ensure:
- Elimination rate matches expectations (2-3 per season)
- Top experts show consistent profitability
- Risk metrics are acceptable

### 2. Compare Betting Strategies

Test different configurations:
- Conservative (low Kelly fraction)
- Aggressive (high Kelly fraction)
- Hybrid strategies

### 3. Stress Testing

Simulate worst-case scenarios:
- Low accuracy periods
- High variance weeks
- Market inefficiencies

### 4. Optimize Parameters

Find optimal values for:
- Kelly fraction
- Minimum confidence threshold
- Elimination threshold
- Starting bankroll

## Limitations

### Current Limitations

1. **Simplified Prediction Model**: Uses statistical simulation instead of real ML models
2. **Independent Games**: Assumes game outcomes are independent
3. **Static Accuracy**: Expert accuracy doesn't change over season
4. **No Learning**: Experts don't adapt based on performance
5. **Simplified Odds**: Uses -110 for all bets

### Future Enhancements

- Integrate real expert ML models
- Add correlation between games
- Implement adaptive learning
- Variable odds based on market conditions
- Multi-season simulations with expert replacement

## Performance

- **Runtime**: ~30-60 seconds for 1000 simulations (8 experts, 18 weeks)
- **Memory**: < 500 MB for 1000 simulations
- **Scalability**: Linear with number of simulations

## Integration with Backtesting

Combine with backtesting for comprehensive validation:

```python
# 1. Run backtest on historical data
from tests.backtesting import BacktestRunner
runner = BacktestRunner()
historical_metrics = runner.replay_season(2023)

# 2. Run Monte Carlo with same configuration
from tests.simulation import MonteCarloSimulator
simulator = MonteCarloSimulator()
simulated_metrics = simulator.run_simulations()

# 3. Compare results
print("Historical ROI:", historical_metrics['overall_roi'])
print("Simulated ROI:", simulated_metrics['overall']['avg_roi'])
```

## Dependencies

```bash
pip install numpy matplotlib
```

## Next Steps

1. **Add Real Expert Models**: Integrate actual ML prediction models
2. **Market Simulation**: Add line movement and odds variation
3. **Correlation Modeling**: Model dependencies between games
4. **Multi-Season**: Extend to multi-season simulations with replacements
5. **Web Dashboard**: Create interactive visualization dashboard

## Contact

For questions or issues, refer to the main project documentation at `/docs/COMPREHENSIVE_GAP_ANALYSIS.md`.