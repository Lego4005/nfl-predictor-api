# Task 3.1: Grading Service - Implementation Guide

## Overview

Task 3.1 implements the Grading Service that handles prediction scoring after games are completed. The service supports multiple grading methods for different prediction types: Binary/Enum exact + Brier scoring and Numeric Gaussian kernel scoring.

## Implementation

### Core Service (`src/services/grading_service.py`)

The Grading Service provides comprehensive prediction scoring with:

1. **Binary Prediction Grading**: Exact match + Brier score
2. **Enum Prediction Grading**: Exact match + Brier score
3. **Numeric Prediction Grading**: Gaussian kernel with category sigma
4. **Expert Grade Aggregation**: Overall performance calculation
5. **Category Performance Analysis**: Detailed breakdown by prediction category

### Grading Methods

#### 1. Binary Predictions
```python
# Scoring: 70% exact match + 30% Brier score
exact_match = predicted_value == actual_value
brier_score = (forecast_probability - outcome)^2
final_score = 0.7 * exact_component + 0.3 * (1 - brier_score)
```

**Example:**
- Prediction: `True` with confidence `0.8`
- Actual: `True`
- Exact match: `True` (1.0 points)
- Brier score: `(0.8 - 1.0)^2 = 0.04` → Brier component: `0.96`
- Final score: `0.7 * 1.0 + 0.3 * 0.96 = 0.988`

#### 2. Enum Predictions
```python
# Similar to binary but treats enum as categorical
exact_match = predicted_option == actual_option
brier_score = confidence^2 if wrong, (confidence - 1)^2 if correct
final_score = 0.7 * exact_component + 0.3 * (1 - brier_score)
```

#### 3. Numeric Predictions
```python
# Gaussian kernel scoring with category-specific sigma
distance = abs(predicted_value - actual_value)
gaussian_score = exp(-0.5 * (distance / sigma)^2)
confidence_factor = 1.0 + 0.2 * (confidence - 0.5) * gaussian_score
final_score = gaussian_score * confidence_factor
```

**Example:**
- Prediction: `24.5` points with confidence `0.8`
- Actual: `25.0` points
- Distance: `0.5`
- Sigma: `3.0` (for team total points)
- Gaussian score: `exp(-0.5 * (0.5/3.0)^2) = 0.986`
- Final score: `0.986 * 1.06 = 1.0` (capped at 1.0)

### Key Classes

#### PredictionType Enum
```python
class PredictionType(Enum):
    BINARY = "binary"    # True/False predictions
    ENUM = "enum"        # Categorical predictions
    NUMERIC = "numeric"  # Continuous value predictions
```

#### GradingResult Dataclass
```python
@dataclass
class GradingResult:
    prediction_id: str
    category: str
    pred_type: PredictionType
    predicted_value: Union[bool, str, float]
    actual_value: Union[bool, str, float]
    confidence: float

    # Scores
    exact_match: bool
    brier_score: Optional[float]      # Binary/Enum
    gaussian_score: Optional[float]   # Numeric
    final_score: float

    # Metadata
    grading_method: str
    sigma_used: Optional[float]
    processing_time_ms: float
```

### Default Sigma Values

The service includes optimized sigma values for different prediction categories:

```python
default_sigmas = {
    'total_game_score': 3.0,           # ±3 points tolerance
    'home_team_total_points': 3.0,     # ±3 points tolerance
    'away_team_total_points': 3.0,     # ±3 points tolerance
    'point_spread': 2.0,               # ±2 points tolerance
    'first_quarter_total': 2.0,        # ±2 points tolerance
    'passing_yards': 25.0,             # ±25 yards tolerance
    'rushing_yards': 15.0,             # ±15 yards tolerance
    'completion_percentage': 5.0,      # ±5% tolerance
    'turnovers': 1.0,                  # ±1 turnover tolerance
    # ... more categories
}
```

### Core Methods

