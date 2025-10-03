#!/usr/bin/env python3
"""
Prediction Validation Framework

Tracks prediction accuracy across different game types, validates reasoning
chain quality, and ensures episodic memories are being used effectively.

Requirements: 2.3, 6.3, 6.4
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Result of a single prediction"""
    game_id: str
    expert_id: str
    expert_name: str

    # Game context
    home_team: str
    away_team: str
    season: int
    week: int
    game_type: str  # 'regular', 'playoff', 'division', 'conference'

    # Predictions
    predicted_winner: str
    predicted_confidence: float
    predicted_spread: float
    predicted_total: float

    # Actual outcomes
    actual_winner: Optional[str] = None
    actual_spread: Optional[float] = None
    actual_total: Optional[float] = None

    # Accuracy metrics
    winner_correct: Optional[bool] = None
    spread_error: Optional[float] = None
    total_error: Optional[float] = None

    # Reasoning quality
    reasoning_length: int = 0
    reasoning_quality_score: float = 0.0
    memory_usage_count: int = 0
    memory_applied: bool = False

    # Metadata
    prediction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    outcome_timestamp: Optional[str] = None


@dataclass
class AccuracyMetrics:
    """Accuracy metrics for a set of predictions"""
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy_rate: float = 0.0

    # Spread accuracy
    average_spread_error: float = 0.0
    median_spread_error: float = 0.0

    # Total accuracy
    average_total_error: float = 0.0
    median_total_error: float = 0.0

    # Confidence calibration
    average_confidence: float = 0.0
    confidence_when_correct: float = 0.0
    confidence_when_wrong: float = 0.0

    # Memory usage
    predictions_with_memory: int = 0
    memory_usage_rate: float = 0.0
    accuracy_with_memory: float = 0.0
    accuracy_without_memory: float = 0.0


