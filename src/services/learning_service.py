"""
Learning & Calibration Service

Implements post-game learning and calibration updates for the Expert Council Betting System.
Handles Beta calibration for binary/enum predictions, EMA updates for numeric predictions,
and factor adjustments with comprehensive audit trails.

Features:
- Beta calibration for binary and enum predictions
- Exponential Moving Average (EMA) for numeric predictions
- Factor updates with multiplicative weight adjustments
- Comprehensive audit trails for all learning updates
- Performance tracking and calibration metrics
- Persona-specific learning rate adjustments

Requirements: 2.6 - Learning & calibration
"""

import logging
import uuid
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

class LearningType(Enum):
    """Types of learning updates"""
    BETA_CALIBRATION = "beta_calibration"
    EMA_NUMERIC = "ema_numeric"
    FACTOR_UPDATE = "factor_update"
    MOMENTUM_UPDATE = "momentum_update"
    OFFENSIVE_EFFICIENCY_UPDATE = "offensive_efficiency_update"

class CalibrationMethod(Enum):
    """Calibration methods for different prediction types"""
    BETA_BINARY = "beta_binary"
    BETA_ENUM = "beta_enum"
    EMA_GAUSSIAN = "ema_gaussian"
    MULTIPLICATIVE_WEIGHTS = "multiplicative_weights"

@dataclass
class BetaCalibrationState:
    """Beta distribution parameters for binary/enum calibration"""
    alpha: float = 1.0  # Success count + prior
    beta: float = 1.0   # Failure count + prior

    # Metadata
    total_predictions: int = 0
    correct_predictions: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def get_mean(self) -> float:
        """Get the mean of the beta distribution"""
        return self.alpha / (self.alpha + self.beta)

    def get_variance(self) -> float:
        """Get the variance of the beta distribution"""
        return (self.alpha * self.beta) / ((self.alpha + self.beta)**2 * (self.alpha + self.beta + 1))

    def get_confidence_interval(self, confidence: float = 0.95) -> Tuple[float, float]:
        """Get confidence interval for the beta distribution"""
        from scipy.stats import beta
        alpha_level = (1 - confidence) / 2
        lower = beta.ppf(alpha_level, self.alpha, self.beta)
        upper = beta.ppf(1 - alpha_level, self.alpha, self.beta)
        return lower, upper

@dataclass
class EMAState:
    """Exponential Moving Average state foredictions"""
    mu: float = 0.0      # Mean estimate
    sigma: float = 1.0   # Standard deviation estimate
    alpha: float = 0.1   # Learning rate

    # Metadata
    total_predictions: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def update(self, observed_value: float, predicted_value: float) -> None:
        """Update EMA estimates with new observation"""
        error = observed_value - predicted_value

        # Update mean (bias correction)
        self.mu = (1 - self.alpha) * self.mu + self.alpha * error

        # Update variance estimate
        squared_error = error ** 2
        self.sigma = np.sqrt((1 - self.alpha) * self.sigma**2 + self.alpha * squared_error)

        self.total_predictions += 1
        self.last_updated = datetime.utcnow()

