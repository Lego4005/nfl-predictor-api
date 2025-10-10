"""
Grading Service

Implements predictading for the Expert Council Betting System.
Handles Binary/Enum exact + Brier scoring and Numeric Gaussian kernel scoring.

Grading Methods:
- Binary/Enum: Exact match + Brier score for calibration
- Numeric: Gaussian kernel with category-specific sigma values

Requirements: 2.5 - Settlement & bankroll
"""

import logging
import math
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class PredictionType(Enum):
    """Prediction types for grading"""
    BINARY = "binary"
    ENUM = "enum"
    NUMERIC = "numeric"

@dataclass
class GradingResult:
    """Result of grading a single prediction"""
    prediction_id: str
    category: str
    pred_type: PredictionType
    predicted_value: Union[bool, str, float]
    actual_value: Union[bool, str, float]
    confidence: float

    # Grading scores
    exact_match: bool
    brier_score: Optional[float]  # For binary/enum
    gaussian_score: Optional[float]  # For numeric
    final_score: float

    # Metadata
    grading_method: str
    sigma_used: Optional[float]  # For numeric predictions
    processing_time_ms: float

@dataclass
class CategoryGradingConfig:
    """Configuration for grading a specific category"""
    category: str
    pred_type: PredictionType
    sigma: Optional[float] = None  # For numeric predictions
    enum_values: Optional[List[str]] = None  # For enum predictions

    # Scoring weights
    exact_weight: float = 0.7
    calibration_weight: float = 0.3

