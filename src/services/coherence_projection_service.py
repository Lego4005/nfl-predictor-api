"""
Coherence Projecice

Implements least-squares projection with hard constraints to ensure platform aggregate
predictions are mathematically coherent. Only adjusts platform aggregates, never touches
individual expert predictions.

Hard Constraints:
- home_score + away_score = total_game_score
- Σ quarter_totals = total_game_score
- Σ halves = total_game_score
- winner ↔ margin consistency
- team totals/props consistent with game totals

Target: projection p95 < 150ms
"""

import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from scipy.optimize import minimize
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class ConstraintViolation:
    """Represents a constraint violation with details"""
    constraint_type: str
    category: str
    expected_value: float
    actual_value: float
    delta: float
    severity: str  # 'minor', 'moderate', 'severe'

@dataclass
class ProjectionResult:
    """Result of coherence projection"""
    success: bool
    original_predictions: Dict[str, Any]
    projected_predictions: Dict[str, Any]
    violations: List[ConstraintViolation]
    deltas_applied: Dict[str, float]
    processing_time_ms: float
    constraint_satisfaction: float  # 0-1 score

class CoherenceProjectionService:
    """
    Service for applying coherence constraints to platform aggregate predictions

    Uses least-squares optimization to minimize changes while satisfying hard constraints
    """

    def __init__(self):
        self.constraint_weights = {
            'total_consistency': 10.0,      # home + away = total
            'quarter_consistency': 8.0,     # quarters sum to total
            'half_consistency': 8.0,        # halves sum to total
            'winner_margin': 6.0,           # winner consistent with margin
            'team_props': 4.0               # team totals consistent
        }

        # Performance tracking
        self.projection_times = []
        self.violation_counts = {'minor': 0, 'moderate': 0, 'severe': 0}

    def project_coherent_predictions(
        self,
        platform_aggregate: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> ProjectionResult:
        """
        Apply coherence projection to platform aggregate predictions

        Args:
            platform_aggregate: Aggregated predictions from council
            game_context: Game information for context

        Returns:
            ProjectionResult with coherent predictions and violation details
        """
        start_time = time.time()

        try:
            logger.info(f"Starting coherence projection for game {game_context.get('game_id', 'unknown')}")

            # Extract predictions by category
            predictions = self._extract_predictions(platform_aggregate)

            # Identify constraint violations
            violations = self._identify_violations(predictions, game_context)

            # Apply least-squares projection if violations exist
            if violations:
                projected_predictions = self._apply_projection(predictions, violations, game_context)
                deltas = self._calculate_deltas(predictions, projected_predictions)
            else:
                projected_predictions = predictions.copy()
                deltas = {}

            # Validate final coherence
            final_violations = self._identify_violations(projected_predictions, game_context)
            constraint_satisfaction = self._calculate_satisfaction_score(final_violations)

            processing_time = (time.time() - start_time) * 1000
            self.projection_times.append(processing_time)

            # Log violations for monitoring
            self._log_violations(violations, final_violations, game_context.get('game_id'))

            result = ProjectionResult(
                success=len(final_violations) == 0,
                original_predictions=predictions,
                projected_predictions=projected_predictions,
                violations=final_violations,
                deltas_applied=deltas,
                processing_time_ms=processing_time,
                constraint_satisfaction=constraint_satisfaction
            )

            logger.info(f"Coherence projection completed in {processing_time:.1f}ms, "
                       f"satisfaction: {constraint_satisfaction:.3f}")

            return result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Coherence projection failed: {e}")

            return ProjectionResult(
                success=False,
                original_predictions=predictions if 'predictions' in locals() else {},
                projected_predictions={},
                violations=[],
                deltas_applied={},
                processing_time_ms=processing_time,
                constraint_satisfaction=0.0
            )

    def _extract_predictions(self, platform_aggregate: Dict[str, Any]) -> Dict[str, float]:
        """Extract numeric predictions from platform aggregate"""

        predictions = {}

        # Extract from predictions array
        if 'predictions' in platform_aggregate:
            for pred in platform_aggregate['predictions']:
                category = pred.get('category', '')
                value = pred.get('value')

                # Only process numeric predictions for coherence
                if isinstance(value, (int, float)):
                    predictions[category] = float(value)

        # Extract from overall section
        if 'overall' in platform_aggregate:
            overall = platform_aggregate['overall']
            if 'home_win_prob' in overall:
                predictions['home_win_prob'] = float(overall['home_win_prob'])
            if 'away_win_prob' in overall:
                predictions['away_win_prob'] = float(overall['away_win_prob'])

        return predictions

    def _identify_violations(
        self,
        predictions: Dict[str, float],
        game_context: Dict[str, Any]
    ) -> List[ConstraintViolation]:
        """Identify constraint violations in predictions"""

        violations = []

        # 1. Total game score consistency: home_score + away_score = total_game_score
        home_score = predictions.get('home_team_total_points', 0)
        away_score = predictions.get('away_team_total_points', 0)
        total_score = predictions.get('total_game_score', 0)

        if home_score > 0 and away_score > 0 and total_score > 0:
            expected_total = home_score + away_score
            delta = abs(expected_total - total_score)

            if delta > 0.5:  # Allow small rounding differences
                violations.append(ConstraintViolation(
                    constraint_type='total_consistency',
                    category='total_game_score',
                    expected_value=expected_total,
                    actual_value=total_score,
                    delta=delta,
                    severity='severe' if delta > 3.0 else ('moderate' if delta > 1.0 else 'minor')
                ))

        # 2. Quarter totals consistency: Σ quarter_totals = total_game_score
        quarter_categories = [
            'first_quarter_total', 'second_quarter_total',
            'third_quarter_total', 'fourth_quarter_total'
        ]

        quarter_sum = sum(predictions.get(cat, 0) for cat in quarter_categories)
        if quarter_sum > 0 and total_score > 0:
            delta = abs(quarter_sum - total_score)

            if delta > 0.5:
                violations.append(ConstraintViolation(
                    constraint_type='quarter_consistency',
                    category='quarter_totals',
                    expected_value=total_score,
                    actual_value=quarter_sum,
                    delta=delta,
                    severity='moderate' if delta > 2.0 else 'minor'
                ))

        # 3. Half totals consistency: Σ halves = total_game_score
        first_half = predictions.get('first_half_total', 0)
        second_half = predictions.get('second_half_total', 0)

        if first_half > 0 and second_half > 0 and total_score > 0:
            half_sum = first_half + second_half
            delta = abs(half_sum - total_score)

            if delta > 0.5:
                violations.append(ConstraintViolation(
                    constraint_type='half_consistency',
                    category='half_totals',
                    expected_value=total_score,
                    actual_value=half_sum,
                    delta=delta,
                    severity='moderate' if delta > 2.0 else 'minor'
                ))

        # 4. Winner ↔ margin consistency
        home_win_prob = predictions.get('home_win_prob', 0.5)
        margin = predictions.get('point_spread', 0)

        # If home is favored (negative spread) but has low win probability
        if margin < -1.0 and home_win_prob < 0.5:
            delta = abs(0.6 - home_win_prob)  # Expected at least 60% for favorites
            violations.append(ConstraintViolation(
                constraint_type='winner_margin',
                category='home_win_prob',
                expected_value=0.6,
                actual_value=home_win_prob,
                delta=delta,
                severity='minor'
            ))

        # If away is favored (positive spread) but home has high win probability
        elif margin > 1.0 and home_win_prob > 0.5:
            delta = abs(home_win_prob - 0.4)  # Expected at most 40% for underdogs
            violations.append(ConstraintViolation(
                constraint_type='winner_margin',
                category='home_win_prob',
                expected_value=0.4,
                actual_value=home_win_prob,
                delta=delta,
                severity='minor'
            ))

        # 5. Team props consistency (simplified)
        # Check if individual team totals are reasonable relative to game total
        if home_score > 0 and total_score > 0:
            if home_score > total_score * 0.8:  # One team can't score >80% of total
                violations.append(ConstraintViolation(
                    constraint_type='team_props',
                    category='home_team_total_points',
                    expected_value=total_score * 0.7,
                    actual_value=home_score,
                    delta=home_score - total_score * 0.7,
                    severity='moderate'
                ))

        return violations

    def _apply_projection(
        self,
        predictions: Dict[str, float],
        violations: List[ConstraintViolation],
        game_context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Apply least-squares projection to fix violations"""

        # Create optimization problem
        original_values = np.array(list(predictions.values()))
        categories = list(predictions.keys())

        def objective(x):
            """Minimize squared changes from original predictions"""
            return np.sum((x - original_values) ** 2)

        def constraint_total_consistency(x):
            """home_score + away_score = total_score"""
            try:
                home_idx = categories.index('home_team_total_points')
                away_idx = categories.index('away_team_total_points')
                total_idx = categories.index('total_game_score')
                return x[home_idx] + x[away_idx] - x[total_idx]
            except ValueError:
                return 0  # Categories not found

        def constraint_quarter_consistency(x):
            """Σ quarters = total"""
            try:
                quarter_cats = ['first_quarter_total', 'second_quarter_total',
                               'third_quarter_total', 'fourth_quarter_total']
                quarter_indices = [categories.index(cat) for cat in quarter_cats if cat in categories]
                total_idx = categories.index('total_game_score')

                if quarter_indices and total_idx >= 0:
                    return sum(x[i] for i in quarter_indices) - x[total_idx]
                return 0
            except ValueError:
                return 0

        def constraint_half_consistency(x):
            """first_half + second_half = total"""
            try:
                first_idx = categories.index('first_half_total')
                second_idx = categories.index('second_half_total')
                total_idx = categories.index('total_game_score')
                return x[first_idx] + x[second_idx] - x[total_idx]
            except ValueError:
                return 0

        # Set up constraints
        constraints = []

        # Only add constraints for violations that exist
        violation_types = {v.constraint_type for v in violations}

        if 'total_consistency' in violation_types:
            constraints.append({'type': 'eq', 'fun': constraint_total_consistency})

        if 'quarter_consistency' in violation_types:
            constraints.append({'type': 'eq', 'fun': constraint_quarter_consistency})

        if 'half_consistency' in violation_types:
            constraints.append({'type': 'eq', 'fun': constraint_half_consistency})

        # Bounds to keep predictions reasonable
        bounds = []
        for i, category in enumerate(categories):
            original_val = original_values[i]

            if 'prob' in category.lower():
                # Probabilities bounded [0, 1]
                bounds.append((0.0, 1.0))
            elif 'total' in category.lower() or 'score' in category.lower():
                # Scores bounded to reasonable range
                bounds.append((max(0, original_val - 10), original_val + 10))
            else:
                # Other predictions with reasonable bounds
                bounds.append((original_val - 5, original_val + 5))

        # Solve optimization problem
        try:
            result = minimize(
                objective,
                original_values,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 100, 'ftol': 1e-6}
            )

            if result.success:
                projected_values = result.x
            else:
                logger.warning("Optimization failed, using original values")
                projected_values = original_values

        except Exception as e:
            logger.error(f"Projection optimization failed: {e}")
            projected_values = original_values

        # Convert back to dictionary
        projected_predictions = dict(zip(categories, projected_values))

        return projected_predictions

    def _calculate_deltas(
        self,
        original: Dict[str, float],
        projected: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate deltas between original and projected predictions"""

        deltas = {}

        for category in original:
            if category in projected:
                delta = projected[category] - original[category]
                if abs(delta) > 0.01:  # Only log meaningful deltas
                    deltas[category] = delta

        return deltas

    def _calculate_satisfaction_score(self, violations: List[ConstraintViolation]) -> float:
        """Calculate constraint satisfaction score (0-1)"""

        if not violations:
            return 1.0

        # Weight violations by severity
        severity_weights = {'minor': 0.1, 'moderate': 0.3, 'severe': 1.0}

        total_penalty = sum(severity_weights.get(v.severity, 0.5) for v in violations)
        max_penalty = len(violations) * 1.0  # Assume all severe

        satisfaction = max(0.0, 1.0 - (total_penalty / max_penalty))

        return satisfaction

    def _log_violations(
        self,
        original_violations: List[ConstraintViolation],
        final_violations: List[ConstraintViolation],
        game_id: Optional[str]
    ):
        """Log constraint violations for monitoring"""

        if original_violations:
            logger.info(f"Game {game_id}: Found {len(original_violations)} constraint violations")

            for violation in original_violations:
                logger.info(f"  {violation.constraint_type} - {violation.category}: "
                           f"expected {violation.expected_value:.2f}, "
                           f"got {violation.actual_value:.2f}, "
                           f"delta {violation.delta:.2f} ({violation.severity})")

                # Update violation counts
                self.violation_counts[violation.severity] += 1

        if final_violations:
            logger.warning(f"Game {game_id}: {len(final_violations)} violations remain after projection")
        else:
            logger.info(f"Game {game_id}: All constraints satisfied after projection")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""

        if not self.projection_times:
            return {
                'projection_count': 0,
                'avg_time_ms': 0,
                'p95_time_ms': 0,
                'violation_counts': self.violation_counts.copy()
            }

        times = np.array(self.projection_times)

        return {
            'projection_count': len(times),
            'avg_time_ms': float(np.mean(times)),
            'p95_time_ms': float(np.percentile(times, 95)),
            'p99_time_ms': float(np.percentile(times, 99)),
            'max_time_ms': float(np.max(times)),
            'violation_counts': self.violation_counts.copy(),
            'target_p95_ms': 150.0,
            'performance_ok': np.percentile(times, 95) < 150.0
        }

    def reset_metrics(self):
        """Reset performance tracking metrics"""
        self.projection_times.clear()
        self.violation_counts = {'minor': 0, 'moderate': 0, 'severe': 0}