@dataclass
class FactorState:
    """Factor weights for different prediction categories"""
    momentum_factor: float = 1.02      # Slight positive momentum bias
    offensive_efficiency_factor: float = 0.95  # Down-weight offensive efficiency
    defensive_factor: float = 1.0
    weather_factor: float = 1.0
    home_field_factor: float = 1.0
    injury_factor: float = 1.0

    # Metadata
    last_updated: datetime = field(default_factory=datetime.utcnow)
    update_count: int = 0

    def get_factor(self, category: str) -> float:
        """Get factor weight for a specific category"""
        category_lower = category.lower()

        if 'momentum' in category_lower:
            return self.momentum_factor
        elif 'offensive' in category_lower or 'offense' in category_lower:
            return self.offensive_efficiency_factor
        elif 'defensive' in category_lower or 'defense' in category_lower:
            return self.defensive_factor
        elif 'weather' in category_lower:
            return self.weather_factor
        elif 'home' in category_lower:
            return self.home_field_factor
        elif 'injury' in category_lower or 'injured' in category_lower:
            return self.injury_factor
        else:
            return 1.0  # Default factor

    def update_factor(self, category: str, multiplier: float) -> bool:
        """Update factor with multiplicative adjustment"""
        try:
            category_lower = category.lower()

            if 'momentum' in category_lower:
                self.momentum_factor *= multiplier
            elif 'offensive' in category_lower or 'offense' in category_lower:
                self.offensive_efficiency_factor *= multiplier
            elif 'defensive' in category_lower or 'defense' in category_lower:
                self.defensive_factor *= multiplier
            elif 'weather' in category_lower:
                self.weather_factor *= multiplier
            elif 'home' in category_lower:
                self.home_field_factor *= multiplier
            elif 'injury' in category_lower or 'injured' in category_lower:
                self.injury_factor *= multiplier
            else:
                return False  # Unknown category

            self.update_count += 1
            self.last_updated = datetime.utcnow()
            return True

        except Exception as e:
            logger.error(f"Failed to update factor for {category}: {e}")
            return False

@dataclass
class LearningUpdate:
    """Record of a learning update"""
    update_id: str
    expert_id: str
    game_id: str
    category: str

    # Update details
    learning_type: LearningType
    calibration_method: CalibrationMethod

    # Before/after states
    state_before: Dict[str, Any]
    state_after: Dict[str, Any]

    # Update parameters
    observed_value: Any
    predicted_value: Any
    prediction_confidence: float
    grading_score: float

    # Metadata
    update_time: datetime
    processing_time_ms: float
    persona_adjustments: Dict[str, float] = field(default_factory=dict)

@dataclass
class LearningSession:
    """Summary of learning updates for an expert after a game"""
    expert_id: str
    game_id: str

    # Update counts
    total_updates: int
    beta_updates: int
    ema_updates: int
    factor_updates: int

    # Performance changes
    calibration_improvement: float
    prediction_accuracy_change: float

    # Processing metadata
    session_time: datetime
    processing_time_ms: float
    updates: List[LearningUpdate] = field(default_factory=list)