class GradingService:
    """
    Service for grading expert predictions after game completion

    Implements multiple scoring methods:
    - Binary: Exact match + Brier score
    - Enum: Exact match + Brier score
    - Numeric: Gaussian kernel with category sigma
    """

    def __init__(self):
        # Default sigma values for numeric categories
        self.default_sigmas = {
            'total_game_score': 3.0,
            'home_team_total_points': 3.0,
            'away_team_total_points': 3.0,
            'point_spread': 2.0,
            'first_quarter_total': 2.0,
            'second_quarter_total': 2.0,
            'third_quarter_total': 2.0,
            'fourth_quarter_total': 2.0,
            'first_half_total': 2.5,
            'second_half_total': 2.5,
            'passing_yards': 25.0,
            'rushing_yards': 15.0,
            'receiving_yards': 20.0,
            'completion_percentage': 5.0,
            'time_of_possession': 2.0,
            'turnovers': 1.0,
            'penalties': 2.0,
            'penalty_yards': 15.0
        }

        # Performance tracking
        self.grading_times = []
        self.grading_counts = {'binary': 0, 'enum': 0, 'numeric': 0}

    def grade_predictions(
        self,
        predictions: List[Dict[str, Any]],
        actual_outcomes: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> List[GradingResult]:
        """
        Grade a list of predictions against actual outcomes

        Args:
            predictions: List of prediction dictionaries
            actual_outcomes: Dictionary of actual game outcomes
            game_context: Game context for additional information

        Returns:
            List of GradingResult objects
        """
        start_time = datetime.utcnow()

        try:
            logger.info(f"Grading {len(predictions)} predictions for game {game_context.get('game_id', 'unknown')}")

            grading_results = []

            for prediction in predictions:
                try:
                    result = self._grade_single_prediction(prediction, actual_outcomes, game_context)
                    if result:
                        grading_results.append(result)

                        # Update counters
                        pred_type = result.pred_type.value
                        self.grading_counts[pred_type] += 1

                except Exception as e:
                    logger.error(f"Failed to grade prediction {prediction.get('category', 'unknown')}: {e}")
                    continue

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.grading_times.append(processing_time)

            logger.info(f"Graded {len(grading_results)} predictions in {processing_time:.1f}ms")

            return grading_results

        except Exception as e:
            logger.error(f"Prediction grading failed: {e}")
            return []

    def _grade_single_prediction(
        self,
        prediction: Dict[str, Any],
        actual_outcomes: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> Optional[GradingResult]:
        """Grade a single prediction"""

        start_time = datetime.utcnow()

        try:
            category = prediction.get('category', '')
            pred_type_str = prediction.get('pred_type', 'binary')
            predicted_value = prediction.get('value')
            confidence = prediction.get('confidence', 0.5)
            prediction_id = prediction.get('id', f"{category}_{datetime.utcnow().timestamp()}")

            # Get actual value for this category
            actual_value = actual_outcomes.get(category)
            if actual_value is None:
                logger.warning(f"No actual outcome found for category: {category}")
                return None

            # Determine prediction type
            pred_type = PredictionType(pred_type_str)

            # Grade based on prediction type
            if pred_type == PredictionType.BINARY:
                exact_match, brier_score, final_score = self._grade_binary_prediction(
                    predicted_value, actual_value, confidence
                )
                gaussian_score = None
                sigma_used = None
                grading_method = "binary_exact_brier"

            elif pred_type == PredictionType.ENUM:
                exact_match, brier_score, final_score = self._grade_enum_prediction(
                    predicted_value, actual_value, confidence
                )
                gaussian_score = None
                sigma_used = None
                grading_method = "enum_exact_brier"

            elif pred_type == PredictionType.NUMERIC:
                exact_match, gaussian_score, final_score, sigma_used = self._grade_numeric_prediction(
                    predicted_value, actual_value, confidence, category
                )
                brier_score = None
                grading_method = "numeric_gaussian"

            else:
                logger.error(f"Unknown prediction type: {pred_type_str}")
                return None

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return GradingResult(
                prediction_id=prediction_id,
                category=category,
                pred_type=pred_type,
                predicted_value=predicted_value,
                actual_value=actual_value,
                confidence=confidence,
                exact_match=exact_match,
                brier_score=brier_score,
                gaussian_score=gaussian_score,
                final_score=final_score,
                grading_method=grading_method,
                sigma_used=sigma_used,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"Failed to grade single prediction: {e}")
            return None

    def _grade_binary_prediction(
        self,
        predicted_value: bool,
        actual_value: bool,
        confidence: float
    ) -> Tuple[bool, float, float]:
        """
        Grade binary prediction using exact match + Brier score

        Returns:
            (exact_match, brier_score, final_score)
        """
        try:
            # Exact match
            exact_match = bool(predicted_value) == bool(actual_value)

            # Brier score for calibration
            # Brier score = (forecast - outcome)^2
            # Lower is better, so we use (1 - brier_score) for scoring
            forecast_prob = confidence if predicted_value else (1 - confidence)
            outcome = 1.0 if actual_value else 0.0

            brier_score = (forecast_prob - outcome) ** 2
            brier_component = 1.0 - brier_score  # Convert to score (higher is better)

            # Combined score: 70% exact match, 30% calibration
            exact_component = 1.0 if exact_match else 0.0
            final_score = 0.7 * exact_component + 0.3 * brier_component

            return exact_match, brier_score, final_score

        except Exception as e:
            logger.error(f"Binary grading failed: {e}")
            return False, 1.0, 0.0

    def _grade_enum_prediction(
        self,
        predicted_value: str,
        actual_value: str,
        confidence: float
    ) -> Tuple[bool, float, float]:
        """
        Grade enum prediction using exact match + Brier score

        Returns:
            (exact_match, brier_score, final_score)
        """
        try:
            # Exact match
            exact_match = str(predicted_value) == str(actual_value)

            # Brier score for enum (treat as binary for the predicted option)
            # If we predicted option A with confidence C, and A was correct:
            # Brier = (C - 1)^2 if correct, (C - 0)^2 if incorrect
            if exact_match:
                brier_score = (confidence - 1.0) ** 2
            else:
                brier_score = confidence ** 2

            brier_component = 1.0 - brier_score

            # Combined score: 70% exact match, 30% calibration
            exact_component = 1.0 if exact_match else 0.0
            final_score = 0.7 * exact_component + 0.3 * brier_component

            return exact_match, brier_score, final_score

        except Exception as e:
            logger.error(f"Enum grading failed: {e}")
            return False, 1.0, 0.0

    def _grade_numeric_prediction(
        self,
        predicted_value: float,
        actual_value: float,
        confidence: float,
        category: str
    ) -> Tuple[bool, float, float, float]:
        """
        Grade numeric prediction using Gaussian kernel

        Returns:
            (exact_match, gaussian_score, final_score, sigma_used)
        """
        try:
            predicted_val = float(predicted_value)
            actual_val = float(actual_value)

            # Exact match (within small tolerance)
            exact_match = abs(predicted_val - actual_val) < 0.5

            # Get sigma for this category
            sigma = self.default_sigmas.get(category, 3.0)

            # Gaussian kernel score
            # Score = exp(-0.5 * ((predicted - actual) / sigma)^2)
            # This gives score of 1.0 for exact match, decreasing with distance
            distance = abs(predicted_val - actual_val)
            gaussian_score = math.exp(-0.5 * (distance / sigma) ** 2)

            # Confidence adjustment (optional)
            # Higher confidence should be rewarded for accurate predictions
            # and penalized for inaccurate ones
            confidence_factor = 1.0 + 0.2 * (confidence - 0.5) * gaussian_score
            confidence_factor = max(0.5, min(1.5, confidence_factor))

            final_score = gaussian_score * confidence_factor
            final_score = max(0.0, min(1.0, final_score))

            return exact_match, gaussian_score, final_score, sigma

        except Exception as e:
            logger.error(f"Numeric grading failed: {e}")
            return False, 0.0, 0.0, 3.0

    def calculate_expert_grade(
        self,
        grading_results: List[GradingResult]
    ) -> Dict[str, Any]:
        """
        Calculate overall grade for an expert based on all their predictions

        Args:
            grading_results: List of grading results for the expert

        Returns:
            Dictionary with expert grading summary
        """
        try:
            if not grading_results:
                return {
                    'total_predictions': 0,
                    'overall_score': 0.0,
                    'exact_matches': 0,
                    'exact_match_rate': 0.0,
                    'average_brier_score': None,
                    'average_gaussian_score': None,
                    'scores_by_type': {}
                }

            total_predictions = len(grading_results)
            total_score = sum(result.final_score for result in grading_results)
            overall_score = total_score / total_predictions

            exact_matches = sum(1 for result in grading_results if result.exact_match)
            exact_match_rate = exact_matches / total_predictions

            # Calculate type-specific metrics
            binary_results = [r for r in grading_results if r.pred_type == PredictionType.BINARY]
            enum_results = [r for r in grading_results if r.pred_type == PredictionType.ENUM]
            numeric_results = [r for r in grading_results if r.pred_type == PredictionType.NUMERIC]

            # Brier scores (binary + enum)
            brier_results = [r for r in grading_results if r.brier_score is not None]
            average_brier_score = (
                sum(r.brier_score for r in brier_results) / len(brier_results)
                if brier_results else None
            )

            # Gaussian scores (numeric)
            gaussian_results = [r for r in grading_results if r.gaussian_score is not None]
            average_gaussian_score = (
                sum(r.gaussian_score for r in gaussian_results) / len(gaussian_results)
                if gaussian_results else None
            )

            # Scores by type
            scores_by_type = {}

            if binary_results:
                scores_by_type['binary'] = {
                    'count': len(binary_results),
                    'average_score': sum(r.final_score for r in binary_results) / len(binary_results),
                    'exact_match_rate': sum(1 for r in binary_results if r.exact_match) / len(binary_results),
                    'average_brier': sum(r.brier_score for r in binary_results) / len(binary_results)
                }

            if enum_results:
                scores_by_type['enum'] = {
                    'count': len(enum_results),
                    'average_score': sum(r.final_score for r in enum_results) / len(enum_results),
                    'exact_match_rate': sum(1 for r in enum_results if r.exact_match) / len(enum_results),
                    'average_brier': sum(r.brier_score for r in enum_results) / len(enum_results)
                }

            if numeric_results:
                scores_by_type['numeric'] = {
                    'count': len(numeric_results),
                    'average_score': sum(r.final_score for r in numeric_results) / len(numeric_results),
                    'exact_match_rate': sum(1 for r in numeric_results if r.exact_match) / len(numeric_results),
                    'average_gaussian': sum(r.gaussian_score for r in numeric_results) / len(numeric_results)
                }

            return {
                'total_predictions': total_predictions,
                'overall_score': overall_score,
                'exact_matches': exact_matches,
                'exact_match_rate': exact_match_rate,
                'average_brier_score': average_brier_score,
                'average_gaussian_score': average_gaussian_score,
                'scores_by_type': scores_by_type
            }

        except Exception as e:
            logger.error(f"Failed to calculate expert grade: {e}")
            return {'error': str(e)}

    def get_category_performance(
        self,
        grading_results: List[GradingResult]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get performance breakdown by category

        Args:
            grading_results: List of grading results

        Returns:
            Dictionary with performance by category
        """
        try:
            category_performance = {}

            # Group results by category
            by_category = {}
            for result in grading_results:
                category = result.category
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(result)

            # Calculate metrics for each category
            for category, results in by_category.items():
                if not results:
                    continue

                total_count = len(results)
                exact_matches = sum(1 for r in results if r.exact_match)
                total_score = sum(r.final_score for r in results)

                category_performance[category] = {
                    'prediction_count': total_count,
                    'exact_matches': exact_matches,
                    'exact_match_rate': exact_matches / total_count,
                    'average_score': total_score / total_count,
                    'prediction_type': results[0].pred_type.value,
                    'best_score': max(r.final_score for r in results),
                    'worst_score': min(r.final_score for r in results)
                }

                # Add type-specific metrics
                if results[0].pred_type in [PredictionType.BINARY, PredictionType.ENUM]:
                    brier_scores = [r.brier_score for r in results if r.brier_score is not None]
                    if brier_scores:
                        category_performance[category]['average_brier_score'] = sum(brier_scores) / len(brier_scores)

                elif results[0].pred_type == PredictionType.NUMERIC:
                    gaussian_scores = [r.gaussian_score for r in results if r.gaussian_score is not None]
                    if gaussian_scores:
                        category_performance[category]['average_gaussian_score'] = sum(gaussian_scores) / len(gaussian_scores)

                    # Average prediction error
                    errors = [abs(r.predicted_value - r.actual_value) for r in results]
                    category_performance[category]['average_error'] = sum(errors) / len(errors)
                    category_performance[category]['sigma_used'] = results[0].sigma_used

            return category_performance

        except Exception as e:
            logger.error(f"Failed to get category performance: {e}")
            return {}

    def update_category_sigma(self, category: str, new_sigma: float) -> None:
        """Update sigma value for a category"""
        try:
            old_sigma = self.default_sigmas.get(category, 3.0)
            self.default_sigmas[category] = new_sigma
            logger.info(f"Updated sigma for {category}: {old_sigma} -> {new_sigma}")
        except Exception as e:
            logger.error(f"Failed to update sigma for {category}: {e}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get grading service performance metrics"""
        try:
            if not self.grading_times:
                return {
                    'total_gradings': 0,
                    'average_time_ms': 0,
                    'grading_counts': self.grading_counts.copy()
                }

            times = np.array(self.grading_times)
            total_gradings = sum(self.grading_counts.values())

            return {
                'total_gradings': total_gradings,
                'average_time_ms': float(np.mean(times)),
                'p95_time_ms': float(np.percentile(times, 95)),
                'p99_time_ms': float(np.percentile(times, 99)),
                'max_time_ms': float(np.max(times)),
                'grading_counts': self.grading_counts.copy(),
                'default_sigmas': self.default_sigmas.copy()
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}

    def reset_metrics(self) -> None:
        """Reset performance tracking metrics"""
        self.grading_times.clear()
        self.grading_counts = {'binary': 0, 'enum': 0, 'numeric': 0}