class PredictionValidationFramework:
    """
    Framework for validating predictions and tracking accuracy

    Tracks:
    - Prediction accuracy across different game types
    - Reasoning chain quality and consistency
    - Episodic memory usage and effectiveness
    - Confidence calibration
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Storage for predictions
        self.predictions: List[PredictionResult] = []
        self.predictions_by_expert: Dict[str, List[PredictionResult]] = {}
        self.predictions_by_game_type: Dict[str, List[PredictionResult]] = {}

        # Validation statistics
        self.validation_stats = {
            'total_predictions': 0,
            'predictions_validated': 0,
            'reasoning_quality_checks': 0,
            'memory_usage_checks': 0
        }

        self.logger.info("🎯 Prediction Validation Framework initialized")

    def record_prediction(
        self,
        game_id: str,
        expert_id: str,
        expert_name: str,
        prediction_data: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> PredictionResult:
        """Record a prediction for later validation"""

        # Extract game type
        game_type = self._determine_game_type(game_context)

        # Create prediction result
        result = PredictionResult(
            game_id=game_id,
            expert_id=expert_id,
            expert_name=expert_name,
            home_team=game_context.get('home_team', 'Unknown'),
            away_team=game_context.get('away_team', 'Unknown'),
            season=game_context.get('season', 0),
            week=game_context.get('week', 0),
            game_type=game_type,
            predicted_winner=prediction_data.get('winner_prediction', 'home'),
            predicted_confidence=prediction_data.get('winner_confidence', 0.5),
            predicted_spread=prediction_data.get('spread_prediction', 0.0),
            predicted_total=prediction_data.get('total_prediction', 45.0),
            reasoning_length=len(prediction_data.get('reasoning', '')),
            memory_usage_count=prediction_data.get('memories_consulted', 0),
            memory_applied=prediction_data.get('memory_enhanced', False)
        )

        # Validate reasoning quality
        result.reasoning_quality_score = self._assess_reasoning_quality(prediction_data)

        # Store prediction
        self.predictions.append(result)

        # Index by expert
        if expert_id not in self.predictions_by_expert:
            self.predictions_by_expert[expert_id] = []
        self.predictions_by_expert[expert_id].append(result)

        # Index by game type
        if game_type not in self.predictions_by_game_type:
            self.predictions_by_game_type[game_type] = []
        self.predictions_by_game_type[game_type].append(result)

        self.validation_stats['total_predictions'] += 1

        self.logger.info(f"📝 Recorded prediction for {expert_name}: {result.away_team} @ {result.home_team}")
        self.logger.debug(f"   Winner: {result.predicted_winner}, Confidence: {result.predicted_confidence:.1%}")

        return result

    def validate_prediction(
        self,
        game_id: str,
        actual_outcome: Dict[str, Any]
    ) -> Optional[PredictionResult]:
        """Validate a prediction against actual outcome"""

        # Find prediction
        prediction = None
        for pred in self.predictions:
            if pred.game_id == game_id and pred.actual_winner is None:
                prediction = pred
                break

        if not prediction:
            self.logger.warning(f"⚠️  No unvalidated prediction found for game {game_id}")
            return None

        # Extract actual outcomes
        prediction.actual_winner = actual_outcome.get('winner', 'unknown')
        prediction.actual_spread = actual_outcome.get('spread', 0.0)
        prediction.actual_total = actual_outcome.get('total_points', 0.0)
        prediction.outcome_timestamp = datetime.now().isoformat()

        # Calculate accuracy
        prediction.winner_correct = (
            prediction.predicted_winner.lower() == prediction.actual_winner.lower()
        )

        if prediction.actual_spread is not None:
            prediction.spread_error = abs(prediction.predicted_spread - prediction.actual_spread)

        if prediction.actual_total is not None:
            prediction.total_error = abs(prediction.predicted_total - prediction.actual_total)

        self.validation_stats['predictions_validated'] += 1

        result_emoji = "✅" if prediction.winner_correct else "❌"
        self.logger.info(f"{result_emoji} Validated prediction for {prediction.expert_name}")
        self.logger.info(f"   Game: {prediction.away_team} @ {prediction.home_team}")
        self.logger.info(f"   Predicted: {prediction.predicted_winner} (conf: {prediction.predicted_confidence:.1%})")
        self.logger.info(f"   Actual: {prediction.actual_winner}")

        if prediction.spread_error is not None:
            self.logger.info(f"   Spread error: {prediction.spread_error:.1f} points")
        if prediction.total_error is not None:
            self.logger.info(f"   Total error: {prediction.total_error:.1f} points")

        return prediction

    def get_accuracy_metrics(
        self,
        expert_id: Optional[str] = None,
        game_type: Optional[str] = None
    ) -> AccuracyMetrics:
        """Calculate accuracy metrics for predictions"""

        # Filter predictions
        predictions = self.predictions
        if expert_id:
            predictions = self.predictions_by_expert.get(expert_id, [])
        if game_type:
            predictions = [p for p in predictions if p.game_type == game_type]

        # Filter to validated predictions only
        validated = [p for p in predictions if p.actual_winner is not None]

        if not validated:
            return AccuracyMetrics()

        # Calculate metrics
        metrics = AccuracyMetrics()
        metrics.total_predictions = len(validated)
        metrics.correct_predictions = sum(1 for p in validated if p.winner_correct)
        metrics.accuracy_rate = metrics.correct_predictions / metrics.total_predictions

        # Spread accuracy
        spread_errors = [p.spread_error for p in validated if p.spread_error is not None]
        if spread_errors:
            metrics.average_spread_error = sum(spread_errors) / len(spread_errors)
            metrics.median_spread_error = sorted(spread_errors)[len(spread_errors) // 2]

        # Total accuracy
        total_errors = [p.total_error for p in validated if p.total_error is not None]
        if total_errors:
            metrics.average_total_error = sum(total_errors) / len(total_errors)
            metrics.median_total_error = sorted(total_errors)[len(total_errors) // 2]

        # Confidence calibration
        metrics.average_confidence = sum(p.predicted_confidence for p in validated) / len(validated)

        correct_preds = [p for p in validated if p.winner_correct]
        if correct_preds:
            metrics.confidence_when_correct = sum(p.predicted_confidence for p in correct_preds) / len(correct_preds)

        wrong_preds = [p for p in validated if not p.winner_correct]
        if wrong_preds:
            metrics.confidence_when_wrong = sum(p.predicted_confidence for p in wrong_preds) / len(wrong_preds)

        # Memory usage
        with_memory = [p for p in validated if p.memory_applied]
        metrics.predictions_with_memory = len(with_memory)
        metrics.memory_usage_rate = len(with_memory) / len(validated)

        if with_memory:
            metrics.accuracy_with_memory = sum(1 for p in with_memory if p.winner_correct) / len(with_memory)

        without_memory = [p for p in validated if not p.memory_applied]
        if without_memory:
            metrics.accuracy_without_memory = sum(1 for p in without_memory if p.winner_correct) / len(without_memory)

        return metrics

    def validate_reasoning_quality(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the quality and consistency of reasoning chains"""

        self.validation_stats['reasoning_quality_checks'] += 1

        validation_result = {
            'has_reasoning': False,
            'reasoning_length': 0,
            'quality_score': 0.0,
            'issues': []
        }

        reasoning = prediction_data.get('reasoning', '') or prediction_data.get('reasoning_discussion', '')

        if not reasoning:
            validation_result['issues'].append("No reasoning provided")
            return validation_result

        validation_result['has_reasoning'] = True
        validation_result['reasoning_length'] = len(reasoning)

        # Check reasoning quality
        quality_score = 0.0

        # Length check (should be substantial)
        if len(reasoning) > 100:
            quality_score += 0.2
        if len(reasoning) > 300:
            quality_score += 0.2

        # Content checks
        reasoning_lower = reasoning.lower()

        # Check for analytical terms
        analytical_terms = ['because', 'therefore', 'however', 'although', 'considering']
        if any(term in reasoning_lower for term in analytical_terms):
            quality_score += 0.2

        # Check for data references
        data_terms = ['statistics', 'data', 'numbers', 'percentage', 'average']
        if any(term in reasoning_lower for term in data_terms):
            quality_score += 0.2

        # Check for uncertainty acknowledgment
        uncertainty_terms = ['uncertain', 'unclear', 'difficult', 'challenging', 'may', 'might']
        if any(term in reasoning_lower for term in uncertainty_terms):
            quality_score += 0.2

        validation_result['quality_score'] = min(1.0, quality_score)

        if quality_score < 0.4:
            validation_result['issues'].append("Low quality reasoning (score < 0.4)")

        return validation_result

    def validate_memory_usage(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that episodic memories are being used effectively"""

        self.validation_stats['memory_usage_checks'] += 1

        validation_result = {
            'memory_enabled': False,
            'memories_consulted': 0,
            'memories_applied': False,
            'memory_impact': 0.0,
            'issues': []
        }

        # Check if memory system is enabled
        if prediction_data.get('memory_enhanced'):
            validation_result['memory_enabled'] = True
            validation_result['memories_consulted'] = prediction_data.get('memories_consulted', 0)
            validation_result['memories_applied'] = validation_result['memories_consulted'] > 0

            # Check memory impact
            confidence_adjustment = prediction_data.get('confidence_adjustment', 0.0)
            validation_result['memory_impact'] = abs(confidence_adjustment)

            if validation_result['memories_consulted'] == 0:
                validation_result['issues'].append("Memory enabled but no memories consulted")

            if validation_result['memory_impact'] < 0.01:
                validation_result['issues'].append("Memories consulted but minimal impact on prediction")
        else:
            validation_result['issues'].append("Memory system not enabled for this prediction")

        return validation_result

    def generate_validation_report(
        self,
        expert_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive validation report"""

        metrics = self.get_accuracy_metrics(expert_id=expert_id)

        # Get predictions for report
        predictions = self.predictions
        if expert_id:
            predictions = self.predictions_by_expert.get(expert_id, [])

        validated = [p for p in predictions if p.actual_winner is not None]

        report = {
            'summary': {
                'total_predictions': len(predictions),
                'validated_predictions': len(validated),
                'validation_rate': len(validated) / len(predictions) if predictions else 0.0
            },
            'accuracy': {
                'overall_accuracy': metrics.accuracy_rate,
                'correct_predictions': metrics.correct_predictions,
                'total_predictions': metrics.total_predictions,
                'average_spread_error': metrics.average_spread_error,
                'average_total_error': metrics.average_total_error
            },
            'confidence_calibration': {
                'average_confidence': metrics.average_confidence,
                'confidence_when_correct': metrics.confidence_when_correct,
                'confidence_when_wrong': metrics.confidence_when_wrong,
                'calibration_gap': abs(metrics.confidence_when_correct - metrics.accuracy_rate)
            },
            'memory_usage': {
                'predictions_with_memory': metrics.predictions_with_memory,
                'memory_usage_rate': metrics.memory_usage_rate,
                'accuracy_with_memory': metrics.accuracy_with_memory,
                'accuracy_without_memory': metrics.accuracy_without_memory,
                'memory_effectiveness': metrics.accuracy_with_memory - metrics.accuracy_without_memory
            },
            'reasoning_quality': {
                'average_reasoning_length': sum(p.reasoning_length for p in predictions) / len(predictions) if predictions else 0,
                'average_quality_score': sum(p.reasoning_quality_score for p in predictions) / len(predictions) if predictions else 0
            },
            'game_type_breakdown': self._generate_game_type_breakdown(),
            'validation_stats': self.validation_stats
        }

        return report

    def _determine_game_type(self, game_context: Dict[str, Any]) -> str:
        """Determine the type of game"""
        week = game_context.get('week', 0)

        if week > 18:
            return 'playoff'
        elif game_context.get('is_division_game'):
            return 'division'
        elif game_context.get('is_conference_game'):
            return 'conference'
        else:
            return 'regular'

    def _assess_reasoning_quality(self, prediction_data: Dict[str, Any]) -> float:
        """Assess the quality of reasoning provided"""
        validation = self.validate_reasoning_quality(prediction_data)
        return validation['quality_score']

    def _generate_game_type_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Generate accuracy breakdown by game type"""
        breakdown = {}

        for game_type in self.predictions_by_game_type.keys():
            metrics = self.get_accuracy_metrics(game_type=game_type)
            breakdown[game_type] = {
                'total_predictions': metrics.total_predictions,
      'accuracy_rate': metrics.accuracy_rate,
                'average_spread_error': metrics.average_spread_error,
                'average_total_error': metrics.average_total_error
            }

        return breakdown

    def print_validation_report(self, expert_id: Optional[str] = None):
        """Print a formatted validation report"""
        report = self.generate_validation_report(expert_id=expert_id)

        print("\n" + "=" * 80)
        print("📊 PREDICTION VALIDATION REPORT")
        print("=" * 80)

        print(f"\n📈 Summary:")
        print(f"   Total Predictions: {report['summary']['total_predictions']}")
        print(f"   Validated: {report['summary']['validated_predictions']}")
        print(f"   Validation Rate: {report['summary']['validation_rate']:.1%}")

        print(f"\n🎯 Accuracy:")
        print(f"   Overall Accuracy: {report['accuracy']['overall_accuracy']:.1%}")
        print(f"   Correct: {report['accuracy']['correct_predictions']}/{report['accuracy']['total_predictions']}")
        print(f"   Avg Spread Error: {report['accuracy']['average_spread_error']:.2f} points")
        print(f"   Avg Total Error: {report['accuracy']['average_total_error']:.2f} points")

        print(f"\n🎲 Confidence Calibration:")
        print(f"   Average Confidence: {report['confidence_calibration']['average_confidence']:.1%}")
        print(f"   Confidence When Correct: {report['confidence_calibration']['confidence_when_correct']:.1%}")
        print(f"   Confidence When Wrong: {report['confidence_calibration']['confidence_when_wrong']:.1%}")
        print(f"   Calibration Gap: {report['confidence_calibration']['calibration_gap']:.1%}")

        print(f"\n🧠 Memory Usage:")
        print(f"   Predictions with Memory: {report['memory_usage']['predictions_with_memory']}")
        print(f"   Memory Usage Rate: {report['memory_usage']['memory_usage_rate']:.1%}")
        print(f"   Accuracy with Memory: {report['memory_usage']['accuracy_with_memory']:.1%}")
        print(f"   Accuracy without Memory: {report['memory_usage']['accuracy_without_memory']:.1%}")
        print(f"   Memory Effectiveness: {report['memory_usage']['memory_effectiveness']:+.1%}")

        print(f"\n💭 Reasoning Quality:")
        print(f"   Avg Reasoning Length: {report['reasoning_quality']['average_reasoning_length']:.0f} chars")
        print(f"   Avg Quality Score: {report['reasoning_quality']['average_quality_score']:.2f}/1.0")

        if report['game_type_breakdown']:
            print(f"\n🏈 Game Type Breakdown:")
            for game_type, metrics in report['game_type_breakdown'].items():
                print(f"   {game_type.capitalize()}:")
                print(f"      Predictions: {metrics['total_predictions']}")
                print(f"      Accuracy: {metrics['accuracy_rate']:.1%}")

        print("\n" + "=" * 80)


# Global instance
_validation_framework = None

def get_validation_framework() -> PredictionValidationFramework:
    """Get global validation framework instance"""
    global _validation_framework
    if _validation_framework is None:
        _validation_framework = PredictionValidationFramework()
    return _validation_framework