class LearningService:
    """
    Service for post-game learning and calibration updates

    Implements Beta calibration for binary/enum predictions, EMA for numeric predictions,
    and factor updates with comprehensive audit trails
    """

    def __init__(self):
        # Expert learning states (in production, these would be in database)
        self.beta_states: Dict[str, Dict[str, BetaCalibrationState]] = {}  # expert_id -> category -> state
        self.ema_states: Dict[str, Dict[str, EMAState]] = {}  # expert_id -> category -> state
        self.factor_states: Dict[str, FactorState] = {}  # expert_id -> state

        # Audit trail
        self.learning_updates: List[LearningUpdate] = []
        self.learning_sessions: List[LearningSession] = []

        # Performance tracking
        self.update_times: List[float] = []
        self.update_counts = {
            'beta': 0,
            'ema': 0,
            'factor': 0,
            'failed': 0
        }

        # Learning configuration
        self.learning_config = {
            'beta_learning_rate': 0.1,
            'ema_alpha': 0.1,
            'factor_adjustment_rate': 0.05,
            'momentum_prior': 1.02,
            'offensive_efficiency_prior': 0.95,
            'min_predictions_for_update': 3,
            'max_factor_change': 0.2  # Maximum 20% change per update
        }

        # Persona-specific adjustments
        self.persona_adjustments = {
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

    def process_expert_learning(
        self,
        expert_id: str,
        game_id: str,
        predictions: List[Dict[str, Any]],
        grading_results: List[Dict[str, Any]],
        game_context: Dict[str, Any]
    ) -> LearningSession:
        """
        Process all learning updates for an expert after a game

        Args:
            expert_id: Expert identifier
            game_id: Game identifier
            predictions: List of expert predictions
            grading_results: List of grading results from grading service
            game_context: Game context information

        Returns:
            LearningSession with summary of all updates
        """
        start_time = datetime.utcnow()

        try:
            logger.info(f"Processing learning updates for expert {expert_id} in game {game_id}")

            # Initialize expert states if needed
            self._initialize_expert_states(expert_id)

            updates = []
            beta_updates = 0
            ema_updates = 0
            factor_updates = 0

            # Process each prediction-result pair
            for prediction, grading_result in zip(predictions, grading_results):
                try:
                    category = prediction.get('category', '')
                    pred_type = prediction.get('pred_type', '')

                    # Determine learning type based on prediction type
                    if pred_type in ['binary', 'enum']:
                        # Beta calibration update
                        update = self._update_beta_calibration(
                            expert_id, game_id, category, prediction, grading_result
                        )
                        if update:
                            updates.append(update)
                            beta_updates += 1

                    elif pred_type == 'numeric':
                        # EMA update
                        update = self._update_ema_calibration(
                            expert_id, game_id, category, prediction, grading_result
                        )
                        if update:
                            updates.append(update)
                            ema_updates += 1

                    # Factor updates based on category performance
                    factor_update = self._update_category_factors(
                        expert_id, game_id, category, prediction, grading_result
                    )
                    if factor_update:
                        updates.append(factor_update)
                        factor_updates += 1

                except Exception as e:
                    logger.error(f"Failed to process learning for prediction {prediction.get('id', 'unknown')}: {e}")
                    self.update_counts['failed'] += 1
                    continue

            # Calculate performance changes
            calibration_improvement = self._calculate_calibration_improvement(expert_id, updates)
            accuracy_change = self._calculate_accuracy_change(expert_id, updates)

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.update_times.append(processing_time)

            # Create learning session summary
            session = LearningSession(
                expert_id=expert_id,
                game_id=game_id,
                total_updates=len(updates),
                beta_updates=beta_updates,
                ema_updates=ema_updates,
                factor_updates=factor_updates,
                calibration_improvement=calibration_improvement,
                prediction_accuracy_change=accuracy_change,
                session_time=datetime.utcnow(),
                processing_time_ms=processing_time,
                updates=updates
            )

            # Store session
            self.learning_sessions.append(session)

            # Update counters
            self.update_counts['beta'] += beta_updates
            self.update_counts['ema'] += ema_updates
            self.update_counts['factor'] += factor_updates

            logger.info(f"Learning session completed for {expert_id}: "
                       f"{len(updates)} updates, {processing_time:.1f}ms")

            return session

        except Exception as e:
            logger.error(f"Learning session failed for expert {expert_id}: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return LearningSession(
                expert_id=expert_id,
                game_id=game_id,
                total_updates=0,
                beta_updates=0,
                ema_updates=0,
                factor_updates=0,
                calibration_improvement=0.0,
                prediction_accuracy_change=0.0,
                session_time=datetime.utcnow(),
                processing_time_ms=processing_time,
                updates=[]
            )

    def _initialize_expert_states(self, expert_id: str) -> None:
        """Initialize learning states for an expert"""
        if expert_id not in self.beta_states:
            self.beta_states[expert_id] = {}

        if expert_id not in self.ema_states:
            self.ema_states[expert_id] = {}

        if expert_id not in self.factor_states:
            # Initialize with default priors
            self.factor_states[expert_id] = FactorState(
                momentum_factor=self.learning_config['momentum_prior'],
                offensive_efficiency_factor=self.learning_config['offensive_efficiency_prior']
            )

    def _update_beta_calibration(
        self,
        expert_id: str,
        game_id: str,
        category: str,
        prediction: Dict[str, Any],
        grading_result: Dict[str, Any]
    ) -> Optional[LearningUpdate]:
        """Update Beta calibration for binary/enum predictions"""

        try:
            start_time = datetime.utcnow()

            # Get or create beta state for this category
            if category not in self.beta_states[expert_id]:
                self.beta_states[expert_id][category] = BetaCalibrationState()

            beta_state = self.beta_states[expert_id][category]

            # Store state before update
            state_before = {
                'alpha': beta_state.alpha,
                'beta': beta_state.beta,
                'mean': beta_state.get_mean(),
                'variance': beta_state.get_variance(),
                'total_predictions': beta_state.total_predictions,
                'correct_predictions': beta_state.correct_predictions
            }

            # Determine if prediction was correct
            predicted_value = prediction.get('value')
            actual_value = grading_result.get('actual_value')
            exact_match = grading_result.get('exact_match', False)
            grading_score = grading_result.get('final_score', 0.0)

            # Get persona-specific learning rate
            learning_rate = self._get_persona_learning_rate(expert_id, 'beta_learning_rate')

            # Update beta parameters
            if exact_match:
                # Correct prediction - increase alpha
                beta_state.alpha += learning_rate
                beta_state.correct_predictions += 1
            else:
                # Incorrect prediction - increase beta
                beta_state.beta += learning_rate

            beta_state.total_predictions += 1
            beta_state.last_updated = datetime.utcnow()

            # Store state after update
            state_after = {
                'alpha': beta_state.alpha,
                'beta': beta_state.beta,
                'mean': beta_state.get_mean(),
                'variance': beta_state.get_variance(),
                'total_predictions': beta_state.total_predictions,
                'correct_predictions': beta_state.correct_predictions
            }

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Create learning update record
            update = LearningUpdate(
                update_id=str(uuid.uuid4()),
                expert_id=expert_id,
                game_id=game_id,
                category=category,
                learning_type=LearningType.BETA_CALIBRATION,
                calibration_method=CalibrationMethod.BETA_BINARY if prediction.get('pred_type') == 'binary' else CalibrationMethod.BETA_ENUM,
                state_before=state_before,
                state_after=state_after,
                observed_value=actual_value,
                predicted_value=predicted_value,
                prediction_confidence=prediction.get('confidence', 0.5),
                grading_score=grading_score,
                update_time=datetime.utcnow(),
                processing_time_ms=processing_time,
                persona_adjustments={'learning_rate': learning_rate}
            )

            self.learning_updates.append(update)

            logger.debug(f"Beta calibration updated for {expert_id}/{category}: "
                        f"α={beta_state.alpha:.3f}, β={beta_state.beta:.3f}, "
                        f"mean={beta_state.get_mean():.3f}")

            return update

        except Exception as e:
            logger.error(f"Beta calibration update failed for {expert_id}/{category}: {e}")
            return None

    def _update_ema_calibration(
        self,
        expert_id: str,
        game_id: str,
        category: str,
        prediction: Dict[str, Any],
        grading_result: Dict[str, Any]
    ) -> Optional[LearningUpdate]:
        """Update EMA calibration for numeric predictions"""

        try:
            start_time = datetime.utcnow()

            # Get or create EMA state for this category
            if category not in self.ema_states[expert_id]:
                # Get persona-specific alpha
                alpha = self._get_persona_learning_rate(expert_id, 'ema_alpha')
                self.ema_states[expert_id][category] = EMAState(alpha=alpha)

            ema_state = self.ema_states[expert_id][category]

            # Store state before update
            state_before = {
                'mu': ema_state.mu,
                'sigma': ema_state.sigma,
                'alpha': ema_state.alpha,
                'total_predictions': ema_state.total_predictions
            }

            # Get values
            predicted_value = float(prediction.get('value', 0))
            actual_value = float(grading_result.get('actual_value', 0))
            grading_score = grading_result.get('final_score', 0.0)

            # Update EMA estimates
            ema_state.update(actual_value, predicted_value)

            # Store state after update
            state_after = {
                'mu': ema_state.mu,
                'sigma': ema_state.sigma,
                'alpha': ema_state.alpha,
                'total_predictions': ema_state.total_predictions
            }

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Create learning update record
            update = LearningUpdate(
                update_id=str(uuid.uuid4()),
                expert_id=expert_id,
                game_id=game_id,
                category=category,
                learning_type=LearningType.EMA_NUMERIC,
                calibration_method=CalibrationMethod.EMA_GAUSSIAN,
                state_before=state_before,
                state_after=state_after,
                observed_value=actual_value,
                predicted_value=predicted_value,
                prediction_confidence=prediction.get('confidence', 0.5),
                grading_score=grading_score,
                update_time=datetime.utcnow(),
                processing_time_ms=processing_time,
                persona_adjustments={'ema_alpha': ema_state.alpha}
            )

            self.learning_updates.append(update)

            logger.debug(f"EMA calibration updated for {expert_id}/{category}: "
                        f"μ={ema_state.mu:.3f}, σ={ema_state.sigma:.3f}")

            return update

        except Exception as e:
            logger.error(f"EMA calibration update failed for {expert_id}/{category}: {e}")
            return None

    def _update_category_factors(
        self,
        expert_id: str,
        game_id: str,
        category: str,
        prediction: Dict[str, Any],
        grading_result: Dict[str, Any]
    ) -> Optional[LearningUpdate]:
        """Update category-specific factors based on performance"""

        try:
            start_time = datetime.utcnow()

            factor_state = self.factor_states[expert_id]

            # Store state before update
            state_before = {
                'momentum_factor': factor_state.momentum_factor,
                'offensive_efficiency_factor': factor_state.offensive_efficiency_factor,
                'defensive_factor': factor_state.defensive_factor,
                'weather_factor': factor_state.weather_factor,
                'home_field_factor': factor_state.home_field_factor,
                'injury_factor': factor_state.injury_factor
            }

            # Calculate adjustment based on grading score
            grading_score = grading_result.get('final_score', 0.0)
            adjustment_rate = self._get_persona_learning_rate(expert_id, 'factor_adjustment_rate')

            # Calculate multiplier based on performance
            # Score > 0.5 increases factor, score < 0.5 decreases factor
            performance_delta = grading_score - 0.5
            multiplier = 1.0 + (performance_delta * adjustment_rate)

            # Apply bounds to prevent extreme changes
            max_change = self.learning_config['max_factor_change']
            multiplier = max(1.0 - max_change, min(1.0 + max_change, multiplier))

            # Update the relevant factor
            factor_updated = factor_state.update_factor(category, multiplier)

            if not factor_updated:
                return None  # No relevant factor for this category

            # Store state after update
            state_after = {
                'momentum_factor': factor_state.momentum_factor,
                'offensive_efficiency_factor': factor_state.offensive_efficiency_factor,
                'defensive_factor': factor_state.defensive_factor,
                'weather_factor': factor_state.weather_factor,
                'home_field_factor': factor_state.home_field_factor,
                'injury_factor': factor_state.injury_factor
            }

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Create learning update record
            update = LearningUpdate(
                update_id=str(uuid.uuid4()),
                expert_id=expert_id,
                game_id=game_id,
                category=category,
                learning_type=LearningType.FACTOR_UPDATE,
                calibration_method=CalibrationMethod.MULTIPLICATIVE_WEIGHTS,
                state_before=state_before,
                state_after=state_after,
                observed_value=grading_result.get('actual_value'),
                predicted_value=prediction.get('value'),
                prediction_confidence=prediction.get('confidence', 0.5),
                grading_score=grading_score,
                update_time=datetime.utcnow(),
                processing_time_ms=processing_time,
                persona_adjustments={
                    'adjustment_rate': adjustment_rate,
                    'multiplier': multiplier
                }
            )

            self.learning_updates.append(update)

            logger.debug(f"Factor updated for {expert_id}/{category}: "
                        f"multiplier={multiplier:.3f}, score={grading_score:.3f}")

            return update

        except Exception as e:
            logger.error(f"Factor update failed for {expert_id}/{category}: {e}")
            return None

    def _get_persona_learning_rate(self, expert_id: str, parameter: str) -> float:
        """Get persona-specific learning rate"""
        try:
            # Extract persona from expert_id (assuming format like "conservative_analyzer")
            persona = expert_id.lower()

            # Check if the expert_id matches any persona key
            for persona_key in self.persona_adjustments:
                if persona_key in persona or persona in persona_key:
                    persona_config = self.persona_adjustments[persona_key]
                    if parameter in persona_config:
                        return persona_config[parameter]

            # Return default from learning config
            return self.learning_config.get(parameter, 0.1)

        except Exception as e:
            logger.error(f"Failed to get persona learning rate for {expert_id}/{parameter}: {e}")
            return self.learning_config.get(parameter, 0.1)

    def _calculate_calibration_improvement(self, expert_id: str, updates: List[LearningUpdate]) -> float:
        """Calculate overall calibration improvement from updates"""
        try:
            if not updates:
                return 0.0

            # Calculate average improvement in calibration
            improvements = []

            for update in updates:
                if update.learning_type == LearningType.BETA_CALIBRATION:
                    # For beta calibration, improvement is reduction in variance
                    before_var = update.state_before.get('variance', 1.0)
                    after_var = update.state_after.get('variance', 1.0)
                    improvement = before_var - after_var  # Positive = improvement
                    improvements.append(improvement)

                elif update.learning_type == LearningType.EMA_NUMERIC:
                    # For EMA, improvement is reduction in prediction error
                    before_sigma = update.state_before.get('sigma', 1.0)
                    after_sigma = update.state_after.get('sigma', 1.0)
                    improvement = before_sigma - after_sigma  # Positive = improvement
                    improvements.append(improvement)

            return np.mean(improvements) if improvements else 0.0

        except Exception as e:
            logger.error(f"Failed to calculate calibration improvement: {e}")
            return 0.0

    def _calculate_accuracy_change(self, expert_id: str, updates: List[LearningUpdate]) -> float:
        """Calculate change in prediction accuracy"""
        try:
            if not updates:
                return 0.0

            # Calculate weighted average of grading scores
            scores = [update.grading_score for update in updates]
            return np.mean(scores) - 0.5  # Relative to random baseline

        except Exception as e:
            logger.error(f"Failed to calculate accuracy change: {e}")
            return 0.0

    def get_expert_calibration_state(self, expert_id: str) -> Dict[str, Any]:
        """Get current calibration state for an expert"""
        try:
            self._initialize_expert_states(expert_id)

            # Beta states
            beta_summary = {}
            for category, state in self.beta_states[expert_id].items():
                beta_summary[category] = {
                    'mean': state.get_mean(),
                    'variance': state.get_variance(),
                    'total_predictions': state.total_predictions,
                    'correct_predictions': state.correct_predictions,
                    'accuracy': state.correct_predictions / max(state.total_predictions, 1),
                    'last_updated': state.last_updated.isoformat()
                }

            # EMA states
            ema_summary = {}
            for category, state in self.ema_states[expert_id].items():
                ema_summary[category] = {
                    'mu': state.mu,
                    'sigma': state.sigma,
                    'alpha': state.alpha,
                    'total_predictions': state.total_predictions,
                    'last_updated': state.last_updated.isoformat()
                }

            # Factor states
            factor_state = self.factor_states[expert_id]
            factor_summary = {
                'momentum_factor': factor_state.momentum_factor,
                'offensive_efficiency_factor': factor_state.offensive_efficiency_factor,
                'defensive_factor': factor_state.defensive_factor,
                'weather_factor': factor_state.weather_factor,
                'home_field_factor': factor_state.home_field_factor,
                'injury_factor': factor_state.injury_factor,
                'last_updated': factor_state.last_updated.isoformat(),
                'update_count': factor_state.update_count
            }

            return {
                'expert_id': expert_id,
                'beta_calibration': beta_summary,
                'ema_calibration': ema_summary,
                'factor_weights': factor_summary,
                'total_learning_updates': len([u for u in self.learning_updates if u.expert_id == expert_id])
            }

        except Exception as e:
            logger.error(f"Failed to get calibration state for {expert_id}: {e}")
            return {'error': str(e)}

    def get_learning_history(
        self,
        expert_id: Optional[str] = None,
        game_id: Optional[str] = None,
        learning_type: Optional[LearningType] = None,
        limit: Optional[int] = None
    ) -> List[LearningUpdate]:
        """Get learning update history with optional filters"""
        try:
            filtered_updates = self.learning_updates.copy()

            if expert_id:
                filtered_updates = [u for u in filtered_updates if u.expert_id == expert_id]

            if game_id:
                filtered_updates = [u for u in filtered_updates if u.game_id == game_id]

            if learning_type:
                filtered_updates = [u for u in filtered_updates if u.learning_type == learning_type]

            # Sort by update time (newest first)
            filtered_updates.sort(key=lambda u: u.update_time, reverse=True)

            if limit:
                filtered_updates = filtered_updates[:limit]

            return filtered_updates

        except Exception as e:
            logger.error(f"Failed to get learning history: {e}")
            return []

    def get_learning_performance_metrics(self) -> Dict[str, Any]:
        """Get learning service performance metrics"""
        try:
            if not self.update_times:
                return {
                    'total_updates': 0,
                    'average_time_ms': 0,
                    'update_counts': self.update_counts.copy(),
                    'total_experts': len(self.factor_states),
                    'total_sessions': len(self.learning_sessions)
                }

            times = np.array(self.update_times)
            total_updates = sum(self.update_counts.values())

            # Calculate learning effectiveness
            recent_sessions = self.learning_sessions[-10:] if len(self.learning_sessions) >= 10 else self.learning_sessions
            avg_calibration_improvement = np.mean([s.calibration_improvement for s in recent_sessions]) if recent_sessions else 0.0
            avg_accuracy_change = np.mean([s.prediction_accuracy_change for s in recent_sessions]) if recent_sessions else 0.0

            return {
                'total_updates': total_updates,
                'average_time_ms': float(np.mean(times)),
                'p95_time_ms': float(np.percentile(times, 95)),
                'p99_time_ms': float(np.percentile(times, 99)),
                'max_time_ms': float(np.max(times)),
                'update_counts': self.update_counts.copy(),
                'total_experts': len(self.factor_states),
                'total_sessions': len(self.learning_sessions),
                'avg_calibration_improvement': avg_calibration_improvement,
                'avg_accuracy_change': avg_accuracy_change,
                'learning_config': self.learning_config.copy()
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}

    def update_learning_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update learning configuration"""
        try:
            for key, value in config_updates.items():
                if key in self.learning_config:
                    old_value = self.learning_config[key]
                    self.learning_config[key] = value
                    logger.info(f"Updated learning config {key}: {old_value} -> {value}")
                else:
                    logger.warning(f"Unknown learning config key: {key}")

            return True

        except Exception as e:
            logger.error(f"Failed to update learning config: {e}")
            return False

    def reset_expert_learning(self, expert_id: str) -> bool:
        """Reset all learning states for an expert"""
        try:
            if expert_id in self.beta_states:
                del self.beta_states[expert_id]

            if expert_id in self.ema_states:
                del self.ema_states[expert_id]

            if expert_id in self.factor_states:
                del self.factor_states[expert_id]

            # Remove learning updates for this expert
            self.learning_updates = [u for u in self.learning_updates if u.expert_id != expert_id]
            self.learning_sessions = [s for s in self.learning_sessions if s.expert_id != expert_id]

            logger.info(f"Reset learning states for expert {expert_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset learning for {expert_id}: {e}")
            return False

    def clear_all_data(self) -> None:
        """Clear all learning data (for testing)"""
        self.beta_states.clear()
        self.ema_states.clear()
        self.factor_states.clear()
        self.learning_updates.clear()
        self.learning_sessions.clear()
        self.update_times.clear()
        self.update_counts = {'beta': 0, 'ema': 0, 'factor': 0, 'failed': 0}
