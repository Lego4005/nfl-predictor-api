# Task 2.1: CoherenceProjection Service - Implementation Guide

## Overview

Task 2.1 implements the CoherenceProjection Service that applies least-squares projection with hard constraints to ensure platform aggregate predictions are mathematically coherent. This service only adjusts platform aggregates and never touches individual expert predictions.

## Implementation

### Core Service (`src/services/coherence_projection_service.py`)

The CoherenceProjection Service provides:

1. **Constraint Violation Detection**
2. **Least-Squares Projection Optimization**
3. **Performance Monitoring (p95 <150ms)**
4. **Delta Logging and Tracking**

### Hard Constraints Implemented

#### 1. Total Game Score Consistency
```python
home_score + away_score = total_game_score
```

#### 2. Quarter Totals Consistency
```python
Σ quarter_totals = total_game_score
first_quarter + second_quarter + third_quarter + fourth_quarter = total
```

#### 3. Half Totals Consistency
```python
Σ halves = total_game_score
first_half + second_half = total
```

#### 4. Winner ↔ Margin Consistency
- If home team is favored (negative spread), home win probability should be >50%
- If away team is favored (positive spread), home win probability should be <50%

#### 5. Team Props Consistency
- Individual team totals should be reasonable relative to game total
- No team should score >80% of total game points

### Key Classes

#### ConstraintViolation
```python
@dataclass
class ConstraintViolation:
    constraint_type: str      # Type of constraint violated
    category: str            # Prediction category affected
    expected_value: float    # Expected value per constraint
    actual_value: float      # Actual predicted value
    delta: float            # Magnitude of violation
    severity: str           # 'minor', 'moderate', 'severe'
```

#### ProjectionResult
```python
@dataclass
class ProjectionResult:
    success: bool                           # Projection success
    original_predictions: Dict[str, Any]    # Original platform aggregate
    projected_predictions: Dict[str, Any]   # Coherent projections
    violations: List[ConstraintViolation]   # Remaining violations
    deltas_applied: Dict[str, float]        # Changes made
    processing_time_ms: float               # Performance tracking
    constraint_satisfaction: float         # 0-1 satisfaction score
```

### Core Methods

#### project_coherent_predictions()
Main entry point that:
1. Extracts predictions from platform aggregate
2. Identifies constraint violations
3. Applies least-squares projection if needed
4. Validates final coherence
5. Returns comprehensive results

#### _identify_violations()
Detects all constraint violations with severity classification:
- **Minor**: Small inconsistencies (delta <1.0)
- **Moderate**: Noticeable violations (delta 1.0-3.0)
- **Severe**: Major inconsistencies (delta >3.0)

#### _apply_projection()
Uses scipy.optimize.minimize with:
- **Objective**: Minimize squared changes from original
- **Method**: SLSQP (Sequential Least Squares Programming)
- **Constraints**: Equality constraints for hard requirements
- **Bounds**: Reasonable ranges for each prediction type

### Performance Features

- **Target**: p95 processing time <150ms
- **Tracking**: All projection times recorded
- **Metrics**: Comprehensive performance monitoring
- **Optimization**: Efficient constraint solving

### Usage Example

```python
from src.services.coherence_projection_service import CoherenceProjectionService

service = CoherenceProjectionService()

# Platform aggregate from council selection
platform_aggregate = {
    'overall': {'home_win_prob': 0.6, 'away_win_prob': 0.4},
    'predictions': [
        {'category': 'home_team_total_points', 'value': 24.0, 'pred_type': 'numeric'},
        {'category': 'away_team_total_points', 'value': 21.0, 'pred_type': 'numeric'},
        {'category': 'total_game_score', 'value': 50.0, 'pred_type': 'numeric'},  # Violation!
        # ... more predictions
    ]
}

game_context = {'game_id': 'KC_vs_BUF_2025_W1'}

# Apply coherence projection
result = service.project_coherent_predictions(platform_aggregate, game_context)

if result.success:
    print(f"Coherent predictions generated in {result.processing_time_ms:.1f}ms")
    print(f"Constraint satisfaction: {result.constraint_satisfaction:.3f}")
    print(f"Deltas applied: {len(result.deltas_applied)}")
else:
    print("Projection failed - check violations")
```

### Integration Points

1. **Council Selection**: Receives aggregated predictions from council
2. **Platform Slate API**: Provides coherent predictions for client consumption
3. **Monitoring**: Logs constraint violations for system health
4. **Performance**: Tracks p95 times for SLA compliance

### Performance Monitoring

```python
# Get performance metrics
metrics = service.get_performance_metrics()

print(f"Projections processed: {metrics['projection_count']}")
print(f"Average time: {metrics['avg_time_ms']:.1f}ms")
print(f"P95 time: {metrics['p95_time_ms']:.1f}ms")
print(f"Target met: {metrics['performance_ok']}")
print(f"Violations: {metrics['violation_counts']}")
```

### Testing

- **Basic functionality**: `test_coherence_projection_simple.py`
- **Comprehensive tests**: `test_coherence_projection_service.py`
- **Validation**: `validate_coherence_simple.py`

### Key Design Principles

1. **Expert Sovereignty**: Never modifies individual expert predictions
2. **Platform Only**: Only adjusts final platform aggregates
3. **Minimal Changes**: Least-squares minimizes prediction changes
4. **Hard Constraints**: Mathematical consistency enforced
5. **Performance**: Sub-150ms processing target
6. **Transparency**: Full delta logging and violation tracking

### Gate B Criteria

Task 2.1 contributes to Gate B validation:
- ✅ **Coherence constraints satisfied** on pilot week
- ✅ **Deltas logged** for monitoring
- ✅ **Experts' records untouched** (only platform aggregate adjusted)

### Next Steps

1. **Integration**: Wire into council selection system (Task 2.2)
2. **API Endpoints**: Add to platform slate endpoints
3. **Production**: Monitor constraint violations in live system
4. **Optimization**: Tune constraint weights based on real data

## Files Created

- `src/services/coherence_projection_service.py` - Main service implementation
- `test_coherence_projection_simple.py` - Basic functionality tests
- `validate_coherence_simple.py` - Implementation validation
- `docs/task_2_1_coherence_projection.md` - This documentation

## Task Completion

✅ **Task 2.1 Complete**: CoherenceProjection Service implemented with least-squares projection, hard constraints, performance monitoring, and comprehensive validation.
