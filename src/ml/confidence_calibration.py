"""
Confidence Calibration for NFL Prediction Models
Implements Platt scaling, model agreement scoring, and confidence intervals
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import pickle
import logging
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PlattScaler:
    """Platt scaling for probability calibration"""

    def __init__(self):
        self.calibrator = LogisticRegression()
        self.is_fitted = False

    def fit(self, probabilities: np.ndarray, true_labels: np.ndarray) -> None:
        """Fit Platt scaling parameters"""
        logger.info("Fitting Platt scaling calibrator...")

        # Reshape probabilities if needed
        if probabilities.ndim == 1:
            probabilities = probabilities.reshape(-1, 1)

        # Fit logistic regression for calibration
        self.calibrator.fit(probabilities, true_labels)
        self.is_fitted = True

        # Calculate calibration metrics
        calibrated_probs = self.transform(probabilities.flatten())
        original_brier = brier_score_loss(true_labels, probabilities.flatten())
        calibrated_brier = brier_score_loss(true_labels, calibrated_probs)

        logger.info(f"Original Brier Score: {original_brier:.4f}")
        logger.info(f"Calibrated Brier Score: {calibrated_brier:.4f}")
        logger.info(f"Improvement: {original_brier - calibrated_brier:.4f}")

    def transform(self, probabilities: np.ndarray) -> np.ndarray:
        """Apply Platt scaling to probabilities"""
        if not self.is_fitted:
            raise ValueError("Calibrator must be fitted before transformation")

        if probabilities.ndim == 1:
            probabilities = probabilities.reshape(-1, 1)

        return self.calibrator.predict_proba(probabilities)[:, 1]

    def fit_transform(self, probabilities: np.ndarray, true_labels: np.ndarray) -> np.ndarray:
        """Fit and transform in one step"""
        self.fit(probabilities, true_labels)
        return self.transform(probabilities)


class IsotonicCalibrator:
    """Isotonic regression for probability calibration"""

    def __init__(self):
        self.calibrator = IsotonicRegression(out_of_bounds='clip')
        self.is_fitted = False

    def fit(self, probabilities: np.ndarray, true_labels: np.ndarray) -> None:
        """Fit isotonic regression calibrator"""
        logger.info("Fitting isotonic regression calibrator...")

        self.calibrator.fit(probabilities, true_labels)
        self.is_fitted = True

        # Calculate calibration metrics
        calibrated_probs = self.transform(probabilities)
        original_brier = brier_score_loss(true_labels, probabilities)
        calibrated_brier = brier_score_loss(true_labels, calibrated_probs)

        logger.info(f"Isotonic - Original Brier: {original_brier:.4f}")
        logger.info(f"Isotonic - Calibrated Brier: {calibrated_brier:.4f}")

    def transform(self, probabilities: np.ndarray) -> np.ndarray:
        """Apply isotonic calibration"""
        if not self.is_fitted:
            raise ValueError("Calibrator must be fitted before transformation")

        return self.calibrator.predict(probabilities)

    def fit_transform(self, probabilities: np.ndarray, true_labels: np.ndarray) -> np.ndarray:
        """Fit and transform in one step"""
        self.fit(probabilities, true_labels)
        return self.transform(probabilities)


class ModelAgreementScorer:
    """Calculate agreement between different models"""

    def __init__(self):
        self.agreement_history = []

    def calculate_agreement(self,
                          predictions: Dict[str, np.ndarray],
                          weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """Calculate agreement scores between models"""

        if weights is None:
            weights = {model: 1.0 for model in predictions.keys()}

        agreement_metrics = {}

        # Convert predictions to arrays
        pred_arrays = {}
        for model, preds in predictions.items():
            pred_arrays[model] = np.array(preds)

        model_names = list(pred_arrays.keys())
        n_models = len(model_names)

        if n_models < 2:
            return {'overall_agreement': 1.0}

        # Pairwise agreement
        pairwise_agreements = []
        for i in range(n_models):
            for j in range(i + 1, n_models):
                model_i = model_names[i]
                model_j = model_names[j]

                # Calculate correlation between predictions
                correlation = np.corrcoef(pred_arrays[model_i], pred_arrays[model_j])[0, 1]
                if np.isnan(correlation):
                    correlation = 0.0

                # Calculate mean absolute difference
                mad = np.mean(np.abs(pred_arrays[model_i] - pred_arrays[model_j]))

                # Combined agreement score
                agreement_score = correlation * (1 - min(mad / np.mean(list(pred_arrays.values())), 1.0))
                pairwise_agreements.append(agreement_score)

                agreement_metrics[f'{model_i}_{model_j}_agreement'] = agreement_score

        # Overall agreement
        overall_agreement = np.mean(pairwise_agreements)
        agreement_metrics['overall_agreement'] = overall_agreement

        # Variance-based agreement
        all_predictions = np.array(list(pred_arrays.values()))
        prediction_variance = np.var(all_predictions, axis=0)
        variance_agreement = 1 - np.mean(prediction_variance) / np.var(all_predictions.flatten())
        agreement_metrics['variance_agreement'] = max(0, variance_agreement)

        # Weighted agreement
        if len(set(weights.values())) > 1:  # Different weights
            weighted_predictions = []
            total_weight = sum(weights.values())

            for model, preds in pred_arrays.items():
                weight = weights[model] / total_weight
                weighted_predictions.append(preds * weight)

            weighted_mean = np.sum(weighted_predictions, axis=0)
            weighted_variance = np.var([preds - weighted_mean for preds in pred_arrays.values()])
            agreement_metrics['weighted_agreement'] = 1 - np.mean(weighted_variance)

        self.agreement_history.append(agreement_metrics)
        return agreement_metrics

    def get_consistency_score(self, recent_agreements: int = 10) -> float:
        """Get consistency score based on recent agreements"""
        if len(self.agreement_history) < 2:
            return 0.5

        recent_scores = [
            agreement['overall_agreement']
            for agreement in self.agreement_history[-recent_agreements:]
        ]

        # Consistency is inverse of variance
        consistency = 1 - min(np.var(recent_scores) * 4, 1.0)  # Scale variance
        return max(0, consistency)


class ConfidenceIntervalCalculator:
    """Calculate confidence intervals for predictions"""

    def __init__(self):
        self.historical_errors = {'game_winner': [], 'total_points': [], 'player_props': []}

    def calculate_prediction_interval(self,
                                   prediction: float,
                                   prediction_type: str,
                                   confidence_level: float = 0.95) -> Tuple[float, float]:
        """Calculate prediction interval based on historical errors"""

        if prediction_type not in self.historical_errors:
            # Default intervals if no history
            if prediction_type == 'game_winner':
                return max(0, prediction - 0.2), min(1, prediction + 0.2)
            else:
                return prediction - 10, prediction + 10

        errors = self.historical_errors[prediction_type]
        if len(errors) < 10:
            # Insufficient data for reliable intervals
            if prediction_type == 'game_winner':
                margin = 0.15
            else:
                margin = 5.0

            return prediction - margin, prediction + margin

        # Calculate empirical quantiles
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        error_array = np.array(errors)
        lower_bound = prediction + np.percentile(error_array, lower_percentile)
        upper_bound = prediction + np.percentile(error_array, upper_percentile)

        # Apply bounds based on prediction type
        if prediction_type == 'game_winner':
            lower_bound = max(0, min(lower_bound, 0.99))
            upper_bound = min(1, max(upper_bound, 0.01))
        elif prediction_type == 'total_points':
            lower_bound = max(0, lower_bound)
            upper_bound = max(lower_bound + 1, upper_bound)

        return float(lower_bound), float(upper_bound)

    def update_errors(self,
                     predictions: Dict[str, float],
                     actuals: Dict[str, float]) -> None:
        """Update historical errors with new observations"""

        for pred_type in predictions:
            if pred_type in actuals and pred_type in self.historical_errors:
                error = actuals[pred_type] - predictions[pred_type]
                self.historical_errors[pred_type].append(error)

                # Keep only recent errors (last 1000)
                if len(self.historical_errors[pred_type]) > 1000:
                    self.historical_errors[pred_type] = self.historical_errors[pred_type][-1000:]


class ConfidenceCalibrator:
    """Main confidence calibration system"""

    def __init__(self):
        self.platt_scaler = PlattScaler()
        self.isotonic_calibrator = IsotonicCalibrator()
        self.agreement_scorer = ModelAgreementScorer()
        self.interval_calculator = ConfidenceIntervalCalculator()
        self.calibration_method = 'platt'  # Default method
        self.is_fitted = False

    def fit(self,
            probabilities: np.ndarray,
            true_labels: np.ndarray,
            validation_split: float = 0.3) -> None:
        """Fit calibration models"""
        logger.info("Fitting confidence calibration models...")

        # Split data for calibration method selection
        split_idx = int(len(probabilities) * (1 - validation_split))
        train_probs, val_probs = probabilities[:split_idx], probabilities[split_idx:]
        train_labels, val_labels = true_labels[:split_idx], true_labels[split_idx:]

        # Fit both calibration methods
        self.platt_scaler.fit(train_probs, train_labels)
        self.isotonic_calibrator.fit(train_probs, train_labels)

        # Evaluate on validation set
        platt_calibrated = self.platt_scaler.transform(val_probs)
        isotonic_calibrated = self.isotonic_calibrator.transform(val_probs)

        platt_brier = brier_score_loss(val_labels, platt_calibrated)
        isotonic_brier = brier_score_loss(val_labels, isotonic_calibrated)

        # Select best method
        if platt_brier <= isotonic_brier:
            self.calibration_method = 'platt'
            logger.info(f"Selected Platt scaling (Brier: {platt_brier:.4f})")
        else:
            self.calibration_method = 'isotonic'
            logger.info(f"Selected Isotonic regression (Brier: {isotonic_brier:.4f})")

        self.is_fitted = True

    def calibrate_probabilities(self, probabilities: np.ndarray) -> np.ndarray:
        """Calibrate probabilities using fitted method"""
        if not self.is_fitted:
            logger.warning("Calibrator not fitted, returning original probabilities")
            return probabilities

        if self.calibration_method == 'platt':
            return self.platt_scaler.transform(probabilities)
        else:
            return self.isotonic_calibrator.transform(probabilities)

    def calculate_comprehensive_confidence(self,
                                         predictions: Dict[str, np.ndarray],
                                         model_weights: Optional[Dict[str, float]] = None,
                                         historical_performance: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Calculate comprehensive confidence metrics"""

        # Model agreement
        agreement_metrics = self.agreement_scorer.calculate_agreement(predictions, model_weights)

        # Base confidence from agreement
        base_confidence = agreement_metrics['overall_agreement']

        # Adjust for historical performance
        if historical_performance:
            performance_weight = np.mean(list(historical_performance.values()))
            base_confidence = (base_confidence * 0.7) + (performance_weight * 0.3)

        # Calculate consistency
        consistency_score = self.agreement_scorer.get_consistency_score()

        # Final confidence score
        final_confidence = (base_confidence * 0.6) + (consistency_score * 0.4)

        # Confidence intervals for each prediction type
        confidence_intervals = {}
        for pred_type, pred_values in predictions.items():
            if len(pred_values) > 0:
                mean_pred = np.mean(pred_values)
                lower, upper = self.interval_calculator.calculate_prediction_interval(
                    mean_pred, pred_type
                )
                confidence_intervals[pred_type] = {
                    'lower_bound': lower,
                    'upper_bound': upper,
                    'interval_width': upper - lower
                }

        return {
            'confidence_score': float(final_confidence),
            'model_agreement': agreement_metrics,
            'consistency_score': float(consistency_score),
            'confidence_intervals': confidence_intervals,
            'calibration_method': self.calibration_method
        }

    def get_prediction_reliability(self,
                                 predictions: np.ndarray,
                                 confidence_scores: np.ndarray) -> Dict[str, float]:
        """Assess prediction reliability"""

        # Bin predictions by confidence
        n_bins = 10
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]

        reliability_metrics = {}
        for i in range(n_bins):
            # Find predictions in this confidence bin
            in_bin = (confidence_scores > bin_lowers[i]) & (confidence_scores <= bin_uppers[i])

            if np.sum(in_bin) > 0:
                bin_confidence = np.mean(confidence_scores[in_bin])
                bin_predictions = predictions[in_bin]

                # For classification problems, calculate accuracy in bin
                if np.all((predictions >= 0) & (predictions <= 1)):
                    # Assume binary classification
                    bin_accuracy = np.mean(bin_predictions)  # This would need true labels
                    reliability_metrics[f'bin_{i}_reliability'] = abs(bin_confidence - bin_accuracy)

        overall_reliability = np.mean(list(reliability_metrics.values())) if reliability_metrics else 0.5
        reliability_metrics['overall_reliability'] = overall_reliability

        return reliability_metrics

    def save_calibrator(self, filepath: str) -> None:
        """Save calibration models"""
        calibrator_data = {
            'platt_scaler': self.platt_scaler,
            'isotonic_calibrator': self.isotonic_calibrator,
            'calibration_method': self.calibration_method,
            'is_fitted': self.is_fitted,
            'agreement_history': self.agreement_scorer.agreement_history,
            'historical_errors': self.interval_calculator.historical_errors
        }

        with open(filepath, 'wb') as f:
            pickle.dump(calibrator_data, f)

        logger.info(f"Confidence calibrator saved to: {filepath}")

    def load_calibrator(self, filepath: str) -> None:
        """Load calibration models"""
        try:
            with open(filepath, 'rb') as f:
                calibrator_data = pickle.load(f)

            self.platt_scaler = calibrator_data['platt_scaler']
            self.isotonic_calibrator = calibrator_data['isotonic_calibrator']
            self.calibration_method = calibrator_data['calibration_method']
            self.is_fitted = calibrator_data['is_fitted']
            self.agreement_scorer.agreement_history = calibrator_data.get('agreement_history', [])
            self.interval_calculator.historical_errors = calibrator_data.get('historical_errors', {})

            logger.info(f"Confidence calibrator loaded from: {filepath}")

        except Exception as e:
            logger.error(f"Error loading calibrator: {e}")
            raise


def calculate_calibration_curve(y_true: np.ndarray,
                              y_prob: np.ndarray,
                              n_bins: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate calibration curve (reliability diagram)"""

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    mean_predicted_values = []
    fraction_positives = []

    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        # Find predictions in this bin
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)

        if np.sum(in_bin) > 0:
            mean_predicted_values.append(np.mean(y_prob[in_bin]))
            fraction_positives.append(np.mean(y_true[in_bin]))
        else:
            mean_predicted_values.append(0)
            fraction_positives.append(0)

    return np.array(fraction_positives), np.array(mean_predicted_values)


def expected_calibration_error(y_true: np.ndarray,
                             y_prob: np.ndarray,
                             n_bins: int = 10) -> float:
    """Calculate Expected Calibration Error (ECE)"""

    fraction_positives, mean_predicted_values = calculate_calibration_curve(y_true, y_prob, n_bins)

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    ece = 0
    for i, (bin_lower, bin_upper) in enumerate(zip(bin_lowers, bin_uppers)):
        # Find predictions in this bin
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = np.sum(in_bin) / len(y_prob)

        if prop_in_bin > 0:
            ece += prop_in_bin * abs(mean_predicted_values[i] - fraction_positives[i])

    return ece