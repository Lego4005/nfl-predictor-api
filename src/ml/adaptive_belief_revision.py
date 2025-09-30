#!/usr/bin/env python3
"""
Adaptive Belief Revision System for Prediction Adaptation
Detects when experts should change their approach and triggers adaptive actions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
from supabase import Client

logger = logging.getLogger(__name__)


class RevisionTriggerType(Enum):
    """Types of triggers that cause belief revision"""
    CONSECUTIVE_INCORRECT = "consecutive_incorrect"  # 3+ wrong in a row
    CONFIDENCE_MISALIGNMENT = "confidence_misalignment"  # High confidence but wrong
    PATTERN_REPETITION = "pattern_repetition"  # Same mistake repeatedly
    PERFORMANCE_DECLINE = "performance_decline"  # Overall accuracy dropping
    CONTEXTUAL_SHIFT = "contextual_shift"  # Game context changed significantly


class RevisionAction(Enum):
    """Actions to take when revision is triggered"""
    ADJUST_CONFIDENCE_THRESHOLD = "adjust_confidence_threshold"
    CHANGE_FACTOR_WEIGHTS = "change_factor_weights"
    UPDATE_STRATEGY = "update_strategy"
    INCREASE_CAUTION = "increase_caution"
    BROADEN_ANALYSIS = "broaden_analysis"


@dataclass
class RevisionTrigger:
    """Details about what triggered the revision"""
    trigger_type: RevisionTriggerType
    severity: float  # 0-1, how severe the issue is
    evidence: Dict[str, Any]  # Supporting data
    timestamp: datetime
    expert_id: str
    description: str


@dataclass
class RevisionActionPlan:
    """Plan for adapting expert behavior"""
    action: RevisionAction
    parameters: Dict[str, Any]  # What to change and by how much
    rationale: str
    expected_impact: float  # 0-1, expected improvement
    priority: int  # 1-5, execution priority


@dataclass
class BeliefRevisionRecord:
    """Complete record of a belief revision event"""
    revision_id: str
    expert_id: str
    trigger: RevisionTrigger
    actions: List[RevisionActionPlan]
    pre_revision_state: Dict[str, Any]
    post_revision_state: Dict[str, Any]
    timestamp: datetime
    effectiveness_score: Optional[float] = None  # Measured after implementation


class BeliefRevisionService:
    """
    Service that monitors expert performance and triggers adaptive revisions
    when patterns indicate the need for strategy changes
    """

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.revision_thresholds = {
            'consecutive_incorrect_threshold': 3,
            'confidence_misalignment_threshold': 0.25,  # 25% gap
            'pattern_repetition_threshold': 3,
            'performance_decline_threshold': 0.15,  # 15% drop
        }

    async def initialize(self):
        """Initialize service"""
        logger.info("✅ Adaptive Belief Revision Service initialized")

    async def close(self):
        """Cleanup"""
        logger.info("✅ Adaptive Belief Revision Service closed")

    async def check_revision_triggers(
        self,
        expert_id: str,
        recent_predictions: List[Dict[str, Any]],
        window_size: int = 10
    ) -> List[RevisionTrigger]:
        """
        Check if any revision triggers are activated

        Args:
            expert_id: Expert to check
            recent_predictions: Recent prediction outcomes
            window_size: Number of recent predictions to analyze

        Returns:
            List of triggered revision conditions
        """
        triggers = []

        # Limit to most recent predictions
        predictions = recent_predictions[-window_size:] if len(recent_predictions) > window_size else recent_predictions

        if len(predictions) < 3:
            return triggers  # Need minimum data

        # Check for consecutive incorrect predictions
        consecutive_trigger = self._check_consecutive_incorrect(expert_id, predictions)
        if consecutive_trigger:
            triggers.append(consecutive_trigger)

        # Check for confidence misalignment
        misalignment_trigger = self._check_confidence_misalignment(expert_id, predictions)
        if misalignment_trigger:
            triggers.append(misalignment_trigger)

        # Check for pattern repetition
        pattern_trigger = self._check_pattern_repetition(expert_id, predictions)
        if pattern_trigger:
            triggers.append(pattern_trigger)

        # Check for performance decline
        decline_trigger = self._check_performance_decline(expert_id, predictions)
        if decline_trigger:
            triggers.append(decline_trigger)

        return triggers

    def _check_consecutive_incorrect(
        self,
        expert_id: str,
        predictions: List[Dict[str, Any]]
    ) -> Optional[RevisionTrigger]:
        """Check for consecutive incorrect predictions"""
        consecutive_count = 0
        max_consecutive = 0

        for pred in reversed(predictions):
            is_correct = pred.get('was_correct', False)
            if not is_correct:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 0

        threshold = self.revision_thresholds['consecutive_incorrect_threshold']

        if max_consecutive >= threshold:
            severity = min(1.0, (max_consecutive - threshold + 1) / 5.0)
            return RevisionTrigger(
                trigger_type=RevisionTriggerType.CONSECUTIVE_INCORRECT,
                severity=severity,
                evidence={
                    'consecutive_incorrect': max_consecutive,
                    'threshold': threshold,
                    'recent_predictions': predictions[-max_consecutive:]
                },
                timestamp=datetime.now(),
                expert_id=expert_id,
                description=f"Expert has {max_consecutive} consecutive incorrect predictions"
            )

        return None

    def _check_confidence_misalignment(
        self,
        expert_id: str,
        predictions: List[Dict[str, Any]]
    ) -> Optional[RevisionTrigger]:
        """Check for high confidence but incorrect predictions"""
        high_confidence_errors = []

        for pred in predictions:
            confidence = pred.get('confidence', 0.5)
            was_correct = pred.get('was_correct', False)

            if confidence >= 0.7 and not was_correct:
                gap = confidence - 0.5  # Gap from neutral
                high_confidence_errors.append({
                    'game_id': pred.get('game_id'),
                    'confidence': confidence,
                    'gap': gap
                })

        if len(high_confidence_errors) >= 2:
            avg_gap = sum(e['gap'] for e in high_confidence_errors) / len(high_confidence_errors)
            threshold = self.revision_thresholds['confidence_misalignment_threshold']

            if avg_gap >= threshold:
                severity = min(1.0, len(high_confidence_errors) / 5.0)
                return RevisionTrigger(
                    trigger_type=RevisionTriggerType.CONFIDENCE_MISALIGNMENT,
                    severity=severity,
                    evidence={
                        'high_confidence_errors': high_confidence_errors,
                        'error_count': len(high_confidence_errors),
                        'avg_confidence_gap': avg_gap
                    },
                    timestamp=datetime.now(),
                    expert_id=expert_id,
                    description=f"Expert shows confidence misalignment with {len(high_confidence_errors)} high-confidence errors"
                )

        return None

    def _check_pattern_repetition(
        self,
        expert_id: str,
        predictions: List[Dict[str, Any]]
    ) -> Optional[RevisionTrigger]:
        """Check for repeated mistakes with similar patterns"""
        error_patterns = {}

        for pred in predictions:
            if not pred.get('was_correct', False):
                # Categorize the error
                pattern_key = self._categorize_error(pred)
                if pattern_key not in error_patterns:
                    error_patterns[pattern_key] = []
                error_patterns[pattern_key].append(pred)

        # Find the most repeated pattern
        max_pattern = max(error_patterns.items(), key=lambda x: len(x[1]), default=(None, []))
        pattern_key, pattern_errors = max_pattern

        threshold = self.revision_thresholds['pattern_repetition_threshold']

        if pattern_key and len(pattern_errors) >= threshold:
            severity = min(1.0, len(pattern_errors) / 6.0)
            return RevisionTrigger(
                trigger_type=RevisionTriggerType.PATTERN_REPETITION,
                severity=severity,
                evidence={
                    'pattern_type': pattern_key,
                    'occurrences': len(pattern_errors),
                    'examples': pattern_errors[:3]
                },
                timestamp=datetime.now(),
                expert_id=expert_id,
                description=f"Expert repeating '{pattern_key}' mistake {len(pattern_errors)} times"
            )

        return None

    def _check_performance_decline(
        self,
        expert_id: str,
        predictions: List[Dict[str, Any]]
    ) -> Optional[RevisionTrigger]:
        """Check for overall performance decline"""
        if len(predictions) < 6:
            return None

        # Split into two halves
        mid = len(predictions) // 2
        first_half = predictions[:mid]
        second_half = predictions[mid:]

        # Calculate accuracy for each half
        first_accuracy = sum(1 for p in first_half if p.get('was_correct', False)) / len(first_half)
        second_accuracy = sum(1 for p in second_half if p.get('was_correct', False)) / len(second_half)

        decline = first_accuracy - second_accuracy
        threshold = self.revision_thresholds['performance_decline_threshold']

        if decline >= threshold:
            severity = min(1.0, decline / 0.3)
            return RevisionTrigger(
                trigger_type=RevisionTriggerType.PERFORMANCE_DECLINE,
                severity=severity,
                evidence={
                    'first_half_accuracy': first_accuracy,
                    'second_half_accuracy': second_accuracy,
                    'decline': decline,
                    'sample_size': len(predictions)
                },
                timestamp=datetime.now(),
                expert_id=expert_id,
                description=f"Performance declined by {decline:.1%} over recent predictions"
            )

        return None

    def _categorize_error(self, prediction: Dict[str, Any]) -> str:
        """Categorize type of prediction error for pattern detection"""
        # Look at prediction characteristics to categorize error
        confidence = prediction.get('confidence', 0.5)
        margin = prediction.get('predicted_margin', 0)
        actual_margin = prediction.get('actual_margin', 0)

        if confidence > 0.75:
            return "overconfident_error"
        elif abs(margin) > 10 and abs(actual_margin) > 10 and (margin * actual_margin < 0):
            return "direction_reversal_error"
        elif abs(margin - actual_margin) > 14:
            return "large_margin_error"
        elif 0.45 <= confidence <= 0.55:
            return "uncertain_prediction_error"
        else:
            return "general_error"

    async def generate_revision_actions(
        self,
        expert_id: str,
        triggers: List[RevisionTrigger],
        current_state: Dict[str, Any]
    ) -> List[RevisionActionPlan]:
        """
        Generate specific actions to take based on triggers

        Args:
            expert_id: Expert to adapt
            triggers: Activated triggers
            current_state: Current expert configuration

        Returns:
            List of recommended actions
        """
        actions = []

        for trigger in triggers:
            if trigger.trigger_type == RevisionTriggerType.CONSECUTIVE_INCORRECT:
                actions.append(self._action_for_consecutive_errors(trigger, current_state))

            elif trigger.trigger_type == RevisionTriggerType.CONFIDENCE_MISALIGNMENT:
                actions.append(self._action_for_confidence_misalignment(trigger, current_state))

            elif trigger.trigger_type == RevisionTriggerType.PATTERN_REPETITION:
                actions.append(self._action_for_pattern_repetition(trigger, current_state))

            elif trigger.trigger_type == RevisionTriggerType.PERFORMANCE_DECLINE:
                actions.append(self._action_for_performance_decline(trigger, current_state))

        # Sort by priority
        actions.sort(key=lambda x: x.priority, reverse=True)

        return actions

    def _action_for_consecutive_errors(
        self,
        trigger: RevisionTrigger,
        current_state: Dict[str, Any]
    ) -> RevisionActionPlan:
        """Generate action for consecutive incorrect predictions"""
        consecutive_count = trigger.evidence.get('consecutive_incorrect', 0)

        # Increase caution significantly
        current_confidence_multiplier = current_state.get('confidence_multiplier', 1.0)
        reduction = min(0.3, consecutive_count * 0.05)
        new_multiplier = max(0.5, current_confidence_multiplier - reduction)

        return RevisionActionPlan(
            action=RevisionAction.ADJUST_CONFIDENCE_THRESHOLD,
            parameters={
                'confidence_multiplier': new_multiplier,
                'reduction_amount': reduction,
                'reason': 'consecutive_errors'
            },
            rationale=f"Reduce confidence by {reduction:.1%} due to {consecutive_count} consecutive errors",
            expected_impact=trigger.severity * 0.7,
            priority=5
        )

    def _action_for_confidence_misalignment(
        self,
        trigger: RevisionTrigger,
        current_state: Dict[str, Any]
    ) -> RevisionActionPlan:
        """Generate action for confidence misalignment"""
        error_count = trigger.evidence.get('error_count', 0)
        avg_gap = trigger.evidence.get('avg_confidence_gap', 0)

        # Recalibrate confidence calculation
        current_threshold = current_state.get('high_confidence_threshold', 0.75)
        new_threshold = min(0.85, current_threshold + 0.1)

        return RevisionActionPlan(
            action=RevisionAction.ADJUST_CONFIDENCE_THRESHOLD,
            parameters={
                'high_confidence_threshold': new_threshold,
                'confidence_penalty': 0.15,
                'recalibration_window': 5
            },
            rationale=f"Increase confidence threshold to {new_threshold:.2f} due to {error_count} overconfident errors",
            expected_impact=trigger.severity * 0.6,
            priority=4
        )

    def _action_for_pattern_repetition(
        self,
        trigger: RevisionTrigger,
        current_state: Dict[str, Any]
    ) -> RevisionActionPlan:
        """Generate action for repeated pattern mistakes"""
        pattern_type = trigger.evidence.get('pattern_type', 'unknown')
        occurrences = trigger.evidence.get('occurrences', 0)

        # Adjust factor weights based on pattern
        weight_adjustments = self._get_weight_adjustments_for_pattern(pattern_type)

        return RevisionActionPlan(
            action=RevisionAction.CHANGE_FACTOR_WEIGHTS,
            parameters={
                'weight_adjustments': weight_adjustments,
                'pattern_detected': pattern_type,
                'learning_rate': 0.2
            },
            rationale=f"Adjust weights to counteract {pattern_type} pattern ({occurrences} occurrences)",
            expected_impact=trigger.severity * 0.8,
            priority=5
        )

    def _action_for_performance_decline(
        self,
        trigger: RevisionTrigger,
        current_state: Dict[str, Any]
    ) -> RevisionActionPlan:
        """Generate action for overall performance decline"""
        decline = trigger.evidence.get('decline', 0)

        return RevisionActionPlan(
            action=RevisionAction.UPDATE_STRATEGY,
            parameters={
                'strategy_shift': 'conservative',
                'analysis_depth': 'increased',
                'factor_consideration': 'expanded',
                'recalibration_needed': True
            },
            rationale=f"Shift to conservative strategy due to {decline:.1%} performance decline",
            expected_impact=trigger.severity * 0.7,
            priority=3
        )

    def _get_weight_adjustments_for_pattern(self, pattern_type: str) -> Dict[str, float]:
        """Get factor weight adjustments for specific error patterns"""
        adjustments = {}

        if pattern_type == "overconfident_error":
            adjustments = {
                'historical_performance': +0.15,
                'gut_instinct': -0.15,
                'recent_form': +0.10
            }
        elif pattern_type == "direction_reversal_error":
            adjustments = {
                'matchup_analysis': +0.20,
                'situational_factors': +0.15,
                'momentum': -0.10
            }
        elif pattern_type == "large_margin_error":
            adjustments = {
                'defensive_ratings': +0.15,
                'scoring_variance': +0.10,
                'blowout_tendency': -0.15
            }
        elif pattern_type == "uncertain_prediction_error":
            adjustments = {
                'confidence_floor': +0.10,
                'data_quality_weight': +0.15
            }

        return adjustments

    async def store_revision(
        self,
        revision: BeliefRevisionRecord
    ) -> bool:
        """Store belief revision record in Supabase"""
        try:
            revision_data = {
                'revision_id': revision.revision_id,
                'expert_id': revision.expert_id,
                'trigger_type': revision.trigger.trigger_type.value,
                'trigger_severity': revision.trigger.severity,
                'trigger_evidence': json.dumps(revision.trigger.evidence),
                'trigger_description': revision.trigger.description,
                'actions_taken': json.dumps([{
                    'action': a.action.value,
                    'parameters': a.parameters,
                    'rationale': a.rationale,
                    'expected_impact': a.expected_impact,
                    'priority': a.priority
                } for a in revision.actions]),
                'pre_revision_state': json.dumps(revision.pre_revision_state),
                'post_revision_state': json.dumps(revision.post_revision_state),
                'effectiveness_score': revision.effectiveness_score
            }

            result = self.supabase.table('expert_belief_revisions').insert(revision_data).execute()

            if result.data:
                logger.info(f"✅ Stored belief revision for expert {revision.expert_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Failed to store belief revision: {e}")
            return False

    async def retrieve_revisions(
        self,
        expert_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve recent belief revisions for an expert"""
        try:
            result = self.supabase.table('expert_belief_revisions') \
                .select('*') \
                .eq('expert_id', expert_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"❌ Failed to retrieve revisions: {e}")
            return []

    async def measure_revision_effectiveness(
        self,
        revision_id: str,
        post_revision_predictions: List[Dict[str, Any]],
        window_size: int = 5
    ) -> float:
        """
        Measure effectiveness of a revision by comparing performance after

        Args:
            revision_id: ID of revision to measure
            post_revision_predictions: Predictions made after revision
            window_size: Number of predictions to evaluate

        Returns:
            Effectiveness score (0-1)
        """
        if len(post_revision_predictions) < window_size:
            return 0.0  # Not enough data yet

        recent = post_revision_predictions[:window_size]
        accuracy = sum(1 for p in recent if p.get('was_correct', False)) / len(recent)

        # Score based on improvement from baseline
        baseline = 0.55  # Expected baseline accuracy
        effectiveness = min(1.0, max(0.0, (accuracy - baseline) / (1.0 - baseline)))

        # Update the revision record
        try:
            self.supabase.table('expert_belief_revisions') \
                .update({'effectiveness_score': effectiveness}) \
                .eq('revision_id', revision_id) \
                .execute()
        except Exception as e:
            logger.error(f"❌ Failed to update effectiveness score: {e}")

        return effectiveness