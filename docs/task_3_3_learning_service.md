# Task 3.3: Learning & Calibration Service - Implementation Guide

## Overview

Task 3.3 implements the Learning & Calibration Service that handles post-game learning and calibration updates for experts in the Expert Council Betting System. The service implements Beta calibration for binary/enum predictions, EMA (Exponential Moving Average) for numeric predictions, and factor updates with comprehensive audit trails.

## Implementation

### Core Service (`src/services/learning_service.py`)

The Learning Service provides comprehensive learning and calibration with:

1. **Beta Calibration**: For binary and enum predictions using Beta distribution parameters
2. **EMA Calibration**: For numeric predictions using exponential moving averages
3. **Factor Updates**: Category-specific multiplicative weight adjustments
4. **Audit Trails**: Complete tracking of all learning updates
5. **Persona Adjustments**: Expert-specific learning rate customization

### Key Components

#### Learning Process Flow
```
1. Receive expert predictions and grading results
2. Initialize expert learning states if needed
3. Process each prediction-result pair:
   - Binary/Enum → Beta calibration update
   - Numeric → EMA calibration update
   - All → Factor updates based on category performance
4. Calculate calibration improvements
5. Generate learning session summary
6. Store audit trail
```

#### Beta Calibration
```python
# Beta distribution parameters
α (alpha) = success count + prior
β (beta) = failure count + prior

# Updates based on prediction accuracy
if exact_match:
    α += learning_rate  # Increase success parameter
else:
    β += learning_rate  # Increase failure parameter

# Calibration metrics
mean = α / (α + β)
variance = (α * β) / ((α + β)² * (α + β + 1))
```

#### EMA Calibration
```python
# Exponential Moving Average updates
error = observed_value - predicted_value

# Update bias estimate
μ = (1 - α) * μ + α * error

# Update variance estimate
σ = √((1 - α) * σ² + α * error²)
```

#### Factor Updates
```python
# Performance-based factor adjustments
performance_delta = grading_score - 0.5
multiplier = 1.0 + (performance_delta * adjustment_rate)

# Apply bounds to prevent extreme changes
multiplier = max(1.0 - max_change, min(1.0 + max_change, multiplier))

# Update relevant factor
factor *= multiplier
```

### Data Structures

#### BetaCalibrationState
```python
@dataclass
class BetaCalibrationState:
    alpha: float = 1.0  # Success count + prior
    beta: float = 1.0   # Failure count + prior
    total_predictions: int = 0
    correct_predictions: int = 0
    last_updated: datetime

    def get_mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def get_variance(self) -> float:
        return (self.alpha * self.beta) / ((self.alpha + self.beta)**2 * (self.alpha + self.beta + 1))
```

#### EMAState
```python
@dataclass
class EMAState:
    mu: float = 0.0      # Mean estimate (bias)
    sigma: float = 1.0   # Standard deviation estimate
    alpha: float = 0.1   # Learning rate
    total_predictions: int = 0
    last_updated: datetime

    def update(self, observed_value: float, predicted_value: float):
        error = observed_value - predicted_value
        self.mu = (1 - self.alpha) * self.mu + self.alpha * error
        self.sigma = sqrt((1 - self.alpha) * self.sigma**2 + self.alpha * error**2)
```

#### FactorState
```python
@dataclass
class FactorState:
    momentum_factor: float = 1.02      # Slight positive momentum bias
    offensive_efficiency_factor: float = 0.95  # Down-weight offensive efficiency
    defensive_factor: float = 1.0
    weather_factor: float = 1.0
    home_field_factor: float = 1.0
    injury_factor: float = 1.0
    last_updated: datetime
    update_count: int = 0
```

### Persona-Specific Adjustments

The service includes persona-aware learning rates:

```python
persona_adjustments = {
    'conservative_analyzer': {
        'beta_learning_rate': 0.08,  # Slower learning
        'ema_alpha': 0.08,
        'factor_adjustment_rate': 0.03
    },
    'momentum_rider': {
        'momentum_factor_boost': 1.1,  # Extra momentum sensitivity
        'ema_alpha': 0.12
    },
    'contrarian_rebel': {
        'beta_learning_rate': 0.15,  # Faster adaptation
        'factor_adjustment_rate': 0.08
    },
    'value_hunter': {
        'ema_alpha': 0.15,  # More responsive to value changes
        'factor_adjustment_rate': 0.06
    }
}
```

### Learning Configuration

Default learning parameters:

```python
learning_config = {
    'beta_learning_rate': 0.1,
    'ema_alpha': 0.1,
    'factor_adjustment_rate': 0.05,
    'momentum_prior': 1.02,           # Slight positive momentum bias
    'offensive_efficiency_prior': 0.95,  # Down-weight offensive efficiency
    'min_predictions_for_update': 3,
    'max_factor_change': 0.2          # Maximum 20% change per update
}
```

### Audit Trail

Complete tracking of all learning updates:

```python
@dataclass
class LearningUpdate:
    update_id: str
    expert_id: str
    game_id: str
    category: str
    learning_type: LearningType
    calibration_method: CalibrationMethod
    state_before: Dict[str, Any]
    state_after: Dict[str, Any]
    observed_value: Any
    predicted_value: Any
    prediction_confidence: float
    grading_score: float
    update_time: datetime
    processing_time_ms: float
    persona_adjustments: Dict[str, float]
```

## API Methods

### Core Learning Methods

- `process_expert_learning()`: Process all learning updates for an expert after a game
- `get_expert_calibration_state()`: Get current calibration state for an expert
- `get_learning_history()`: Get learning update history with filters
- `get_learning_performance_metrics()`: Get service performance metrics

### Configuration Methods

- `update_learning_config()`: Update learning configuration parameters
- `reset_expert_learning()`: Reset all learning states for an expert
- `clear_all_data()`: Clear all learning data (for testing)

## Integration Points

### With Grading Service (Task 3.1)
- Receives grading results for prediction accuracy
- Uses grading scores for calibration updates
- Processes exact match indicators for Beta updates

### With Settlement Service (Task 3.2)
- Learning updates triggered after settlement
- Calibration improvements affect future predictions
- Factor adjustments influence betting strategies

### Future Integration (Task 3.4)
- Reflection system will use learning insights
- Learning patterns inform reflection prompts
- Calibration drift triggers reflection calls

## Performance Characteristics

- **Processing Speed**: Sub-millisecond updates per prediction
- **Memory Efficiency**: Lightweight state storage per expert/category
- **Scalability**: Independent expert learning states
- **Audit Completeness**: Full history of all learning updates

## Testing

Comprehensive test coverage includes:
- Beta calibration state management
- EMA state updates and calculations
- Factor state retrieval and updates
- Individual learning method validation
- Full expert learning session processing
- Calibration state retrieval
- Learning history and performance metrics
- Persona-specific adjustment validation
- Configuration management
- Edge case handling

## Next Steps

1. **Database Integration**: Persist learning states to Supabase
2. **Real-time Monitoring**: Add learning performance dashboards
3. **Calibration Alerts**: Notify on significant calibration drift
4. **Advanced Analytics**: Learning effectiveness analysis
5. **Production Deployment**: Monitor learning in live environment

## Requirements Satisfied

✅ **2.6 Learning & calibration (per game)**
- Beta calibration for binary/enum predictions
- EMA μ/σ updates for numeric predictions
- Factor updates with multiplicative weight adjustments
- Comprehensive audit trails
- Default priors reflecting observed learning patterns
- Persona-specific overrides and adjustments
