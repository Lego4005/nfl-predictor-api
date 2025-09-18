"""
Learning Coordinator for NFL Prediction System

Tracks all prediction outcomes, updates expert weights based on accuracy,
triggers belief revisions for poor predictions, and manages episodic memory updates.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set
import logging
import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque

# Import our existing services
try:
    from .belief_revision_service import BeliefRevisionService
    from .episodic_memory_manager import EpisodicMemoryManager
    from .expert_memory_service import ExpertMemoryService
    from .continuous_learner import ContinuousLearner
except ImportError:
    # Handle imports during testing
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningEvent(Enum):
    """Types of learning events"""
    PREDICTION_OUTCOME = "prediction_outcome"
    BELIEF_REVISION = "belief_revision"
    EXPERT_WEIGHT_UPDATE = "expert_weight_update"
    MEMORY_UPDATE = "memory_update"
    DRIFT_DETECTION = "drift_detection"
    RETRAINING_TRIGGER = "retraining_trigger"

@dataclass
class ExpertPerformance:
    """Track expert performance over time"""
    expert_id: str
    total_predictions: int
    correct_predictions: int
    accuracy: float
    confidence_weighted_accuracy: float
    recent_accuracy: float  # Last 10 predictions
    trend: str  # 'improving', 'declining', 'stable'
    specialty_areas: List[str]
    last_updated: datetime
    weight: float
    confidence_score: float

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data

@dataclass
class PredictionOutcome:
    """Record of a prediction and its outcome"""
    prediction_id: str
    expert_id: str
    game_id: str
    prediction_type: str  # 'spread', 'total', 'moneyline'
    predicted_value: float
    confidence: float
    actual_value: float
    was_correct: bool
    error_magnitude: float
    timestamp: datetime
    context: Dict[str, Any]

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class BeliefRevisionRecord:
    """Record of belief revision events"""
    revision_id: str
    expert_id: str
    trigger_reason: str
    old_beliefs: Dict[str, Any]
    new_beliefs: Dict[str, Any]
    confidence_change: float
    timestamp: datetime
    performance_impact: Optional[float] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class LearningCoordinator:
    """Coordinates all learning activities across the prediction system"""

    def __init__(self, db_path: str = "data/learning_coordination.db"):
        self.db_path = db_path
        self.expert_performances = {}
        self.prediction_history = deque(maxlen=1000)  # Keep last 1000 predictions
        self.learning_events = deque(maxlen=500)
        self.belief_revisions = []
        self.weight_update_threshold = 0.1  # Trigger weight updates when accuracy changes by 10%
        self.revision_threshold = 0.3  # Trigger belief revision when accuracy drops below 70%
        self.memory_update_frequency = 5  # Update memory every 5 predictions

        # Initialize services
        self.belief_service = None
        self.memory_manager = None
        self.expert_memory = None
        self.continuous_learner = None

        self._init_database()
        self._init_services()

    def _init_database(self):
        """Initialize database for learning coordination"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Expert performance tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expert_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expert_id TEXT,
                    timestamp TEXT,
                    total_predictions INTEGER,
                    correct_predictions INTEGER,
                    accuracy REAL,
                    confidence_weighted_accuracy REAL,
                    recent_accuracy REAL,
                    trend TEXT,
                    weight REAL,
                    confidence_score REAL,
                    specialty_areas TEXT
                )
            """)

            # Prediction outcomes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prediction_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id TEXT UNIQUE,
                    expert_id TEXT,
                    game_id TEXT,
                    prediction_type TEXT,
                    predicted_value REAL,
                    confidence REAL,
                    actual_value REAL,
                    was_correct BOOLEAN,
                    error_magnitude REAL,
                    timestamp TEXT,
                    context TEXT
                )
            """)

            # Learning events
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    expert_id TEXT,
                    timestamp TEXT,
                    details TEXT,
                    impact_score REAL
                )
            """)

            # Belief revisions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS belief_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    revision_id TEXT UNIQUE,
                    expert_id TEXT,
                    trigger_reason TEXT,
                    old_beliefs TEXT,
                    new_beliefs TEXT,
                    confidence_change REAL,
                    timestamp TEXT,
                    performance_impact REAL
                )
            """)

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expert_performance_expert_id ON expert_performance(expert_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prediction_outcomes_expert_id ON prediction_outcomes(expert_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prediction_outcomes_game_id ON prediction_outcomes(game_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_learning_events_expert_id ON learning_events(expert_id)")

    def _init_services(self):
        """Initialize learning services"""
        try:
            self.belief_service = BeliefRevisionService()
            self.memory_manager = EpisodicMemoryManager()
            self.expert_memory = ExpertMemoryService()
            self.continuous_learner = ContinuousLearner()
            logger.info("Successfully initialized learning services")
        except Exception as e:
            logger.warning(f"Could not initialize all services: {e}")
            # Initialize mock services for testing
            self.belief_service = MockBeliefRevisionService()
            self.memory_manager = MockEpisodicMemoryManager()
            self.expert_memory = MockExpertMemoryService()
            self.continuous_learner = MockContinuousLearner()

    def register_expert(self, expert_id: str, initial_weight: float = 1.0,
                       specialty_areas: List[str] = None):
        """Register a new expert for tracking"""
        specialty_areas = specialty_areas or []

        performance = ExpertPerformance(
            expert_id=expert_id,
            total_predictions=0,
            correct_predictions=0,
            accuracy=0.5,  # Start with neutral accuracy
            confidence_weighted_accuracy=0.5,
            recent_accuracy=0.5,
            trend='stable',
            specialty_areas=specialty_areas,
            last_updated=datetime.now(),
            weight=initial_weight,
            confidence_score=0.5
        )

        self.expert_performances[expert_id] = performance

        # Store in database
        self._store_expert_performance(performance)

        logger.info(f"Registered expert {expert_id} with initial weight {initial_weight}")

    def record_prediction_outcome(self, prediction_id: str, expert_id: str,
                                game_id: str, prediction_type: str,
                                predicted_value: float, confidence: float,
                                actual_value: float, context: Dict[str, Any] = None):
        """Record the outcome of a prediction and trigger learning"""
        context = context or {}

        # Determine if prediction was correct
        was_correct = self._evaluate_prediction_correctness(
            prediction_type, predicted_value, actual_value
        )

        # Calculate error magnitude
        error_magnitude = abs(predicted_value - actual_value)

        # Create outcome record
        outcome = PredictionOutcome(
            prediction_id=prediction_id,
            expert_id=expert_id,
            game_id=game_id,
            prediction_type=prediction_type,
            predicted_value=predicted_value,
            confidence=confidence,
            actual_value=actual_value,
            was_correct=was_correct,
            error_magnitude=error_magnitude,
            timestamp=datetime.now(),
            context=context
        )

        # Store outcome
        self.prediction_history.append(outcome)
        self._store_prediction_outcome(outcome)

        # Trigger learning processes
        self._process_prediction_outcome(outcome)

        logger.info(f"Recorded prediction outcome for {expert_id}: "
                   f"{'Correct' if was_correct else 'Incorrect'} "
                   f"(error: {error_magnitude:.3f})")

    def _evaluate_prediction_correctness(self, prediction_type: str,
                                       predicted: float, actual: float) -> bool:
        """Evaluate if a prediction was correct based on type"""
        if prediction_type == 'moneyline':
            # For moneyline, check if prediction and actual have same sign
            return (predicted > 0.5) == (actual > 0.5)
        elif prediction_type in ['spread', 'total']:
            # For spread and total, use a tolerance
            tolerance = 3.0 if prediction_type == 'spread' else 7.0
            return abs(predicted - actual) <= tolerance
        else:
            # Generic binary classification
            return (predicted > 0.5) == (actual > 0.5)

    def _process_prediction_outcome(self, outcome: PredictionOutcome):
        """Process prediction outcome and trigger appropriate learning actions"""
        expert_id = outcome.expert_id

        # Update expert performance
        self._update_expert_performance(outcome)

        # Check if weight update is needed
        if self._should_update_weights(expert_id):
            self._update_expert_weights(expert_id)

        # Check if belief revision is needed
        if self._should_trigger_belief_revision(expert_id):
            self._trigger_belief_revision(expert_id, outcome)

        # Update episodic memory
        if len(self.prediction_history) % self.memory_update_frequency == 0:
            self._update_episodic_memory(outcome)

        # Log learning event
        self._log_learning_event(
            LearningEvent.PREDICTION_OUTCOME,
            expert_id,
            {"outcome": outcome.to_dict()}
        )

    def _update_expert_performance(self, outcome: PredictionOutcome):
        """Update expert performance metrics"""
        expert_id = outcome.expert_id

        if expert_id not in self.expert_performances:
            self.register_expert(expert_id)

        performance = self.expert_performances[expert_id]

        # Update totals
        performance.total_predictions += 1
        if outcome.was_correct:
            performance.correct_predictions += 1

        # Update accuracy
        performance.accuracy = performance.correct_predictions / performance.total_predictions

        # Update confidence-weighted accuracy
        if outcome.confidence > 0:
            weight = outcome.confidence
            weighted_correct = 1.0 if outcome.was_correct else 0.0
            # Running average with confidence weighting
            old_weighted_acc = performance.confidence_weighted_accuracy
            performance.confidence_weighted_accuracy = (
                old_weighted_acc * 0.9 + weighted_correct * weight * 0.1
            )

        # Update recent accuracy (last 10 predictions)
        recent_outcomes = [
            p for p in self.prediction_history
            if p.expert_id == expert_id
        ][-10:]

        if len(recent_outcomes) > 0:
            recent_correct = sum(1 for p in recent_outcomes if p.was_correct)
            performance.recent_accuracy = recent_correct / len(recent_outcomes)

            # Determine trend
            if len(recent_outcomes) >= 5:
                first_half = recent_outcomes[:len(recent_outcomes)//2]
                second_half = recent_outcomes[len(recent_outcomes)//2:]

                first_acc = sum(1 for p in first_half if p.was_correct) / len(first_half)
                second_acc = sum(1 for p in second_half if p.was_correct) / len(second_half)

                if second_acc > first_acc + 0.1:
                    performance.trend = 'improving'
                elif second_acc < first_acc - 0.1:
                    performance.trend = 'declining'
                else:
                    performance.trend = 'stable'

        # Update confidence score based on recent performance
        performance.confidence_score = min(1.0, performance.recent_accuracy * 1.2)

        # Update timestamp
        performance.last_updated = datetime.now()

        # Store updated performance
        self._store_expert_performance(performance)

    def _should_update_weights(self, expert_id: str) -> bool:
        """Check if expert weights should be updated"""
        if expert_id not in self.expert_performances:
            return False

        performance = self.expert_performances[expert_id]

        # Update if significant change in accuracy or after certain number of predictions
        accuracy_change = abs(performance.accuracy - 0.5)  # Compared to neutral
        prediction_count = performance.total_predictions

        return (
            accuracy_change >= self.weight_update_threshold or
            prediction_count % 10 == 0  # Update every 10 predictions
        )

    def _update_expert_weights(self, expert_id: str):
        """Update expert weights based on performance"""
        if expert_id not in self.expert_performances:
            return

        performance = self.expert_performances[expert_id]

        # Calculate new weight based on multiple factors
        accuracy_factor = performance.accuracy
        confidence_factor = performance.confidence_weighted_accuracy
        recency_factor = performance.recent_accuracy
        trend_factor = {'improving': 1.1, 'stable': 1.0, 'declining': 0.9}[performance.trend]

        # Combine factors
        new_weight = (
            accuracy_factor * 0.4 +
            confidence_factor * 0.3 +
            recency_factor * 0.2 +
            trend_factor * 0.1
        )

        # Apply bounds
        new_weight = max(0.1, min(2.0, new_weight))

        old_weight = performance.weight
        performance.weight = new_weight

        # Log weight update
        self._log_learning_event(
            LearningEvent.EXPERT_WEIGHT_UPDATE,
            expert_id,
            {
                "old_weight": old_weight,
                "new_weight": new_weight,
                "accuracy": performance.accuracy,
                "trend": performance.trend
            },
            impact_score=abs(new_weight - old_weight)
        )

        logger.info(f"Updated weight for {expert_id}: {old_weight:.3f} -> {new_weight:.3f}")

    def _should_trigger_belief_revision(self, expert_id: str) -> bool:
        """Check if belief revision should be triggered"""
        if expert_id not in self.expert_performances:
            return False

        performance = self.expert_performances[expert_id]

        # Trigger if recent accuracy drops significantly
        return (
            performance.recent_accuracy < self.revision_threshold and
            performance.total_predictions >= 5 and
            performance.trend == 'declining'
        )

    def _trigger_belief_revision(self, expert_id: str, trigger_outcome: PredictionOutcome):
        """Trigger belief revision for an expert"""
        try:
            if not self.belief_service:
                logger.warning("Belief revision service not available")
                return

            performance = self.expert_performances[expert_id]

            # Get recent poor predictions as evidence
            recent_outcomes = [
                p for p in self.prediction_history
                if p.expert_id == expert_id and not p.was_correct
            ][-5:]  # Last 5 incorrect predictions

            # Create revision context
            revision_context = {
                'expert_id': expert_id,
                'trigger_outcome': trigger_outcome.to_dict(),
                'recent_performance': performance.to_dict(),
                'evidence': [outcome.to_dict() for outcome in recent_outcomes]
            }

            # Get old beliefs
            old_beliefs = self.expert_memory.get_expert_beliefs(expert_id) if self.expert_memory else {}

            # Perform belief revision
            revision_result = self.belief_service.revise_beliefs(revision_context)

            if revision_result:
                # Create revision record
                revision = BeliefRevisionRecord(
                    revision_id=f"rev_{expert_id}_{int(datetime.now().timestamp())}",
                    expert_id=expert_id,
                    trigger_reason="poor_performance",
                    old_beliefs=old_beliefs,
                    new_beliefs=revision_result.get('new_beliefs', {}),
                    confidence_change=revision_result.get('confidence_change', 0.0),
                    timestamp=datetime.now()
                )

                self.belief_revisions.append(revision)
                self._store_belief_revision(revision)

                # Update expert memory with new beliefs
                if self.expert_memory:
                    self.expert_memory.update_expert_beliefs(expert_id, revision.new_beliefs)

                # Log revision event
                self._log_learning_event(
                    LearningEvent.BELIEF_REVISION,
                    expert_id,
                    revision.to_dict(),
                    impact_score=abs(revision.confidence_change)
                )

                logger.info(f"Triggered belief revision for {expert_id}")

        except Exception as e:
            logger.error(f"Error triggering belief revision: {e}")

    def _update_episodic_memory(self, outcome: PredictionOutcome):
        """Update episodic memory with new outcome"""
        try:
            if not self.memory_manager:
                return

            # Create memory episode
            episode = {
                'type': 'prediction_outcome',
                'expert_id': outcome.expert_id,
                'game_id': outcome.game_id,
                'prediction_type': outcome.prediction_type,
                'was_correct': outcome.was_correct,
                'error_magnitude': outcome.error_magnitude,
                'confidence': outcome.confidence,
                'context': outcome.context,
                'timestamp': outcome.timestamp
            }

            # Store episode
            self.memory_manager.store_episode(episode)

            # Log memory update
            self._log_learning_event(
                LearningEvent.MEMORY_UPDATE,
                outcome.expert_id,
                {"episode": episode}
            )

        except Exception as e:
            logger.error(f"Error updating episodic memory: {e}")

    def _log_learning_event(self, event_type: LearningEvent, expert_id: str,
                          details: Dict[str, Any], impact_score: float = 0.0):
        """Log learning events for analysis"""
        event = {
            'event_type': event_type.value,
            'expert_id': expert_id,
            'timestamp': datetime.now(),
            'details': details,
            'impact_score': impact_score
        }

        self.learning_events.append(event)

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO learning_events (event_type, expert_id, timestamp, details, impact_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_type.value,
                expert_id,
                event['timestamp'].isoformat(),
                json.dumps(details, default=str),
                impact_score
            ))

    def _store_expert_performance(self, performance: ExpertPerformance):
        """Store expert performance in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO expert_performance
                (expert_id, timestamp, total_predictions, correct_predictions, accuracy,
                 confidence_weighted_accuracy, recent_accuracy, trend, weight,
                 confidence_score, specialty_areas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                performance.expert_id,
                performance.last_updated.isoformat(),
                performance.total_predictions,
                performance.correct_predictions,
                performance.accuracy,
                performance.confidence_weighted_accuracy,
                performance.recent_accuracy,
                performance.trend,
                performance.weight,
                performance.confidence_score,
                json.dumps(performance.specialty_areas)
            ))

    def _store_prediction_outcome(self, outcome: PredictionOutcome):
        """Store prediction outcome in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO prediction_outcomes
                (prediction_id, expert_id, game_id, prediction_type, predicted_value,
                 confidence, actual_value, was_correct, error_magnitude, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome.prediction_id,
                outcome.expert_id,
                outcome.game_id,
                outcome.prediction_type,
                outcome.predicted_value,
                outcome.confidence,
                outcome.actual_value,
                outcome.was_correct,
                outcome.error_magnitude,
                outcome.timestamp.isoformat(),
                json.dumps(outcome.context, default=str)
            ))

    def _store_belief_revision(self, revision: BeliefRevisionRecord):
        """Store belief revision in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO belief_revisions
                (revision_id, expert_id, trigger_reason, old_beliefs, new_beliefs,
                 confidence_change, timestamp, performance_impact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                revision.revision_id,
                revision.expert_id,
                revision.trigger_reason,
                json.dumps(revision.old_beliefs, default=str),
                json.dumps(revision.new_beliefs, default=str),
                revision.confidence_change,
                revision.timestamp.isoformat(),
                revision.performance_impact
            ))

    # Analysis and reporting methods

    def get_expert_performance(self, expert_id: Optional[str] = None) -> Dict[str, ExpertPerformance]:
        """Get current expert performance metrics"""
        if expert_id:
            return {expert_id: self.expert_performances.get(expert_id)}
        return self.expert_performances.copy()

    def get_learning_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get learning activity summary"""
        cutoff = datetime.now() - timedelta(days=days)

        recent_events = [
            e for e in self.learning_events
            if e['timestamp'] >= cutoff
        ]

        recent_outcomes = [
            o for o in self.prediction_history
            if o.timestamp >= cutoff
        ]

        event_counts = defaultdict(int)
        for event in recent_events:
            event_counts[event['event_type']] += 1

        accuracy_by_expert = {}
        for outcome in recent_outcomes:
            expert_id = outcome.expert_id
            if expert_id not in accuracy_by_expert:
                accuracy_by_expert[expert_id] = {'correct': 0, 'total': 0}

            accuracy_by_expert[expert_id]['total'] += 1
            if outcome.was_correct:
                accuracy_by_expert[expert_id]['correct'] += 1

        # Calculate accuracies
        for expert_id in accuracy_by_expert:
            total = accuracy_by_expert[expert_id]['total']
            correct = accuracy_by_expert[expert_id]['correct']
            accuracy_by_expert[expert_id]['accuracy'] = correct / total if total > 0 else 0.0

        return {
            'period_days': days,
            'total_events': len(recent_events),
            'event_breakdown': dict(event_counts),
            'total_predictions': len(recent_outcomes),
            'expert_accuracies': accuracy_by_expert,
            'active_experts': len(self.expert_performances),
            'belief_revisions': len([r for r in self.belief_revisions if r.timestamp >= cutoff])
        }

    def get_top_performing_experts(self, n: int = 10, metric: str = 'accuracy') -> List[Tuple[str, float]]:
        """Get top performing experts by specified metric"""
        performances = list(self.expert_performances.values())

        if metric == 'accuracy':
            performances.sort(key=lambda p: p.accuracy, reverse=True)
        elif metric == 'confidence_weighted_accuracy':
            performances.sort(key=lambda p: p.confidence_weighted_accuracy, reverse=True)
        elif metric == 'recent_accuracy':
            performances.sort(key=lambda p: p.recent_accuracy, reverse=True)
        elif metric == 'weight':
            performances.sort(key=lambda p: p.weight, reverse=True)

        return [(p.expert_id, getattr(p, metric)) for p in performances[:n]]

    def trigger_system_retraining(self, reason: str = "scheduled"):
        """Trigger system-wide retraining"""
        try:
            # Create retraining flag
            flag_path = Path("data/retrain_flags/system_retrain.flag")
            flag_path.parent.mkdir(parents=True, exist_ok=True)

            with open(flag_path, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'reason': reason,
                    'expert_performances': {
                        eid: perf.to_dict() for eid, perf in self.expert_performances.items()
                    }
                }, f, indent=2)

            # Log retraining trigger
            self._log_learning_event(
                LearningEvent.RETRAINING_TRIGGER,
                'system',
                {'reason': reason},
                impact_score=1.0
            )

            logger.info(f"Triggered system retraining: {reason}")

        except Exception as e:
            logger.error(f"Error triggering system retraining: {e}")

    def export_learning_data(self, filepath: str):
        """Export learning data for analysis"""
        try:
            export_data = {
                'expert_performances': {
                    eid: perf.to_dict() for eid, perf in self.expert_performances.items()
                },
                'prediction_history': [outcome.to_dict() for outcome in self.prediction_history],
                'learning_events': list(self.learning_events),
                'belief_revisions': [rev.to_dict() for rev in self.belief_revisions],
                'export_timestamp': datetime.now().isoformat()
            }

            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"Exported learning data to {filepath}")

        except Exception as e:
            logger.error(f"Error exporting learning data: {e}")

# Mock services for testing
class MockBeliefRevisionService:
    def revise_beliefs(self, context):
        return {'new_beliefs': {'mock': True}, 'confidence_change': 0.1}

class MockEpisodicMemoryManager:
    def store_episode(self, episode):
        pass

class MockExpertMemoryService:
    def get_expert_beliefs(self, expert_id):
        return {'mock_belief': True}

    def update_expert_beliefs(self, expert_id, beliefs):
        pass

class MockContinuousLearner:
    pass

# Example usage
if __name__ == "__main__":
    # Initialize learning coordinator
    coordinator = LearningCoordinator()

    # Register some experts
    coordinator.register_expert("momentum_expert", 1.0, ["spread", "momentum"])
    coordinator.register_expert("weather_expert", 0.8, ["total", "weather"])

    # Simulate prediction outcomes
    coordinator.record_prediction_outcome(
        prediction_id="pred_1",
        expert_id="momentum_expert",
        game_id="game_123",
        prediction_type="spread",
        predicted_value=0.7,
        confidence=0.8,
        actual_value=1.0
    )

    # Get performance summary
    summary = coordinator.get_learning_summary()
    print(f"Learning summary: {summary}")

    # Get top experts
    top_experts = coordinator.get_top_performing_experts()
    print(f"Top experts: {top_experts}")