#### grade_predictions()
Main entry point for grading multiple predictions:
```python
grading_results = service.grade_predictions(
    predictions=expert_predictions,
    actual_outcomes=game_outcomes,
    game_context={'game_id': 'KC_vs_BUF_2025_W1'}
)
```

#### calculate_expert_grade()
Aggregates individual prediction scores into overall expert performance:
```python
expert_grade = service.calculate_expert_grade(grading_results)
# Returns: overall_score, exact_match_rate, scores_by_type, etc.
```

#### get_category_performance()
Analyzes performance by prediction category:
```python
category_perf = service.get_category_performance(grading_results)
# Returns: performance metrics for each category
```

### Usage Example

```python
from src.services.grading_service import GradingService

service = GradingService()

# Expert predictions
predictions = [
    {
        'id': 'pred_1',
        'category': 'game_winner',
        'pred_type': 'binary',
        'value': True,
        'confidence': 0.75
    },
    {
        'id': 'pred_2',
        'category': 'total_game_score',
        'pred_type': 'numeric',
        'value': 45.0,
        'confidence': 0.8
    }
]

# Actual game outcomes
actual_outcomes = {
    'game_winner': True,      # Correct prediction
    'total_game_score': 47.0  # Close prediction (diff = 2.0)
}

# Grade predictions
results = service.grade_predictions(
    predictions,
    actual_outcomes,
    {'game_id': 'test_game'}
)

# Calculate expert grade
expert_grade = service.calculate_expert_grade(results)
print(f"Expert overall score: {expert_grade['overall_score']:.3f}")
```

### Performance Features

- **Fast Processing**: Optimized scoring algorithms
- **Batch Grading**: Process multiple predictions efficiently
- **Performance Tracking**: Monitor grading times and counts
- **Configurable Sigmas**: Tune tolerance per category
- **Comprehensive Metrics**: Detailed performance breakdown

### Integration Points

1. **Settlement Service**: Provides graded scores for bet settlement
2. **Learning Service**: Uses grades for expert calibration updates
3. **Bankroll Management**: Determines payout amounts
4. **Performance Analytics**: Tracks expert accuracy over time

### Testing

- **Comprehensive Tests**: `test_grading_service.py`
- **Validation**: `validate_grading_service_implementation.py`
- **All Grading Methods**: Binary, Enum, and Numeric scoring
- **Edge Cases**: Confidence bounds, extreme values, missing data

### Key Design Principles

1. **Accuracy First**: Exact matches weighted heavily (70%)
2. **Calibration Matters**: Brier scores reward good confidence calibration
3. **Distance-Based**: Gaussian kernel rewards close numeric predictions
4. **Category-Specific**: Different sigma values for different prediction types
5. **Confidence-Aware**: Higher confidence rewarded for accurate predictions
6. **Performance Optimized**: Fast processing for real-time settlement

### Scoring Summary

| Prediction Type | Exact Match Weight | Calibration Weight | Distance Scoring |
|----------------|-------------------|-------------------|------------------|
| Binary         | 70%               | 30% (Brier)       | N/A              |
| Enum           | 70%               | 30% (Brier)       | N/A              |
| Numeric        | N/A               | Confidence Adj.    | Gaussian Kernel  |

### Next Steps

1. **Integration**: Connect with Settlement Service (Task 3.2)
2. **Real Data**: Connect to actual game outcome feeds
3. **Sigma Tuning**: Optimize sigma values based on prediction accuracy
4. **Performance**: Monitor grading speed and accuracy in production
5. **Analytics**: Build dashboards for grading performance tracking

## Files Created

- `src/services/grading_service.py` - Main service implementation
- `test_grading_service.py` - Comprehensive functionality tests
- `validate_grading_service_implementation.py` - Implementation validation
- `docs/task_3_1_grading_service.md` - This documentation

## Task Completion

✅ **Task 3.1 Complete**: Grading Service implemented with Binary/Enum + Brier scoring, Numeric Gaussian kernel scoring, expert grade aggregation, and comprehensive performance analysis.
