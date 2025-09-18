"""
Continuous Learning System for NFL Predictions

This module implements online learning that updates models after each game,
detects concept drift, triggers automatic retraining, and tracks performance over time.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass, asdict
from sklearn.base import BaseEstimator
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
import pickle
import json
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelPerformance:
    """Track model performance over time"""
    model_id: str
    timestamp: datetime
    accuracy: float
    log_loss: float
    brier_score: float
    prediction_count: int
    correct_predictions: int
    confidence_calibration: float
    drift_score: float

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class DriftDetection:
    """Drift detection results"""
    is_drift: bool
    drift_score: float
    drift_type: str  # 'gradual', 'sudden', 'seasonal'
    affected_features: List[str]
    recommendation: str
    confidence: float

class OnlineLearner:
    """Implements online learning for continuous model updates"""

    def __init__(self, learning_rate: float = 0.01, window_size: int = 50):
        self.learning_rate = learning_rate
        self.window_size = window_size
        self.prediction_buffer = []
        self.outcome_buffer = []
        self.feature_buffer = []
        self.weights_history = []

    def update_weights(self, prediction: float, actual: float, features: np.ndarray,
                      model: BaseEstimator) -> BaseEstimator:
        """Update model weights based on prediction outcome"""
        try:
            # Calculate prediction error
            error = actual - prediction

            # Store in buffers
            self.prediction_buffer.append(prediction)
            self.outcome_buffer.append(actual)
            self.feature_buffer.append(features)

            # Keep only recent observations
            if len(self.prediction_buffer) > self.window_size:
                self.prediction_buffer.pop(0)
                self.outcome_buffer.pop(0)
                self.feature_buffer.pop(0)

            # Online gradient update for compatible models
            if hasattr(model, 'partial_fit'):
                model.partial_fit(features.reshape(1, -1), [actual])
            elif hasattr(model, 'coef_'):
                # Manual gradient update for linear models
                gradient = error * features
                model.coef_ += self.learning_rate * gradient

            # Store weights history
            if hasattr(model, 'coef_'):
                self.weights_history.append(model.coef_.copy())

            logger.info(f"Updated model weights. Error: {error:.4f}, Learning rate: {self.learning_rate}")
            return model

        except Exception as e:
            logger.error(f"Error updating model weights: {e}")
            return model

class DriftDetector:
    """Detects concept drift in prediction patterns"""

    def __init__(self, window_size: int = 100, threshold: float = 0.1):
        self.window_size = window_size
        self.threshold = threshold
        self.reference_window = []
        self.current_window = []
        self.drift_history = []

    def detect_drift(self, predictions: List[float], actuals: List[float],
                    features: np.ndarray) -> DriftDetection:
        """Detect concept drift using multiple methods"""
        try:
            if len(predictions) < self.window_size:
                return DriftDetection(False, 0.0, 'none', [], 'Insufficient data', 0.0)

            # Performance-based drift detection
            performance_drift = self._detect_performance_drift(predictions, actuals)

            # Feature distribution drift
            feature_drift = self._detect_feature_drift(features)

            # Prediction distribution drift
            prediction_drift = self._detect_prediction_drift(predictions)

            # Combine drift scores
            combined_score = (performance_drift + feature_drift + prediction_drift) / 3
            is_drift = combined_score > self.threshold

            # Determine drift type
            drift_type = self._classify_drift_type(predictions, actuals)

            # Generate recommendation
            recommendation = self._generate_recommendation(combined_score, drift_type)

            drift_result = DriftDetection(
                is_drift=is_drift,
                drift_score=combined_score,
                drift_type=drift_type,
                affected_features=self._identify_affected_features(features),
                recommendation=recommendation,
                confidence=min(combined_score * 2, 1.0)
            )

            self.drift_history.append({
                'timestamp': datetime.now(),
                'drift_score': combined_score,
                'is_drift': is_drift
            })

            logger.info(f"Drift detection: {drift_result.drift_type} drift (score: {combined_score:.4f})")
            return drift_result

        except Exception as e:
            logger.error(f"Error detecting drift: {e}")
            return DriftDetection(False, 0.0, 'error', [], f'Error: {e}', 0.0)

    def _detect_performance_drift(self, predictions: List[float], actuals: List[float]) -> float:
        """Detect drift based on performance degradation"""
        if len(predictions) < self.window_size * 2:
            return 0.0

        # Split into reference and current windows
        mid_point = len(predictions) // 2
        ref_pred = predictions[:mid_point]
        ref_actual = actuals[:mid_point]
        cur_pred = predictions[mid_point:]
        cur_actual = actuals[mid_point:]

        # Calculate accuracy for both windows
        ref_accuracy = accuracy_score([1 if a > 0.5 else 0 for a in ref_actual],
                                     [1 if p > 0.5 else 0 for p in ref_pred])
        cur_accuracy = accuracy_score([1 if a > 0.5 else 0 for a in cur_actual],
                                     [1 if p > 0.5 else 0 for p in cur_pred])

        # Return normalized performance difference
        return max(0, ref_accuracy - cur_accuracy)

    def _detect_feature_drift(self, features: np.ndarray) -> float:
        """Detect drift in feature distributions"""
        if len(features) < self.window_size * 2:
            return 0.0

        # Split features into reference and current windows
        mid_point = len(features) // 2
        ref_features = features[:mid_point]
        cur_features = features[mid_point:]

        # Calculate distribution differences using Kolmogorov-Smirnov test approximation
        drift_scores = []
        for i in range(features.shape[1]):
            ref_col = ref_features[:, i]
            cur_col = cur_features[:, i]

            # Simple distribution comparison
            ref_mean, ref_std = np.mean(ref_col), np.std(ref_col)
            cur_mean, cur_std = np.mean(cur_col), np.std(cur_col)

            if ref_std > 0 and cur_std > 0:
                mean_diff = abs(ref_mean - cur_mean) / ref_std
                std_diff = abs(ref_std - cur_std) / ref_std
                drift_scores.append((mean_diff + std_diff) / 2)

        return np.mean(drift_scores) if drift_scores else 0.0

    def _detect_prediction_drift(self, predictions: List[float]) -> float:
        """Detect drift in prediction distributions"""
        if len(predictions) < self.window_size * 2:
            return 0.0

        # Split predictions
        mid_point = len(predictions) // 2
        ref_pred = predictions[:mid_point]
        cur_pred = predictions[mid_point:]

        # Compare prediction distributions
        ref_mean = np.mean(ref_pred)
        cur_mean = np.mean(cur_pred)
        ref_std = np.std(ref_pred)
        cur_std = np.std(cur_pred)

        if ref_std > 0:
            mean_diff = abs(ref_mean - cur_mean) / ref_std
            std_diff = abs(ref_std - cur_std) / max(ref_std, 0.001)
            return (mean_diff + std_diff) / 2

        return 0.0

    def _classify_drift_type(self, predictions: List[float], actuals: List[float]) -> str:
        """Classify type of drift detected"""
        if len(predictions) < self.window_size:
            return 'none'

        # Analyze trend over time
        recent_errors = [abs(p - a) for p, a in zip(predictions[-20:], actuals[-20:])]
        older_errors = [abs(p - a) for p, a in zip(predictions[-40:-20], actuals[-40:-20])]

        if len(recent_errors) < 10 or len(older_errors) < 10:
            return 'gradual'

        recent_avg = np.mean(recent_errors)
        older_avg = np.mean(older_errors)

        if recent_avg > older_avg * 1.5:
            return 'sudden'
        elif recent_avg > older_avg * 1.2:
            return 'gradual'
        else:
            return 'seasonal'

    def _identify_affected_features(self, features: np.ndarray) -> List[str]:
        """Identify which features are most affected by drift"""
        # This would require feature names - for now return generic indices
        if len(features) < self.window_size:
            return []

        # Simple feature importance based on variance change
        mid_point = len(features) // 2
        ref_features = features[:mid_point]
        cur_features = features[mid_point:]

        affected = []
        for i in range(features.shape[1]):
            ref_var = np.var(ref_features[:, i])
            cur_var = np.var(cur_features[:, i])

            if ref_var > 0 and abs(ref_var - cur_var) / ref_var > 0.5:
                affected.append(f'feature_{i}')

        return affected[:5]  # Return top 5 affected features

    def _generate_recommendation(self, drift_score: float, drift_type: str) -> str:
        """Generate recommendation based on drift detection"""
        if drift_score < self.threshold:
            return "No action needed - model performing well"
        elif drift_score < self.threshold * 2:
            return f"Monitor closely - {drift_type} drift detected, consider online learning"
        elif drift_score < self.threshold * 3:
            return f"Update weights - significant {drift_type} drift, trigger online updates"
        else:
            return f"Retrain model - severe {drift_type} drift detected, full retraining recommended"

class ContinuousLearner:
    """Main continuous learning system coordinator"""

    def __init__(self, db_path: str = "data/continuous_learning.db"):
        self.db_path = db_path
        self.online_learner = OnlineLearner()
        self.drift_detector = DriftDetector()
        self.performance_history = []
        self.models = {}
        self.learning_active = True
        self._init_database()

    def _init_database(self):
        """Initialize database for tracking learning progress"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT,
                    timestamp TEXT,
                    accuracy REAL,
                    log_loss REAL,
                    brier_score REAL,
                    prediction_count INTEGER,
                    correct_predictions INTEGER,
                    confidence_calibration REAL,
                    drift_score REAL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS drift_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    model_id TEXT,
                    drift_type TEXT,
                    drift_score REAL,
                    affected_features TEXT,
                    recommendation TEXT,
                    action_taken TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    game_id TEXT,
                    prediction REAL,
                    actual REAL,
                    error REAL,
                    model_updated BOOLEAN,
                    learning_rate REAL
                )
            """)

    def register_model(self, model_id: str, model: BaseEstimator):
        """Register a model for continuous learning"""
        self.models[model_id] = model
        logger.info(f"Registered model {model_id} for continuous learning")

    def process_game_outcome(self, game_id: str, predictions: Dict[str, float],
                           actual_results: Dict[str, float], features: np.ndarray):
        """Process game outcome and update models"""
        if not self.learning_active:
            return

        try:
            timestamp = datetime.now()

            for model_id, prediction in predictions.items():
                if model_id in self.models:
                    actual = actual_results.get(model_id, 0.0)
                    error = abs(prediction - actual)

                    # Update model weights
                    updated_model = self.online_learner.update_weights(
                        prediction, actual, features, self.models[model_id]
                    )
                    self.models[model_id] = updated_model

                    # Log learning event
                    self._log_learning_event(timestamp, game_id, prediction, actual,
                                           error, True, self.online_learner.learning_rate)

                    # Check for drift
                    if len(self.online_learner.prediction_buffer) >= 20:
                        drift_result = self.drift_detector.detect_drift(
                            self.online_learner.prediction_buffer,
                            self.online_learner.outcome_buffer,
                            np.array(self.online_learner.feature_buffer)
                        )

                        if drift_result.is_drift:
                            self._handle_drift(model_id, drift_result, timestamp)

                    # Update performance tracking
                    self._update_performance_tracking(model_id, timestamp)

            logger.info(f"Processed game {game_id} outcomes for continuous learning")

        except Exception as e:
            logger.error(f"Error processing game outcome: {e}")

    def _handle_drift(self, model_id: str, drift_result: DriftDetection, timestamp: datetime):
        """Handle detected concept drift"""
        try:
            # Log drift event
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO drift_events
                    (timestamp, model_id, drift_type, drift_score, affected_features, recommendation, action_taken)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp.isoformat(),
                    model_id,
                    drift_result.drift_type,
                    drift_result.drift_score,
                    json.dumps(drift_result.affected_features),
                    drift_result.recommendation,
                    'weights_adjusted'
                ))

            # Adjust learning rate based on drift severity
            if drift_result.drift_score > 0.3:
                self.online_learner.learning_rate *= 1.5  # Increase learning rate
            elif drift_result.drift_score > 0.5:
                # Trigger retraining flag
                self._trigger_retraining(model_id, drift_result)

            logger.warning(f"Drift detected for {model_id}: {drift_result.drift_type} "
                          f"(score: {drift_result.drift_score:.4f})")

        except Exception as e:
            logger.error(f"Error handling drift: {e}")

    def _trigger_retraining(self, model_id: str, drift_result: DriftDetection):
        """Trigger model retraining due to severe drift"""
        try:
            # Create retraining flag file
            flag_path = Path(f"data/retrain_flags/{model_id}_retrain.flag")
            flag_path.parent.mkdir(parents=True, exist_ok=True)

            with open(flag_path, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'concept_drift',
                    'drift_score': drift_result.drift_score,
                    'drift_type': drift_result.drift_type,
                    'affected_features': drift_result.affected_features
                }, f, indent=2)

            logger.warning(f"Triggered retraining for {model_id} due to severe drift")

        except Exception as e:
            logger.error(f"Error triggering retraining: {e}")

    def _update_performance_tracking(self, model_id: str, timestamp: datetime):
        """Update performance tracking metrics"""
        try:
            if len(self.online_learner.prediction_buffer) < 10:
                return

            recent_predictions = self.online_learner.prediction_buffer[-10:]
            recent_actuals = self.online_learner.outcome_buffer[-10:]

            # Calculate metrics
            binary_predictions = [1 if p > 0.5 else 0 for p in recent_predictions]
            binary_actuals = [1 if a > 0.5 else 0 for a in recent_actuals]

            accuracy = accuracy_score(binary_actuals, binary_predictions)
            log_loss_val = log_loss(binary_actuals, recent_predictions, eps=1e-15)
            brier_score = brier_score_loss(binary_actuals, recent_predictions)

            # Confidence calibration (simplified)
            confidence_calibration = 1.0 - abs(np.mean(recent_predictions) - np.mean(recent_actuals))

            # Get latest drift score
            drift_score = self.drift_detector.drift_history[-1]['drift_score'] if self.drift_detector.drift_history else 0.0

            performance = ModelPerformance(
                model_id=model_id,
                timestamp=timestamp,
                accuracy=accuracy,
                log_loss=log_loss_val,
                brier_score=brier_score,
                prediction_count=len(recent_predictions),
                correct_predictions=sum(1 for p, a in zip(binary_predictions, binary_actuals) if p == a),
                confidence_calibration=confidence_calibration,
                drift_score=drift_score
            )

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO model_performance
                    (model_id, timestamp, accuracy, log_loss, brier_score,
                     prediction_count, correct_predictions, confidence_calibration, drift_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    performance.model_id,
                    performance.timestamp.isoformat(),
                    performance.accuracy,
                    performance.log_loss,
                    performance.brier_score,
                    performance.prediction_count,
                    performance.correct_predictions,
                    performance.confidence_calibration,
                    performance.drift_score
                ))

            self.performance_history.append(performance)

        except Exception as e:
            logger.error(f"Error updating performance tracking: {e}")

    def _log_learning_event(self, timestamp: datetime, game_id: str, prediction: float,
                           actual: float, error: float, model_updated: bool, learning_rate: float):
        """Log individual learning events"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO learning_events
                    (timestamp, game_id, prediction, actual, error, model_updated, learning_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp.isoformat(),
                    game_id,
                    prediction,
                    actual,
                    error,
                    model_updated,
                    learning_rate
                ))

        except Exception as e:
            logger.error(f"Error logging learning event: {e}")

    def get_performance_metrics(self, model_id: Optional[str] = None, days: int = 30) -> List[Dict]:
        """Get performance metrics for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if model_id:
                    query = """
                        SELECT * FROM model_performance
                        WHERE model_id = ? AND timestamp > datetime('now', '-{} days')
                        ORDER BY timestamp DESC
                    """.format(days)
                    cursor = conn.execute(query, (model_id,))
                else:
                    query = """
                        SELECT * FROM model_performance
                        WHERE timestamp > datetime('now', '-{} days')
                        ORDER BY timestamp DESC
                    """.format(days)
                    cursor = conn.execute(query)

                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return []

    def get_drift_events(self, model_id: Optional[str] = None, days: int = 30) -> List[Dict]:
        """Get drift events for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if model_id:
                    query = """
                        SELECT * FROM drift_events
                        WHERE model_id = ? AND timestamp > datetime('now', '-{} days')
                        ORDER BY timestamp DESC
                    """.format(days)
                    cursor = conn.execute(query, (model_id,))
                else:
                    query = """
                        SELECT * FROM drift_events
                        WHERE timestamp > datetime('now', '-{} days')
                        ORDER BY timestamp DESC
                    """.format(days)
                    cursor = conn.execute(query)

                columns = [desc[0] for desc in cursor.description]
                events = [dict(zip(columns, row)) for row in cursor.fetchall()]

                # Parse JSON fields
                for event in events:
                    if event.get('affected_features'):
                        event['affected_features'] = json.loads(event['affected_features'])

                return events

        except Exception as e:
            logger.error(f"Error getting drift events: {e}")
            return []

    def save_models(self, save_path: str = "models/continuous_learning"):
        """Save current model states"""
        try:
            Path(save_path).mkdir(parents=True, exist_ok=True)

            for model_id, model in self.models.items():
                model_path = Path(save_path) / f"{model_id}_model.pkl"
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)

            # Save learning state
            state_path = Path(save_path) / "learning_state.json"
            with open(state_path, 'w') as f:
                json.dump({
                    'learning_rate': self.online_learner.learning_rate,
                    'window_size': self.online_learner.window_size,
                    'drift_threshold': self.drift_detector.threshold,
                    'learning_active': self.learning_active,
                    'last_update': datetime.now().isoformat()
                }, f, indent=2)

            logger.info(f"Saved {len(self.models)} models and learning state")

        except Exception as e:
            logger.error(f"Error saving models: {e}")

    def load_models(self, load_path: str = "models/continuous_learning"):
        """Load saved model states"""
        try:
            load_dir = Path(load_path)
            if not load_dir.exists():
                logger.warning(f"Model directory {load_path} does not exist")
                return

            # Load models
            for model_path in load_dir.glob("*_model.pkl"):
                model_id = model_path.stem.replace("_model", "")
                with open(model_path, 'rb') as f:
                    self.models[model_id] = pickle.load(f)

            # Load learning state
            state_path = load_dir / "learning_state.json"
            if state_path.exists():
                with open(state_path) as f:
                    state = json.load(f)
                    self.online_learner.learning_rate = state.get('learning_rate', 0.01)
                    self.drift_detector.threshold = state.get('drift_threshold', 0.1)
                    self.learning_active = state.get('learning_active', True)

            logger.info(f"Loaded {len(self.models)} models and learning state")

        except Exception as e:
            logger.error(f"Error loading models: {e}")

    def reset_learning_rate(self):
        """Reset learning rate to default after drift handling"""
        self.online_learner.learning_rate = 0.01
        logger.info("Reset learning rate to default (0.01)")

    def set_learning_active(self, active: bool):
        """Enable or disable continuous learning"""
        self.learning_active = active
        logger.info(f"Continuous learning {'activated' if active else 'deactivated'}")

# Example usage
if __name__ == "__main__":
    # Initialize continuous learner
    learner = ContinuousLearner()

    # Simulate model registration and learning
    from sklearn.linear_model import LogisticRegression

    model = LogisticRegression()
    learner.register_model("spread_model", model)

    # Simulate processing game outcomes
    predictions = {"spread_model": 0.65}
    actuals = {"spread_model": 1.0}
    features = np.random.random((1, 10))[0]

    learner.process_game_outcome("game_123", predictions, actuals, features)

    # Get performance metrics
    metrics = learner.get_performance_metrics()
    print(f"Performance metrics: {len(metrics)} entries")

    # Save models
    learner.save_models()