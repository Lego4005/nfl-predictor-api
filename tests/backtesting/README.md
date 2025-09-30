# Backtesting Framework

Comprehensive backtesting system to validate expert predictions against historical NFL data.

## Overview

This framework enables you to:

- Load historical NFL game data (2023-2024 seasons)
- Replay seasons week-by-week with expert predictions
- Calculate comprehensive performance metrics
- Validate system accuracy before production

## Components

### 1. Historical Data Loader (`historical_data_loader.py`)

Loads and manages historical NFL game data.

**Features:**
- Load entire seasons or specific weeks
- Support for CSV and JSON formats
- Automatic game outcome calculation (spread, total, moneyline)
- Season statistics generation
- Sample data creation for testing

**Usage:**
```python
from tests.backtesting import HistoricalDataLoader

loader = HistoricalDataLoader()

# Load entire season
games_2023 = loader.load_season(2023)

# Load specific week
week1_games = loader.load_week(2023, 1)

# Get season statistics
stats = loader.get_season_stats(2023)
```

### 2. Metrics Calculator (`metrics.py`)

Calculates comprehensive performance metrics.

**Metrics Included:**
- **Accuracy**: Overall prediction accuracy
- **ATS Accuracy**: Against-the-spread accuracy
- **ROI**: Return on investment
- **Sharpe Ratio**: Risk-adjusted returns
- **ECE**: Expected Calibration Error (measures confidence calibration)
- **Kelly Criterion**: Optimal bet sizing

**Usage:**
```python
from tests.backtesting import MetricsCalculator

calc = MetricsCalculator()

# Calculate accuracy
accuracy = calc.calculate_accuracy(results)

# Calculate ROI
roi = calc.calculate_roi(results)

# Calculate calibration
ece = calc.calculate_calibration_ece(results)

# Calculate optimal bet size
bet_size = calc.calculate_kelly_bet_size(
    bankroll=10000,
    confidence=0.75,
    american_odds="-110"
)
```

### 3. Backtest Runner (`backtest_runner.py`)

Replays historical seasons to validate expert performance.

**Features:**
- Week-by-week season replay
- Expert prediction generation
- Bet sizing and placement
- Bankroll tracking
- Elimination detection
- Comprehensive reporting

**Usage:**
```python
from tests.backtesting import BacktestRunner, ExpertConfig

# Define experts to test
experts = [
    ExpertConfig("quant_master", "The Quant Master", "data_driven"),
    ExpertConfig("gambler", "The Gambler", "high_risk"),
]

# Run backtest
runner = BacktestRunner(experts)
metrics = runner.replay_season(2023, verbose=True)

# Export results
runner.export_results("tests/reports/backtest_2023.json")
```

## Running Backtests

### Quick Start

```bash
# Run backtest on 2023 season
cd /home/iris/code/experimental/nfl-predictor-api
python -m tests.backtesting.backtest_runner
```

### Custom Configuration

```python
from tests.backtesting import BacktestRunner, ExpertConfig

# Create custom expert configurations
experts = [
    ExpertConfig(
        expert_id="custom_expert",
        name="My Custom Expert",
        archetype="balanced",
        starting_bankroll=15000.0,
        min_confidence_threshold=0.75,
        kelly_fraction=0.20
    )
]

# Run backtest
runner = BacktestRunner(experts)
results = runner.replay_season(2023, verbose=True)
```

## Data Format

### Historical Game Data (CSV)

```csv
game_id,season,week,home_team,away_team,home_score,away_score,vegas_spread,vegas_total,game_date,weather_temp,weather_wind,weather_conditions
2023_W1_G1,2023,1,KC,DET,21,20,-7.5,52.5,2023-09-07,72,8,Clear
```

### Historical Game Data (JSON)

```json
[
  {
    "game_id": "2023_W1_G1",
    "season": 2023,
    "week": 1,
    "home_team": "KC",
    "away_team": "DET",
    "home_score": 21,
    "away_score": 20,
    "vegas_spread": -7.5,
    "vegas_total": 52.5,
    "game_date": "2023-09-07",
    "weather_temp": 72,
    "weather_wind": 8,
    "weather_conditions": "Clear"
  }
]
```

## Performance Targets

### Accuracy Targets
- **Overall Accuracy**: > 55%
- **ATS Accuracy**: > 55%
- **Calibration (ECE)**: < 0.10

### Risk Targets
- **ROI**: > 5% per season
- **Sharpe Ratio**: > 0.5
- **Elimination Rate**: 2-3 experts per season

## Sample Output

```
================================================================================
Starting Backtest: 2023 NFL Season
================================================================================
Experts: 5
Starting Bankrolls: $10,000.00
================================================================================

--- Week 1 ---
Games: 16
  Predictions: 42
  Accuracy: 57.1%
  Wagered: $8,450.00
  Net Profit: +$425.50

  Expert Bankrolls:
    The Quant Master: $10,642.30 (+$642.30)
    The Conservative: $10,385.20 (+$385.20)
    The Veteran: $10,156.80 (+$156.80)
    The Gambler: $9,785.40 (-$214.60)
    The Rebel: $9,923.50 (-$76.50)

...

================================================================================
Season Complete: 2023
================================================================================

Overall Performance:
  Total Predictions: 756
  Overall Accuracy: 56.35%
  ATS Accuracy: 56.35%
  Total ROI: 12.85%
  Sharpe Ratio: 0.642

Expert Results:

  quant_master:
    Accuracy: 58.24%
    ROI: 18.50%
    Final Bankroll: $13,842.00
    Net Profit: +$3,842.00
    Calibration (ECE): 0.045

  conservative:
    Accuracy: 56.80%
    ROI: 9.20%
    Final Bankroll: $11,520.00
    Net Profit: +$1,520.00
    Calibration (ECE): 0.038

Eliminated Experts: 1
  - The Gambler
```

## Next Steps

1. **Add Real Historical Data**: Replace sample data with actual 2023-2024 NFL results
2. **Integrate Expert Models**: Connect real ML models for prediction generation
3. **Add More Metrics**: Implement additional performance metrics as needed
4. **CI/CD Integration**: Add backtesting to continuous integration pipeline

## Directory Structure

```
tests/
├── backtesting/
│   ├── __init__.py
│   ├── README.md
│   ├── historical_data_loader.py
│   ├── metrics.py
│   └── backtest_runner.py
├── fixtures/
│   ├── nfl_2023_season.csv
│   ├── nfl_2023_season.json
│   ├── nfl_2024_season.csv
│   └── nfl_2024_season.json
└── reports/
    ├── backtest_2023.json
    └── backtest_2024.json
```

## Dependencies

```bash
pip install numpy pandas matplotlib
```

## Contact

For questions or issues, refer to the main project documentation at `/docs/COMPREHENSIVE_GAP_ANALYSIS.md`.